"""EOS control-token protocol — the org's control plane.

The two meanings of EOS collapse here: a seat ends its TURN (End-of-Sequence)
by emitting exactly one TYPED terminator that says WHAT kind of stop it is. The
orchestrator routes on the terminator TYPE instead of parsing prose — no regex
hunting for 'AWAITING VISIONARY INPUT' in a paragraph.

Grammar (one per turn, on the final line, followed by the hard-stop mark):
    ⟦EOS_REPORT: <one-line metric report>⟧⟦END⟧     departmental seat finished reporting
    ⟦EOS_ESCALATE: <one question for Evan>⟧⟦END⟧    Integrator needs the Visionary
    ⟦EOS_RESOLVED: <issue_id>⟧⟦END⟧                 Integrator closed a real issue
    ⟦EOS_HOLD: <reason>⟧⟦END⟧                        nothing to act on (clean IDS exit)
    ⟦EOS_ADJOURN⟧⟦END⟧                               Integrator ends the meeting

Every routed terminator is appended to state/eos_control_log.jsonl — an auditable
control-event stream, the routing analogue of the integrity log.
"""
import json, os, re
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
CTRL_LOG = os.path.join(HERE, "state", "eos_control_log.jsonl")

VERBS = {"REPORT", "ESCALATE", "RESOLVED", "HOLD", "ADJOURN"}
STOP_MARK = "⟦END⟧"                       # proxy hard-cap sequence
_RE = re.compile(r"⟦EOS_([A-Z]+)(?::\s*(.*?))?\s*⟧", re.DOTALL)

# Block injected into every seat's system instructions.
INSTRUCTIONS = (
    "CONTROL PROTOCOL (mandatory): end EVERY turn with EXACTLY ONE control terminator "
    "on its own final line, then STOP immediately — emit nothing after it and NEVER "
    "fabricate tool output. The terminator is the only way to hand control back.\n"
    "  ⟦EOS_REPORT: <your one-line metric report>⟧⟦END⟧   (departmental seat, after reporting its number)\n"
    "  ⟦EOS_ESCALATE: <one precise question for Evan>⟧⟦END⟧ (Integrator, when Visionary input is needed)\n"
    "  ⟦EOS_RESOLVED: <issue_id>⟧⟦END⟧                    (Integrator, ONLY after a real close_issue call)\n"
    "  ⟦EOS_HOLD: <reason>⟧⟦END⟧                          (Integrator, when there is nothing to act on — e.g. no open issues)\n"
    "  ⟦EOS_ADJOURN⟧⟦END⟧                                 (Integrator, to end the meeting)\n"
    "If your work for the turn is done, emit the terminator and ⟦END⟧ and stop. Do not loop."
)

def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def parse(text):
    """Return (verb, payload) from the LAST control terminator in text.
    verb is None if none present, 'UNKNOWN' if an unrecognized verb was used."""
    ms = list(_RE.finditer(text or ""))
    if not ms:
        return (None, None)
    m = ms[-1]
    verb = m.group(1)
    payload = (m.group(2) or "").strip()
    return (verb if verb in VERBS else "UNKNOWN", payload)

def _log(seat, verb, payload, routed):
    rec = {"utc": _now(), "seat": seat, "verb": verb, "payload": payload, "routed": routed}
    with open(CTRL_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")

def route(seat, text):
    """Parse the seat's terminator and take the mapped control action.
    Returns {verb, payload, routed, adjourn}. Never raises on a missing terminator."""
    verb, payload = parse(text)
    adjourn = False
    if verb is None:
        routed = "NO TERMINATOR — seat did not hand control back cleanly"
    elif verb == "ESCALATE":
        try:
            import escalation
            eid = escalation.raise_escalation("approval", payload or "(no question given)")
            routed = f"escalation {eid} queued for Visionary"
        except Exception as e:
            routed = f"escalate (queue write failed: {e})"
    elif verb == "ADJOURN":
        adjourn = True
        routed = "meeting adjourned by Integrator"
    elif verb == "RESOLVED":
        routed = f"issue resolved: {payload or '(no id)'}"
    elif verb == "HOLD":
        routed = f"hold / no action: {payload or '(none)'}"
    elif verb == "REPORT":
        routed = "report acknowledged"
    else:
        routed = f"UNKNOWN terminator '{verb}' — treated as no-op"
    _log(seat, verb, payload, routed)
    return {"verb": verb, "payload": payload, "routed": routed, "adjourn": adjourn}

def banner(seat, decision):
    v = decision["verb"] or "—"
    return f"[EOS ⟦{v}⟧ {seat}] {decision['routed']}" + (
        f" :: {decision['payload']}" if decision["payload"] and v in ("ESCALATE", "HOLD") else "")
