# Tier 33 org chart — 33 Grok bots + you

**Structure:** you → chief → 2 deputies → 4 leads → workers
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

### syndicate-global (1)
- **Syndicator (Global + Turkey)** (`syndicator`)

### syndicate-turkey (3)
- **Turkey Syndicate Lead** (`turkey-lead`)
- **DonanımHaber Agent** (`donanimhaber`)
- **Technopat Agent** (`technopat`)

## Handoff chain

```
intel scouts → sync-lead/scout → build → validate → publisher →
turkey syndicate → global/music syndicate → social/postiz → qa → digest → you
```

## Upgrade path

Current: **33**. Next preset: **42**.
Run: `python3 grok-bots/generate-org.py --tier <N>`
