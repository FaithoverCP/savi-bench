import argparse
import json
from pathlib import Path
from datetime import datetime


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate benchmark report")
    parser.add_argument(
        "--config", default="bench/config.yaml", help="Path to configuration file"
    )
    parser.add_argument(
        "--output", default="reports/summary.json", help="Report output file"
    )
    args = parser.parse_args()

    config = load_config(args.config)
    results_dir = Path(config.get("results_dir", "results"))

    summary = {}
    if results_dir.exists():
        for file in results_dir.glob("*.txt"):
            summary[file.stem] = file.read_text(encoding="utf-8").strip()

    report = {
        "generated": datetime.utcnow().isoformat(),
        "results": summary,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Wrote report to {output_path}")


if __name__ == "__main__":
    main()
