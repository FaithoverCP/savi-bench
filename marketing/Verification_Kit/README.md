# Verification Kit — DS005

> **Status notice (2026-10-28).** This repository is a benchmark harness under repair and does not currently publish verified benchmark results. The DS005 "10,000-agent / $250-cap" proof pack was generated in synthetic mode: its manifest records `mode: synthetic` with no model or API, and its task count and cost were computed from configuration rather than executed. Dashboard scores produced in synthetic mode were random placeholders, an automatic "pass" row was added for every run regardless of outcome, and every real-mode task logged so far scored 0. Automatic hourly runs are paused. Please do not cite figures from this repository until a verified run is published.

Contents
- Executive Summary (docs/Executive_One_Pager.md)
- Technical Whitepaper (docs/Whitepaper_Draft.md)
- Screenshots (capture from index.html + reports/latest.html)
- DS005 Proof Pack (download from release)
- Verification Instructions (below)

Verification Steps (Windows PowerShell)
1) Download `proof_pack_FULL.tgz` and `sha256sums.txt` from the DS005 release.
2) In your download folder (quote paths that contain spaces):
   - `Get-FileHash .\\proof_pack_FULL.tgz -Algorithm SHA256`
   - `Get-Content   .\\sha256sums.txt`
   - Ensure the tarball hash appears in `sha256sums.txt` (case‑insensitive).
3) Optional: verify CSV/HTML too:
   - `Get-FileHash .\\latency_summary.csv -Algorithm SHA256`
   - `Get-FileHash .\\latest.html         -Algorithm SHA256`
4) (Repo replay) Clone repo and run a capped replay using `tools/replay.ps1`.
5) Rebuild the pack: `python tools/summarize_and_pack.py`; compare hashes.

Linux/macOS
- Use `sha256sum` to compute hashes and compare to `sha256sums.txt`.

Release Link
- DS005: https://github.com/FaithoverCP/savi-bench/releases/tag/DS005-20250908
