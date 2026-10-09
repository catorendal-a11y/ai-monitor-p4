# Automatic Codex setup for new users

This is a PC-app onboarding feature for people who choose Codex. It is not an automatic AI agent for GitHub development. No provider is preselected, and choosing another provider never installs or signs into Codex.

## First installation

1. Extract the full Windows release and open **AI-Monitor.exe**.
2. Choose **1 - First-time setup**, explicitly select Codex (alone or with other tools), and choose the display's USB port.
3. If the official Codex CLI is missing, setup offers the official OpenAI installer. Accept to install it, or decline to finish later. Existing CLI installations are reused.
4. Setup checks sign-in quietly. If needed, it offers **official Codex sign-in**. Accept and finish the vendor's browser/terminal flow with your own ChatGPT account. The monitor never asks for or copies your OpenAI password/access token.
5. Choose **2 - Start host**. Your choices remain selected if an installation or login was skipped or failed. Choose **7 - Provider integration help** to retry.

The installer and first sign-in need internet access. Windows uses OpenAI's standalone PowerShell installer; Linux/macOS source installations use its documented shell installer. No personal OpenAI key, GitHub key or credentials are shipped with the release.

## Existing accounts and storage

The CLI keeps control of its existing credential store, including supported file/keyring modes. Setup does not rewrite global Codex configuration or silently switch storage to a plaintext file. `CODEX_HOME` and `CODEX_INSTALL_DIR` are respected for compatible custom installations. Login status output is not copied into monitor logs.

Plan quota is read through the official CLI app-server `account/rateLimits/read` method after initialization. No model turn, code-generation request, credit-reset redemption or notification email is started by the monitor. Local token activity still uses the numeric SQLite counter under `CODEX_HOME`. If the CLI is absent, an already-existing file-login quota adapter remains as a legacy fallback; setup never copies that file into project configuration.

Quota requires a ChatGPT-backed account. API-key-only mode does not become a subscription quota, and ephemeral credentials are not guaranteed to work across independent processes. Missing/unsupported account data is shown as unavailable rather than invented. Use the official CLI to change account/storage deliberately when needed.

## If setup is incomplete

| State | Action |
| --- | --- |
| CLI missing | Accept the official installer in First-time setup / Provider integration help. |
| CLI not found after installation | Restart the menu so updated paths are available, then retry. |
| Sign-in skipped/cancelled | Retry through Provider integration help or sign in with the official CLI. |
| Quota unavailable | Verify ChatGPT sign-in and update the official CLI if its account interface is unsupported. |
| Tokens unavailable | Use Codex sessions that update the supported local numeric database; token registration may lag requests. |
| Another provider selected | Codex setup is not run; use that provider's guide. |

Your display's USB settings, selected providers, Z.AI key, and robot/theme preferences remain independent of Codex login. No extra AI is enabled when a step fails.

Official references: [CLI installation](https://learn.chatgpt.com/docs/cli), [authentication/storage](https://learn.chatgpt.com/docs/auth), [account rate-limit interface](https://learn.chatgpt.com/docs/app-server), [CODEX_HOME and installation directories](https://learn.chatgpt.com/docs/config-file/environment-variables).
