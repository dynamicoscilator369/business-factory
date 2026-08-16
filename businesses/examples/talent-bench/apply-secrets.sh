#!/usr/bin/env bash
# Apply Grok Bot secrets to config.json (run on bot computer, not in chat).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$ROOT/config.json"

python3 - <<PY
import json, os, pathlib
cfg = json.loads(pathlib.Path("$CONFIG").read_text())
code = os.environ.get("MERCOR_REFERRAL_CODE", "")
base = os.environ.get("SITE_BASE_URL", "")
if code and "YOUR_CODE" in cfg.get("referralUrl", ""):
    cfg["referralUrl"] = f"https://work.mercor.com/?referralCode={code}"
    cfg.setdefault("sourceReferrals", {})["mercor"] = cfg["referralUrl"]
if base and "example.com" in cfg.get("baseUrl", ""):
    cfg["baseUrl"] = base.rstrip("/")
    cfg["hiringOrganization"]["url"] = cfg["baseUrl"]
    cfg["hiringOrganization"]["logo"] = f"{cfg['baseUrl']}/logo.png"
pathlib.Path("$CONFIG").write_text(json.dumps(cfg, indent=2) + "\\n")
print("config.json updated from environment secrets")
PY
