# SAVI Bench — Demo Flow (DS005)

1) Open the DS005 release
- URL: https://github.com/FaithoverCP/savi-bench/releases/tag/DS005-20250908
- Point out the green status + latest.html asset.

2) Show the human report
- Open `latest.html` directly from assets.
- Call out phase stats, best Competition run, retries, and pass rate.

3) Show the proof mechanics
- Highlight `proof_pack_FULL.tgz` and `sha256sums.txt`.
- Explain integrity: any third party can hash the files and match against `sha256sums.txt`.

4) (If technical) Replay locally
- Use `tools/replay.ps1` for a capped run: `./tools/replay.ps1 -Profile savi_openai_1000 -Budget 250 -Config bench/config.json`.
- Then `python tools/summarize_and_pack.py` to rebuild the pack; verify with `tools/verify.ps1`.

Key lines to rehearse
- “Others test once; we test every hour.”
- “Every result has a manifest and checksum — no smoke & mirrors.”
- “Budget caps are enforced by design; you can see stop_reason in the manifest.”
