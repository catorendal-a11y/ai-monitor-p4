# Security

Firmware needs no provider credentials. The Python companion reads local credentials at runtime and sends quota/activity over USB. Token activity uses read-only queries of numeric counters and identifiers.

Do not commit `tools/aim_host.json`, environment files, CLI auth, keys, databases or logs. The example key stays empty. `.env.example` is documentation only; the companion does not automatically load it. Keep logs private even when error messages are sanitized.

Tests must use synthetic credentials/responses. Do not mix debug serial logging with a production companion on the same port. Provider responses and USB messages are untrusted; retain size limits, type validation and bounded buffers.

## Reporting

If the published GitHub repository enables private reporting, use **Security → Report a vulnerability**. Otherwise contact the repository owner privately through a channel listed on their GitHub profile. Do not post exploit details, credentials or account data in public issues. This source package contains no maintainer email or promised response deadline.

Include version, impact and a minimal synthetic reproduction. Revoke exposed keys through their provider before sharing a report. Deleting a file does not remove it from Git history.

Fixes target the current release; older forks may need backports.