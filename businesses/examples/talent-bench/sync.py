#!/usr/bin/env python3
"""
Sync live listings from Mercor, Outlier, and DataAnnotation into jobs.json.

Tracks first-seen / last-seen per source ID so new postings and takedowns
are detected on every run. Keeps the board fresh.

Usage:
    python3 sync.py              # sync music/production/turkey focus (config)
    python3 sync.py --all        # sync every Mercor listing on explore
    python3 sync.py --sources mercor,outlier
    python3 sync.py --dry-run    # report changes without writing jobs.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).parent
STATE_DIR = ROOT / ".state"
STATE_FILE = STATE_DIR / "sync-state.json"
JOBS_FILE = ROOT / "jobs.json"
CONFIG_FILE = ROOT / "config.json"

sys.path.insert(0, str(ROOT))

from sources.common import RawJob, matches_filter, slugify  # noqa: E402
from sources import dataannotation, mercor, outlier  # noqa: E402

FETCHERS = {
    "mercor": lambda cfg: mercor.fetch_all(
        referral_url=cfg.get("referralUrl"),
        url_keywords=cfg.get("_mercor_url_keywords"),
    ),
    "outlier": lambda cfg: outlier.fetch_all(),
    "dataannotation": lambda cfg: dataannotation.fetch_all(),
}


def load_json(path: pathlib.Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def save_json(path: pathlib.Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def job_slug(raw: RawJob) -> str:
    return slugify(f"{raw.source}-{raw.source_id}")[:96]


def merge_apply_url(raw: RawJob, cfg: dict) -> str | None:
    referrals = cfg.get("sourceReferrals", {})
    default = referrals.get(raw.source) or cfg.get("referralUrl")
    # Keep platform-specific signup links for non-Mercor sources.
    if raw.source != "mercor":
        return raw.apply_url or default
    return default


def raw_to_export(raw: RawJob, cfg: dict) -> dict:
    d = raw.to_job_dict(job_slug(raw))
    d["applyUrl"] = merge_apply_url(raw, cfg)
    return d


def load_state() -> dict:
    return load_json(STATE_FILE, {"sources": {}, "history": []})


def update_state(state: dict, active: dict[str, RawJob], now: str) -> tuple[list[str], list[str]]:
    """Return (new_ids, removed_ids) keyed as source:source_id."""
    prev_active = {
        k for k, v in state.get("sources", {}).items()
        if v.get("status") == "active"
    }
    curr_active = set(active.keys())

    new_ids = sorted(curr_active - prev_active)
    removed_ids = sorted(prev_active - curr_active)

    sources = state.setdefault("sources", {})
    for key, raw in active.items():
        entry = sources.setdefault(key, {})
        entry.update({
            "source": raw.source,
            "sourceId": raw.source_id,
            "sourceUrl": raw.source_url,
            "title": raw.title,
            "firstSeen": entry.get("firstSeen") or now,
            "lastSeen": now,
            "status": "active",
        })

    for key in removed_ids:
        entry = sources.setdefault(key, {})
        entry["status"] = "removed"
        entry["removedAt"] = now
        state.setdefault("history", []).append({
            "at": now,
            "event": "removed",
            "key": key,
            "title": entry.get("title"),
        })

    for key in new_ids:
        state.setdefault("history", []).append({
            "at": now,
            "event": "added",
            "key": key,
            "title": active[key].title,
        })

    state["lastSync"] = now
    return new_ids, removed_ids


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync aggregator job sources")
    parser.add_argument("--all", action="store_true", help="Disable vertical keyword filter")
    parser.add_argument("--sources", default="", help="Comma-separated: mercor,outlier,dataannotation")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cfg = load_json(CONFIG_FILE, {})
    sync_cfg = cfg.get("sync", {})
    keywords = [] if args.all else sync_cfg.get("keywords", [
        "music", "lyrics", "audio", "production", "sound", "composer",
        "mix", "master", "studio", "turkish", "turkey", "video creator",
    ])
    enabled = [s.strip() for s in (args.sources or ",".join(sync_cfg.get("sources", FETCHERS))).split(",") if s.strip()]

    # Pre-filter Mercor URL slugs before fetching 300+ detail pages.
    if keywords and "mercor" in enabled:
        cfg["_mercor_url_keywords"] = [
            k for k in keywords
            if k in ("music", "lyrics", "audio", "production", "video", "turkish", "sound")
        ] or ["music"]
    else:
        cfg["_mercor_url_keywords"] = None

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    state = load_state()
    collected: list[RawJob] = []

    print(f"Sync started {now}")
    for name in enabled:
        if name not in FETCHERS:
            print(f"  ! unknown source: {name}")
            continue
        print(f"  → fetching {name}…", end=" ", flush=True)
        try:
            batch = FETCHERS[name](cfg)
        except Exception as exc:
            print(f"FAILED ({exc})")
            continue
        before = len(batch)
        if keywords:
            batch = [j for j in batch if matches_filter(j, keywords)]
        print(f"{before} raw → {len(batch)} after filter")
        collected.extend(batch)

    active_map: dict[str, RawJob] = {}
    for raw in collected:
        key = f"{raw.source}:{raw.source_id}"
        active_map[key] = raw

    new_ids, removed_ids = update_state(state, active_map, now)

    jobs = [raw_to_export(raw, cfg) for raw in collected]
    # stable sort: newest first, then title
    jobs.sort(key=lambda j: (j.get("datePosted", ""), j.get("title", "")), reverse=True)

    print(f"\nActive listings: {len(jobs)}")
    print(f"  New since last run: {len(new_ids)}")
    print(f"  Removed since last run: {len(removed_ids)}")

    if new_ids:
        print("\n  Added:")
        for k in new_ids[:15]:
            print(f"    + {active_map[k].title} ({k})")
        if len(new_ids) > 15:
            print(f"    … and {len(new_ids) - 15} more")

    if removed_ids:
        print("\n  Removed:")
        for k in removed_ids[:15]:
            t = state["sources"].get(k, {}).get("title", k)
            print(f"    - {t} ({k})")
        if len(removed_ids) > 15:
            print(f"    … and {len(removed_ids) - 15} more")

    if args.dry_run:
        print("\n(dry run — jobs.json and state not written)")
        return

    save_json(JOBS_FILE, jobs)
    save_json(STATE_FILE, state)
    print(f"\nWrote {len(jobs)} jobs → {JOBS_FILE}")
    print(f"State → {STATE_FILE}")
    print("\nNext: python3 build.py && python3 validate.py")


if __name__ == "__main__":
    main()
