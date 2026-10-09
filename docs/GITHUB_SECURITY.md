# GitHub security

Public source does not grant a reader access to the maintainer's PC. Readers can copy the code and propose pull requests; they cannot push changes to this repository without explicit write permission. The monitor does not auto-pull or execute code from GitHub on the maintainer's PC. Review a contribution before running it locally or merging it.

## Repository controls verified on 2026-10-09

- The owner is the only account with repository write/admin access. No deploy keys, webhooks or self-hosted Actions runners are configured. Repository Actions secrets and variables are empty. Builds run on GitHub-hosted Ubuntu/Windows machines.
- The default workflow token is read-only and cannot approve pull requests. All external contributor workflows require maintainer approval. Read the code and workflow diff before approving; approval permits code execution on a GitHub runner.
- Actions are limited to checkout, setup-python, upload-artifact and download-artifact from the official `actions` organization. Full commit SHA pinning is required by repository policy. Checkouts do not retain Git credentials.
- Main branch deletion and force pushes are blocked. Existing `v*` tags cannot be moved or deleted. Only administrators can create new version tags. Normal owner commits remain possible.
- Build/test jobs use read-only repository permission. Release publishing is a separate job: it downloads this run's package and creates a draft with an existing version tag. It does not check out or execute repository code, install dependencies, or run the generated executables. Only that publisher has contents-write permission. A maintainer still reviews and publishes the draft.
- Secret scanning, push protection, private vulnerability reporting and Dependabot security updates are enabled. CI checks dependency advisories. Local provider keys/configuration, CLI auth, logs and databases are excluded from Git and release exports.
- Release immutability is enabled for future publications. Once a new immutable release is published, its assets and associated tag are locked. Existing v1.12.0/v1.12.1 release assets were published before this setting and are not retroactively immutable; their tags are separately protected by the repository rules. Do not replace published assets: make a new reviewed version.

The repository cannot protect against takeover of its owner's GitHub account. Keep two-factor authentication or a passkey enabled, keep recovery methods private, and review newly authorized GitHub applications/tokens. The current API connection does not expose the owner's two-factor status; it was not verified. Checksums alone do not authenticate an asset obtained with its checksum from a compromised account.

Policy tests check pinned Actions, disabled checkout credential persistence, GitHub-hosted runners, the isolated write-permission job, draft-only/tag-verified publishing and absence of privileged pull-request triggers or named secrets. Install `scripts/requirements-test.txt` to run these tests locally. These tests complement the server settings; those settings must be reviewed independently if the repository is copied to another owner.

Sources: [fork workflow approval and repository Actions policy](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository), [immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases), [future-only release immutability](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes).
