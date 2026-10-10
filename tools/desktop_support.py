"""Validated native-desktop actions; no model turns or network listener."""
from pathlib import Path
import os
import subprocess
import sys
import time

import aim_control as control
from board_profiles import get_board
from host_security import safe_text, serial_port
from provider_catalog import selected_providers
from host_status import validate_options, read_status


def load_settings(root: Path) -> dict:
    config = control.local_config(root)
    validate_options(config)
    if type(config['interval_s']) is not int or not 15 <= config['interval_s'] <= 240:
        raise control.SetupError('Invalid refresh interval in local configuration.')
    control.host.credential(config['zai_key'], optional=True)
    return config


def reset_invalid_settings(root: Path) -> None:
    """Explicit recovery only: keep the original private bytes in a local backup."""
    try:
        load_settings(root)
    except (ValueError, OSError):
        pass
    else:
        raise control.SetupError('Settings are valid; recovery is unnecessary.')
    source = root / 'tools/aim_host.json'
    with source.open('rb') as stream:
        raw = stream.read(65537)
    if len(raw) > 65536: raise control.SetupError('Configuration is too large for safe recovery. Repair it locally.')
    backup = source.with_name('aim_host.invalid-' + str(time.time_ns()) + '.json')
    with backup.open('xb') as stream:
        stream.write(raw)
    control.stop_host(root)
    control.save_config(dict(control.host.DEFAULT_CONFIG), root)


def save_settings(root: Path, board: str, providers: list[str], port: str,
                  interval: int, key: str = '', clear_key: bool = False, options=None) -> dict:
    get_board(board)
    config = load_settings(root)
    choices = selected_providers({'providers': providers})
    if not choices:
        raise control.SetupError('Choose at least one AI provider before saving.')
    port = serial_port(port)
    if type(interval) is not int or not 15 <= interval <= 240:
        raise control.SetupError('Quota refresh must be between 15 and 240 seconds.')
    if type(clear_key) is not bool or not isinstance(key, str):
        raise control.SetupError('Invalid key settings. Nothing was saved.')
    updated = dict(config, board=board, providers=choices, port=port,
                   interval_s=interval, zai_provider='zcode')
    if options is not None:
        from host_status import OPTIONS, FLAGS
        if not isinstance(options, dict) or set(options) - (set(OPTIONS) | set(FLAGS)):
            raise control.SetupError('Unknown host preference. Nothing was saved.')
        updated.update(options)
    validate_options(updated)
    if clear_key:
        updated['zai_key'] = ''
    elif key.strip():
        try:
            updated['zai_key'] = control.host.credential(key)
        except ValueError:
            raise control.SetupError('Use a single printable API key. Nothing was saved.') from None
    control.save_config(updated, root)
    return updated


def connection_summary(root: Path, processes) -> str:
    if not processes: return 'HOST STOPPED'
    status = read_status(root, {process.pid for process in processes})
    if not status: return 'HOST RUNNING • USB STATUS UNCONFIRMED'
    state = status['state']
    port = safe_text(status.get('port', ''), 64)
    return {'starting': 'HOST STARTING', 'waiting_usb': 'WAITING FOR USB SELECTION',
            'connecting': f'CONNECTING • {port}', 'connected': f'USB CONNECTED • {port}',
            'reconnecting': f'USB RECONNECTING • {port}', 'stopped': 'HOST STOPPING',
            'error': 'HOST ERROR • CHECK LOG'}[state]


def check_connection(root: Path, emit) -> None:
    """Read device identity; no flash, quota requests or settings mutation."""
    config = load_settings(root)
    board = get_board(config['board'])
    processes = control.owned_hosts(root)
    if processes:
        status = read_status(root, {process.pid for process in processes})
        if (status and status['state'] == 'connected' and status.get('board') == board.id
                and config['port'] in ('auto', status['port'])):
            emit('The host has a verified USB connection on ' + status['port'] + '.')
            return
        raise control.SetupError('The host is running but USB is not confirmed. Stop host before checking the display; then select its port and retry.')
    port = control.host.find_port(config['port'], board.id)
    if not port: raise control.SetupError('Choose an explicit display port in Setup, save settings and retry. Use a USB data cable.')
    panel = None
    try:
        panel = control.host.Panel(port)
        time.sleep(0.5)
        panel.send_line('{"cmd":"get_info"}')
        info = panel.wait_for('info')
        from board_profiles import matches_info
        if not matches_info(board, info):
            raise control.SetupError('This port does not report the selected AI Monitor board. Check the port and board; a new factory display needs firmware installation.')
        emit('Verified AI Monitor display: ' + board.name + ' on ' + port + '. No firmware or settings were changed.')
    except (TimeoutError, OSError, RuntimeError, control.host.serial.SerialException):
        raise control.SetupError('The display did not respond. Check its USB data port/cable, close other serial tools, or install firmware on a new board.') from None
    finally:
        if panel is not None: panel.close()


