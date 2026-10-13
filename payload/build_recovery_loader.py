"""ARMv4T recovery loader: verified reads and bounded writes with readback.

Writes are restricted to BCT slots, RBL, and one unused diagnostic sector.
Original storage/controller helpers select the hardware partition. The only
cloned routine is CMD dispatch, with its forced read-direction bit omitted.
"""
import pathlib
import struct

import capstone

from layout import BASE, DIRECTORY, PATCH, load_pristine
from build_protocol_probe import Thumb1Code, build as build_reader
from thumb1 import (build_addr, cmp_imm, ldr_imm, ldrb_imm, ldr_sp_imm,
                             mov_imm, mov_reg, pop, push, str_imm)

SHIM = 0x40028000
READER = 0x40028200
WRITER = 0x40029400
PAYLOAD = 0x4002A000
VERIFY = 0x4002A200
META = 0x4002A400
CONTAINER = 0x4002A800
CLONE = 0x4002AC00


def emit_poll(code, prefix):
    code.raw(build_addr(5, 100000))
    code.label(prefix)
    code.raw(struct.pack('<H', 0x3D01))
    code.conditional('reject', 0)
    code.call(0x4000EDF6)
    code.raw(cmp_imm(0, 2))
    code.conditional(prefix, 0)
    code.raw(cmp_imm(0, 1))
    code.conditional('reject', 1)


def compare(code, register, value, condition, label):
    code.raw(build_addr(0, value))
    code.raw(struct.pack('<H', 0x4280 | (register << 0)))  # cmp Rn, r0.
    code.conditional(label, condition)


def build_cmd_clone(pristine):
    code = Thumb1Code(CLONE, wide=True)
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    instructions = list(decoder.disasm(pristine[0xC22:0xCE2], 0x4000EC22))
    assert sum(item.size for item in instructions) == 0xC0
    for item in instructions:
        code.label(f'original_{item.address:x}')
        if item.address in (0x4000EC4E, 0x4000EC50):
            code.raw(struct.pack('<H', 0x46C0))  # Remove RD1WT0 forcing.
        elif item.address in (0x4000EC26, 0x4000EC9A):
            register = 0 if item.address == 0x4000EC26 else 1
            literal = 0x4001DFA0 if register == 0 else 0x78000600
            code.raw(build_addr(register, literal))
        elif item.mnemonic == 'bl':
            code.call(int(item.op_str.lstrip('#'), 16))
        elif item.mnemonic in ('beq', 'bne'):
            code.conditional(f'original_{int(item.op_str.lstrip("#"), 16):x}',
                             0 if item.mnemonic == 'beq' else 1)
        elif item.mnemonic == 'b':
            target = int(item.op_str.lstrip('#'), 16)
            if target == 0x4000E944:
                code.jump(target)
            else:
                code.branch(f'original_{target:x}')
        else:
            code.raw(item.bytes)
    result = code.finish()
    assert len(result) < 0x200
    return result


