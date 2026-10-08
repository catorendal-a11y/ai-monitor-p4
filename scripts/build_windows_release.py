"""Build a portable Windows ZIP from the public source and verified firmware."""
import argparse
import hashlib
from importlib import metadata
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def run(*arguments):
    subprocess.run([sys.executable, *arguments], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--firmware-dir', type=Path, required=True, help='Directory containing application.bin and factory.bin')
    parser.add_argument('--output', type=Path, default=ROOT / 'work/windows-release')
    parser.add_argument('--executables-dir', type=Path, help='Reuse executables already built from the same reviewed source')
    args = parser.parse_args()
    if sys.platform != 'win32':
        parser.error('Windows executables must be built on Windows.')
    git_root = Path(subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', '--show-toplevel'], text=True).strip())
    if git_root.resolve() != ROOT.resolve():
        parser.error('Release building requires this project to be its own Git root; parent repositories are refused.')
    version = re.search(r'#define FW_VERSION "([^"]+)"', (ROOT / 'src/config.h').read_text(encoding='utf-8-sig')).group(1)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    package = output / ('ai-monitor-p4-' + version + '-windows')
    if package.exists():
        parser.error('Package directory already exists; use a new output directory.')
    package.mkdir()
    scratch = ROOT / 'work/windows-build'
    scratch.mkdir(parents=True, exist_ok=True)
    common = ['-m', 'PyInstaller', '--noconfirm', '--clean', '--onefile', '--console',
              '--distpath', str(package), '--workpath', str(scratch / 'build'), '--specpath', str(scratch)]
    if args.executables_dir:
        for name in ('AI-Monitor.exe', 'firmware-flasher.exe'):
            shutil.copy2(args.executables_dir / name, package / name)
    else:
        run(*common, '--name', 'AI-Monitor', '--paths', str(ROOT / 'tools'), '--exclude-module', 'esptool',
            str(ROOT / 'tools/aim_control.py'))
        run(*common, '--name', 'firmware-flasher', '--collect-all', 'esptool', '--collect-all', 'esp_pylib',
            str(ROOT / 'scripts/esptool_entry.py'))
    files = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files'], text=True).splitlines()
    # Export reviewed source; never recursively copy runtime/private directories.
    for name in files:
        relative = Path(name)
        if any(part in {'.git', '.pio', '.venv', '.codex', '.zcode', 'node_modules', 'work', '__pycache__', 'outputs'} for part in relative.parts):
            raise RuntimeError('Private/generated path in tracked release source')
        if relative.parts[:2] == ('tools', 'activity'):
            raise RuntimeError('Runtime activity records must not be exported')
        if relative.name in {'aim_host.json', 'auth.json', 'credentials.json', 'secrets.json', '.env'} or \
                (relative.name.startswith('.env.') and relative.name != '.env.example') or \
                relative.suffix in {'.log', '.db', '.sqlite', '.sqlite3', '.jsonl', '.lock', '.bin', '.exe', '.lnk', '.pem', '.key'}:
            raise RuntimeError('Private/generated file in tracked release source')
        target = package / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    firmware = package / 'firmware'
    firmware.mkdir()
    manifest = {'version': version, 'board': 'GUITION JC4880P433', 'chip': 'esp32p4', 'files': {}}
    for name in ('application.bin', 'factory.bin'):
        image = args.firmware_dir / name
        if not image.is_file():
            raise RuntimeError('Required prebuilt firmware is missing')
        shutil.copy2(image, firmware / name)
        manifest['files'][name] = {'sha256': hashlib.sha256(image.read_bytes()).hexdigest(), 'bytes': image.stat().st_size}
    (firmware / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    licenses = package / 'licenses'
    licenses.mkdir()
    for distribution in metadata.distributions():
        name = distribution.metadata['Name']
        directory = licenses / name
        directory.mkdir(exist_ok=True)
        copied = False
        for item in distribution.files or []:
            if item.name.lower().startswith(('license', 'copying', 'notice')):
                path = distribution.locate_file(item)
                if path.is_file():
                    target = directory / (str(item).replace('/', '_').replace('\\', '_'))
                    shutil.copy2(path, target)
                    copied = True
        info = {'name': name, 'version': distribution.version,
                'license': distribution.metadata.get('License-Expression') or distribution.metadata.get('License'),
                'source': distribution.metadata.get_all('Project-URL') or [distribution.metadata.get('Home-page')],
                'license_files_copied': copied}
        (directory / 'metadata.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
    # Preserve the interpreter license shipped with the build environment.
    python_license = Path(sys.base_prefix) / 'LICENSE.txt'
    if not python_license.exists():
        raise RuntimeError('Python runtime license missing from the build environment')
    shutil.copy2(python_license, licenses / 'Python-LICENSE.txt')
    sources = package / 'third-party-source'
    sources.mkdir()
    run('-m', 'pip', 'download', '--no-deps', '--no-binary=:all:', '--dest', str(sources), 'esptool==5.4.0')
    hashes = []
    for path in sorted(package.rglob('*')):
        if path.is_file():
            hashes.append(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.relative_to(package).as_posix())
    (package / 'SHA256SUMS.txt').write_text('\n'.join(hashes) + '\n', encoding='utf-8')
    archive = output / (package.name + '.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(package.rglob('*')):
            if path.is_file():
                bundle.write(path, package.name + '/' + path.relative_to(package).as_posix())
    print('Portable package: ' + str(archive))


if __name__ == '__main__':
    main()
