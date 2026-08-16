#!/usr/bin/env bash
# Start a new business idea from the template.
set -euo pipefail
ID="${1:?Usage: new-business.sh <id>}"
NAME="${2:-$ID}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
DEST="$ROOT/businesses/$ID"
if [[ -e "$DEST" ]]; then
  echo "Already exists: $DEST" >&2
  exit 1
fi
cp -R "$ROOT/businesses/_template" "$DEST"
python3 - <<PY
import json, pathlib
p = pathlib.Path("$DEST/manifest.json")
m = json.loads(p.read_text())
m["id"] = "$ID"
m["name"] = "$NAME"
p.write_text(json.dumps(m, indent=2) + "\\n")
PY
echo "Created $DEST"
echo "  Edit manifest.json, scorecard.csv, pipeline/run.py"
echo "  Run: python3 main.py pipeline $ID"