def recent_log(root: Path, secrets: tuple[str, ...] = ()) -> str:
    path = root / 'tools/aim_host.log'
    try:
        with path.open('rb') as stream:
            stream.seek(0, 2)
            length = stream.tell()
            stream.seek(max(0, length - 12000))
            text = stream.read(12000).decode('utf-8', errors='replace')
    except OSError:
        return ''
    for secret in secrets:
        if secret:
            text = text.replace(secret, '[REDACTED]')
    if length > 12000:
        text = text.partition('\n')[2]
    return '\n'.join(safe_text(line) for line in text.splitlines()[-100:])


def integration_command(root: Path, codex_only=False) -> list[str]:
    option = '--setup-codex' if codex_only else '--integrations'
    if getattr(sys, 'frozen', False):
        helper = root / 'AI-Monitor-Console.exe'
        if not helper.is_file():
            raise control.SetupError('Console helper missing. Extract the complete Windows package.')
        return [str(helper), option]
    return [sys.executable, str(root / 'tools/aim_control.py'), option]


def open_integrations(root: Path, codex_only=False) -> None:
    if os.name != 'nt':
        raise control.SetupError('Use tools/aim_control.py in a terminal for provider setup on this platform.')
    environment = dict(os.environ)
    environment['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
    subprocess.Popen(integration_command(root, codex_only), cwd=root, env=environment,
                     creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)


def prepare_flash(root: Path, board_id: str, kind: str) -> tuple[str, list[str]]:
    config = load_settings(root)
    if config.get('board') != board_id:
        raise control.SetupError('Save the selected board before preparing firmware.')
    board = get_board(board_id)
    port = control.host.find_port(config['port'], board.id)
    if not port:
        raise control.SetupError('No unambiguous USB port. Choose an explicit port and save settings.')
    return port, control.flash_command(kind, port, root, board.id)


def write_firmware(root: Path, board_id: str, kind: str, port: str, emit) -> None:
    # Revalidate the current files and configuration after the dialog, before
    # stopping the host or invoking any tool. Do not trust a prepared command.
    current_port, command = prepare_flash(root, board_id, kind)
    if current_port != port:
        raise control.SetupError('USB selection changed. Prepare firmware again.')
    control.stop_host(root)
    if kind == 'update':
        # Application-only updates require this project's existing layout.
        panel = None
        try:
            panel = control.host.Panel(port)
            panel.expected_board = get_board(board_id)
            time.sleep(0.5)
            panel.heartbeat()
        except (RuntimeError, TimeoutError, OSError, control.host.serial.SerialException):
            raise control.SetupError('Existing AI Monitor identity could not be verified. '
                'Check the board/port. A factory demo or another project requires First installation. '
                'The host is stopped; no firmware was written.') from None
        finally:
            if panel is not None:
                panel.close()
    environment = dict(os.environ)
    environment['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
    with subprocess.Popen(command, cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, errors='replace', env=environment,
                          creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0) as process:
        for line in iter(lambda: process.stdout.readline(512), ''):
            emit(safe_text(line))
        if process.wait() != 0:
            raise control.SetupError('Firmware tool failed. Check the USB port and device connection.')
    emit('Firmware written. The display will reboot; reconnect if needed.')


def check_flasher_runtime(root: Path) -> bool:
    """Read image metadata using the exact child EXE, without opening USB."""
    environment = dict(os.environ); environment['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
    try:
        for board in control.BOARDS.values():
            image = control.firmware_file('update', root, board.id)
            result = subprocess.run([str(root/'firmware-flasher.exe'), '--chip', board.chip, 'image-info', str(image)],
                cwd=root, env=environment, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=30, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if result.returncode:
                return False
    except (control.SetupError, OSError, subprocess.TimeoutExpired):
        return False
    return True
