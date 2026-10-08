"""Read numeric local token counters only. No chat content or credentials."""
import sqlite3
from contextlib import closing
import time
from pathlib import Path


class TokenReporter:
    def __init__(self, home=None, clock=None):
        home = Path.home() if home is None else Path(home)
        self.paths = {"codex": home / ".codex/state_5.sqlite", "zcode": home / ".zcode/cli/db/db.sqlite"}
        self.clock = time.monotonic if clock is None else clock
        self.started = None
        self.previous = {}
        self.last_use = None
        self.last_poll = None

    @staticmethod
    def read_counts(provider, path):
        if not path.is_file():
            return None
        query = ("SELECT id,tokens_used FROM threads ORDER BY updated_at_ms DESC LIMIT 512" if provider == "codex" else
                 "SELECT id,computed_total_tokens FROM model_usage ORDER BY started_at DESC LIMIT 4096")
        try:
            with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=0.15)) as database:
                database.execute("PRAGMA query_only=ON")
                return {str(key): count for key, count in database.execute(query)
                        if type(count) is int and 0 <= count <= 0xffffffffffffffff}
        except (sqlite3.Error, OSError):
            return None

    def poll(self):
        now = self.clock()
        if self.started is None:
            self.started = now
        if self.last_poll is not None and now - self.last_poll < 2:
            return None
        self.last_poll = now
        delta, sources = 0, 0
        for provider, bit in [("codex", 1), ("zcode", 2)]:
            counts = self.read_counts(provider, self.paths[provider])
            if counts is None:
                continue
            sources |= bit
            previous = self.previous.get(provider)
            if previous is not None:
                for key, value in counts.items():
                    # Codex forks/imports can contain history on first sight. Baseline new thread IDs.
                    old = previous.get(key, value if provider == "codex" else 0)
                    delta += max(0, value - old)
            self.previous[provider] = dict(counts)
        if delta:
            self.last_use = now
        idle = max(0, int(now - (self.last_use if self.last_use is not None else self.started)))
        return {"cmd": "token_activity", "known": bool(sources), "seen": self.last_use is not None,
                "sources": sources, "idleSeconds": min(0xffffffff, idle), "delta": min(0xffffffffffffffff, delta)}
