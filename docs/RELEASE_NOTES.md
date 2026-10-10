# AI Monitor v1.16.1 (unreleased)

- **SET > AI USAGE** explains each provider's quota windows and PC setup. Each choice shows remaining quota and REPORTED/NOT REPORTED/OFFLINE/ERROR/UPDATING/STALE status.
- Known windows can be selected while waiting for data, without fabricated percentages. Live values update in Settings without rebinding touch targets; REFRESH reloads choices explicitly.
- ZCode now includes the monthly MCP tool quota and correctly labels its model weekly quota as 7 DAYS. Monthly MCP is not a monthly model-token budget.
- Missing-data, live-update, quota selection, text layout and ZCode API fixtures are covered by regression tests.

# AI Monitor v1.16.0

The NOVA/ORBIT companion panel is narrower, leaving more room for readable AI status and usage on the right. The robot keeps its original size and is recentered by trimming transparent canvas margins.

- Companion card: 430 to 350 pixels wide. Provider area: 310 to 390 pixels wide.
- Percentages: 26 to 40 pixels. Provider names: 14 to 20 pixels. Quota-window/status text: 12 to 16 pixels.
- Larger activity headings, token messages and navigation captions, with checks for clipping and overlap across every provider and tiny/full/LOCAL values.
- Updated actual LVGL previews for NOVA, ORBIT and the four themes.
- 29 linked project badges in README, including live release/commit/build/star badges and accurate board, provider, feature and privacy information. Experimental/activity-only integrations remain explicitly labeled.

The previous per-provider **SET > QUOTA WINDOW** preferences, larger notifications and guided Windows installer remain available. Existing selections survive application updates; missing windows remain unavailable and alerts still watch all windows.

- Larger notifications: 136-pixel banner, 24-pixel heading, 20-pixel quota text and a 60-pixel-high DISMISS button.
- Visible instructions for all eight AI choices, including ZCode's Coding Plan key, official Codex/Claude setup and activity-only bridge requirements.
- **AI-Monitor-Setup-v1.16.0-windows.exe** installs the complete app for the current user and opens setup. No Python, PlatformIO or administrator rights are required. The portable ZIP remains available.
- Double-clicking the command-line firmware helper explains its purpose and offers to open the graphical Firmware tab. Writes retain progress/error messages; the app cannot close during a write and can start the host after success.
- Packaged Qt diagnostics invoke the exact flasher child on both images without USB writes. Installer checks cover clean setup, runtime startup, upgrade and settings-preserving uninstall.
- The independent host keeps running after closing the app, until stopped, sign-out or shutdown. Private keys/configuration are not distributed.

**Windows trust:** this release is unsigned. SmartScreen may warn; version metadata and an installer do not replace trusted signing/reputation. Windows protections remain enabled. See the Windows trust guide included in the package.

**Hardware:** P4 and the original Waveshare S3 have separate firmware. S3 remains experimental and unverified on physical S3 hardware; B/C variants are unsupported. Use an application update on an existing AI Monitor to retain settings; First installation resets them. Stop a portable host from its original folder before switching to the installer version.
