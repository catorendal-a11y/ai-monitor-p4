"""Explicit local integration setup. Preserve unrelated client settings."""
import base64
import os
from pathlib import Path
import shutil
import sys
import time
from host_security import powershell_executable, read_local_json
from telemetry_bridge import write_record


def claude_command(root):
    if getattr(sys, 'frozen', False):
        helper = root / 'AI-Monitor-Console.exe'
        if not helper.is_file(): raise ValueError('Console helper missing. Reinstall the complete release.')
        command = [str(helper), '--claude-statusline']
    else:
        command = [sys.executable, str(root / 'tools/aim_control.py'), '--claude-statusline']
    if os.name == 'nt':
        expression = '$payload=[Console]::In.ReadToEnd(); $payload | & ' + ' '.join("'" + arg.replace("'", "''") + "'" for arg in command)
        encoded = base64.b64encode(expression.encode('utf-16le')).decode('ascii')
        return '"' + powershell_executable() + '" -NoProfile -EncodedCommand ' + encoded
    import shlex
    return shlex.join(command)


def claude_bridge(root, remove=False, home=None):
    settings = (Path.home() if home is None else Path(home)) / '.claude/settings.json'
    document = read_local_json(settings, 65536) if settings.exists() else {}
    if not isinstance(document, dict): raise ValueError('Claude settings are invalid; nothing changed.')
    expected = {'type': 'command', 'command': claude_command(root)}
    current = document.get('statusLine')
    if remove:
        if current != expected: raise ValueError('This installation does not own the statusline. Existing settings were preserved.')
        del document['statusLine']
    elif current == expected:
        return 'Claude quota link is already installed. Use Claude Code to receive fresh quota data.'
    elif current:
        raise ValueError('Existing custom Claude statusline preserved. Remove it in Claude settings or keep local activity only.')
    else:
        document['statusLine'] = expected
    settings.parent.mkdir(parents=True, exist_ok=True)
    if settings.exists():
        shutil.copy2(settings, settings.with_name('settings.ai-monitor-backup-' + str(time.time_ns()) + '.json'))
    write_record(settings, document)
    return ('Claude quota link removed. Local activity remains available.' if remove else
            'Claude quota link installed. Use Claude Code to receive fresh data. A private settings backup is on this PC.')


def readiness(root, emit):
    from aim_control import local_config
    from codex_support import codex_command
    from provider_catalog import PROVIDERS
    from token_activity import TokenReporter
    config = local_config(root)
    reporter = TokenReporter(providers=config['providers'], activity_dir=root/'tools/activity')
    sample = reporter.poll()
    for provider in config['providers']:
        name, bit, _ = PROVIDERS[provider]
        source = 'Local token source readable.' if sample['sources'] & bit else 'No readable token source yet. Use the client once, then check again.'
        if provider == 'codex':
            extra = ('Official CLI found; Provider setup checks sign-in. Account quotas are checked by the host.' if codex_command() else
                     'Official CLI missing. Click Provider setup to install and sign in.')
        elif provider == 'zcode':
            extra = 'Quota key saved; the host checks its plan.' if config['zai_key'] else 'For quotas, enter your own Z.AI Coding Plan key in Setup. Local activity needs no monitor key.'
        elif provider == 'claude':
            extra = 'Click Link Claude quota for subscription windows; a custom statusline is preserved.'
        elif provider in ('gemini', 'opencode'):
            extra = 'Local activity integration; remaining account quota is unavailable.'
        else:
            extra = 'Advanced integration: a numeric bridge is required. Selection alone cannot read this editor.'
        emit(name + ': ' + source + ' ' + extra)
    emit('This check read local numeric usage only. It did not contact a model, flash the display or change client settings.')
