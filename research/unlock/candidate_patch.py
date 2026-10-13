#!/usr/bin/env python3
"""Patch EBT.bin (LG D625 Tegra4i bootloader) to bypass the boot-image
signature verification check, without skipping the actual verify call
(preserves any side effects the real verify routine needs).

Patch: live file offset 0x125e4, Thumb16 BEQ (1B D0) -> unconditional
B (1B E0), preserving the destination. The staging/USP file has a 0x1c-byte
prefix; its historical offset 0x12600 must not be used on this live backup.
This is the branch that decides pass/fail after
the streaming-verify "finalize" callback returns; forcing
it to always take the success path leaves the real verify call intact.

Variant v2 additionally replaces the wrapper's CBZ with a branch to the
same success continuation at live offset 0xec5e (88 B1 -> 11 E0).
See docs/UNLOCK_RESEARCH.md for hardware validation and limitations.
This tool never accesses the phone.
"""
import hashlib
import argparse

EXPECTED_ORIG_SHA256 = '10bc066b7f99256f87b05e82b5087c5c6f815a3e865dc094169176fcc69706f7'

PATCHES = [
    (0x125e4, bytes.fromhex("1be0"), bytes.fromhex("1bd0")),  # beq -> b, same target
]


def patch(data: bytearray, variant: str = 'v1') -> bytearray:
    if variant not in ('v1', 'v2'):
        raise ValueError('Unknown variant')
    patches = PATCHES + ([(0xec5e, bytes.fromhex('11e0'), bytes.fromhex('88b1'))] if variant == 'v2' else [])
    for off, new, expected_old in patches:
        old = bytes(data[off:off + len(new)])
        if old != expected_old:
            raise ValueError(
                f"Unexpected bytes at offset {hex(off)}: found {old.hex()}, "
                f"expected {expected_old.hex()} — refusing to patch a file "
                f"that doesn't match what this patch was derived from."
            )
        data[off:off + len(new)] = new
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    parser.add_argument('output')
    parser.add_argument('--variant', choices=('v1', 'v2'), default='v1')
    args = parser.parse_args()

    with open(args.input, "rb") as f:
        data = bytearray(f.read())

    orig_hash = hashlib.sha256(data).hexdigest()
    print(f"input SHA256:  {orig_hash}")
    if EXPECTED_ORIG_SHA256 and orig_hash != EXPECTED_ORIG_SHA256:
        raise ValueError('Input is not the verified stock bootloader')

    data = patch(data, args.variant)

    with open(args.output, "wb") as f:
        f.write(data)

    print(f"output SHA256: {hashlib.sha256(data).hexdigest()}")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
