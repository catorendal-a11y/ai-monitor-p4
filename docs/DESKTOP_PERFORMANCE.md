# Desktop performance check

Controlled Windows offscreen measurements on October 10, 2026 compared tagged v1.17.2 with v1.18.1. Each version used the same synthetic Copilot/COM9999 configuration. Token-source polling was mocked; no accounts, provider API calls or USB writes were used. A 20 ms event-loop probe also contributes to the reported CPU use.

| Measurement | v1.17.2 | v1.18.1 |
| --- | --- | --- |
| Warm startup to constructed widgets, reverse-order repeat | 163 ms | 168 ms |
| Visible RSS, two samples | 67.9–68.9 MiB | 69.3–69.9 MiB |
| Minimized RSS, two samples | 68.2–69.4 MiB | 69.3–70.0 MiB |
| Event-loop delay p95, visible/minimized | About 2 ms | About 2 ms |
| UI status/token refreshes in a 10 s minimized phase | 4 | 0 |
| UI status/token refreshes in a 5 s minimized phase | 2 | 0 |

CPU was below 1% of one core in all fixture phases. At this low load, Windows CPU-time tick quantization and the probe dominate short samples, so the data does not establish a precise CPU percentage reduction. The reliable improvement is that hidden windows stop redundant GUI token/database polling while the independent host continues monitoring. Lightweight tray status runs every ten seconds. Restore starts a fresh local activity baseline instead of displaying a catch-up burst.

The first baseline startup took 454 ms and the first candidate 180 ms; DLL/file cache conditions differed. These values are not evidence of a startup speedup. The reverse-order warm repeat was effectively unchanged. Memory increased by about 1–2 MiB in the controlled source test; packaged/native rendering and real provider databases need separate measurements.

Run the reproducible fixture from the public source:

```text
python scripts/benchmark_desktop.py --seconds 10 --output work/desktop-performance.json
```

This measures GUI work, not network/provider latency or physical display rendering. It must not generate model requests or use real credentials. Runtime measurements on a user's PC should retain logs and identifiers locally, not include them in public exports.
