"""Explicit provider choices and their supported data sources."""
PROVIDERS = {
    'codex': ('Codex', 1, 'Local tokens + existing CLI-login quota adapter'),
    'zcode': ('ZCode', 2, 'Local tokens + optional Z.AI coding-plan quota key'),
    'claude': ('Claude Code', 4, 'Local CLI token logs + optional official statusline quota bridge'),
    'gemini': ('Gemini CLI', 8, 'Local CLI tokens; automatic account quota not available'),
    'copilot': ('GitHub Copilot', 16, 'External numeric bridge required; SDK usage events are supported'),
    'cursor': ('Cursor', 32, 'External numeric bridge required; no automatic personal-quota adapter'),
    'antigravity': ('Antigravity', 64, 'External numeric bridge required; no automatic quota adapter'),
    'opencode': ('OpenCode', 128, 'External numeric bridge required; SDK usage export can be supplied'),
}


def selected_providers(config, legacy=False):
    values = config.get('providers')
    if values is None:
        # Preserve the choices implied by old installed configs, never a new installation.
        values = ['codex'] + (['zcode'] if config.get('zai_key') else []) if legacy else []
    if not isinstance(values, list) or len(values) > len(PROVIDERS) or any(not isinstance(v, str) or v not in PROVIDERS for v in values):
        raise ValueError('providers must be a list of supported provider IDs')
    if len(set(values)) != len(values):
        raise ValueError('providers must not contain duplicates')
    return list(values)
