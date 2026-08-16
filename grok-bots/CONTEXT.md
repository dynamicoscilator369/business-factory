# Talent Bench — Grok Bot context (paste this whole file into your first bot message)

You are operating the **Talent Bench** job aggregator at:

```
/Users/evansmacbookair/Projects/job-board/jobboard
```

## What this project does

1. **Sync** live AI-training / music-production contract roles from Mercor, Outlier, and DataAnnotation
2. **Detect** new postings and takedowns (state in `.state/sync-state.json`)
3. **Build** a static site with Google for Jobs JSON-LD (`site/`)
4. **Distribute** syndication copy to global + **Turkey music/production** forums (`outbox/`)

## One-command pipeline

```bash
cd /Users/evansmacbookair/Projects/job-board/jobboard && bash run-pipeline.sh
```

## Key files

| File | Purpose |
|---|---|
| `config.json` | Brand, `referralUrl`, `baseUrl`, sync keywords |
| `jobs.json` | Auto-generated listings (do not hand-edit) |
| `sync.py` | Pull sources, diff adds/removes |
| `build.py` | Generate `site/` |
| `distribute.py` | Write forum/social posts to `outbox/<date>/` |
| `distribute.json` | Channel list (DonanımHaber, Technopat, KVR, Reddit, Postiz…) |
| `.state/handoff.json` | Written after each pipeline run — pass to Syndicator bot |

## Secrets (store in Grok Bot Secrets, never in chat)

- `MERCOR_REFERRAL_CODE` — your Mercor referral code
- `SITE_BASE_URL` — e.g. `https://talentbench.example.com`
- `POSTIZ_API_KEY` — optional, for social auto-post
- `CLOUDFLARE_API_TOKEN` — optional, for Pages deploy

## Bot swarm — scale 3 → 111

**Full tier index:** `grok-bots/TIER-INDEX.md`

| Tier | Bots | Layout |
|---:|---:|---|
| **3** | 3 | you → Chief → Scout + Syndicator |
| **5** | 5 | + Publisher + Turkey lead |
| **7** | 7 | + Mercor lead + Global syndicator |
| **9** | 9 | + Validate + Outlier scout |
| **13** | 13 | + QA + digests + deputies |
| **21** | 21 | Full department leads |
| **33** | 33 | Regional + social split |
| **42** | 42 | Per-forum agents |
| **55** | 55 | Staging + metrics |
| **69** | 69 | TikTok + extra social |
| **72** | 72 | — |
| **88** | 88 | Specialist overflow |
| **96** | 96 | — |
| **111** | 111 | Full factory |

Generate briefs: `python3 grok-bots/generate-org.py --tier 21`

Each tier lives in `grok-bots/generated/tier-NNN/agents/` — **one Grok Bot per `.md` file**.

Handoff rule: Scout writes `.state/handoff.json` → downstream bots read slices by department.

## Turkey priority

Always syndicate these roles first when present:
- Music & Lyrics Expert — Turkish
- Music Production Expert — Turkish

Channels (manual forum login on Grok Bot computer):
- DonanımHaber Müzik: https://forum.donanimhaber.com/muzik--f180
- Technopat Müzik & Ses: https://www.technopat.net/sosyal/kategori/muzik-ve-ses-sistemleri.596/

Copy is pre-written in Turkish under `outbox/<date>/turkey/`.

## Guardrails

- Do NOT paste API keys in chat or commit them to git
- Forum posts: max 1 thread per forum per day; vary title slightly
- Money/legal/customer-facing: ask me before first post to a new channel
- If sync returns 0 jobs, alert me — likely a scraper break

## Success = 

- `validate.py` passes
- Site live at `baseUrl`
- New Mercor music roles syndicated within 24h
- Removed roles gone from site within one sync cycle