def build():
    original = load_pristine()
    reader = build_reader(initialize=True, read=True, entry=READER)
    image = bytearray(reader + bytes(CLONE + 0x200 - (BASE + len(reader))))

    shim = Thumb1Code(SHIM, wide=True)
    shim.raw(ldr_sp_imm(1, 0x48 // 4))
    shim.raw(cmp_imm(1, 0))
    shim.conditional('try_write', 1)
    shim.jump(READER)
    shim.label('try_write')
    shim.raw(cmp_imm(1, 5))
    shim.conditional('fallback', 1)
    shim.jump(WRITER)
    shim.label('fallback')
    shim.raw(ldr_sp_imm(0, 0x4C // 4))
    shim.raw(mov_imm(1, 2))
    shim.call(0x400128CA)
    shim.jump(0x4001D5CC)
    shim_bytes = shim.finish()
    assert len(shim_bytes) < READER - SHIM

    code = Thumb1Code(WRITER, wide=True)
    code.raw(ldr_sp_imm(0, 0x4C // 4))
    code.raw(push([4, 5, 6, 7, 'lr']))
    code.raw(mov_reg(4, 0))
    code.call(0x40012916)
    code.raw(cmp_imm(0, 0))
    code.conditional('cleanup', 1)
    code.raw(mov_reg(0, 4))
    code.raw(build_addr(1, META))
    code.raw(mov_imm(2, 8))
    code.raw(mov_imm(3, 0))
    code.call(0x40012950)
    code.raw(cmp_imm(0, 0))
    code.conditional('cleanup', 1)
    code.raw(build_addr(2, META))
    code.raw(ldr_imm(6, 2, 0))
    code.raw(ldr_imm(7, 2, 1))
    code.raw(cmp_imm(7, 0))
    code.conditional('reject', 0)
    compare(code, 7, 2048, 8, 'reject')  # unsigned count > limit.
    # Check whole requested range before receiving or writing any sector.
    compare(code, 6, 4096, 1, 'try_bct')
    code.raw(cmp_imm(7, 1))
    code.conditional('reject', 1)
    code.branch('initialize')
    code.label('try_bct')
    compare(code, 6, 128, 3, 'reject')  # unsigned sector < BCT start.
    compare(code, 6, 2048, 2, 'try_rbl')  # unsigned sector >= BCT end.
    code.raw(struct.pack('<H', 0x19F1))  # adds r1,r6,r7: range end.
    compare(code, 1, 2048, 8, 'reject')
    code.branch('initialize')
    code.label('try_rbl')
    compare(code, 6, 12288, 3, 'reject')
    compare(code, 6, 13968, 2, 'reject')
    code.raw(struct.pack('<H', 0x19F1))
    compare(code, 1, 13968, 8, 'reject')
    code.label('initialize')
    code.raw(build_addr(0, CONTAINER))
    code.raw(mov_imm(1, 4))
    code.raw(mov_imm(2, 0x11))
    code.call(0x4001CA74)
    code.raw(cmp_imm(0, 0))
    code.conditional('reject', 1)
    code.label('sector')
    code.raw(mov_reg(0, 4))
    code.raw(build_addr(1, PAYLOAD))
    code.raw(mov_imm(2, 0x80))
    code.raw(struct.pack('<H', 0x0092))
    code.raw(mov_imm(3, 0))
    code.call(0x40012950)  # Payload ACK means received, not written.
    code.raw(cmp_imm(0, 0))
    code.conditional('cleanup', 1)

    # Same native hardware-partition selection as the original page reader.
    code.raw(mov_reg(0, 6))
    code.raw(struct.pack('<H', 0x0940))  # lsrs r0,r0,#5.
    code.raw(build_addr(2, META + 8))
    code.raw(str_imm(0, 2, 0))
    code.raw(mov_reg(1, 6))
    code.raw(mov_imm(0, 31))
    code.raw(struct.pack('<H', 0x4001))  # ands r1,r0.
    code.raw(str_imm(1, 2, 1))
    code.raw(mov_reg(0, 2))
    code.raw(build_addr(1, META + 12))
    code.call(0x4000F794)
    code.raw(cmp_imm(0, 0))
    code.conditional('reject', 1)

    code.raw(build_addr(2, META + 8))
    code.raw(ldr_imm(0, 2, 0))
    code.raw(struct.pack('<H', 0x0140))  # lsls r0,r0,#5.
    code.raw(ldr_imm(1, 2, 1))
    code.raw(struct.pack('<H', 0x1840))  # adds r0,r0,r1.
    code.raw(mov_reg(5, 0))  # Physical card address after partition mapping.
    code.raw(build_addr(0, 0x4001DFA0))
    code.raw(ldr_imm(0, 0, 1))
    code.raw(struct.pack('<H', 0x3020))  # adds r0,#0x20.
    code.raw(ldrb_imm(0, 0, 6))  # High-capacity/addressing flag at +0x26.
    code.raw(cmp_imm(0, 0))
    code.conditional('block_addressed', 1)
    code.raw(struct.pack('<H', 0x026D))  # lsls r5,r5,#9 for byte addressing.
    code.label('block_addressed')
    code.raw(build_addr(0, 0x78000600))
    code.raw(build_addr(1, PAYLOAD))
    code.raw(str_imm(1, 0, 0))
    code.raw(mov_imm(0, 0x80))
    code.raw(struct.pack('<H', 0x0080))  # lsls r0,r0,#2.
    code.raw(mov_imm(1, 1))
    code.call(0x4000F780)
    code.raw(mov_imm(0, 24))
    code.raw(mov_reg(1, 5))
    code.raw(mov_imm(2, 1))
    code.raw(mov_imm(3, 1))
    code.call(CLONE)  # CMD24: original command logic with write direction.
    code.raw(cmp_imm(0, 0))
    code.conditional('reject', 1)
    code.raw(mov_imm(0, 24))
    code.raw(mov_imm(1, 0))
    code.call(0x4000ED68)
    code.raw(cmp_imm(0, 0))
    code.conditional('reject', 1)
    code.raw(build_addr(0, 0x4001DFA0))
    code.raw(ldr_imm(5, 0, 1))
    code.raw(mov_imm(0, 2))
    code.raw(str_imm(0, 5, 7))  # Native context transfer state +0x1c.
    code.call(0x4001B69E)
    code.raw(str_imm(0, 5, 8))  # Native timeout timestamp +0x20.
    code.raw(build_addr(0, 0x454))
    code.raw(struct.pack('<H', 0x1828))  # adds r0,r5,r0.
    code.raw(build_addr(1, PAYLOAD))
    code.raw(str_imm(1, 0, 0))  # Native DMA-buffer context pointer.
    emit_poll(code, 'write_poll')

    # Read the same logical sector into a separate buffer. The host must
    # compare these bytes and ACK them before the next sector can be written.
    code.raw(mov_reg(0, 6))
    code.raw(mov_reg(1, 6))
    code.raw(struct.pack('<H', 0x0940))
    code.raw(mov_imm(2, 31))
    code.raw(struct.pack('<H', 0x4011))
    code.raw(build_addr(2, VERIFY))
    code.call(0x4000F5B4)
    code.raw(cmp_imm(0, 0))
    code.conditional('reject', 1)
    emit_poll(code, 'readback_poll')
    code.raw(mov_reg(0, 4))
    code.raw(build_addr(1, VERIFY))
    code.raw(mov_imm(2, 0x80))
    code.raw(struct.pack('<H', 0x0092))
    code.raw(mov_imm(3, 0))
    code.call(0x40012D88)
    code.raw(cmp_imm(0, 0))
    code.conditional('cleanup', 1)
    code.raw(struct.pack('<H', 0x3F01))
    code.conditional('cleanup', 0)
    code.raw(struct.pack('<H', 0x3601))
    code.branch('sector')
    code.label('cleanup')
    code.raw(pop([4, 5, 6, 7]))
    code.raw(pop([3]))
    code.jump(0x4001D5CC)
    code.label('reject')
    code.raw(mov_reg(0, 4))
    code.raw(mov_imm(1, 3))
    code.call(0x400128CA)
    code.branch('cleanup')
    writer_bytes = code.finish()
    assert len(writer_bytes) < PAYLOAD - WRITER
    clone_bytes = build_cmd_clone(original)

    for address, contents in ((SHIM, shim_bytes), (WRITER, writer_bytes), (CLONE, clone_bytes)):
        image[address - BASE:address - BASE + len(contents)] = contents
    image[PATCH - BASE:PATCH - BASE + 10] = struct.pack('<HHIH', 0x4B00, 0x4718, SHIM | 1, 0x46C0)
    output = DIRECTORY / 't148_nvflash_miniloader_ARMV4_RECOVERY.bin'
    output.write_bytes(image)
    print(f'{output.name}: {len(image)} bytes; writer={len(writer_bytes)}, clone={len(clone_bytes)}')
    return bytes(image)


if __name__ == '__main__':
    build()
