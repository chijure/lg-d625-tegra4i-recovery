"""Extract the version-pinned T148 miniloader without executing nvflash."""
import argparse
import hashlib
import pathlib

import pefile

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXPECTED_EXE = '000fa264d6614a1d3490b81c0e8fba5a72b0f70e74ca8141e108229dc7fab466'
EXPECTED_LOADER = '5dc183e08aafc6e8e3a55b29738ac4bbe049ea15159ff872b0a6ef74bca7f6d5'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('nvflash', type=pathlib.Path)
    args = parser.parse_args()
    source = args.nvflash.read_bytes()
    if hashlib.sha256(source).hexdigest() != EXPECTED_EXE:
        raise ValueError('nvflash.exe is not the reviewed 4.10.1800 input')
    pe = pefile.PE(data=source)
    if pe.OPTIONAL_HEADER.ImageBase != 0x400000 or pe.get_data(0xC2DD, 4) != bytes.fromhex('837dec14'):
        raise ValueError('T148 selector does not match')
    data = pe.get_data(0x708B8, 0x10620)
    if len(data) != 67104 or hashlib.sha256(data).hexdigest() != EXPECTED_LOADER:
        raise ValueError('Extracted T148 input does not match')
    target = ROOT / 'vendor/t148_nvflash_miniloader.bin'
    if target.exists() and target.read_bytes() != data:
        raise ValueError('Existing vendor input differs; refusing to overwrite')
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(data)
    print(f'Extracted and verified: {target.name} ({len(data)} bytes)')


if __name__ == '__main__':
    main()
