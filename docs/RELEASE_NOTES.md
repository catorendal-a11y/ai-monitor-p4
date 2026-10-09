Security update v1.12.1 blocks authenticated API redirects, rejects current/project-folder Codex executables, validates USB serial paths, bounds local configuration reads and removes terminal control characters from logs. Actions are pinned and dependency security checks are enabled. Read docs/SECURITY_REVIEW.md for evidence and remaining limits.

Download **ai-monitor-p4-v1.12.1-windows.zip**. Extract the entire ZIP, open **AI-Monitor.exe** and follow First-time setup. Python, the host, the firmware flasher and prebuilt GUITION JC4880P433 firmware are included. Existing v1.12.0 display firmware remains compatible; the security changes are in the PC host, so it does not require flashing.

On a new board, use Install firmware / First installation; on an existing AI Monitor P4 board, use the application update. First installation resets display settings. Select the correct USB data port. Start host afterward; it runs invisibly after the menu closes.

Codex quota requires a local Codex CLI login. ZCode quota optionally requires your own Z.AI coding-plan key. No personal credentials are included. Read the README and Quick Start before installing.

The automatic Source code ZIP is for developers and does not contain the portable executables or firmware. The standalone Windows archive contains reviewed source, firmware hashes and dependency notices/source.
