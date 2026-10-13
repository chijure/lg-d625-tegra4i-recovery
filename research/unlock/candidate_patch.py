#!/usr/bin/env python3
"""Patch EBT.bin (LG D625 Tegra4i bootloader) to bypass the boot-image
signature verification check, without skipping the actual verify call
(preserves any side effects the real verify routine needs).

Patch: file offset 0x12600, Thumb16 `beq #0x1263a` (1B D0) -> unconditional
`b #0x1263a` (1B E0). This is the branch that decides pass/fail right after
the streaming-verify "finalize" callback (blx r3 at 0x125dc) returns; forcing
it to always take the success path leaves the real verify call intact.

STATUS: historical offline candidate; a working D625 unlock is NOT established.
See docs/UNLOCK_RESEARCH.md. This tool never accesses the phone.
"""
import hashlib
import sys

EXPECTED_ORIG_SHA256 = '10bc066b7f99256f87b05e82b5087c5c6f815a3e865dc094169176fcc69706f7'

PATCHES = [
    (0x12600, bytes.fromhex("1be0"), bytes.fromhex("1bd0")),  # beq -> b, same target 0x1263a
]


def patch(data: bytearray) -> bytearray:
    for off, new, expected_old in PATCHES:
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
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <ebt_orig.bin> <ebt_patched.bin>")
        sys.exit(1)

    with open(sys.argv[1], "rb") as f:
        data = bytearray(f.read())

    orig_hash = hashlib.sha256(data).hexdigest()
    print(f"input SHA256:  {orig_hash}")
    if EXPECTED_ORIG_SHA256 and orig_hash != EXPECTED_ORIG_SHA256:
        raise ValueError('Input is not the verified stock bootloader')

    data = patch(data)

    with open(sys.argv[2], "wb") as f:
        f.write(data)

    print(f"output SHA256: {hashlib.sha256(data).hexdigest()}")
    print(f"wrote {sys.argv[2]}")


if __name__ == "__main__":
    main()
