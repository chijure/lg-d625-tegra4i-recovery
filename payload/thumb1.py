"""Small Thumb-1 encoders used by the verified ARMv4T payload."""

def mov_imm(rd, imm8): return bytes([imm8, 0x20 | rd])

def add_imm8(rdn, imm8): v = 0x3000 | (rdn << 8) | imm8; return bytes([v & 0xFF, v >> 8])

def lsl_imm(rd, rm, imm5): v = (imm5 << 6) | (rm << 3) | rd; return bytes([v & 0xFF, v >> 8])

def cmp_imm(rn, imm8): v = 0x2800 | (rn << 8) | imm8; return bytes([v & 0xFF, v >> 8])

def ldr_imm(rt, rn, imm5w): v = (0b01101 << 11) | (imm5w << 6) | (rn << 3) | rt; return bytes([v & 0xFF, v >> 8])

def str_imm(rt, rn, imm5w): v = (0b01100 << 11) | (imm5w << 6) | (rn << 3) | rt; return bytes([v & 0xFF, v >> 8])

def ldrb_imm(rt, rn, imm5b): v = (0b01111 << 11) | (imm5b << 6) | (rn << 3) | rt; return bytes([v & 0xFF, v >> 8])

def ldr_sp_imm(rt, imm8w): v = 0x9800 | (rt << 8) | imm8w; return bytes([v & 0xFF, v >> 8])

def mov_reg(rd, rm):
    v = 0x4600 | ((rd & 8) << 4) | (rm << 3) | (rd & 7)
    return bytes([v & 0xFF, v >> 8])

def push(regs):
    mask = 0; lr = 0
    for r in regs:
        if r == 'lr': lr = 1
        else: mask |= (1 << r)
    v = 0xB400 | (lr << 8) | mask
    return bytes([v & 0xFF, v >> 8])

def pop(regs):
    mask = 0; pc = 0
    for r in regs:
        if r == 'pc': pc = 1
        else: mask |= (1 << r)
    v = 0xBC00 | (pc << 8) | mask
    return bytes([v & 0xFF, v >> 8])

def build_addr(reg, target_addr):
    b0 = (target_addr >> 24) & 0xFF; b1 = (target_addr >> 16) & 0xFF
    b2 = (target_addr >> 8) & 0xFF; b3 = target_addr & 0xFF
    out = bytearray()
    out += mov_imm(reg, b0); out += lsl_imm(reg, reg, 8); out += add_imm8(reg, b1)
    out += lsl_imm(reg, reg, 8); out += add_imm8(reg, b2); out += lsl_imm(reg, reg, 8)
    out += add_imm8(reg, b3)
    return bytes(out)
