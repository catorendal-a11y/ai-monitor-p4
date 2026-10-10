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


def load_settings(root: Path) -> dict:
    config = control.local_config(root)
    if type(config['interval_s']) is not int or not 15 <= config['interval_s'] <= 240:
        raise control.SetupError('Invalid refresh interval in local configuration.')
    control.host.credential(config['zai_key'], optional=True)
    return config


def save_settings(root: Path, board: str, providers: list[str], port: str,
                  interval: int, key: str = '', clear_key: bool = False) -> dict:
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
    if clear_key:
        updated['zai_key'] = ''
    elif key.strip():
        try:
            updated['zai_key'] = control.host.credential(key)
        except ValueError:
            raise control.SetupError('Use a single printable API key. Nothing was saved.') from None
    control.save_config(updated, root)
    return updated


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


def integration_command(root: Path) -> list[str]:
    if getattr(sys, 'frozen', False):
        helper = root / 'AI-Monitor-Console.exe'
        if not helper.is_file():
            raise control.SetupError('Console helper missing. Extract the complete Windows package.')
        return [str(helper), '--integrations']
    return [sys.executable, str(root / 'tools/aim_control.py'), '--integrations']


def open_integrations(root: Path) -> None:
    if os.name != 'nt':
        raise control.SetupError('Use tools/aim_control.py in a terminal for provider setup on this platform.')
    environment = dict(os.environ)
    environment['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
    subprocess.Popen(integration_command(root), cwd=root, env=environment,
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
    for board in control.BOARDS.values():
        image = control.firmware_file('update', root, board.id)
        result = subprocess.run([str(root/'firmware-flasher.exe'), '--chip', board.chip, 'image-info', str(image)],
            cwd=root, env=environment, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=30, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        if result.returncode:
            return False
    return True
