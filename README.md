# savi-bench

> **Status (2026-10-28).** This repository is a small benchmark harness. It does not publish verified benchmark results. On 2026-10-28 the earlier dashboard data and the DS005 "10,000-agent / $250-cap" proof pack were removed because they did not reflect real runs: the proof pack was generated in synthetic mode (no model or API was called, and its task count and cost were computed from configuration), synthetic dashboard scores were random placeholders, an automatic "pass" row was added for every run, and every real-mode task logged scored 0. The removed files remain in git history. Automatic runs are paused.

## What this is
A minimal harness that sends a small task suite (`bench/suites/`) to an OpenAI-compatible endpoint, grades the replies (`bench/grade.py`) and writes a report.
With no API key configured it runs in synthetic mode, which writes placeholder rows labelled `synthetic`. Those are never benchmark results.

## Run it
```
python -m bench.run --config bench/config.json --profile savi_openai_62
python -m bench.report --config bench/config.json
```
Set `OPENAI_API_KEY` (or `SAVI_API_KEY` and `SAVI_API_BASE`) for a real run. Manifests record only tasks that actually executed.
