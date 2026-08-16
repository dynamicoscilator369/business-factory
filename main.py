#!/usr/bin/env python3
"""Company kernel CLI — run pipeline or L10 for any business module."""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from kernel.business import business_root, list_businesses, load_manifest, load_pipeline  # noqa: E402


def _setup_orchestrator(business_id: str) -> dict:
    manifest = load_manifest(business_id)
    root = business_root(business_id)
    scorecard = root / "scorecard.csv"
    os.environ["COMPANY_KERNEL_ROOT"] = str(ROOT)
    os.environ["BUSINESS_ID"] = business_id
    os.environ["BUSINESS_ROOT"] = str(root)
    os.environ["SCORECARD_REGISTRY"] = str(scorecard)
    os.environ["ORCHESTRATOR_STATE"] = str(root / ".state" / "eos")
    (root / ".state" / "eos").mkdir(parents=True, exist_ok=True)
    return manifest


def cmd_pipeline(business_id: str) -> int:
    pipeline = load_pipeline(business_id)
    result = pipeline.run()
    runs_file = business_root(business_id) / ".state" / "pipeline_runs.txt"
    try:
        n = int(runs_file.read_text().strip()) if runs_file.exists() else 0
    except ValueError:
        n = 0
    runs_file.write_text(str(n + 1), encoding="utf-8")
    print(result)
    return 0


def cmd_l10(business_id: str) -> int:
    manifest = _setup_orchestrator(business_id)
    sys.path.insert(0, str(ROOT / "orchestrator"))
    from l10_business import run_l10_for_business  # noqa: E402

    asyncio.run(run_l10_for_business(manifest))
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    for bid in list_businesses():
        m = load_manifest(bid)
        print(f"  {bid:20} {m.get('name', '')}")
    print(f"\n  _template/              copy source — run ./new-business.sh <id>")
    print(f"  examples/               reference implementations (not your active businesses)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Company kernel — any business idea")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("pipeline", help="Run sync → build → validate → distribute")
    p_run.add_argument("business", help="Business id (folder under businesses/)")

    p_l10 = sub.add_parser("l10", help="Run EOS Level 10 meeting for this business")
    p_l10.add_argument("business", help="Business id")

    sub.add_parser("list", help="List registered businesses")

    args = parser.parse_args()
    if args.cmd == "list":
        return cmd_list(args)
    if args.cmd == "pipeline":
        return cmd_pipeline(args.business)
    if args.cmd == "l10":
        return cmd_l10(args.business)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
