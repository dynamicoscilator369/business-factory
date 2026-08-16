"""Escalation queue — the org's shoulder-tap to the Visionary.
raise_escalation() when the org needs a number or an approval it can't self-source.
answer() ingests Evan's reply: a 'value' answer writes to the target source (provenance
stamped as operator-authored — external to the agent, so NOT a forge); an 'approval'
answer records YES/NO. Durable, tamper-visible via the same integrity engine.
"""
import json, os, re
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
Q = os.path.join(HERE, "state", "escalations.jsonl")

def _now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _valid_value(text):
    """A kind='value' answer must be a bare number (optional decimal, optional
    trailing %). This is the chokepoint that stops prose — e.g. a voicemail
    transcript captured by the voice bridge — from ever masquerading as a metric."""
    return bool(re.fullmatch(r"\s*-?\d+(?:\.\d+)?\s*%?\s*", text or ""))

def _load():
    out = []
    if os.path.exists(Q):
        for ln in open(Q, encoding="utf-8"):
            ln = ln.strip()
            if ln: out.append(json.loads(ln))
    return out

def _save(items):
    with open(Q, "w", encoding="utf-8") as f:
        for it in items: f.write(json.dumps(it) + "\n")

def raise_escalation(kind, prompt, target=None):
    """kind='value' -> answer writes to target metric's source. kind='approval' -> YES/NO."""
    items = _load()
    eid = f"esc_{len(items) + 1}"
    items.append({"id": eid, "kind": kind, "prompt": prompt, "target": target,
                  "status": "pending", "created_utc": _now(), "answer": None})
    _save(items)
    return eid

def pending():
    return [i for i in _load() if i["status"] == "pending"]

def answer(eid, text):
    items = _load()
    hit = next((i for i in items if i["id"] == eid and i["status"] == "pending"), None)
    if not hit:
        return f"no pending escalation {eid}"
    # GUARD: a 'value' answer must be numeric. Reject prose (voicemail transcripts,
    # etc.) and keep the escalation PENDING so a real number can still arrive.
    if hit["kind"] == "value" and not _valid_value(text):
        hit.setdefault("rejected", []).append({"utc": _now(), "text": text})
        _save(items)
        return (f"REJECTED: {(text or '').strip()[:60]!r} is not a number. "
                f"Escalation {eid} stays pending — reply a bare number "
                f"(e.g. 88 or 99.5%) for metric '{hit.get('target')}'.")
    text = text.strip()
    hit["status"] = "answered"; hit["answer"] = text; hit["answered_utc"] = _now()
    if hit["kind"] == "value" and hit.get("target"):
        import integrity
        path = os.path.join(HERE, "state", "sources", f"{hit['target']}.value")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f: f.write(text.strip())
        integrity.record_provenance(hit["target"], path)  # operator-authored = legit external input
        result = f"wrote {text.strip()!r} to {hit['target']} source (provenance stamped)"
    else:
        result = f"approval recorded: {text.strip()!r}"
    _save(items)
    return result
