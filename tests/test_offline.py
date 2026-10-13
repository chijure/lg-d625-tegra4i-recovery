"""Offline checks only: no real USB discovery, claim, read or write."""
import hashlib
import json
import pathlib
import struct
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'payload'))
sys.path.insert(0, str(ROOT / 'utils'))
from layout import SOURCE, legacy_bl
from build_protocol_probe import Thumb1Code
from nv3p import NV3P


class FakeUSB:
    def __init__(self, chunks):
        self.chunks = list(chunks)

    def read(self, endpoint, size, timeout):
        return self.chunks.pop(0)


class OfflineTests(unittest.TestCase):
    def test_legacy_bl_matches_original_compiler_instruction(self):
        self.assertEqual(legacy_bl(0x4001D622, 0x4001C130), bytes.fromhex('fef785fd'))
        with self.assertRaises(ValueError):
            legacy_bl(0x40000000, 0x41000000)

    def test_indirect_jump_literal_alignment(self):
        for address in (0x1000, 0x1002):
            code = Thumb1Code(address)
            code.jump(0x40028000)
            data = code.finish()
            literal_offset = ((address + 7) & ~3) - address
            self.assertEqual(struct.unpack_from('<I', data, literal_offset)[0], 0x40028001)
            self.assertEqual(struct.unpack_from('<H', data, 2)[0], 0x4718)

    def test_nv3p_buffered_response_and_checksum(self):
        header = struct.pack('<III', 1, 2, 17)
        payload = bytes(range(256)) * 2
        packet = header + struct.pack('<I', 512) + payload
        packet += struct.pack('<I', (-sum(packet)) & 0xFFFFFFFF)
        client = object.__new__(NV3P)
        client.device = FakeUSB([packet[:7], packet[7:16], packet[16:200], packet[200:]])
        client.pending = bytearray()
        self.assertEqual(client.receive(), (2, 17, payload))

    def test_bad_checksum_is_rejected(self):
        client = object.__new__(NV3P)
        client.device = FakeUSB([struct.pack('<IIII', 1, 4, 0, 0)])
        client.pending = bytearray()
        with self.assertRaisesRegex(RuntimeError, 'checksum'):
            client.receive()

    def test_unreviewed_write_is_rejected_before_usb_access(self):
        client = object.__new__(NV3P)
        with self.assertRaises(ValueError):
            client.write_verified(0, bytes(512))

    @unittest.skipUnless(SOURCE.exists(), 'Local vendor input is deliberately not published')
    def test_payload_reproduces_hardware_tested_baseline(self):
        from build_recovery_loader import build
        image = build()
        expected = json.loads((ROOT / 'evidence/payload.json').read_text())
        self.assertEqual(len(image), expected['recovery_bytes'])
        self.assertEqual(hashlib.sha256(image).hexdigest(), expected['recovery_sha256'])
        original = SOURCE.read_bytes()
        differences = [i for i, (a, b) in enumerate(zip(original, image)) if a != b]
        self.assertTrue(differences)
        self.assertTrue(all(0xF6D0 <= index < 0xF6DA for index in differences))


if __name__ == '__main__':
    unittest.main()
