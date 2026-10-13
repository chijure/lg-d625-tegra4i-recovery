"""Read and restore reviewed ranges through the running ARMv4T miniloader."""
import argparse
import hashlib
import pathlib
import struct
import time

import libusb_package
import usb.util


class NV3P:
    def __init__(self):
        self.device = libusb_package.find(idVendor=0x0955, idProduct=0x7714)
        if self.device is None:
            raise RuntimeError('APX device is not connected')
        usb.util.claim_interface(self.device, 0)
        self.pending = bytearray()
        self.sequence = 0

    def close(self):
        usb.util.dispose_resources(self.device)

    def exact(self, count):
        while len(self.pending) < count:
            chunk = bytes(self.device.read(0x81, 4096, timeout=10000))
            if not chunk:
                raise RuntimeError('Empty USB response')
            self.pending += chunk
        result = bytes(self.pending[:count])
        del self.pending[:count]
        return result

    def send(self, kind, payload=b'', sequence=None):
        if sequence is None:
            sequence = self.sequence
            self.sequence += 1
        packet = struct.pack('<III', 1, kind, sequence) + payload
        packet += struct.pack('<I', (-sum(packet)) & 0xFFFFFFFF)
        sent = self.device.write(0x01, packet, timeout=10000)
        if sent != len(packet):
            raise RuntimeError('Truncated USB write')

    def receive(self):
        header = self.exact(12)
        version, kind, sequence = struct.unpack('<III', header)
        if version != 1:
            raise RuntimeError(f'Unexpected protocol version {version}')
        if kind == 2:
            length = self.exact(4)
            size, = struct.unpack('<I', length)
            if not 0 < size <= 4096:
                raise RuntimeError(f'Unexpected DATA size {size}')
            payload = self.exact(size)
            prefix = header + length + payload
        elif kind == 4:
            payload = b''
            prefix = header
        elif kind == 5:
            payload = self.exact(4)
            prefix = header + payload
        else:
            raise RuntimeError(f'Unexpected packet type {kind}')
        checksum, = struct.unpack('<I', self.exact(4))
        if ((sum(prefix) + checksum) & 0xFFFFFFFF) != 0:
            raise RuntimeError('Response checksum mismatch')
        if kind == 5:
            raise RuntimeError(f'Device NACK {struct.unpack("<I", payload)[0]:#x}')
        return kind, sequence, payload

    def ack(self):
        kind, _, _ = self.receive()
        if kind != 4:
            raise RuntimeError(f'Expected ACK, got type {kind}')

    def read(self, sector, count, filename):
        if not 0 <= sector < 0x10000000 or not 1 <= count <= 2048:
            raise ValueError('Read range out of bounds')
        self.send(1, struct.pack('<II', 0, 0))  # zero args; custom opcode 0.
        self.ack()
        metadata = struct.pack('<II', sector, count)
        self.send(2, struct.pack('<I', len(metadata)) + metadata)
        self.ack()
        started = time.monotonic()
        with pathlib.Path(filename).open('xb') as destination:
            for index in range(count):
                kind, sequence, payload = self.receive()
                if kind != 2 or len(payload) != 512:
                    raise RuntimeError('Expected one 512-byte DATA packet')
                destination.write(payload)
                self.send(4, sequence=sequence)
                if (index + 1) % 128 == 0 or index + 1 == count:
                    print(f'{index + 1}/{count} sectors; {time.monotonic() - started:.1f}s', flush=True)

    def write_verified(self, sector, payload):
        root = pathlib.Path(__file__).resolve().parent.parent
        if sector == 4096:
            before = (root / 'private/backups/scratch-sector4096-before.bin').read_bytes()
            allowed = len(payload) == 512 and payload in (before, bytes(range(256)) * 2)
        elif sector == 12288:
            allowed = (payload == (root / 'private/backups/bootloader-original.bin').read_bytes()
                       and hashlib.sha256(payload).hexdigest() == '10bc066b7f99256f87b05e82b5087c5c6f815a3e865dc094169176fcc69706f7')
        elif sector == 128:
            allowed = (payload == (root / 'private/backups/bct-original-60-slots.bin').read_bytes()
                       and hashlib.sha256(payload).hexdigest() == '1771092fc30b1ec43921eab3784f32c649afedd817cc248776d4a0adc7976107')
        else:
            allowed = False
        if not allowed:
            raise ValueError('Write does not match a reviewed recovery target and exact source bytes')
        count = len(payload) // 512
        self.send(1, struct.pack('<II', 0, 5))
        self.ack()
        metadata = struct.pack('<II', sector, count)
        self.send(2, struct.pack('<I', 8) + metadata)
        self.ack()
        started = time.monotonic()
        for index in range(count):
            expected = payload[index * 512:(index + 1) * 512]
            self.send(2, struct.pack('<I', 512) + expected)
            self.ack()  # Received by device; write completion is below.
            kind, sequence, actual = self.receive()
            if kind != 2 or actual != expected:
                self.send(5, struct.pack('<I', 3), sequence=sequence)
                raise RuntimeError(f'Write readback mismatch at sector {sector + index}; stopped')
            self.send(4, sequence=sequence)
            if (index + 1) % 128 == 0 or index + 1 == count:
                print(f'{index + 1}/{count} sectors written and readback verified; {time.monotonic() - started:.1f}s', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('sector', type=lambda value: int(value, 0))
    parser.add_argument('count', type=int)
    parser.add_argument('output')
    parser.add_argument('--write-verified', action='store_true')
    args = parser.parse_args()
    connection = NV3P()
    try:
        if args.write_verified:
            payload = pathlib.Path(args.output).read_bytes()
            if len(payload) != args.count * 512:
                raise ValueError('File size does not match sector count')
            connection.write_verified(args.sector, payload)
        else:
            connection.read(args.sector, args.count, args.output)
    finally:
        connection.close()


if __name__ == '__main__':
    main()
