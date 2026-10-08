"""First-run setup and host controls. Also the portable Windows entry point."""
import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

import psutil
from serial.tools import list_ports
import aim_host as host
from provider_catalog import PROVIDERS, selected_providers
import base64


class SetupError(ValueError):
    """A safe, actionable error message for the setup menu."""


ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]


def local_config(root=ROOT):
    path = root / "tools/aim_host.json"
    if not path.exists():
        return dict(host.DEFAULT_CONFIG)
    try:
        config = json.loads(path.read_text(encoding="utf-8-sig"))
    except (ValueError, OSError):
        raise SetupError("Local configuration is unreadable. Repair tools/aim_host.json before setup.") from None
    if not isinstance(config, dict):
        raise SetupError("Local configuration must be a JSON object.")
    output = dict(host.DEFAULT_CONFIG, **config)
    output['providers'] = selected_providers(config, legacy=True)
    return output


def save_config(config, root=ROOT):
    directory = root / "tools"
    directory.mkdir(exist_ok=True)
    path = directory / "aim_host.json"
    descriptor, temporary = tempfile.mkstemp(prefix=".aim-config-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(config, output, indent=2)
            output.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def choose_port(current="auto", ask=input):
    ports = sorted(list_ports.comports(), key=lambda port: port.device)
    print("\nConnect the display using its USB data port.")
    for index, port in enumerate(ports, 1):
        print(f"  {index}. {port.device} - {port.description}")
    if not ports:
        print("No serial ports found. Check the cable; you can configure again later.")
    print(f"Enter a listed number, a port name, or auto. Enter keeps {current}.")
    while True:
        answer = ask("USB port: ").strip()
        if not answer:
            return current
        if answer.isdecimal():
            index = int(answer) - 1
            if 0 <= index < len(ports):
                return ports[index].device
        elif answer == "auto" or re.fullmatch(r"COM[1-9][0-9]*|/dev/[A-Za-z0-9._/-]+", answer, re.I):
            return answer
        print("Choose a listed number, COM port, /dev/... port or auto.")


def choose_providers(current, ask=input):
    keys = list(PROVIDERS)
    print('\nChoose the AI tools you want to monitor (no first-run default):')
    for index, key in enumerate(keys, 1):
        name, _, support = PROVIDERS[key]
        print(f'  {index}. {name} - {support}')
    if current:
        print('Enter keeps: ' + ', '.join(PROVIDERS[key][0] for key in current))
    while True:
        answer = ask('Provider numbers, separated by commas: ').strip()
        if not answer and current: return list(current)
        choices = [part.strip() for part in answer.split(',')]
        if choices and all(part.isdecimal() and 1 <= int(part) <= len(keys) for part in choices):
            selected = [keys[int(part) - 1] for part in choices]
            if len(set(selected)) == len(selected): return selected
        print('Select at least one provider explicitly; duplicates are not allowed.')


def configure(root=ROOT, ask=input, read_secret=getpass.getpass):
    config = local_config(root)
    config['providers'] = choose_providers(config['providers'], ask)
    config["port"] = choose_port(config["port"], ask)
    if 'codex' in config['providers']:
        print('Codex uses the existing CLI login; no key needs to be pasted.')
    key = ''
    if 'zcode' in config['providers']:
        print('ZCode quota key is optional. Enter keeps it; clear removes it. Input is hidden.')
        key = read_secret('Optional Z.AI key: ').strip()
    if key == "clear":
        config["zai_key"] = ""
    elif key:
        try:
            config["zai_key"] = host.credential(key)
        except ValueError:
            raise SetupError("The key must be a single printable token. No settings were changed.") from None
    config["zai_provider"] = "zcode"
    save_config(config, root)
    print("Saved tools/aim_host.json. Existing settings were preserved.")
    print("Use Start host next, or Install firmware if this is a new display.")


def owned_hosts(root=ROOT):
    expected = {(root / "tools/aim_host.py").resolve(), (root / "tools/aim_control.py").resolve()}
    portable = (root / "AI-Monitor.exe").resolve()
    found = []
    for process in psutil.process_iter(["pid", "cmdline", "exe"]):
        try:
            if process.pid == os.getpid():
                continue
            command = process.info.get("cmdline") or []
            if "--host" in command and process.info.get("exe") and Path(process.info["exe"]).resolve() == portable:
                found.append(process)
                continue
            for argument in command[1:]:
                if argument.endswith(("aim_host.py", "aim_control.py")) and Path(argument).is_absolute():
                    if Path(argument).resolve() in expected and (argument.endswith("aim_host.py") or "--host" in command):
                        found.append(process)
                        break
        except (psutil.Error, OSError):
            continue
    return found


def stop_host(root=ROOT):
    processes = owned_hosts(root)
    for process in processes:
        try:
            process.terminate()
        except psutil.NoSuchProcess:
            pass
    _, alive = psutil.wait_procs(processes, timeout=5)
    if alive:
        raise SetupError("Host could not stop. Close it before flashing.")
    print("Host stopped." if processes else "Host is already stopped.")


def start_host(root=ROOT):
    # Validate before replacing the running host. Never echo configuration/keys.
    config = host.load_config()
    if not config['providers']:
        raise SetupError('Choose your AI providers in First-time setup before starting the host.')
    stop_host(root)
    if getattr(sys, "frozen", False):
        command = [sys.executable, "--host"]
    else:
        python = Path(sys.executable)
        pythonw = python.with_name("pythonw.exe")
        command = [str(pythonw if os.name == "nt" and pythonw.exists() else python), str(root / "tools/aim_host.py")]
    environment = dict(os.environ)
    if getattr(sys, "frozen", False):
        # The child must keep its own extracted runtime after this menu closes.
        environment["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    process = subprocess.Popen(command, cwd=root, env=environment, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, start_new_session=os.name != "nt", creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    time.sleep(1)
    if process.poll() is not None:
        raise SetupError("Host exited during startup. Use Status and View log.")
    print("Host started in the background. You may close this window.")


def firmware_file(kind, root=ROOT):
    name = "factory.bin" if kind == "install" else "application.bin"
    path = root / "firmware" / name
    manifest_path = root / "firmware/manifest.json"
    if not path.is_file() or not manifest_path.is_file():
        raise SetupError("Prebuilt firmware is missing. Download the Windows release package or see the developer guide.")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = manifest["files"][name]["sha256"]
        if manifest["board"] != "GUITION JC4880P433" or manifest["chip"] != "esp32p4":
            raise ValueError()
        if not isinstance(expected, str) or not re.fullmatch(r"[a-f0-9]{64}", expected):
            raise ValueError()
    except (ValueError, KeyError, TypeError):
        raise SetupError("Firmware manifest is invalid.") from None
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise SetupError("Firmware checksum failed. Extract a fresh copy of the release package.")
    return path


def flash_command(kind, port, root=ROOT):
    path = firmware_file(kind, root)
    tool = root / "firmware-flasher.exe"
    command = [str(tool)] if tool.exists() else [sys.executable, "-m", "esptool"]
    if getattr(sys, "frozen", False) and not tool.exists():
        raise SetupError("Firmware flasher is missing. Extract the complete Windows package.")
    return command + ["--chip", "esp32p4", "--port", port, "--baud", "115200", "write-flash",
                      "0x0" if kind == "install" else "0x10000", str(path)]


def flash(root=ROOT, ask=input):
    print("\nOnly for the GUITION JC4880P433 ESP32-P4 board with ST7701S/GT911.")
    print("1. First installation (writes bootloader/partitions; resets display settings)")
    print("2. Update an existing AI Monitor P4 installation (keeps its partition layout/settings)")
    choice = ask("Choose 1 or 2; Enter cancels: ").strip()
    if choice not in {"1", "2"}:
        return
    kind = "install" if choice == "1" else "update"
    config = local_config(root)
    port = choose_port(config["port"], ask)
    if port == "auto":
        ports = list({p.device for p in list_ports.comports() if p.vid == 0x303A})
        if len(ports) != 1:
            raise SetupError("Select an explicit port before flashing; no unambiguous display was found.")
        port = ports[0]
    command = flash_command(kind, port, root)
    if ask(f"Write firmware to {port} on this GUITION board? Type FLASH to proceed: ").strip() != "FLASH":
        print("Cancelled. Nothing was written.")
        return
    stop_host(root)
    result = subprocess.run(command, cwd=root, check=False)
    if result.returncode:
        raise SetupError("Firmware installation failed. Check USB cable/port and close other serial clients.")
    config["port"] = port
    save_config(config, root)
    print("Firmware written. Use Start host next. The first display connection can take a few seconds.")


def status(root=ROOT):
    config = local_config(root)
    providers = config['providers']
    print(f"Host: {'running' if owned_hosts(root) else 'stopped'} / USB port: {config['port']}")
    print('Selected providers: ' + (', '.join(PROVIDERS[key][0] for key in providers) or 'none - open First-time setup'))
    if 'codex' in providers:
        print(f"Codex CLI login file: {'found' if host.CODEX_AUTH.is_file() else 'missing - sign in to Codex CLI'}")
    if 'zcode' in providers:
        print(f"ZCode quota key: {'configured' if os.environ.get('ZAI_API_KEY') or config.get('zai_key') else 'optional, not configured'}")
    counters = host.TokenReporter(providers=providers, activity_dir=root / 'tools/activity').poll()
    mask = counters["sources"]
    print('Readable token counters: ' + (' + '.join(PROVIDERS[key][0] for key in providers if mask & PROVIDERS[key][1]) or 'none'))
    print("Available USB ports: " + (", ".join(p.device for p in list_ports.comports()) or "none"))
    print("Messages: tools/aim_host.log. Counter updates can lag until requests finish.")


def view_log(root=ROOT):
    path = root / "tools/aim_host.log"
    if not path.exists():
        print("No log yet. Start the host first.")
        return
    with path.open("rb") as log:
        log.seek(max(0, path.stat().st_size - 8192))
        lines = log.read().decode("utf-8", errors="replace").splitlines()
    print("\n".join(lines[-25:]))


def integration_help(root=ROOT, ask=input, home=None):
    config = local_config(root)
    for key in config['providers']:
        print(PROVIDERS[key][0] + ': ' + PROVIDERS[key][2])
    print('Full instructions: docs/PROVIDERS.md. No app passwords or browser cookies are imported.')
    if 'claude' not in config['providers']: return
    settings = (Path.home() if home is None else Path(home)) / '.claude/settings.json'
    print('Optional Claude quota bridge uses the documented statusline fields.')
    if ask('Install the Claude quota bridge? Type INSTALL, or Enter to skip: ').strip() != 'INSTALL': return
    document = json.loads(settings.read_text(encoding='utf-8-sig')) if settings.exists() else {}
    if not isinstance(document, dict): raise SetupError('Claude settings are invalid; nothing changed.')
    if document.get('statusLine'):
        raise SetupError('Existing Claude statusline preserved. See docs/PROVIDERS.md to integrate manually.')
    if getattr(sys, 'frozen', False):
        command = [sys.executable, '--claude-statusline']
    else:
        command = [sys.executable, str(root / 'tools/aim_control.py'), '--claude-statusline']
    if os.name == 'nt':
        expression = '$payload=[Console]::In.ReadToEnd(); $payload | & ' + ' '.join("'" + argument.replace("'", "''") + "'" for argument in command)
        encoded = base64.b64encode(expression.encode('utf-16le')).decode('ascii')
        shell_command = 'powershell.exe -NoProfile -EncodedCommand ' + encoded
    else:
        import shlex
        shell_command = shlex.join(command)
    document['statusLine'] = {'type': 'command', 'command': shell_command}
    settings.parent.mkdir(parents=True, exist_ok=True)
    if settings.exists():
        import shutil
        backup = settings.with_name('settings.ai-monitor-backup-' + str(time.time_ns()) + '.json')
        shutil.copy2(settings, backup)
    from telemetry_bridge import write_record
    write_record(settings, document)
    print('Claude quota bridge installed. Restart Claude Code. Existing statuslines are never replaced.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", action="store_true", help="Run the background companion")
    parser.add_argument("--check", action="store_true", help="Show local diagnostics without connecting to the panel or API")
    parser.add_argument('--ingest', choices=list(PROVIDERS), help='Read a cumulative numeric telemetry record from stdin')
    parser.add_argument('--claude-statusline', action='store_true', help='Receive documented Claude statusline quota fields')
    args = parser.parse_args(argv)
    (ROOT / "tools").mkdir(exist_ok=True)
    if args.ingest or args.claude_statusline:
        from telemetry_bridge import ingest, claude_statusline
        try:
            raw = sys.stdin.buffer.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024: return 1
            data = json.loads(raw)
            if args.ingest: ingest(args.ingest, data, ROOT / 'tools/activity')
            else: print(claude_statusline(data, ROOT / 'tools/activity'))
            return 0
        except (ValueError, OSError, TypeError): return 1
    if args.host:
        return host.main()
    if args.check:
        status()
        return 0
    actions = {"1": configure, "2": start_host, "3": stop_host, "4": flash, "5": status, "6": view_log, '7': integration_help}
    while True:
        print("\nAI MONITOR P4\n1. First-time setup / choose AI providers\n2. Start host (hidden)\n3. Stop host\n4. Install / update display firmware\n5. Status / connection help\n6. View recent log\n7. Provider integration help\n0. Exit")
        try:
            choice = input("Choose: ").strip()
            if choice == "0":
                return 0
            if choice in actions:
                actions[choice]()
            else:
                print("Choose a number from the menu.")
        except SetupError as error:
            print(str(error))
        except (ValueError, RuntimeError, OSError, psutil.Error):
            # Credential errors can contain user input in third-party exceptions.
            print("Action failed. Check local configuration, permissions and the connection. No keys were printed.")
        except (KeyboardInterrupt, EOFError):
            return 0


if __name__ == "__main__":
    sys.exit(main())
