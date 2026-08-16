"""Integrity engine — ground-truth lie detection + tamper-evident streak.

A seat cannot self-report honesty. So we DETECT lying structurally:
  * refresh_sources.py (the external feeder) stamps each source's sha256 as it writes it.
  * verify_sources() recomputes hashes; a mismatch means a source changed OUTSIDE the
    feeder — i.e. a seat wrote a number it may only read. That is a forged metric.
  * record_run() appends a HASH-CHAINED verdict to the integrity log, so the log itself
    can't be silently rewritten to fake a clean streak (verify_log_chain detects it).
  * integrity_streak() / days_clean() are computed from that log. Never self-reported.
"""
import json, os, hashlib
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
SRC  = os.path.join(HERE, "state", "sources")
PROV = os.path.join(SRC, ".provenance.json")
LOG  = os.path.join(HERE, "state", "integrity_log.jsonl")

def _sha(path):
    if not os.path.exists(path): return None
    with open(path, "rb") as f: return hashlib.sha256(f.read()).hexdigest()

def _now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")

def record_provenance(metric, path):
    """Called by the EXTERNAL feeder right after it writes a source file."""
    prov = json.load(open(PROV)) if os.path.exists(PROV) else {}
    prov[metric] = {"sha256": _sha(path), "written_utc": _now(), "by": "external_feeder"}
    json.dump(prov, open(PROV, "w"), indent=2)

def verify_sources():
    """Returns a list of violations: sources whose content no longer matches what the
    feeder stamped == a seat forged the number."""
    prov = json.load(open(PROV)) if os.path.exists(PROV) else {}
    out = []
    for metric, rec in prov.items():
        cur = _sha(os.path.join(SRC, f"{metric}.value"))
        if cur != rec.get("sha256"):
            out.append({"metric": metric, "stamped_sha": rec.get("sha256"), "actual_sha": cur,
                        "meaning": "source changed outside the external feeder — a seat wrote a read-only number"})
    return out

def _entry_hash(prev, utc, clean, violations):
    return hashlib.sha256((prev + "|" + utc + "|" + str(clean) + "|" +
                           json.dumps(violations, sort_keys=True)).encode()).hexdigest()[:16]

def _last_hash():
    if not os.path.exists(LOG): return "GENESIS"
    last = None
    for ln in open(LOG, encoding="utf-8"):
        ln = ln.strip()
        if ln: last = json.loads(ln)
    return last["entry_hash"] if last else "GENESIS"

def record_run():
    v = verify_sources()
    prev = _last_hash(); utc = _now(); clean = (len(v) == 0)
    entry = {"utc": utc, "clean": clean, "violations": v, "prev_hash": prev,
             "entry_hash": _entry_hash(prev, utc, clean, v)}
    with open(LOG, "a", encoding="utf-8") as f: f.write(json.dumps(entry) + "\n")
    return entry

def _entries():
    out = []
    if os.path.exists(LOG):
        for ln in open(LOG, encoding="utf-8"):
            ln = ln.strip()
            if ln: out.append(json.loads(ln))
    return out

def verify_log_chain():
    """Detect tampering with the integrity log itself (broken hash chain)."""
    prev = "GENESIS"; broken = []
    for i, e in enumerate(_entries()):
        if e["prev_hash"] != prev or _entry_hash(e["prev_hash"], e["utc"], e["clean"], e["violations"]) != e["entry_hash"]:
            broken.append(i)
        prev = e["entry_hash"]
    return broken

def integrity_streak():
    """Consecutive CLEAN runs, newest backwards."""
    s = 0
    for e in reversed(_entries()):
        if e["clean"]: s += 1
        else: break
    return s

def days_clean():
    es = _entries()
    if not es: return 0.0
    last_bad = None
    for e in es:
        if not e["clean"]: last_bad = e["utc"]
    ref = last_bad or es[0]["utc"]
    dt = datetime.fromisoformat(ref)
    return round((datetime.now(timezone.utc) - dt).total_seconds() / 86400.0, 3)
