#!/usr/bin/env python3
"""
Generate syndication posts for every channel in distribute.json.

Writes ready-to-paste (or Postiz-ready) copy into ./outbox/<date>/.

Usage:
    python3 distribute.py
    python3 distribute.py --turkey-only
    python3 distribute.py --job mercor-music-lyrics-expert-turkish
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from datetime import date

ROOT = pathlib.Path(__file__).parent
OUTBOX = ROOT / "outbox"
JOBS_FILE = ROOT / "jobs.json"
CONFIG_FILE = ROOT / "config.json"
DIST_FILE = ROOT / "distribute.json"

# Minimal TR gloss for forum posts when we don't have a native description.
TR_HINTS = {
    "music": "Müzik ve yapay zeka eğitimi",
    "production": "Prodüksiyon / ses",
    "turkey": "Türkiye / Türkçe",
    "remote": "Uzaktan",
}


def load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def money(job: dict) -> str:
    lo, hi = job.get("payMin"), job.get("payMax")
    if not lo and not hi:
        return "See listing"
    cur = {"USD": "$", "EUR": "€", "GBP": "£"}.get(job.get("currency", "USD"), "$")
    unit = {"HOUR": "/hr", "DAY": "/day", "MONTH": "/mo"}.get(job.get("payUnit", "HOUR"), "/hr")
    if lo and hi and lo != hi:
        return f"{cur}{lo:g}–{cur}{hi:g}{unit}"
    return f"{cur}{(lo or hi):g}{unit}"


def job_url(job: dict, cfg: dict) -> str:
    base = cfg.get("baseUrl", "https://example.com").rstrip("/")
    return f"{base}/jobs/{job['id']}.html"


def summary_tr(job: dict) -> str:
    base = job.get("summary", job.get("title", ""))
    extras = []
    for v in job.get("verticals", []):
        if v in TR_HINTS:
            extras.append(TR_HINTS[v])
    if "turkish" in job.get("title", "").lower() or "turkey" in job.get("region", "").lower():
        extras.append("Türk müzik sahnesi bilgisi aranıyor")
    suffix = " · ".join(dict.fromkeys(extras))
    return f"{base} ({suffix})" if suffix else base


def vertical_match(job: dict, channel: dict) -> bool:
    req = channel.get("verticals")
    if not req:
        return True
    job_v = set(job.get("verticals", []))
    job_v.update(job.get("tags", []))
    title = job.get("title", "").lower()
    if "turkey" in req and ("turkish" in title or job.get("region", "").lower() == "turkey"):
        job_v.add("turkey")
    return bool(job_v & set(req)) or not req


def pick_template(channel: dict, templates: dict) -> str:
    lang = channel.get("lang", "en")
    ctype = channel.get("type", "forum")
    if lang == "tr":
        return templates["tr_social" if ctype == "social" else "tr_forum"]
    return templates["en_social" if ctype == "social" else "en_forum"]


def render(template: str, job: dict, cfg: dict) -> str:
    return template.format(
        title=job.get("title", ""),
        summary=job.get("summary", ""),
        summary_tr=summary_tr(job),
        pay=money(job),
        region=job.get("region", "Worldwide"),
        source=job.get("source", "aggregator").title(),
        category=job.get("category", "Contract"),
        job_url=job_url(job, cfg),
    )


def safe_name(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", s).strip("-")[:60]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--turkey-only", action="store_true")
    parser.add_argument("--job", default="", help="Single job id slug")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    cfg = load_json(CONFIG_FILE)
    dist = load_json(DIST_FILE)
    jobs = load_json(JOBS_FILE)
    templates = dist["templates"]

    if args.job:
        jobs = [j for j in jobs if j["id"] == args.job]
        if not jobs:
            raise SystemExit(f"No job with id {args.job!r}")

    if args.turkey_only:
        jobs = [
            j for j in jobs
            if "turkey" in j.get("verticals", [])
            or "turkish" in j.get("title", "").lower()
            or j.get("region", "").lower() == "turkey"
        ]

    if args.limit:
        jobs = jobs[: args.limit]

    today = date.today().isoformat()
    day_dir = OUTBOX / today
    day_dir.mkdir(parents=True, exist_ok=True)

    manifest = {"date": today, "posts": []}
    postiz_queue = []

    sections = {"global": dist["channels"]["global"]}
    if not args.turkey_only:
        sections["turkey"] = dist["channels"]["turkey"]
    else:
        sections = {"turkey": dist["channels"]["turkey"]}

    for section, channels in sections.items():
        sec_dir = day_dir / section
        sec_dir.mkdir(exist_ok=True)
        for job in jobs:
            for ch in channels:
                if not vertical_match(job, ch):
                    continue
                body = render(pick_template(ch, templates), job, cfg)
                fname = safe_name(f"{ch['id']}__{job['id']}.txt")
                out_path = sec_dir / fname
                post_via = "manual paste" if ch.get("type") == "forum" else ch.get("type", "social")
                header = (
                    f"# Channel: {ch['name']}\n"
                    f"# Job: {job['title']}\n"
                    f"# URL: {ch.get('url', 'n/a')}\n"
                    f"# Post via: {post_via}\n"
                )
                if ch.get("notes"):
                    header += f"# Notes: {ch['notes']}\n"
                header += "\n"
                out_path.write_text(header + body + "\n", encoding="utf-8")

                entry = {
                    "channel": ch["id"],
                    "channelName": ch["name"],
                    "jobId": job["id"],
                    "file": str(out_path.relative_to(ROOT)),
                    "lang": ch.get("lang", "en"),
                    "postiz": bool(ch.get("postiz")),
                }
                manifest["posts"].append(entry)
                if ch.get("postiz"):
                    postiz_queue.append({
                        "integration_hint": ch["id"],
                        "content": body,
                        "job_url": job_url(job, cfg),
                    })

    (day_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (day_dir / "postiz-queue.json").write_text(
        json.dumps(postiz_queue, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Generated {len(manifest['posts'])} posts → {day_dir}")
    print(f"  Postiz-ready: {len(postiz_queue)}")
    print(f"  Manifest: {day_dir / 'manifest.json'}")
    if cfg.get("baseUrl", "").startswith("https://example.com"):
        print("\n  ! Set baseUrl in config.json before publishing — job links are placeholders.")


if __name__ == "__main__":
    main()
