#!/usr/bin/env bash
# Full job-board pipeline — designed for Grok Bot routines.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Apply secrets from Grok Bot environment if present
if [[ -n "${MERCOR_REFERRAL_CODE:-}" || -n "${SITE_BASE_URL:-}" ]]; then
  bash apply-secrets.sh
fi

log() { echo "[$(date -Iseconds)] $*"; }

log "=== Talent Bench pipeline start ==="

log "1/4 sync"
python3 sync.py | tee -a .state/pipeline.log

log "2/4 build"
python3 build.py

log "3/4 validate"
python3 validate.py

log "4/4 distribute"
python3 distribute.py

TODAY=$(date +%Y-%m-%d)
NEW=$(python3 - <<'PY'
import json, pathlib
s = json.loads(pathlib.Path(".state/sync-state.json").read_text())
added = sum(1 for h in s.get("history", []) if h.get("event") == "added")
print(added)
PY
)

log "=== done ==="
log "Jobs: $(python3 -c 'import json; print(len(json.load(open("jobs.json"))))')"
log "Outbox: outbox/${TODAY}/"
log "Postiz queue: outbox/${TODAY}/postiz-queue.json"

# Handoff file for Syndicator bot
mkdir -p .state
python3 - <<PY
import json, pathlib
from datetime import date
today = date.today().isoformat()
jobs = json.loads(pathlib.Path("jobs.json").read_text())
state = json.loads(pathlib.Path(".state/sync-state.json").read_text())
recent = [h for h in state.get("history", []) if h.get("event") == "added"][-20:]
turkey = [
    j for j in jobs
    if "turkey" in j.get("verticals", [])
    or "turkish" in j.get("title", "").lower()
    or j.get("region", "").lower() == "turkey"
]
handoff = {
    "date": today,
    "totalJobs": len(jobs),
    "recentlyAdded": recent,
    "turkeyJobs": [{"id": j["id"], "title": j["title"], "url": f"jobs/{j['id']}.html"} for j in turkey],
    "outboxDir": f"outbox/{today}",
    "postizQueue": f"outbox/{today}/postiz-queue.json",
}
pathlib.Path(".state/handoff.json").write_text(json.dumps(handoff, indent=2) + "\\n")
print(f"Wrote handoff → .state/handoff.json ({len(turkey)} TR jobs)")
PY
