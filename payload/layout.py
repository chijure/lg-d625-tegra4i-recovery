"""Version-pinned vendor input and generated-output paths."""
import hashlib
import pathlib
import struct

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = 0x4000E000
PATCH = 0x4001D6D0
DIRECTORY = ROOT / 'out'
DIRECTORY.mkdir(exist_ok=True)
SOURCE = ROOT / 'vendor/t148_nvflash_miniloader.bin'
EXPECTED_SHA256 = '5dc183e08aafc6e8e3a55b29738ac4bbe049ea15159ff872b0a6ef74bca7f6d5'


def load_pristine():
    data = SOURCE.read_bytes()
    if len(data) != 67104 or hashlib.sha256(data).hexdigest() != EXPECTED_SHA256:
        raise ValueError('Vendor miniloader does not match the reviewed T148 binary')
    return data


def legacy_bl(address, target):
    offset = target - (address + 4)
    if offset % 2 or not -(1 << 22) <= offset < (1 << 22):
        raise ValueError('Target out of ARMv4T Thumb BL range')
    return struct.pack('<HH', 0xF000 | ((offset >> 12) & 0x7FF),
                       0xF800 | ((offset >> 1) & 0x7FF))
