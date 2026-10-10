# AI Monitor v1.15.1

Choose the quota window shown by NOVA/ORBIT independently for each AI in **SET > QUOTA WINDOW**. Codex offers 5-hour/7-day rows; ZCode offers 5-hour/monthly rows when its plan reports them. Other providers list actual available quotas. AUTO keeps the most urgent quota visible. Selections survive reboot and application updates; missing selected windows remain unavailable, and alerts still watch all windows.

- Larger notifications: 136-pixel banner, 24-pixel heading, 20-pixel quota text and a 60-pixel-high DISMISS button.
- Visible instructions for all eight AI choices, including ZCode's Coding Plan key, official Codex/Claude setup and activity-only bridge requirements.
- **AI-Monitor-Setup-v1.15.1-windows.exe** installs the complete app for the current user and opens setup. No Python, PlatformIO or administrator rights are required. The portable ZIP remains available.
- Double-clicking the command-line firmware helper explains its purpose and offers to open the graphical Firmware tab. Writes retain progress/error messages; the app cannot close during a write and can start the host after success.
- Packaged Qt diagnostics invoke the exact flasher child on both images without USB writes. Installer checks cover clean setup, runtime startup, upgrade and settings-preserving uninstall.
- The independent host keeps running after closing the app, until stopped, sign-out or shutdown. Private keys/configuration are not distributed.

**Windows trust:** this release is unsigned. SmartScreen may warn; version metadata and an installer do not replace trusted signing/reputation. Windows protections remain enabled. See the Windows trust guide included in the package.

**Hardware:** P4 and the original Waveshare S3 have separate firmware. S3 remains experimental and unverified on physical S3 hardware; B/C variants are unsupported. Use an application update on an existing AI Monitor to retain settings; First installation resets them. Stop a portable host from its original folder before switching to the installer version.
