# Tier 9 org chart — 9 Grok bots + you

**Structure:** you → chief → 8 workers
**Depth:** 3 management layers

## By department

### command (3)
- **Chief Coordinator** (`chief`)
- **Deputy — Operations** (`deputy-ops`)
- **Deputy — Intelligence** (`deputy-intel`)

### intelligence (2)
- **Mercor Scout Lead** (`mercor-lead`)
- **Mercor Music Scout** (`mercor-music`)

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

Current: **9**. Next preset: **13**.
Run: `python3 grok-bots/generate-org.py --tier <N>`
