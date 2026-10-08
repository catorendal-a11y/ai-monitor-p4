# Download, connect, run

## Recommended: portable Windows package

Use Windows 10/11 x64, the **GUITION JC4880P433 ESP32-P4** display and a USB data cable. No Python, PlatformIO, Node.js or Git installation is needed for this package.

1. Open **Releases** on this repository and download **ai-monitor-p4-v1.10.0-windows.zip**. Choose this asset, rather than GitHub's automatic **Source code (zip)**.
2. Right-click the ZIP and choose **Extract All**. Keep the entire folder together in a writable location, such as Documents. Do not run it inside the ZIP.
3. Connect the screen's USB data port and double-click **AI-Monitor.exe**.
4. Choose **1 â€” First-time setup**. Select the display's USB port from the numbered list. Leave the optional Z.AI key empty for Codex-only use. Enter preserves existing settings/keys; `clear` removes a saved Z.AI key. Keys are entered without echoing them to the screen.
5. For a new board, choose **4 â€” Install / update display firmware**, then **1 â€” First installation**. Check the board and port, and type `FLASH` when ready. This installs the firmware and resets display settings. **Skip this step if AI Monitor P4 is already installed.**
6. Choose **2 â€” Start host**. The companion runs in the background. Close the menu; keep the display connected. NOVA appears on the display when the host connects.

For Codex quota data, sign in through the [Codex CLI](https://developers.openai.com/codex/cli/) on this computer first. Desktop-app login alone may not supply the CLI login file used by this companion. Setup never asks for your OpenAI password or copies login credentials. ZCode quota requires your own Z.AI coding-plan key; ZCode's encrypted login is not imported. See [provider configuration](../README.md#provider-setup).

## Everyday use

Double-click **AI-Monitor.exe**, choose **2 â€” Start host**, then close the menu. Choose **3 â€” Stop host** before disconnecting for flashing. Choose **5 â€” Status** or **6 â€” View recent log** when a connection fails.

For firmware upgrades, choose **4**, then **2 â€” Update existing installation**. This writes the application and retains settings only when the board already uses this project's partition layout. For a different project's firmware, use First installation.

Copy the new package into a new folder, stop the old host, and run setup in the new folder. If desired, copy your private `tools/aim_host.json` from the old folder into the new one before setup. Do not share this file. The portable package cannot automatically stop hosts belonging to a different extracted folder.

## Downloaded the source ZIP instead?

Source code needs **Python 3.10+** and internet access for first setup. On Windows, install Python from [python.org](https://www.python.org/downloads/windows/), extract the source ZIP and double-click **AI-Monitor.bat**. It creates `.venv`, installs the small host dependencies and opens the same menu. Existing local configuration is preserved. Source ZIPs contain no prebuilt firmware or portable executables; use the Windows release for firmware installation, or the [developer guide](DEVELOPMENT.md) to build it.

On Linux/macOS:

```sh
sh setup.sh
.venv/bin/python tools/aim_control.py
```

The source menu can configure and start/stop the companion. A Windows portable package runs on Windows only. Building firmware and setting serial permissions on Linux/macOS are covered in the [developer guide](DEVELOPMENT.md).

## If something does not work

| Symptom | What to do |
| --- | --- |
| No USB port | Use a data-capable cable, the board's USB data port, and reconnect. Close other serial tools. |
| Several COM ports | Unplug the display, reopen setup and compare the list after reconnecting. Select its numbered port explicitly. |
| Codex quota unavailable | Sign in with Codex CLI, then use Status to check whether its login file is present. |
| ZCode quota unavailable | Configure your Z.AI coding-plan key. Leave it empty if you only use Codex. |
| NOVA does not react immediately | Counters may update when model requests finish. Status lists readable token sources. Quota polling is a separate signal. |
| Checksum or missing-flasher message | Extract the complete release ZIP again; keep the executables, firmware and manifest together. |
| Firmware connection fails | Stop the host, close serial monitors, check the chosen port, then retry. If normal upload cannot connect, follow the board's BOOT/RESET instructions. |
| Source setup cannot find Python | Use the portable Windows release, or install Python 3.10+ and retry AI-Monitor.bat. |

The host log is local at `tools/aim_host.log`. Never post keys, authentication files or unredacted private data in issues.
