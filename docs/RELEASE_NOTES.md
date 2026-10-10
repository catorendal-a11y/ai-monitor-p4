# AI Monitor v1.14.0

The Windows PC companion now opens as a graphical desktop app with the original NOVA artwork and a NOVA application icon. Save board/provider settings with checkboxes and dropdowns, start/stop the hidden host, and read its terminal-style Activity and Host log panels.

- Keyboard-accessible native controls, masked optional API-key entry and bounded, redacted logs.
- Separate background/console helper preserves host lifetime after the window closes and retains numeric telemetry/stdin support.
- Verified board-specific firmware installation still requires a review dialog and typing FLASH. Cancellation leaves the host and display untouched.
- Provider setup opens the existing official Codex/Claude onboarding console only after a user requests it. No model generation or incoming network service is added.
- Clean-path Qt packaging and an exact EXE smoke test catch incompatible runtime DLLs before release. Keep the _internal folder beside AI-Monitor.exe.

The package includes both P4 and experimental original Waveshare S3 firmware. **S3 is still unverified on physical hardware; B/C variants are unsupported.** Existing P4 v1.12.0+ firmware can keep working with the updated host. No local maintainer credentials or usage records are distributed.

Download ai-monitor-p4-v1.14.0-windows.zip, extract the complete folder, then open AI-Monitor.exe. Advanced CLI/telemetry uses AI-Monitor-Console.exe. Stop your previous folder's host before upgrading; privately copy tools/aim_host.json if you want to preserve settings.
