# Tier 5 org chart — 5 Grok bots + you

**Structure:** you → chief → 4 workers
**Depth:** 3 management layers

## By department

### command (1)
- **Chief Coordinator** (`chief`)

### pipeline (1)
- **Scout (Pipeline Runner)** (`scout`)

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

Current: **5**. Next preset: **7**.
Run: `python3 grok-bots/generate-org.py --tier <N>`
