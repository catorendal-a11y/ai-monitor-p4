# AI Monitor P4

A USB touchscreen desk companion for your AI tools. See usage limits at a glance and let **NOVA** or **ORBIT** react to recorded token activity on your PC.

[![Build and test](https://github.com/catorendal-a11y/ai-monitor-p4/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/catorendal-a11y/ai-monitor-p4/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**[Download for Windows](https://github.com/catorendal-a11y/ai-monitor-p4/releases/latest)** · [Quick Start](docs/QUICK_START.md) · [Provider setup](docs/PROVIDERS.md)

## Meet your desk companion

| NOVA | ORBIT with the Ocean theme |
| --- | --- |
| ![NOVA showing AI activity and usage](docs/nova-preview.png) | ![ORBIT on the Ocean companion screen](docs/ui/orbit-ocean.png) |

These previews are rendered from the actual LVGL interface using synthetic data. They are UI renders, not photographs of the display.

## What you need

- **GUITION JC4880P433 ESP32-P4** board with the 4.3-inch ST7701S display and GT911 touch controller. The supplied firmware is for this board.
- A **USB data cable** connected to the board's USB data port.
- A **Windows 10/11 x64 PC** for the ready-to-run package, plus your own AI account or local CLI installation.

The Windows package includes the Python runtime, PC companion, firmware flasher and prebuilt firmware. You do not need to install development tools. Linux/macOS users can run the companion from source.

## Get running on Windows

1. **Download and extract.** Open [Releases](https://github.com/catorendal-a11y/ai-monitor-p4/releases/latest) and download **ai-monitor-p4-v1.12.1-windows.zip**. Extract the entire ZIP into a writable folder; keep its contents together.
2. **Connect and open.** Connect the display and double-click **AI-Monitor.exe**.
3. **Choose your AI tools.** Select **1 - First-time setup**, choose one or more providers, then select the display's USB port. No AI is preselected. If you choose Codex, setup offers the official CLI installation and sign-in when needed. ZCode's quota key is optional and requested only if selected.
4. **Prepare the display.** On a new board, choose **4 - Install / update display firmware**, then **1 - First installation**. Check the board and port and type `FLASH`. This resets display settings. For an older AI Monitor installation, use the application update; firmware from another project needs First installation.
5. **Start the companion.** Select **2 - Start host**. Close the menu; the host keeps running invisibly while the display remains connected.

**Already on display firmware v1.12.0 or later?** Skip flashing. The v1.12.1 security fixes are in the PC host and work with existing v1.12.0 display firmware.

**[Direct Windows ZIP](https://github.com/catorendal-a11y/ai-monitor-p4/releases/download/v1.12.1/ai-monitor-p4-v1.12.1-windows.zip)** · [SHA-256 checksum](https://github.com/catorendal-a11y/ai-monitor-p4/releases/download/v1.12.1/SHA256SUMS.txt) · [Full setup and troubleshooting](docs/QUICK_START.md)

GitHub's **Source code (zip)** download contains source only; it does not include the portable programs or prebuilt firmware.

## Provider setup

Token activity and account quota are separate signals. A provider can animate the robot from local token records without providing a remaining-quota percentage.

| Provider | Token activity | Quota display |
| --- | --- | --- |
| **Codex** | Local Codex database | Signed-in official Codex CLI; setup offers installation/sign-in. |
| **ZCode** | Local ZCode database | Your optional Z.AI coding-plan API key. |
| **Claude Code** | Local CLI usage records | Optional documented statusline bridge, offered in menu 7. |
| **Gemini CLI** | Recorded local CLI sessions | Activity only; automatic account quota is unavailable. |
| **GitHub Copilot** | External numeric bridge | Activity only; editor usage is not imported automatically. |
| **Cursor** | External numeric bridge | Activity only. |
| **Antigravity** | External numeric bridge | Activity only. |
| **OpenCode** | External numeric bridge | Activity only. |

**External bridge** means you must connect an integration that supplies cumulative token counts. Selecting that provider alone does not enable automatic tracking. See [provider requirements and bridge examples](docs/PROVIDERS.md).

Codex setup uses the official client and your own sign-in flow; the monitor does not ask for an OpenAI password or key. Existing CLI installations and account storage are reused. You can decline installation/sign-in and finish later with **7 - Provider integration help**. [Codex setup guide](docs/CODEX_SETUP.md).

## Make it yours

On the display, open **SET > APPEARANCE**. Choose **NOVA** or **ORBIT**, then **Forest**, **Ocean**, **Amethyst** or **Ember**. Changes apply immediately and are saved on the display. Provider branding and warning colors keep their meanings across themes.

| Robot and color settings | Provider dashboard |
| --- | --- |
| ![Robot selection and theme settings](docs/ui/settings-appearance-ocean.png) | ![Provider dashboard in the Ocean theme](docs/ui/dashboard-ocean.png) |

| ORBIT in Amethyst | NOVA in Ember |
| --- | --- |
| ![ORBIT companion in the Amethyst theme](docs/ui/orbit-amethyst.png) | ![NOVA companion in the Ember theme](docs/ui/nova-ember.png) |

[View the provider details screen](docs/ui/details-ocean.png).

The display also includes reset countdowns, manual refresh, low/critical quota warnings, session history, brightness presets, gradual idle dimming and scheduled night brightness.

## Everyday use

| Menu choice | What it does |
| --- | --- |
| **1 - First-time setup** | Select providers, USB port and optional provider configuration. |
| **2 - Start host** | Start this folder's companion in the background. |
| **3 - Stop host** | Stop hosts belonging to this folder. |
| **4 - Install / update firmware** | Verify the firmware hash and ask for confirmation before flashing. |
| **5 - Status** | Inspect host status, USB ports and readable token sources without making API calls. |
| **6 - View recent log** | Show recent connection and polling messages. |
| **7 - Provider integration help** | Retry Codex setup or configure the optional Claude quota bridge. |

When upgrading, stop the old host before opening a newly extracted package. To preserve configuration, privately copy `tools/aim_host.json` into the new folder before setup. [Upgrade instructions](docs/QUICK_START.md#everyday-use).

## If the robot is quiet

The robot follows **increases in recorded token counters**. The first sample establishes a baseline; existing totals do not count as fresh activity. Some clients save token usage only when a request finishes, so activity can lag generation.

| Symptom | First check |
| --- | --- |
| No USB connection | Use a data cable and the correct USB port; close other serial tools. |
| Robot does not react | Open Status and check that the selected provider has a readable token source. |
| Codex quota is unavailable | Use menu 7 to finish official CLI sign-in; account quota requires a supported ChatGPT-backed login. |
| External provider stays inactive | Connect its numeric telemetry bridge; selection alone does not supply data. |

This is an activity and quota display, not a billing ledger or per-token stream. Unsupported local formats remain unavailable. Display history clears after a firmware restart. [More troubleshooting](docs/QUICK_START.md#if-something-does-not-work).

## Privacy and security

The PC companion reads selected local usage sources, queries provider quota over HTTPS and sends display data over USB. It has no incoming network listener or automatic GitHub code updater. GitHub Actions run on GitHub-hosted machines; this repository has no runner or webhook connected to the maintainer's PC.

No maintainer credentials are included in the source or release. Your optional Z.AI key is stored in plaintext in local `tools/aim_host.json`, which is ignored by Git; keep that file private. `ZAI_API_KEY` in the process environment takes precedence. The host does not automatically load `.env` files. Windows executables are currently unsigned; obtain the ZIP and checksum from this repository's release page.

[Security and private reporting](SECURITY.md) · [Host security review](docs/SECURITY_REVIEW.md) · [GitHub safeguards](docs/GITHUB_SECURITY.md)

## Run from source or contribute

Source installations require **Python 3.10+**. On Windows, double-click **AI-Monitor.bat** to create the local environment and open the menu. On Linux/macOS:

```sh
sh setup.sh
.venv/bin/python tools/aim_control.py
```

Firmware builds, serial permissions and test dependencies are covered in the [developer guide](docs/DEVELOPMENT.md). The [release guide](docs/RELEASING.md) explains the separate build/publish jobs and reviewed draft releases. Ordinary source pushes do not publish a release.

[Contributing](CONTRIBUTING.md) · [Provider roadmap](docs/PROVIDER_ROADMAP.md) · [All releases](https://github.com/catorendal-a11y/ai-monitor-p4/releases)

Project-owned code and original NOVA/ORBIT artwork use [MIT](LICENSE). Drivers, dependencies, fonts and provider marks retain their own terms: [third-party notices](THIRD_PARTY_NOTICES.md), [NOVA/logo sources](assets/nova/SOURCES.md) and [ORBIT artwork](assets/orbit/SOURCES.md). This is an independent project and is not endorsed by its AI providers.
