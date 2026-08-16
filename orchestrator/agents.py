"""EOS seat configs — NO Google Antigravity.

Builds system prompts + Seat objects for seat_runtime (dry or grok).
"""
from __future__ import annotations

import os

import eos_protocol
from seat_runtime import Seat

INTEGRATOR_METRIC = "integrator_seats_reporting_pct"

INTEGRATOR_SI = f'''You are the Integrator. You run the day-to-day operations and hold the team accountable.

PRIME DIRECTIVES:
1. Evan is the Visionary (human). If you need input on vision, culture, or big decisions, escalate with the control protocol.
2. Every seat has one number measured outside the agent — INCLUDING YOU. Your own scorecard number is `{INTEGRATOR_METRIC}` (or the registry's computed seats metric). NEVER invent or estimate data. If a metric returns "NO DATA", report it exactly.
3. Strict Report vs. Solve. Scorecard and Rock reviews are report-only. Off-track or NO DATA goes to Issues / IDS.
4. Firewall: You may only DRAFT decisions. Money, people, or policy requires human sign-off.
5. Citation: Ground EOS claims using `query_eos_knowledge`. No doctrine from memory alone.
6. Closing an issue requires `close_issue(issue_id, resolution)` — never claim closed without the tool.

During a Level 10 Meeting:
- Lead the meeting and facilitate IDS.
- After departmental seats report, report YOUR OWN number using read_scorecard.
- In IDS, list_open_issues; close only genuinely resolved; escalate what needs Evan.

''' + "\n" + eos_protocol.INSTRUCTIONS


def _backend_for(tier: dict | None) -> str:
    """Resolve seat backend. Antigravity/Gemini hard-lock is DEAD.

    Priority:
      EOS_BACKEND=dry|grok env override
      tier backend grok if key present
      else dry (always works)
    """
    forced = (os.environ.get("EOS_BACKEND") or "").strip().lower()
    if forced in ("dry", "grok"):
        return forced
    key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
    if (tier or {}).get("backend") == "grok" and key:
        return "grok"
    if key and (os.environ.get("EOS_PREFER_GROK", "1") == "1"):
        return "grok"
    return "dry"


def get_integrator_seat(tier=None) -> Seat:
    return Seat(
        name="Integrator",
        system=INTEGRATOR_SI,
        metric_key=INTEGRATOR_METRIC,
        backend=_backend_for(tier),
        model=(tier or {}).get("model"),
    )


def get_departmental_seat(department_name, responsibilities, metric_key, tier=None) -> Seat:
    system = f'''You are the Head of {department_name}.
Your responsibilities:
{responsibilities}

PRIME DIRECTIVES:
1. You have exactly one scorecard number: `{metric_key}`. Read it using the `read_scorecard` tool.
2. NEVER invent, estimate, or self-report your metric. If `read_scorecard` returns "NO DATA", report literally "NO DATA".
3. Report vs. Solve: During the Scorecard segment, ONLY report the value from the tool.
4. Evan is the Visionary (human). Do not simulate him.
5. Ground EOS claims using `query_eos_knowledge` when needed.

During a Level 10 Meeting:
- Report on your Scorecard metric `{metric_key}` using `read_scorecard`.
- End every turn with the control protocol terminator.

''' + "\n" + eos_protocol.INSTRUCTIONS
    return Seat(
        name=department_name,
        system=system,
        metric_key=metric_key,
        backend=_backend_for(tier),
        model=(tier or {}).get("model"),
    )


# Back-compat names used by older callers (return seats, not antigravity configs)
def get_integrator_config(tier=None, grok_base_url=None):
    _ = grok_base_url  # unused — no antigravity proxy required
    return get_integrator_seat(tier)


def get_departmental_config(department_name, responsibilities, metric_key, tier=None):
    return get_departmental_seat(department_name, responsibilities, metric_key, tier)
