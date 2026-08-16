# Tier 55 org chart — 55 Grok bots + you

**Structure:** you → chief → 2 deputies → 7 leads → workers
**Depth:** 5 management layers

## By department

### command (3)
- **Chief Coordinator** (`chief`)
- **Deputy — Operations** (`deputy-ops`)
- **Deputy — Intelligence** (`deputy-intel`)

### intelligence (12)
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

### social (6)
- **Social Director** (`social-lead`)
- **Postiz Queue Runner** (`postiz-runner`)
- **X / Twitter Agent** (`x-poster`)
- **LinkedIn Feed Agent** (`linkedin`)
- **Bluesky Agent** (`bluesky`)
- **Threads Agent** (`threads`)

### syndicate-global (7)
- **Syndicator (Global + Turkey)** (`syndicator`)
- **Global Syndicate Lead** (`global-lead`)
- **Reddit r/remotework Agent** (`reddit-remote`)
- **Reddit Flair & Rules Checker** (`reddit-flair`)
- **Discord Remote Communities** (`discord-remote`)
- **Telegram Remote Groups** (`telegram-remote`)
- **Newsletter & Slack Scout** (`newsletter-scout`)

### syndicate-music (4)
- **KVR Audio Jobs Agent** (`kvr`)
- **VI-Control Agent** (`vi-control`)
- **Gearspace Agent** (`gearspace`)
- **Music Vertical Lead** (`music-lead`)

### syndicate-turkey (9)
- **Turkey Syndicate Lead** (`turkey-lead`)
- **DonanımHaber Agent** (`donanimhaber`)
- **Technopat Agent** (`technopat`)
- **Ekşi Sözlük Agent** (`eksisozluk`)
- **r/Turkey Agent** (`reddit-turkey`)
- **Facebook TR Producers** (`facebook-tr`)
- **Instagram TR Music** (`instagram-tr`)
- **TR Copy Localizer** (`tr-localizer`)
- **TR Forum Reply Agent** (`tr-reply`)

## Handoff chain

```
intel scouts → sync-lead/scout → build → validate → publisher →
turkey syndicate → global/music syndicate → social/postiz → qa → digest → you
```

## Upgrade path

Current: **55**. Next preset: **69**.
Run: `python3 grok-bots/generate-org.py --tier <N>`
