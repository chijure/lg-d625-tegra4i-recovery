"""ARMv4T RAM-only protocol probe: receive metadata, send a known pattern."""
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from layout import BASE, DIRECTORY, PATCH, legacy_bl, load_pristine
from thumb1 import build_addr, cmp_imm, ldr_imm, str_imm, ldr_sp_imm, mov_imm, mov_reg, pop, push

ENTRY = 0x40028000
META = ENTRY + 0x100
DATA = ENTRY + 0x200
PATTERN = bytes(range(256)) * 2


class Thumb1Code:
    def __init__(self, address, wide=False):
        self.base = address
        self.code = bytearray()
        self.labels = {}
        self.fixups = []
        self.wide = wide

    @property
    def address(self):
        return self.base + len(self.code)

    def raw(self, code):
        self.code += code

    def call(self, target):
        self.raw(legacy_bl(self.address, target))

    def label(self, name):
        self.labels[name] = self.address

    def conditional(self, name, condition):
        width = 4 if self.wide else 2
        self.fixups.append((len(self.code), name, condition, width))
        self.raw(bytes(width))

    def branch(self, name):
        self.fixups.append((len(self.code), name, None, 2))
        self.raw(bytes(2))

    def jump(self, target):
        address = self.address
        literal = (address + 7) & ~3
        pc = (address + 4) & ~3
        self.raw(struct.pack('<HH', 0x4B00 | ((literal - pc) // 4), 0x4718))
        while self.address < literal:
            self.raw(struct.pack('<H', 0x46C0))
        self.raw(struct.pack('<I', target | 1))

    def finish(self):
        for offset, name, condition, width in self.fixups:
            difference = self.labels[name] - (self.base + offset + 4)
            assert difference % 2 == 0
            if condition is None:
                assert -2048 <= difference <= 2046
                self.code[offset:offset + 2] = struct.pack('<H', 0xE000 | ((difference // 2) & 0x7FF))
            elif width == 4:
                difference -= 2
                assert -2048 <= difference <= 2046
                self.code[offset:offset + 4] = struct.pack('<HH', 0xD000 | ((condition ^ 1) << 8),
                                                         0xE000 | ((difference // 2) & 0x7FF))
            else:
                assert -256 <= difference <= 254
                self.code[offset:offset + 2] = struct.pack('<H', 0xD000 | (condition << 8) | ((difference // 2) & 0xFF))
        return bytes(self.code)


def build(snapshot=False, initialize=False, read=False, entry=None):
    ENTRY = entry if entry is not None else globals()['ENTRY']
    assert not initialize or snapshot or read
    pristine = load_pristine()
    meta = ENTRY + 0x400 if snapshot or read else META
    data = ENTRY + 0x600 if snapshot or read else DATA
    code = Thumb1Code(ENTRY, wide=initialize)
    code.raw(ldr_sp_imm(0, 0x4C // 4))
    saved_registers = [4, 5, 6, 7] if read else [4, 5, 6]
    code.raw(push(saved_registers + ['lr']))
    code.raw(mov_reg(4, 0))
    code.call(0x40012916)  # Native command ACK.
    code.raw(cmp_imm(0, 0))
    code.conditional('cleanup', 1)
    code.raw(mov_reg(0, 4))
    code.raw(build_addr(1, meta))
    code.raw(mov_imm(2, 8))
    code.raw(mov_imm(3, 0))  # Optional received-length pointer = NULL.
    code.call(0x40012950)  # Native DATA receive, including checksum and ACK.
    code.raw(cmp_imm(0, 0))
    code.conditional('cleanup', 1)
    code.raw(build_addr(1, meta))
    code.raw(ldr_imm(0, 1, 1))
    if read:
        code.raw(cmp_imm(0, 0))
        code.conditional('reject', 0)
        code.raw(build_addr(1, 2048))
        code.raw(struct.pack('<H', 0x4288))  # cmp r0,r1: up to 1MiB.
        code.conditional('reject', 8)  # unsigned higher.
    else:
        code.raw(cmp_imm(0, 1))  # Diagnostic snapshots support one sector.
        code.conditional('reject', 1)
    if initialize:
        # Original storage-table setup: device index 4 (eMMC), config 0x11.
        # This runs the native card/controller initialization, not BCT parsing.
        code.raw(build_addr(0, ENTRY + 0x1000))
        code.raw(mov_imm(1, 4))
        code.raw(mov_imm(2, 0x11))
        code.call(0x4001CA74)
        code.raw(build_addr(1, data + 0xF0))
        code.raw(str_imm(0, 1, 0))
        code.raw(build_addr(0, data + 0x180))
        code.raw(build_addr(1, ENTRY + 0x1000))
        code.raw(mov_imm(2, 32))
        code.call(0x4001054E)
    if read:
        code.raw(build_addr(1, data + 0xF0))
        code.raw(ldr_imm(0, 1, 0))
        code.raw(cmp_imm(0, 0))
        code.conditional('reject', 1)
        code.raw(build_addr(2, meta))
        code.raw(ldr_imm(6, 2, 0))
        code.raw(ldr_imm(7, 2, 1))
        code.label('sector_loop')
        code.raw(mov_reg(0, 6))
        code.raw(mov_reg(1, 0))
        code.raw(struct.pack('<H', 0x0940))  # lsrs r0,r0,#5: 16KiB block index.
        code.raw(mov_imm(2, 31))
        code.raw(struct.pack('<H', 0x4011))  # ands r1,r2: page within block.
        code.raw(build_addr(2, data))
        code.call(0x4000F5B4)  # Native eMMC page read, 512-byte page config.
        code.raw(cmp_imm(0, 0))
        code.conditional('reject', 1)
        code.raw(build_addr(5, 100000))
        code.label('poll')
        code.raw(struct.pack('<H', 0x3D01))  # subs r5,#1: bounded polling.
        code.conditional('reject', 0)
        code.call(0x4000EDF6)
        code.raw(cmp_imm(0, 2))  # Native state 2 = transfer pending.
        code.conditional('poll', 0)
        code.raw(cmp_imm(0, 1))  # State 1 = completed/idle; others are errors.
        code.conditional('reject', 1)
    if snapshot:
        # Snapshot only RAM and read-only SDMMC registers. No storage commands.
        code.raw(build_addr(0, data))
        code.raw(build_addr(1, 0x40000000))
        code.raw(mov_imm(2, 0x80))
        code.call(0x4001054E)
        code.raw(build_addr(0, data + 0x100))
        code.raw(build_addr(1, 0x4001DFA0))
        code.raw(mov_imm(2, 16))
        code.call(0x4001054E)
        code.raw(build_addr(1, 0x78000600))
        code.raw(build_addr(2, data + 0x120))
        for register in range(13):
            code.raw(ldr_imm(0, 1, register))
            code.raw(str_imm(0, 2, register))
    code.raw(mov_reg(0, 4))
    code.raw(build_addr(1, data))
    code.raw(mov_imm(2, 0x80))
    code.raw(struct.pack('<H', 0x0092))  # lsls r2,r2,#2 => 512.
    code.raw(mov_imm(3, 0))
    code.call(0x40012D88)  # Native DATA send, including host ACK.
    if read:
        code.raw(cmp_imm(0, 0))
        code.conditional('cleanup', 1)
        code.raw(struct.pack('<H', 0x3F01))  # subs r7,#1.
        code.conditional('cleanup', 0)
        code.raw(struct.pack('<H', 0x3601))  # adds r6,#1.
        code.branch('sector_loop')
    code.label('cleanup')
    code.raw(pop(saved_registers))
    code.raw(pop([3]))  # Discard this stub's saved LR before dispatcher tail.
    code.jump(0x4001D5CC)
    code.label('reject')
    code.raw(mov_reg(0, 4))
    code.raw(mov_imm(1, 3))
    code.call(0x400128CA)
    code.branch('cleanup')
    instructions = code.finish()
    assert len(instructions) < (meta - ENTRY)
    end = ENTRY + 0x1040 if initialize else data + 512
    result = bytearray(pristine + bytes(end - (BASE + len(pristine))))
    result[ENTRY - BASE:ENTRY - BASE + len(instructions)] = instructions
    result[data - BASE:data - BASE + 512] = bytes(512) if snapshot or read else PATTERN
    result[PATCH - BASE:PATCH - BASE + 10] = struct.pack('<HHIH', 0x4B00, 0x4718, ENTRY | 1, 0x46C0)
    name = 'READPROBE' if read else ('INIT_SNAPSHOT' if initialize else ('SNAPSHOT' if snapshot else 'PROTOCOLPROBE'))
    output = DIRECTORY / f't148_nvflash_miniloader_ARMV4_{name}.bin'
    output.write_bytes(result)
    print(f'{output.name}: {len(result)} bytes; code={len(instructions)} bytes')
    return bytes(result)


if __name__ == '__main__':
    build(snapshot='--snapshot' in sys.argv or '--initialize' in sys.argv,
          initialize='--initialize' in sys.argv or '--read' in sys.argv,
          read='--read' in sys.argv)
