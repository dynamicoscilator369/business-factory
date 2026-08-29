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

from kernel.business import (  # noqa: E402
    business_root,
    list_businesses,
    load_manifest,
    load_pipeline,
    record_pipeline_run,
)


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
    """In-process run (no Temporal). Prefer ``start`` + ``worker`` on Cloud."""
    pipeline = load_pipeline(business_id)
    result = pipeline.run()
    record_pipeline_run(business_id)
    from kernel.hf_bucket import publish_business, resolve_bucket_id

    if resolve_bucket_id(load_manifest(business_id)):
        result["bucket"] = publish_business(business_id)
    print(result)
    return 0


def cmd_publish(business_id: str) -> int:
    from kernel.hf_bucket import publish_business

    print(publish_business(business_id))
    return 0


def cmd_worker() -> int:
    from kernel.temporal.worker import run_worker

    asyncio.run(run_worker())
    return 0


def cmd_start(business_id: str) -> int:
    load_manifest(business_id)
    from kernel.temporal.starter import start_pipeline

    result = asyncio.run(start_pipeline(business_id))
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

    p_run = sub.add_parser(
        "pipeline",
        help="Run sync → build → validate → distribute in-process (no Temporal)",
    )
    p_run.add_argument("business", help="Business id (folder under businesses/)")

    p_start = sub.add_parser(
        "start",
        help="Start a pipeline Workflow on Temporal (cloud-setup profile)",
    )
    p_start.add_argument("business", help="Business id (folder under businesses/)")

    p_pub = sub.add_parser(
        "publish",
        help="Upload pipeline artifacts to the Hugging Face Storage Bucket",
    )
    p_pub.add_argument("business", help="Business id (folder under businesses/)")

    sub.add_parser(
        "worker",
        help="Run the Temporal Worker (cloud-setup profile, task queue business-factory-pipeline)",
    )

    p_l10 = sub.add_parser("l10", help="Run EOS Level 10 meeting for this business")
    p_l10.add_argument("business", help="Business id")

    sub.add_parser("list", help="List registered businesses")

    args = parser.parse_args()
    if args.cmd == "list":
        return cmd_list(args)
    if args.cmd == "pipeline":
        return cmd_pipeline(args.business)
    if args.cmd == "start":
        return cmd_start(args.business)
    if args.cmd == "publish":
        return cmd_publish(args.business)
    if args.cmd == "worker":
        return cmd_worker()
    if args.cmd == "l10":
        return cmd_l10(args.business)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
