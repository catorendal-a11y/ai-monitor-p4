# Download, connect, run

## Recommended: Windows installer

Use Windows 10/11 x64, a **GUITION JC4880P433 ESP32-P4** or **original Waveshare ESP32-S3-Touch-LCD-4.3** display and a USB data cable. S3 support is experimental and unverified on physical hardware; use its **USB TO UART** connector. [Check your board](BOARDS.md). No Python, PlatformIO, Node.js or Git installation is needed for this package.

1. Open **Releases** and download **AI-Monitor-Setup-v1.15.0-windows.exe**. It installs the complete app for your user and opens setup. No administrator access or separate Python installation is required. The release is unsigned; [read the Windows trust notes](WINDOWS_TRUST.md) if SmartScreen warns.
2. For a portable installation instead, download **ai-monitor-p4-v1.15.0-windows.zip** and use **Extract All**. Keep the entire folder, including **_internal**, together. Do not run inside the ZIP. GitHub's **Source code (zip)** contains no ready-to-run programs.
3. Connect the screen's USB data port and double-click **AI-Monitor.exe**.
4. In **Setup**, choose your exact board, providers and USB port. Read the visible instructions for each AI. Codex offers official CLI setup/sign-in; ZCode quota needs your own Z.AI Coding Plan key in the masked field. Without that key, ZCode can still report local activity. Click **Save settings**. A blank key field preserves the saved key; **Clear saved key** removes it. Neither board nor AI is preselected on a fresh installation.
5. For a new board, open **Firmware > Install / update firmware** and choose **First installation**. Review the board/port and type `FLASH`. This resets display settings. For an existing AI Monitor, choose **Update this project's existing installation** to retain settings and enable the new quota selector/large alerts. A new S3 board needs its own factory installation. Progress and errors remain in **Activity**; keep the app and power connected until it finishes.
6. Leave **Start the host after a successful firmware installation** checked, or click **Start host** afterward. Once running, close the window and keep the display connected. The host stays invisible until Stop host, sign-out or shutdown.

When you choose Codex, setup offers the official CLI installer and its sign-in flow automatically when needed. Accept the offered steps with your own account; [Codex setup guide](CODEX_SETUP.md). Desktop-app login alone may not supply the CLI login file used by this companion. Setup never asks for your OpenAI password or copies login credentials. ZCode quota requires your own Z.AI coding-plan key; ZCode's encrypted login is not imported. See [provider configuration](../README.md#provider-setup).

## Personalize the display

Tap **SET**, then **APPEARANCE**. Select NOVA or ORBIT and a Forest/Ocean/Amethyst/Ember theme. Use DONE, then BACK. Choices are stored on the display and survive application updates/reboots. A first factory installation resets device settings. If SAVE FAILED appears, the selection is temporary; retry before restarting.

## Everyday use

For NOVA/ORBIT percentages, open **SET > QUOTA WINDOW**. Select a provider with PREV/NEXT, then its quota window. Codex normally reports **5 HOURS / 7 DAYS**; ZCode lists **5 HOURS / MONTHLY** when those rows are available. **AUTO / MOST URGENT** keeps the most urgent window visible. Each provider's choice is saved independently on the display. Missing selected windows show unavailable; activity-only providers keep LOCAL. Warnings still monitor all quota windows.

Double-click **AI-Monitor.exe**, click **Start host**, then close the window. Use **Stop host** before flashing. The **Activity** and **Host log** tabs show connection messages. The NOVA caption reports readable local token sources; it does not invent activity.

For firmware upgrades, open **Firmware**, then select **Update this project's existing installation**. This writes the application and retains settings only when the board already uses this project's partition layout. For a different project's firmware, use First installation.

Copy the new package into a new folder, stop the old host, and run setup in the new folder. If desired, copy your private `tools/aim_host.json` from the old folder into the new one before setup. Do not share this file. The portable package cannot automatically stop hosts belonging to a different extracted folder.

## Downloaded the source ZIP instead?

Source code needs **Python 3.10+** and internet access for first setup. On Windows, install Python from [python.org](https://www.python.org/downloads/windows/), extract the source ZIP and double-click **AI-Monitor.bat**. It creates `.venv`, installs the host/Qt dependencies and opens the same graphical app. Existing local configuration is preserved. Source ZIPs contain no prebuilt firmware or portable executables; use the Windows release for firmware installation, or the [developer guide](DEVELOPMENT.md) to build it.

On Linux/macOS:

```sh
sh setup.sh
.venv/bin/python tools/aim_control.py
```

The source menu can configure and start/stop the companion. A Windows portable package runs on Windows only. Building firmware and setting serial permissions on Linux/macOS are covered in the [developer guide](DEVELOPMENT.md).

## If something does not work

| Symptom | What to do |
| --- | --- |
| Connected display does not match selected board | Open First-time setup and select the actual model. P4 and S3 use separate firmware. |
| S3 screen looks darker but LEDs stay bright | Intermediate brightness is visual attenuation; only zero switches the original S3 backlight off. |
| Desktop runtime could not load | Extract the complete ZIP into a new folder; keep _internal beside AI-Monitor.exe. Do not copy the EXE alone. |
| Flasher closes when double-clicked | Open AI-Monitor.exe > Firmware. The new helper explains this and offers to open the Firmware tab. |
| Windows says unknown publisher | This release is unsigned. Keep Windows protection enabled; see WINDOWS_TRUST.md. |
| No USB port | Use a data-capable cable, the board's USB data port, and reconnect. Close other serial tools. |
| Several COM ports | Unplug the display, reopen setup and compare the list after reconnecting. Select its numbered port explicitly. |
| Codex quota unavailable | Sign in with Codex CLI, then use Status to check whether its login file is present. |
| ZCode quota unavailable | Configure your Z.AI coding-plan key. Leave it empty if you only use Codex. |
| NOVA does not react immediately | Counters may update when model requests finish. Status lists readable token sources. Quota polling is a separate signal. |
| Checksum or missing-flasher message | Extract the complete release ZIP again; keep the executables, firmware and manifest together. |
| Firmware connection fails | Stop the host, close serial monitors, check the chosen port, then retry. If normal upload cannot connect, follow the board's BOOT/RESET instructions. |
| Source setup cannot find Python | Use the portable Windows release, or install Python 3.10+ and retry AI-Monitor.bat. |

The host log is local at `tools/aim_host.log`. Never post keys, authentication files or unredacted private data in issues.
