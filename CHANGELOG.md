# Changelog

## recovery-v0.1.0 — 2026-10-13

- LG D625 normal Android boot restored and confirmed by its owner.
- ARMv4T payload placement corrected to avoid startup BSS zeroing.
- Native eMMC initialization, partition mapping, reads and bounded writes.
- Every written sector verified through a separate readback buffer.
- RBL and all 60 BCT slots restored; BCT/RBL/EBT verified in full.
- Public source package and private research archive prepared.
- Bootloader unlocking remains a separate research task.
