"""Build the reviewed payload and compare it to the hardware-tested image."""
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'payload'))
from build_recovery_loader import build


def main():
    image = build()
    expected = json.loads((ROOT / 'evidence/payload.json').read_text())
    digest = hashlib.sha256(image).hexdigest()
    if len(image) != expected['recovery_bytes'] or digest != expected['recovery_sha256']:
        raise RuntimeError('Generated image differs from the hardware-tested recovery baseline')
    print(f'Hardware-tested payload reproduced exactly: {digest}')


if __name__ == '__main__':
    main()
