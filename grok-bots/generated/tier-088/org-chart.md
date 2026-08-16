# Tier 88 org chart — 88 Grok bots + you

**Structure:** you → command(3) → directors(4) → leads → 88 total bots
**Depth:** 6 management layers

## By department

### command (3)
- **Chief Coordinator** (`chief`)
- **Deputy — Operations** (`deputy-ops`)
- **Deputy — Intelligence** (`deputy-intel`)

### intelligence (15)
- **Mercor Scout Lead** (`mercor-lead`)
- **Mercor Music Scout** (`mercor-music`)
- **Mercor Turkish Scout** (`mercor-turkish`)
- **Mercor Production Scout** (`mercor-production`)
- **Outlier Scout Lead** (`outlier-lead`)
- **Outlier Video Scout** (`outlier-video`)
- **Outlier Coding Scout** (`outlier-coding`)
- **DataAnnotation Scout** (`da-lead`)
- **New Source Researcher** (`source-research`)
- **Competitor Aggregator Watch** (`competitor-watch`)
- **Rate & Pay Tracker** (`rate-tracker`)
- **Takedown Watch** (`takedown-watch`)
- **Specialist #74 (intelligence)** (`specialist-074`)
- **Specialist #79 (intelligence)** (`specialist-079`)
- **Specialist #84 (intelligence)** (`specialist-084`)

### ops (10)
- **Morning Digest Writer** (`digest-am`)
- **Evening Digest Writer** (`digest-pm`)
- **Incident Commander** (`incident`)
- **Handoff Router** (`handoff-router`)
- **Routine Scheduler** (`routine-scheduler`)
- **Config Patcher** (`config-patcher`)
- **State Backup Agent** (`backup-state`)
- **Metrics & KPI Writer** (`metrics`)
- **Bot Onboarder** (`onboard-bot`)
- **Org Chart Maintainer** (`org-maintainer`)

### pipeline (8)
- **Scout (Pipeline Runner)** (`scout`)
- **Sync Lead** (`sync-lead`)
- **Sync Runner — Off-cycle** (`sync-runner-2`)
- **Build Lead** (`build-lead`)
- **Validate Lead** (`validate-lead`)
- **Handoff Writer** (`handoff-writer`)
- **State Auditor** (`state-auditor`)
- **Pipeline Recovery** (`pipeline-recovery`)

### publish (6)
- **Publisher (Deploy)** (`publisher`)
- **Publish Director** (`publish-lead`)
- **Sitemap & Search Console** (`sitemap`)
- **SEO & Canonical Monitor** (`seo-monitor`)
- **Staging Preview** (`deploy-staging`)
- **CDN Cache Purge** (`cdn-cache`)

### qa (5)
- **QA Director** (`qa-lead`)
- **Link Checker** (`link-checker`)
- **Duplicate Post Guard** (`duplicate-guard`)
- **JSON-LD Spot Check** (`jsonld-spot`)
- **Referral URL Checker** (`referral-check`)

### social (12)
- **Social Director** (`social-lead`)
- **Postiz Queue Runner** (`postiz-runner`)
- **X / Twitter Agent** (`x-poster`)
- **LinkedIn Feed Agent** (`linkedin`)
- **Bluesky Agent** (`bluesky`)
- **Threads Agent** (`threads`)
- **TikTok Caption Agent** (`tiktok-caption`)
- **Social Reply Agent** (`social-reply`)
- **Specialist #73 (social)** (`specialist-073`)
- **Specialist #78 (social)** (`specialist-078`)
- **Specialist #83 (social)** (`specialist-083`)
- **Specialist #88 (social)** (`specialist-088`)

### syndicate-global (10)
- **Syndicator (Global + Turkey)** (`syndicator`)
- **Global Syndicate Lead** (`global-lead`)
- **Reddit r/remotework Agent** (`reddit-remote`)
- **Reddit Flair & Rules Checker** (`reddit-flair`)
- **Discord Remote Communities** (`discord-remote`)
- **Telegram Remote Groups** (`telegram-remote`)
- **Newsletter & Slack Scout** (`newsletter-scout`)
- **Specialist #75 (syndicate-global)** (`specialist-075`)
- **Specialist #80 (syndicate-global)** (`specialist-080`)
- **Specialist #85 (syndicate-global)** (`specialist-085`)

### syndicate-music (7)
- **KVR Audio Jobs Agent** (`kvr`)
- **VI-Control Agent** (`vi-control`)
- **Gearspace Agent** (`gearspace`)
- **Music Vertical Lead** (`music-lead`)
- **Specialist #76 (syndicate-music)** (`specialist-076`)
- **Specialist #81 (syndicate-music)** (`specialist-081`)
- **Specialist #86 (syndicate-music)** (`specialist-086`)

### syndicate-turkey (12)
- **Turkey Syndicate Lead** (`turkey-lead`)
- **DonanımHaber Agent** (`donanimhaber`)
- **Technopat Agent** (`technopat`)
- **Ekşi Sözlük Agent** (`eksisozluk`)
- **r/Turkey Agent** (`reddit-turkey`)
- **Facebook TR Producers** (`facebook-tr`)
- **Instagram TR Music** (`instagram-tr`)
- **TR Copy Localizer** (`tr-localizer`)
- **TR Forum Reply Agent** (`tr-reply`)
- **Specialist #77 (syndicate-turkey)** (`specialist-077`)
- **Specialist #82 (syndicate-turkey)** (`specialist-082`)
- **Specialist #87 (syndicate-turkey)** (`specialist-087`)

## Handoff chain

```
intel scouts → sync-lead/scout → build → validate → publisher →
turkey syndicate → global/music syndicate → social/postiz → qa → digest → you
```

## Upgrade path

Current: **88**. Next preset: **96**.
Run: `python3 grok-bots/generate-org.py --tier <N>`
