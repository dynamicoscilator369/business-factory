# Tier 21 org chart — 21 Grok bots + you

**Structure:** you → chief → 2 leads → workers
**Depth:** 4 management layers

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

### pipeline (3)
- **Scout (Pipeline Runner)** (`scout`)
- **Sync Lead** (`sync-lead`)
- **Sync Runner — Off-cycle** (`sync-runner-2`)

### publish (1)
- **Publisher (Deploy)** (`publisher`)

### syndicate-global (1)
- **Syndicator (Global + Turkey)** (`syndicator`)

### syndicate-turkey (1)
- **Turkey Syndicate Lead** (`turkey-lead`)

## Handoff chain

```
intel scouts → sync-lead/scout → build → validate → publisher →
turkey syndicate → global/music syndicate → social/postiz → qa → digest → you
```

## Upgrade path

Current: **21**. Next preset: **33**.
Run: `python3 grok-bots/generate-org.py --tier <N>`
