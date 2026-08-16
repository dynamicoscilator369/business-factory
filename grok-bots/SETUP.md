# Grok Bot setup — Talent Bench (15 minutes)

Grok Bot runs in the **Grok Bot desktop/iOS app** (Cursor Ultra or SuperGrok Heavy). This repo is ready — you paste agent briefs and show each bot the workflow once.

## Step 0: Download Grok Bot

1. [Grok Bot desktop app](https://x.ai/grok-bot) or from Cursor → Grok Bot
2. Sign in with your **Cursor Ultra** account (same email as Cursor)

## Step 1: Put the project on the Grok Bot computer

The bot's cloud computer needs the repo. Either:

**A) Clone from GitHub** (after you push this repo):
```bash
git clone <your-repo-url> ~/Projects/job-board/jobboard
```

**B) Copy from your Mac** — zip and upload, or tell Scout:
```
Clone or copy the Talent Bench project to ~/Projects/job-board/jobboard on this computer. The source is at /Users/evansmacbookair/Projects/job-board/jobboard on my Mac — I'll upload a zip if needed.
```

## Step 2: Store secrets (Grok Bot → Settings → Secrets)

| Secret | Value |
|---|---|
| `MERCOR_REFERRAL_CODE` | Your Mercor referral code |
| `SITE_BASE_URL` | Your live domain (https://…) |
| `POSTIZ_API_KEY` | Optional — social scheduling |
| `CLOUDFLARE_API_TOKEN` | Optional — Pages deploy |

Never paste these in chat.

## Step 3: Pick your tier (3 → 111)

Open **`grok-bots/TIER-INDEX.md`** and choose a preset:

| Start here | When |
|---|---|
| **Tier 3** | You + Chief + Scout + Syndicator — prove pipeline |
| **Tier 5** | Add dedicated Publisher |
| **Tier 13** | Add QA, digests, deputies |
| **Tier 21+** | One bot per forum/channel |
| **Tier 111** | Full factory — every role named |

Regenerate agent briefs:

```bash
python3 grok-bots/generate-org.py           # all presets
python3 grok-bots/generate-org.py --tier 21 # one tier
```

Create **one Grok Bot per file** in `grok-bots/generated/tier-NNN/agents/`.

## Step 4: Create bots (tier 3 example)

| Bot | Brief file |
|---|---|
| Chief | `generated/tier-003/agents/000-chief.md` |
| Scout | `generated/tier-003/agents/010-scout.md` or sync-lead |
| Syndicator | `generated/tier-003/agents/…-syndicator.md` |

Also paste `grok-bots/CONTEXT.md` into Chief's first message.

Legacy single-file briefs still in `grok-bots/agents/` — use **generated/** for scaled tiers.

## Step 5: Show Scout the workflow once

In Scout's chat:

```
Follow along: cd /Users/evansmacbookair/Projects/job-board/jobboard && bash run-pipeline.sh
Watch each step. When done, read .state/handoff.json and summarize.
```

When it works, say:
```
Save this as routine sync-pipeline. Run every 6 hours. Message me only when jobs are added, removed, or errors occur.
```

## Step 5: Log in on the Grok Bot computer (Syndicator)

Open the Grok Bot browser and sign in once (bots share this computer):

- DonanımHaber
- Technopat
- Reddit
- Postiz (`postiz auth:login` in terminal if CLI installed)

Tell Syndicator: "I'm logged into DonanımHaber and Technopat — post today's Turkey copy from outbox."

## Step 6: Enable routines

| Bot | Routine | Schedule |
|---|---|---|
| Scout | sync-pipeline | Every 6 hours |
| Publisher | deploy-if-fresh | Daily 07:00 UTC |
| Syndicator | turkey-then-global | Daily 10:00 Istanbul |

## Swarm handoff (god-mode)

Scout finishes → tell Publisher:
```
Deploy — handoff is at .state/handoff.json, pipeline ran today.
```

Scout finishes → tell Syndicator:
```
Syndicate new Turkey music jobs from outbox/<today>/turkey/
```

Or create a **Coordinator** bot with one message:

```
You manage Scout, Publisher, and Syndicator for Talent Bench at ~/Projects/job-board/jobboard.
Every 6 hours: tell Scout to run sync-pipeline.
If Scout reports changes: tell Publisher to deploy, then Syndicator to post Turkey jobs first.
Send me one daily digest at 18:00 Istanbul.
```

## Verify

```bash
# On Grok Bot computer terminal
cd ~/Projects/job-board/jobboard
bash run-pipeline.sh
python3 validate.py
ls outbox/$(date +%Y-%m-%d)/turkey/
```

## Troubleshooting

| Problem | Fix |
|---|---|
| Sync returns 0 jobs | Mercor HTML changed — ping me to update `sources/mercor.py` |
| validate.py fails | Run `python3 sync.py && python3 build.py` again |
| Forum post blocked | Syndicator should skip and log; don't spam |
| Apply links dead | Set `referralUrl` in config.json from secrets |
