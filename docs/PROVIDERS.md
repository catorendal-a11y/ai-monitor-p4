# Choose your AI providers

First-time setup has **no preselected AI**. Check one or more providers explicitly in the desktop app, or use the numbered console choices. Unselected providers are not polled or scanned. A missing API key never silently changes your selection. Existing pre-selection configurations retain the old Codex/ZCode combination when loaded; newly created configurations contain `"providers": []` until setup is completed.

## What each choice supports

| Choice | Automatic local token activity | Quota display | Setup |
| --- | --- | --- | --- |
| Codex | Numeric counters in the default local Codex SQLite database | Official CLI account interface, with legacy file fallback | Choose Codex; setup offers official installation/sign-in as needed. See CODEX_SETUP.md. |
| ZCode | Numeric request counters in the local ZCode SQLite database | Existing Z.AI coding-plan adapter | Choose ZCode. Its optional coding-plan key is requested only for this selection. |
| Claude Code | Assistant usage fields from local CLI JSONL transcripts; repeated message IDs are deduplicated | Documented statusline rate-limit fields when supplied | Choose Claude. Local CLI logging is used automatically. Menu 7 offers the optional quota bridge. |
| Gemini CLI | Reported token totals from recorded CLI JSON/JSONL sessions | No automatic account-quota adapter | Choose Gemini CLI and use it normally with session recording. |
| GitHub Copilot | Numeric telemetry bridge | No automatic account-quota adapter in this release | Connect usage events from your Copilot SDK application; editor usage is not automatically imported. |
| Cursor | Numeric telemetry bridge | No automatic personal-quota adapter | Supply cumulative token telemetry from an integration you control. Team Admin API access is a separate capability. |
| Antigravity | Numeric telemetry bridge | No automatic quota adapter | Supply numeric telemetry. The CLI's interactive quota panel is not treated as a stable machine API. |
| OpenCode | Numeric telemetry bridge | No automatic quota adapter | Export cumulative token usage from an SDK integration you control. |

The graphical app exposes these limitations in each provider's tooltip; the console menu also lists them. Selecting an integration is not proof that its source is readable. Status lists the sources actually readable on this machine. The panel shows **LOCAL / Activity only** when no real quota percentage is available. It never substitutes context occupancy, request counts, billing estimates or made-up percentages for a plan quota.

## Claude Code

Local activity uses assistant `message.usage` numeric fields from recent default CLI transcripts under `~/.claude/projects/`. Records with the same `message.id` are not counted twice; increases in a streamed record may still be registered later. Inputs, outputs and reported cache tokens are observed counts, not an invoice. CLI versions may omit or incompletely report output usage. Desktop/web sessions have separate storage and are not automatically covered.

For quota display, click **Provider setup** (or choose **7** in AI-Monitor-Console.exe), then type **INSTALL** for the optional statusline bridge. This adds a command to `~/.claude/settings.json` only when no custom statusline exists. Existing settings are backed up; existing statuslines are preserved. Restart Claude Code afterward. The bridge extracts only `rate_limits.five_hour` and `rate_limits.seven_day`, with their used percentages/reset epochs. Missing fields produce activity-only status; data expires after five minutes. An API key alone is not treated as a Claude subscription quota.

If you already have a custom statusline, retain it and pipe a copy of its original JSON input into `AI-Monitor-Console.exe --claude-statusline` from your script. The bridge prints a short status string; discard or incorporate that output as preferred. It does not use `context_window.used_percentage` or `total_input_tokens` as plan consumption. To remove an installed bridge, restore the backed-up Claude settings or remove only the inserted statusLine entry.

Primary references: [Claude statusline fields](https://code.claude.com/docs/en/statusline), [CLI session storage](https://code.claude.com/docs/en/sessions), [usage monitoring](https://code.claude.com/docs/en/monitoring-usage). The numeric transcript adapter uses a version-sensitive local format; unsupported records remain unavailable.

## Gemini CLI

Recorded sessions live at `~/.gemini/tmp/<project>/chats/session-*`. The adapter supports JSON session files and current JSONL records, retaining only model-message IDs and `tokens.total`. It does not read the local login/token cache. It does not equate context size with the account's remaining quota.

Primary references: [recorded sessions](https://geminicli.com/docs/cli/session-management/), [official token-record types](https://github.com/google-gemini/gemini-cli/blob/main/packages/core/src/services/chatRecordingTypes.ts), [official telemetry](https://geminicli.com/docs/cli/telemetry/).

## External numeric bridge

Cursor, Copilot, Antigravity and OpenCode can be selected, but need an external integration that reports usage. This release does not log into their websites, copy browser cookies or guess private endpoints. Send a JSON record on stdin to the portable executable, for example:

```text
AI-Monitor-Console.exe --ingest copilot
```

Input:

```json
{"session_id":"your-local-session-id","total_tokens":12345}
```

`total_tokens` must be a nonnegative, cumulative integer for that session. The bridge stores only that number, a receive timestamp and a hashed session identifier under ignored `tools/activity/<provider>/`. Prompts, responses, credentials and unrelated fields are discarded. The host detects increases after its startup baseline. The same payload can be supplied with `--ingest cursor`, `--ingest antigravity` or `--ingest opencode`. Source installations use `python tools/aim_control.py` instead of the executable.

Copilot SDK exposes live `assistant.usage` events with input/output token counts, while some events are ephemeral and are not replayed on resume. Accumulate the counts in your SDK application and forward the running total. This does not monitor all VS Code Copilot use automatically. [Official Copilot SDK usage guide](https://github.com/github/copilot-sdk/blob/main/docs/features/usage-and-billing.md).

Cursor's documented [Admin API](https://docs.cursor.com/en/account/teams/admin-api) is a team-admin interface; it is not assumed to provide a personal real-time quota. Antigravity exposes an [interactive usage command](https://www.antigravity.google/docs/cli/commands/usage/), without an adapter for that service here. [OpenCode SDK](https://docs.opencode.ai/docs/sdk/) provides an integration surface; the external export must be supplied by its user.

## Privacy and limits

SQLite sources are queried read-only. Log adapters parse local records to extract usage; conversation content is never retained, logged or exported by the monitor. Reads, file counts and remembered IDs are bounded, so the display is an activity monitor rather than a complete historical ledger. First samples establish baselines. Missing or malformed sources cannot establish activity. Fresh source reports keep NOVA responsive; token registration can lag generation.

Use firmware **v1.11.0+** for the additional provider/source flags. If the display has v1.10.x, use the menu's application update before starting those providers. The host rejects unsupported additional-provider firmware with an update message.
