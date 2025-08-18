import argparse
import json
from pathlib import Path
from datetime import datetime


def load_config(path: str) -> dict:
    """Load configuration from a JSON/YAML file."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SAVI benchmarks")
    parser.add_argument(
        "--config", default="bench/config.yaml", help="Path to configuration file"
    )
    parser.add_argument(
        "--profile", required=True, help="Benchmark profile to execute"
    )
    args = parser.parse_args()

    config = load_config(args.config)
    profiles = config.get("profiles", {})
    if args.profile not in profiles:
        raise SystemExit(f"Profile '{args.profile}' not found in {args.config}")

    results_dir = Path(config.get("results_dir", "results"))
    manifests_dir = Path(config.get("manifests_dir", "manifests"))
    results_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().isoformat()

    result_file = results_dir / f"{args.profile}.txt"
    result_file.write_text(f"profile: {args.profile}\nrun: {timestamp}\n", encoding="utf-8")

    manifest = {
        "profile": args.profile,
        "timestamp": timestamp,
        "config": args.config,
    }
    manifest_file = manifests_dir / f"{args.profile}.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote {result_file} and {manifest_file}")


if __name__ == "__main__":
    main()
