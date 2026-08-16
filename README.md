# Business Factory

**One repo. Empty factory. Each business idea = one folder + four Python methods.**

Grok Bot runs the work. EOS runs accountability. You stay Visionary.

This is **not** a job board repo. This is the **operating system** for running any automated business. Talent Bench ships as a reference example under `businesses/examples/` — copy `_template` for your next idea.

## The factory

```
businesses/
├── _template/                 ← copy this for every new idea
│   ├── manifest.json          ← seats, metrics, Grok org tier
│   ├── scorecard.csv          ← numbers read OUTSIDE the agent
│   └── pipeline/run.py        ← four methods (below)
└── examples/
    └── talent-bench/          ← reference: job board (Mercor, forums, etc.)

kernel/                        ← loads any business folder
orchestrator/                  ← EOS: Integrator, L10, earn/demote tiers
grok-bots/                     ← org chart generator (3 → 111 bots)
```

## Four methods (all you implement per idea)

```python
class Pipeline(PipelineBase):
    def sync(self):       # pull fresh data from the world
    def build(self):      # turn data into your deliverable
    def validate(self):   # gate before ship (optional override)
    def distribute(self): # syndicate, post, outreach
```

`run()` chains them and writes `.state/handoff.json` for Grok Bot handoffs.

## Commands (same forever)

```bash
./new-business.sh my-idea "My Idea"     # copy _template
python3 main.py pipeline my-idea      # workers produce
python3 main.py l10 my-idea             # management meeting
./run-pipeline.sh my-idea               # Grok Bot routine
```

List businesses: `python3 main.py list`

## Three layers

| Layer | Role | Changes per business? |
|---|---|---|
| **Pipeline** | What gets built | Yes — four methods |
| **EOS orchestrator** | L10, scorecard, integrity, escalation | No |
| **Grok Bot** | Browser, terminal, schedules, forum posts | Descriptions only |

## Quick start (your first idea)

```bash
./new-business.sh acme "Acme Co"
# edit businesses/acme/pipeline/run.py — implement sync/build/distribute
# edit businesses/acme/manifest.json — name your seats
# edit businesses/acme/scorecard.csv — external metrics

python3 main.py pipeline acme
python3 main.py l10 acme
```

## Reference example

```bash
python3 main.py pipeline examples/talent-bench   # job board (~90s, needs network)
python3 main.py l10 examples/talent-bench
```

See `businesses/examples/talent-bench/` for a full sync → build → validate → distribute implementation.

## Grok Bot

```bash
./workspace-bootstrap.sh
python3 grok-bots/generate-org.py --tier 5
```

Paste `grok-bots/CONTEXT.template.md` into Chief. Store secrets in Grok Bot Settings — never in chat.

## New repo setup

Read **`SETUP-NEW-REPO.md`**.
