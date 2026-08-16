#!/usr/bin/env python3
"""EOS status — finished product, no re-teach.

Reports Path A/B reality, scorecard packet freshness, control-log presence,
and whether L10 can actually run. Does not invent metrics.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCORE = HERE.parents[1] / "core" / "scorecard"
CTRL_LOG = HERE / "state" / "eos_control_log.jsonl"


def ok(msg: str) -> None:
    print(f"  OK  {msg}")


def bad(msg: str) -> None:
    print(f"  BAD {msg}")


def info(msg: str) -> None:
    print(f"  ·   {msg}")


def can_import(mod: str) -> bool:
    return importlib.util.find_spec(mod) is not None


def main() -> int:
    print("=== EOS STATUS ===")
    print(f"utc: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    print(f"root: {HERE}")
    print()

    print("--- Protocol (Path A kernel on disk) ---")
    for name in (
        "eos_protocol.py",
        "model_tiers.py",
        "integrity.py",
        "escalation.py",
        "l10_meeting.py",
        "eos_grok_proxy.py",
        "PATH_B_PLAN.md",
        "TIMELINE.md",
    ):
        p = HERE / name
        (ok if p.exists() else bad)(name)

    print()
    print("--- L10 runnable? ---")
    l10 = (HERE / "l10_meeting.py").read_text(encoding="utf-8", errors="replace")
    agents = (HERE / "agents.py").read_text(encoding="utf-8", errors="replace")
    if "google.antigravity" in l10 or "google.antigravity" in agents:
        bad("antigravity import still present in l10/agents — rebuild incomplete")
    else:
        ok("l10_meeting.py + agents.py free of google.antigravity")
    if (HERE / "seat_runtime.py").exists():
        ok("seat_runtime.py present (dry|grok)")
    else:
        bad("seat_runtime.py missing")
    backend = (os.environ.get("EOS_BACKEND") or "dry").lower()
    info(f"EOS_BACKEND={backend} (default dry — no cloud required)")
    if os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY"):
        ok("Grok/xAI key present — EOS_BACKEND=grok available")
    else:
        info("no XAI_API_KEY — use dry (default) or export key for grok")
    # google package optional leftover — not required
    if can_import("google"):
        info("python 'google' package installed but NOT required for L10")

    print()
    print("--- Control log ---")
    if CTRL_LOG.exists():
        n = sum(1 for _ in CTRL_LOG.open())
        ok(f"eos_control_log.jsonl lines={n}")
    else:
        info("no control log yet (no L10 turns routed)")

    print()
    print("--- Scorecard ---")
    packet_dir = SCORE / "packets"
    if packet_dir.is_dir():
        packets = sorted(packet_dir.glob("*.md"))
        if packets:
            latest = packets[-1]
            ok(f"latest packet {latest.name}")
            # show OFF / NO DATA counts
            text = latest.read_text(encoding="utf-8", errors="replace")
            for label in ("NO DATA", "**OFF**", "**OK**", "ON"):
                if label in text:
                    info(f"packet contains marker: {label}")
        else:
            bad("no packets — run: cd core/scorecard && python3 packet.py")
    else:
        bad(f"missing {packet_dir}")

    print()
    print("--- Path summary ---")
    info("Path A: antigravity-free L10 (dry default, optional grok) — SHIPPED")
    info("Path B: open-weights terminator tokens — PLANNED only (PATH_B_PLAN.md)")
    info("Run: EOS_BACKEND=dry python3 main.py")
    print()
    print("=== END EOS STATUS ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
