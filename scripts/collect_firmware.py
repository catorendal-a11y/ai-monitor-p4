"""Collect a matched board-specific firmware pair after a successful build."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from board_profiles import BOARDS
from firmware_layout import validate_factory


def collect(environment, output):
    board = next((item for item in BOARDS.values() if item.environment == environment), None)
    if board is None: raise ValueError('Unknown firmware build target')
    build = ROOT / '.pio/build-fw' / environment
    factory = max(build.glob('fw_*.factory.bin'), key=lambda path: path.stat().st_mtime)
    application = factory.with_name(factory.name.replace('.factory.bin', '.bin'))
    version = re.search(r'#define FW_VERSION "([^"]+)"', (ROOT/'src/config.h').read_text()).group(1)
    if version.encode() not in application.read_bytes(): raise ValueError('Application does not match current firmware version')
    validate_factory(factory.read_bytes(), application.read_bytes(), board)
    folder = output / board.id
    folder.mkdir(parents=True, exist_ok=True)
    files = {}
    for name, source, offset in [('application.bin', application, 0x10000), ('factory.bin', factory, 0)]:
        shutil.copy2(source, folder / name)
        data = source.read_bytes()
        files[name] = {'bytes':len(data), 'sha256':hashlib.sha256(data).hexdigest(), 'offset':offset}
    record = {'board':board.name, 'chip':board.chip, 'experimental':board.experimental, 'files':files}
    (folder/'record.json').write_text(json.dumps(record, indent=2)+'\n')
    print('Collected ' + board.name + ' (' + version + ')')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--environment', required=True, choices=[item.environment for item in BOARDS.values()])
    parser.add_argument('--output', type=Path, default=ROOT/'work/prebuilt')
    args = parser.parse_args()
    collect(args.environment, args.output.resolve())
