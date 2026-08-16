#!/usr/bin/env python3
"""
Generate Grok Bot org charts and agent briefs for tier presets 3→111.

Usage:
    python3 generate-org.py              # generate all presets
    python3 generate-org.py --tier 21    # one tier only
    python3 generate-org.py --tier 42 --open-index
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import textwrap

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "generated"
TIERS_FILE = ROOT / "tiers.json"
CONTEXT = ROOT / "CONTEXT.md"

# Priority-ordered role catalog — first N roles fill tier N.
# Scales from 3 bots (chief + scout + syndicator) to full 111-bot factory.
ROLES: list[dict] = [
    # --- command ---
    {"id": "chief", "dept": "command", "title": "Chief Coordinator",
     "job": "You report to the human apex. Route work across all bots. Read .state/handoff.json hourly. Escalate failures."},

    # --- tier 3 core workers (you + chief + these 2 = minimal factory) ---
    {"id": "scout", "dept": "pipeline", "title": "Scout (Pipeline Runner)",
     "job": "Execute run-pipeline.sh every 6h. 5-line summary to chief on changes only."},
    {"id": "syndicator", "dept": "syndicate-global", "title": "Syndicator (Global + Turkey)",
     "job": "Post outbox/ — Turkey forums first, then global. Log .state/syndicated.json."},

    # --- tier 5+ expansion ---
    {"id": "publisher", "dept": "publish", "title": "Publisher (Deploy)",
     "job": "Deploy site/ to Cloudflare Pages after validate passes. Submit sitemap."},
    {"id": "turkey-lead", "dept": "syndicate-turkey", "title": "Turkey Syndicate Lead",
     "job": "Own all TR channels. Priority: Music & Lyrics TR, Music Production TR."},

    {"id": "deputy-ops", "dept": "command", "title": "Deputy — Operations",
     "job": "Backup chief. Own routine schedules, .state/* integrity, and inter-bot messaging."},
    {"id": "deputy-intel", "dept": "command", "title": "Deputy — Intelligence",
     "job": "Own all source scouts. Summarize new/removed listings for chief before pipeline runs."},

    # --- intelligence ---
    {"id": "mercor-lead", "dept": "intelligence", "title": "Mercor Scout Lead",
     "job": "Monitor work.mercor.com/explore. Flag music, production, Turkish slugs. Alert on HTML/schema changes."},
    {"id": "mercor-music", "dept": "intelligence", "title": "Mercor Music Scout",
     "job": "Deep-watch music-lyrics and music-production listings. First to ping on new TR roles."},
    {"id": "mercor-turkish", "dept": "intelligence", "title": "Mercor Turkish Scout",
     "job": "Watch only Turkish music/production Mercor IDs. Compare against .state/sync-state.json."},
    {"id": "mercor-production", "dept": "intelligence", "title": "Mercor Production Scout",
     "job": "Audio, TTS, speech, sound-engineering listings across Mercor."},
    {"id": "outlier-lead", "dept": "intelligence", "title": "Outlier Scout Lead",
     "job": "Poll outlier.ai sitemap expert pages. Filter video-creator and content roles."},
    {"id": "outlier-video", "dept": "intelligence", "title": "Outlier Video Scout",
     "job": "Track Outlier video-creator and production-adjacent funnels."},
    {"id": "outlier-coding", "dept": "intelligence", "title": "Outlier Coding Scout",
     "job": "Track Outlier coding/agent-builder listings relevant to production tooling."},
    {"id": "da-lead", "dept": "intelligence", "title": "DataAnnotation Scout",
     "job": "Watch dataannotation.tech role pages and language directory for new verticals."},
    {"id": "source-research", "dept": "intelligence", "title": "New Source Researcher",
     "job": "Weekly scan for Appen, Scale, Remotasks, Surge — report if worth adding to sync.py."},
    {"id": "competitor-watch", "dept": "intelligence", "title": "Competitor Aggregator Watch",
     "job": "Monitor other job boards reposting Mercor music roles. Note gaps we can fill."},
    {"id": "rate-tracker", "dept": "intelligence", "title": "Rate & Pay Tracker",
     "job": "Log payMin/payMax shifts across sources into .state/rates-history.json."},
    {"id": "takedown-watch", "dept": "intelligence", "title": "Takedown Watch",
     "job": "First responder when sync reports removed jobs — verify live URL 404 on source."},

    # --- pipeline ---
    {"id": "sync-lead", "dept": "pipeline", "title": "Sync Lead",
     "job": "Own bash run-pipeline.sh. Run every 6h. Fix sync.py failures. Write handoff.json."},
    {"id": "sync-runner-2", "dept": "pipeline", "title": "Sync Runner — Off-cycle",
     "job": "Backup pipeline run at +3h offset from primary scout."},
    {"id": "build-lead", "dept": "pipeline", "title": "Build Lead",
     "job": "Run build.py after every successful sync. Confirm site/ card count matches jobs.json."},
    {"id": "validate-lead", "dept": "pipeline", "title": "Validate Lead",
     "job": "Run validate.py. Block deploy if any JobPosting check fails."},
    {"id": "handoff-writer", "dept": "pipeline", "title": "Handoff Writer",
     "job": "Enrich .state/handoff.json with turkeyJobs, recentlyAdded, priority flags."},
    {"id": "state-auditor", "dept": "pipeline", "title": "State Auditor",
     "job": "Audit .state/sync-state.json vs jobs.json for drift. Weekly report."},
    {"id": "pipeline-recovery", "dept": "pipeline", "title": "Pipeline Recovery",
     "job": "On failure: diagnose which source broke, retry once, file incident to chief."},

    # --- publish ---
    {"id": "publish-lead", "dept": "publish", "title": "Publish Director",
     "job": "Gate deploys on validate pass. Coordinate Publisher team."},
    {"id": "sitemap", "dept": "publish", "title": "Sitemap & Search Console",
     "job": "Submit sitemap.xml after deploy. Check Google Search Console job enhancements."},
    {"id": "seo-monitor", "dept": "publish", "title": "SEO & Canonical Monitor",
     "job": "Verify canonical URLs, robots.txt, no example.com left in production."},
    {"id": "deploy-staging", "dept": "publish", "title": "Staging Preview",
     "job": "Optional preview deploy before prod cutover on tiers 55+."},
    {"id": "cdn-cache", "dept": "publish", "title": "CDN Cache Purge",
     "job": "Purge Cloudflare cache after deploy when tier 33+."},

    # --- syndicate turkey ---
    {"id": "donanimhaber", "dept": "syndicate-turkey", "title": "DonanımHaber Agent",
     "job": "Post from outbox/<date>/turkey/donanimhaber-*.txt. Max 1 thread/day. Browser login."},
    {"id": "technopat", "dept": "syndicate-turkey", "title": "Technopat Agent",
     "job": "Post Turkish copy to Technopat Müzik & Ses. Log to .state/syndicated.json."},
    {"id": "eksisozluk", "dept": "syndicate-turkey", "title": "Ekşi Sözlük Agent",
     "job": "Find or create relevant başlık for remote müzik AI işleri. Manual, careful tone."},
    {"id": "reddit-turkey", "dept": "syndicate-turkey", "title": "r/Turkey Agent",
     "job": "Post in career/remote threads only. Link our job page never raw Mercor."},
    {"id": "facebook-tr", "dept": "syndicate-turkey", "title": "Facebook TR Producers",
     "job": "Post to TR home studio / beatmaker groups from outbox turkey copy."},
    {"id": "instagram-tr", "dept": "syndicate-turkey", "title": "Instagram TR Music",
     "job": "Postiz or browser — #müzikprodüksiyon #homestudio #remoteiş hashtags."},
    {"id": "tr-localizer", "dept": "syndicate-turkey", "title": "TR Copy Localizer",
     "job": "Review Turkish outbox copy for natural tone before forum posts go live."},
    {"id": "tr-reply", "dept": "syndicate-turkey", "title": "TR Forum Reply Agent",
     "job": "Monitor DonanımHaber/Technopat threads we posted. Answer questions, link site."},

    # --- syndicate global / music ---
    {"id": "global-lead", "dept": "syndicate-global", "title": "Global Syndicate Lead",
     "job": "Own EN forum rotation after Turkey priority jobs are posted."},
    {"id": "kvr", "dept": "syndicate-music", "title": "KVR Audio Jobs Agent",
     "job": "Post music/production roles to KVR jobs forum."},
    {"id": "vi-control", "dept": "syndicate-music", "title": "VI-Control Agent",
     "job": "Studio & Business forum posts for production-adjacent roles."},
    {"id": "gearspace", "dept": "syndicate-music", "title": "Gearspace Agent",
     "job": "Gearspace jobs board — music engineering listings only."},
    {"id": "reddit-remote", "dept": "syndicate-global", "title": "Reddit r/remotework Agent",
     "job": "Rotate listings across r/remotework, r/forhire, r/WorkOnline."},
    {"id": "reddit-flair", "dept": "syndicate-global", "title": "Reddit Flair & Rules Checker",
     "job": "Pre-flight each sub's rules before any reddit agent posts."},
    {"id": "discord-remote", "dept": "syndicate-global", "title": "Discord Remote Communities",
     "job": "Post to remote work Discord servers where allowed."},
    {"id": "telegram-remote", "dept": "syndicate-global", "title": "Telegram Remote Groups",
     "job": "Syndicate via Telegram communities + Postiz integration."},
    {"id": "newsletter-scout", "dept": "syndicate-global", "title": "Newsletter & Slack Scout",
     "job": "Find niche music/AI newsletters accepting job submissions."},
    {"id": "music-lead", "dept": "syndicate-music", "title": "Music Vertical Lead",
     "job": "Coordinate all music-specific syndication. Tag verticals:music jobs first."},

    # --- social / postiz ---
    {"id": "social-lead", "dept": "social", "title": "Social Director",
     "job": "Own Postiz queue. Max 3 posts/platform/day."},
    {"id": "postiz-runner", "dept": "social", "title": "Postiz Queue Runner",
     "job": "Drain outbox/<date>/postiz-queue.json via postiz CLI after auth:status."},
    {"id": "x-poster", "dept": "social", "title": "X / Twitter Agent",
     "job": "Stagger X posts — one role per post, link to our job page."},
    {"id": "linkedin", "dept": "social", "title": "LinkedIn Feed Agent",
     "job": "Feed posts linking to new music/production listings."},
    {"id": "bluesky", "dept": "social", "title": "Bluesky Agent",
     "job": "Cross-post top new listings to Bluesky via Postiz."},
    {"id": "threads", "dept": "social", "title": "Threads Agent",
     "job": "Threads cross-post for new TR music roles."},
    {"id": "tiktok-caption", "dept": "social", "title": "TikTok Caption Agent",
     "job": "Draft short captions for manual TikTok cross-promo (tier 69+)."},
    {"id": "social-reply", "dept": "social", "title": "Social Reply Agent",
     "job": "Reply to comments on our posts with site link when asked."},

    # --- qa ---
    {"id": "qa-lead", "dept": "qa", "title": "QA Director",
     "job": "Block syndication if validate failed or apply URLs are placeholders."},
    {"id": "link-checker", "dept": "qa", "title": "Link Checker",
     "job": "HTTP 200 every job page and apply button target before syndicate runs."},
    {"id": "duplicate-guard", "dept": "qa", "title": "Duplicate Post Guard",
     "job": "Read .state/syndicated.json — reject duplicate jobId+channel combos."},
    {"id": "jsonld-spot", "dept": "qa", "title": "JSON-LD Spot Check",
     "job": "Random 5 job pages per day — Rich Results Test equivalent checks."},
    {"id": "referral-check", "dept": "qa", "title": "Referral URL Checker",
     "job": "Ensure Mercor apply links use referralUrl not bare work.mercor.com."},

    # --- ops / expand to 111 with regional + specialist clones ---
    {"id": "digest-am", "dept": "ops", "title": "Morning Digest Writer",
     "job": "07:00 Istanbul — jobs count, overnight adds/removes, deploy status."},
    {"id": "digest-pm", "dept": "ops", "title": "Evening Digest Writer",
     "job": "18:00 Istanbul — posts made, errors, tomorrow queue."},
    {"id": "incident", "dept": "ops", "title": "Incident Commander",
     "job": "When any bot fails twice: pause routines, alert human, open .state/incident.json."},
    {"id": "handoff-router", "dept": "ops", "title": "Handoff Router",
     "job": "Route handoff.json slices to correct downstream bots by department."},
    {"id": "routine-scheduler", "dept": "ops", "title": "Routine Scheduler",
     "job": "Maintain Grok Bot routine cadence doc. Audit missed runs."},
    {"id": "config-patcher", "dept": "ops", "title": "Config Patcher",
     "job": "Run apply-secrets.sh when secrets rotate. Never log secret values."},
    {"id": "backup-state", "dept": "ops", "title": "State Backup Agent",
     "job": "Daily copy .state/ to .state/backups/<date>/."},
    {"id": "metrics", "dept": "ops", "title": "Metrics & KPI Writer",
     "job": "Weekly: listings synced, posts sent, TR conversion proxy (clicks if available)."},
    {"id": "onboard-bot", "dept": "ops", "title": "Bot Onboarder",
     "job": "When tier upgrades: paste CONTEXT.md + brief to new bots, verify first run."},
    {"id": "org-maintainer", "dept": "ops", "title": "Org Chart Maintainer",
     "job": "Regenerate generate-org.py output when tier changes. Keep manifest current."},
]

# Pad to 111 with numbered specialist clones for high tiers
_dept_cycle = ["syndicate-global", "syndicate-music", "syndicate-turkey", "social", "intelligence"]
while len(ROLES) < 111:
    n = len(ROLES) + 1
    dept = _dept_cycle[(n - len(_dept_cycle)) % len(_dept_cycle)]
    ROLES.append({
        "id": f"specialist-{n:03d}",
        "dept": dept,
        "title": f"Specialist #{n} ({dept})",
        "job": f"Overflow agent {n}. Follow {dept} lead orders. Rotate through outbox posts "
               f"and source watches not covered by named agents. Report to chief daily.",
    })

PRESETS = [3, 5, 7, 9, 13, 21, 33, 42, 55, 69, 72, 88, 96, 111]


def management_layers(n: int) -> dict:
    """Approximate span-of-control tree depth for org chart display."""
    if n <= 3:
        return {"layers": 2, "you_plus": f"you + {n - 1} bots under Chief" if n >= 2 else "you + chief"}
    if n <= 9:
        return {"layers": 3, "you_plus": f"you → chief → {n - 1} workers"}
    if n <= 21:
        chiefs = 1 + max(1, n // 13)
        return {"layers": 4, "you_plus": f"you → chief → {chiefs} leads → workers"}
    if n <= 55:
        return {"layers": 5, "you_plus": f"you → chief → 2 deputies → {n // 7} leads → workers"}
    return {"layers": 6, "you_plus": f"you → command(3) → directors({max(3, n // 21)}) → leads → {n} total bots"}


def reports_to(index: int, n: int) -> str:
    if index == 0:
        return "human (you)"
    if index == 1 and n > 3:
        return "chief"
    if n <= 7:
        return "chief"
    role = ROLES[index]
    # find lead in same dept
    for j in range(index):
        if ROLES[j]["dept"] == role["dept"] and "lead" in ROLES[j]["id"] or ROLES[j]["dept"] == "command":
            if "lead" in ROLES[j]["id"] or ROLES[j]["id"] in ("chief", "deputy-ops", "deputy-intel"):
                return ROLES[j]["title"]
    return "chief"


def agent_brief(role: dict, index: int, n: int, tier_dir: pathlib.Path) -> str:
    proj = "/Users/evansmacbookair/Projects/job-board/jobboard"
    boss = reports_to(index, n)
    peers = [ROLES[i]["title"] for i in range(min(n, len(ROLES))) if i != index][:8]
    return textwrap.dedent(f"""\
        # {role['title']} — Tier {n} org

        | Field | Value |
        |---|---|
        | Bot ID | `{role['id']}` |
        | Department | {role['dept']} |
        | Reports to | {boss} |
        | Tier size | {n} bots (+ you as apex) |

        ## Paste into Grok Bot (first message)

        ```
        You are **{role['title']}** — tier {n} of the Talent Bench Grok Bot factory ({n} bots + human apex).

        Project root: {proj}
        Read grok-bots/CONTEXT.md on first run.

        Your job: {role['job']}

        Reports to: {boss}
        Peers in this tier: {', '.join(peers[:5])}{'…' if len(peers) > 5 else ''}

        Handoff files:
        - .state/handoff.json — pipeline output (read/write depends on role)
        - .state/syndicated.json — log posts before publishing
        - .state/sync-state.json — source freshness

        Pipeline command (pipeline dept only): bash run-pipeline.sh

        Rules:
        - Never paste secrets in chat
        - Turkey music jobs post before global
        - Ask human before first post to any new channel
        - On failure: notify chief → incident bot at tier 13+

        Confirm you understand, then execute your first assigned task.
        ```
    """)


def org_chart_md(n: int, roles: list[dict]) -> str:
    layers = management_layers(n)
    lines = [
        f"# Tier {n} org chart — {n} Grok bots + you",
        "",
        f"**Structure:** {layers['you_plus']}",
        f"**Depth:** {layers['layers']} management layers",
        "",
        "## By department",
        "",
    ]
    by_dept: dict[str, list] = {}
    for r in roles:
        by_dept.setdefault(r["dept"], []).append(r)
    for dept, members in sorted(by_dept.items()):
        lines.append(f"### {dept} ({len(members)})")
        for m in members:
            lines.append(f"- **{m['title']}** (`{m['id']}`)")
        lines.append("")
    lines.extend([
        "## Handoff chain",
        "",
        "```",
        "intel scouts → sync-lead/scout → build → validate → publisher →",
        "turkey syndicate → global/music syndicate → social/postiz → qa → digest → you",
        "```",
        "",
        "## Upgrade path",
        "",
        f"Current: **{n}**. Next preset: **{next((p for p in PRESETS if p > n), 'max')}**.",
        "Run: `python3 grok-bots/generate-org.py --tier <N>`",
        "",
    ])
    return "\n".join(lines)


def generate_tier(n: int) -> pathlib.Path:
    roles = ROLES[:n]
    tier_dir = OUT / f"tier-{n:03d}"
    agents_dir = tier_dir / "agents"
    if agents_dir.exists():
        for old in agents_dir.glob("*.md"):
            old.unlink()
    agents_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "tier": n,
        "botCount": n,
        "human": "apex approver (you)",
        "tier3Layout": "you → chief → scout + syndicator" if n == 3 else None,
        "management": management_layers(n),
        "departments": {},
        "bots": [],
    }
    for dept in sorted({r["dept"] for r in roles}):
        manifest["departments"][dept] = sum(1 for r in roles if r["dept"] == dept)

    for i, role in enumerate(roles):
        brief_path = agents_dir / f"{i:03d}-{role['id']}.md"
        brief_path.write_text(agent_brief(role, i, n, tier_dir), encoding="utf-8")
        manifest["bots"].append({
            "index": i,
            "id": role["id"],
            "title": role["title"],
            "dept": role["dept"],
            "reportsTo": reports_to(i, n),
            "briefFile": str(brief_path.relative_to(ROOT)),
        })

    (tier_dir / "org-chart.md").write_text(org_chart_md(n, roles), encoding="utf-8")
    (tier_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # ROUTINES.md — tier-appropriate schedules
    routines = [
        f"# Tier {n} routines",
        "",
        "| Bot | Schedule |",
        "|---|---|",
        "| chief | Every 6h — review handoff, delegate |",
    ]
    if n >= 3:
        routines.append("| scout / sync-lead | Every 6h — run-pipeline.sh |")
    if n >= 5:
        routines.append("| publisher | Daily 07:00 UTC after sync |")
    if n >= 7:
        routines.append("| turkey-lead + agents | Daily 10:00 Europe/Istanbul |")
    if n >= 13:
        routines.append("| digest-am / digest-pm | 07:00 & 18:00 Istanbul |")
    if n >= 21:
        routines.append("| qa-lead | Before every syndicate batch |")
    if n >= 55:
        routines.append("| metrics | Weekly Monday 09:00 |")
    (tier_dir / "ROUTINES.md").write_text("\n".join(routines) + "\n", encoding="utf-8")

    return tier_dir


def main():
    parser = argparse.ArgumentParser(description="Generate Grok Bot org tiers")
    parser.add_argument("--tier", type=int, default=0, help="Single tier (3,5,7…111)")
    args = parser.parse_args()

    tiers = [args.tier] if args.tier else PRESETS
    for t in tiers:
        if t not in PRESETS and t != args.tier:
            print(f"skip unknown preset {t}")
            continue
        if t > len(ROLES):
            print(f"! tier {t} exceeds role catalog {len(ROLES)}")
            continue
        path = generate_tier(t)
        print(f"tier {t:3d} → {path} ({t} bots)")

    # Master index
    index_lines = [
        "# Grok Bot tier index — 3 to 111",
        "",
        "You (human) sit above every tier as **apex**. Each tier adds bots below chief.",
        "",
        "| Tier | Bots | You + | Departments | Path |",
        "|---:|---:|---|---|---|",
    ]
    for t in PRESETS:
        m = management_layers(t)
        d = tier_dir = OUT / f"tier-{t:03d}"
        dept_count = len({ROLES[i]["dept"] for i in range(t)})
        index_lines.append(
            f"| {t} | {t} | {m['you_plus']} | {dept_count} | [tier-{t:03d}](generated/tier-{t:03d}/org-chart.md) |"
        )
    index_lines.extend([
        "",
        "## Quick start",
        "",
        "1. Pick tier (start at **3**, scale when handoffs break)",
        "2. Open `generated/tier-NNN/agents/` — create one Grok Bot per file",
        "3. Paste each file's code block into that bot's first message",
        "4. Enable routines from `ROUTINES.md`",
        "",
        "Regenerate: `python3 grok-bots/generate-org.py`",
        "",
    ])
    (ROOT / "TIER-INDEX.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"\nIndex → {ROOT / 'TIER-INDEX.md'}")


if __name__ == "__main__":
    main()
