import json, os
from datetime import datetime, timezone

STATE_DIR = os.path.join(os.path.dirname(__file__), "state")
ISSUES_FILE = os.path.join(STATE_DIR, "issues.json")

def _load():
    if not os.path.exists(ISSUES_FILE):
        return []
    with open(ISSUES_FILE, encoding="utf-8") as f:
        return json.load(f)

def list_open_issues() -> str:
    """List every OPEN issue in the durable Issues List (state/issues.json)."""
    issues = _load()
    opens = [i for i in issues if str(i.get("status", "")).lower() == "open"]
    if not opens:
        return "No open issues."
    return "\n".join(f"- {i['id']}: {i.get('title','')} (owner {i.get('owner','?')})" for i in opens)

def close_issue(issue_id: str, resolution: str) -> str:
    """Close an issue by id — ACTUALLY mutates state/issues.json (not narration).

    Sets status=Closed, records the resolution + UTC timestamp, and writes the file.
    Returns a confirmation, or an error listing valid open ids if not found.
    Only call when an issue is genuinely solved in IDS.
    """
    issues = _load()
    if not issues:
        return "ERROR: no issues file to write."
    for i in issues:
        if i.get("id") == issue_id:
            if str(i.get("status", "")).lower() == "closed":
                return f"Issue '{issue_id}' was already Closed."
            i["status"] = "Closed"
            i["resolution"] = resolution
            i["closed_utc"] = datetime.now(timezone.utc).isoformat()
            with open(ISSUES_FILE, "w", encoding="utf-8") as f:
                json.dump(issues, f, indent=2)
            return f"Issue '{issue_id}' CLOSED and persisted to issues.json. Resolution: {resolution}"
    valid = ", ".join(i.get("id", "?") for i in issues) or "(none)"
    return f"ERROR: issue id '{issue_id}' not found. Valid ids: {valid}"
