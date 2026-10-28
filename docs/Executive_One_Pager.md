# SAVI Bench — Executive One-Pager

> **Status notice (2026-10-28).** This repository is a benchmark harness under repair and does not currently publish verified benchmark results. The DS005 "10,000-agent / $250-cap" proof pack was generated in synthetic mode: its manifest records `mode: synthetic` with no model or API, and its task count and cost were computed from configuration rather than executed. Dashboard scores produced in synthetic mode were random placeholders, an automatic "pass" row was added for every run regardless of outcome, and every real-mode task logged so far scored 0. Automatic hourly runs are paused. Please do not cite figures from this repository until a verified run is published.

- Problem: AI benchmarks are one-off, opaque, and non‑verifiable.
- Solution: SAVI Bench — continuous, transparent, cryptographically verifiable AGI benchmarking.
- Patent‑Pending Innovation: 4‑phase cognitive cycle (Warm‑up → Strength → Endurance → Competition) + tamper‑evident proof packs.

## Proof Points
- 10,000‑agent runs with strict $250 budget cap and manifest evidence (stop_reason=budget_cap_reached_250.0).
- Lower latency and cost per query vs baseline; reproducible success metrics.
- Hourly continuous validation since Sept 2025 with public artifacts and checksums.

## Call to Action
- DS005 Proof Pack and replay: https://github.com/FaithoverCP/savi-bench/releases/tag/DS005-20250908
- Scan QR to open DS005 (insert in materials):
  - PowerShell: `Start-Process https://github.com/FaithoverCP/savi-bench/releases/tag/DS005-20250908`
  - Optional: generate a QR PNG with Python: `pip install qrcode[pil] && python - <<<'import qrcode; qrcode.make("https://github.com/FaithoverCP/savi-bench/releases/tag/DS005-20250908").save("qr_ds005.png")'`
