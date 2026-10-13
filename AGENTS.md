# Working on this repository

The recovery baseline is hardware verified and Android boot is confirmed.
Read README.md, docs/VERIFIED_RESULTS.md and docs/UNLOCK_RESEARCH.md first.
Keep the recovery-v0.1.0 tag intact when investigating bootloader unlocking.

Offline validation must not call USB tools or flash a device. Tests can build
the payload against local ignored vendor inputs and compare the recorded hash.
Use ARMv4T/Thumb-1 for AVP code; never place executable code in the native BSS
zero range. Preserve the proven RAM layout and native partition mapping.

Do not commit private dumps, PCAPs, executables, paths identifying the owner,
or the original full session history. They belong in the separate private
archive. The historical unlock candidate is not a confirmed working unlock.
