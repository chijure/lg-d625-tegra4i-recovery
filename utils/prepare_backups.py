"""Validate local original images and extract recovery inputs, offline."""
import argparse
import hashlib
import pathlib

from Crypto.Cipher import AES
from Crypto.Hash import CMAC

ROOT = pathlib.Path(__file__).resolve().parent.parent


def save(target, data):
    if target.exists() and target.read_bytes() != data:
        raise ValueError(f'Existing backup differs: {target.name}')
    target.write_bytes(data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('bct_raw_dump', type=pathlib.Path)
    parser.add_argument('stock_bootloader', type=pathlib.Path)
    args = parser.parse_args()
    raw = args.bct_raw_dump.read_bytes()
    bootloader = args.stock_bootloader.read_bytes()
    digest = lambda data: hashlib.sha256(data).hexdigest()
    if len(raw) != 4194304 or digest(raw) != '0f44cee2f99c37ee1f5b55768c33f60e129ef9017aa4837d6c4167b79092cd1e':
        raise ValueError('Raw dump is not the reviewed original BCT backup')
    if len(bootloader) != 860160 or digest(bootloader) != '10bc066b7f99256f87b05e82b5087c5c6f815a3e865dc094169176fcc69706f7':
        raise ValueError('Bootloader is not the reviewed stock input')
    copies = [raw[offset:offset + 5424] for offset in range(0x10000, 0x100000, 0x4000)]
    if len(copies) != 60 or any(copy != copies[0] for copy in copies):
        raise ValueError('Original BCT copies are not identical')
    cmac = CMAC.new(bytes(16), ciphermod=AES)
    cmac.update(bootloader)
    if cmac.digest() != copies[0][0x1424:0x1434]:
        raise ValueError('Original BCT hash does not match the stock bootloader')
    output = ROOT / 'private/backups'
    output.mkdir(parents=True, exist_ok=True)
    save(output / 'bct-original-slot.cfg', copies[0])
    save(output / 'bct-original-60-slots.bin', raw[0x10000:0x100000])
    save(output / 'bootloader-original.bin', bootloader)
    print('Originals validated: 60 BCT copies and matching stock bootloader')


if __name__ == '__main__':
    main()
