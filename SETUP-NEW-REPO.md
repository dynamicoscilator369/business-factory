# New repo — Business Factory

This zip **is** the factory repo. Unzip → init git → `./new-business.sh` your first idea.

## 1. Create the repo

```bash
unzip company-kernel-starter.zip
cd company-kernel
git init
git add .
git commit -m "Business factory: kernel + EOS + Grok Bot scaffold"
```

Rename the folder/repo if you want (`business-factory`, `company-kernel`, etc.) — paths are relative.

## 2. Your first business (not the example)

```bash
./new-business.sh my-first-idea "My First Idea"
```

Edit three files:

| File | You define |
|---|---|
| `businesses/my-first-idea/pipeline/run.py` | sync, build, distribute |
| `businesses/my-first-idea/manifest.json` | seats + Grok org tier |
| `businesses/my-first-idea/scorecard.csv` | metrics from external sources |

Run it:

```bash
python3 main.py pipeline my-first-idea
python3 main.py l10 my-first-idea
```

## 3. Grok Bot on the cloud computer

```bash
./workspace-bootstrap.sh
```

Per-business secrets go in Grok Bot Settings (or `apply-secrets.sh` pattern in your pipeline).

Chief runs `./run-pipeline.sh <business-id>` on schedule.

Generate bot roster: `python3 grok-bots/generate-org.py --tier 5`

## 4. Reference example only

`businesses/examples/talent-bench/` is a **finished** job-board pipeline (Mercor sync, site build, forum distribute). Study or copy patterns — don't treat it as the repo's purpose.

```bash
python3 main.py pipeline examples/talent-bench
```

Configure `businesses/examples/talent-bench/config.json` before running.

## 5. Every next idea

```bash
./new-business.sh another-idea "Another Idea"
```

Same kernel. Same EOS. Same Grok Bot tiers. New folder + four methods.

## Repo layout

```
kernel/           — business loader, PipelineBase
orchestrator/     — EOS (Integrator, L10, model tiers, integrity)
grok-bots/        — 3→111 org generator + agent briefs
businesses/
  _template/      — empty slot (copy source)
  examples/       — reference implementations
main.py           — pipeline | l10 | list
```

Generated at runtime (not in zip): `.state/`, `outbox/`, `site/`, idea-specific artifacts.
