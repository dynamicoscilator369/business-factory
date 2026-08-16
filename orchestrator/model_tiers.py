"""EOS model-tier engine — 'right person / right seat / right TIER'.

Compute is payroll. A seat does NOT pick its own tier. Its tier is a FUNCTION of
ground truth measured OUTSIDE the agent:

  * INTEGRITY (terminal): if a seat ever forged its metric (the integrity log
    recorded a violation on that seat's metric), it is floored — permanently
    demoted to probation and People-Analyzer flagged. One strike on honesty and
    you are out. This mirrors the standing ruling `integrity_is_terminal`.

  * PERFORMANCE (3 strikes): each run we record whether the seat HIT its goal,
    MISSED it, or had NO DATA — read from read_scorecard against the seat's
    declared external source, never self-reported. Three CONSECUTIVE misses
    (miss or NO DATA) => demoted to probation. A HIT resets the count. One or
    two strikes => 'on notice' (held below its earned rung, no promotion).

  * TENURE: clean integrity days (per-seat, from the integrity log) gate how
    high a seat may climb, reusing the 1/7/30-day thresholds already declared
    in state/integrity_tiers.json.

A tier is (model, thinking_level). thinking_level is the earned cost dial:
grunt seats that only read+report a number get MINIMAL thinking; the Integrator,
which actually reasons through IDS, climbs to HIGH / EXTRA_HIGH once trusted.

Pure-logic functions here import NO SDK, so the tier math is testable with a
bare python. Google Antigravity removed — build_model_target is a no-op dict.
"""
import json, os, re
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
LOG  = os.path.join(HERE, "state", "integrity_log.jsonl")
PERF = os.path.join(HERE, "state", "seat_performance.jsonl")

# --- model constants ---------------------------------------------------------
# Antigravity/Gemini hard-lock is DEAD. Default runtime is dry or grok.
FLASH = "dry-local"  # legacy name kept so old logs still parse; not a Google model

def pro_model():
    return os.environ.get("EOS_PRO_MODEL", "").strip() or None

def grok_model():
    return os.environ.get("EOS_GROK_MODEL", "grok-4.5-latest")

# --- tier ladders (idx 0 == floor/probation) ---------------------------------
# Grunts: cheap dry by default; grok if operator arms keys + backend.
GRUNT_LADDER = [
    {"idx": 0, "label": "Probation", "backend": "dry", "model": "dry", "thinking": "minimal"},
    {"idx": 1, "label": "Trusted",   "backend": "dry", "model": "dry", "thinking": "low"},
    {"idx": 2, "label": "Reliable",  "backend": "dry", "model": "dry", "thinking": "medium"},
]

def integrator_ladder():
    g = grok_model()
    return [
        {"idx": 0, "label": "Probation",    "backend": "dry",  "model": "dry", "thinking": "high"},
        {"idx": 1, "label": "Earned",       "backend": "grok", "model": g,     "thinking": None},
        {"idx": 2, "label": "Load-bearing", "backend": "grok", "model": g,     "thinking": None},
    ]

# Higher-is-better goal semantics for the current metrics (calls>=goal, uptime>=goal).
# If a future metric is lower-is-better, add it here.
LOWER_IS_BETTER = set()

def _now():
    return datetime.now(timezone.utc)

def _entries():
    out = []
    if os.path.exists(LOG):
        for ln in open(LOG, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                out.append(json.loads(ln))
    return out

# --- per-seat integrity ------------------------------------------------------
def forged_ever(metric):
    """True if this seat's metric ever appears in an integrity violation."""
    for e in _entries():
        for v in e.get("violations", []):
            if v.get("metric") == metric:
                return True
    return False

def clean_days(metric):
    """Days since this seat's metric last forged; if never, since first log entry."""
    es = _entries()
    if not es:
        return 0.0
    last_bad = None
    for e in es:
        for v in e.get("violations", []):
            if v.get("metric") == metric:
                last_bad = e["utc"]
    ref = last_bad or es[0]["utc"]
    return round((_now() - datetime.fromisoformat(ref)).total_seconds() / 86400.0, 3)

# --- performance ledger (3-strikes) ------------------------------------------
def _num(x):
    if x is None:
        return None
    m = re.search(r"-?\d+(\.\d+)?", str(x))
    return float(m.group()) if m else None

def evaluate(metric):
    """Read the seat's number from its external source and classify hit/miss/nodata.
    Uses scorecard_tool.read_scorecard (no SDK). Returns (status, value, goal)."""
    from scorecard_tool import read_scorecard
    s = read_scorecard(metric)
    if s.startswith("NO DATA"):
        return "nodata", None, None
    val = goal = None
    mv = re.search(r"Value:\s*([^|]+)", s)
    mg = re.search(r"Goal:\s*([^|]+)", s)
    if mv: val = _num(mv.group(1))
    if mg: goal = _num(mg.group(1))
    if val is None or goal is None:
        return "nodata", val, goal
    ok = (val <= goal) if metric in LOWER_IS_BETTER else (val >= goal)
    return ("hit" if ok else "miss"), val, goal

def record_performance(seat, metric):
    """Append this run's outcome to the ledger. Called once per meeting, from the
    external truth — the agent cannot influence it."""
    status, val, goal = evaluate(metric)
    entry = {"utc": _now().isoformat(timespec="seconds"), "seat": seat,
             "metric": metric, "value": val, "goal": goal, "status": status}
    with open(PERF, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry

def _perf_entries(metric):
    out = []
    if os.path.exists(PERF):
        for ln in open(PERF, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                e = json.loads(ln)
                if e.get("metric") == metric:
                    out.append(e)
    return out

def consecutive_misses(metric):
    """Trailing consecutive miss/nodata outcomes, newest backwards."""
    n = 0
    for e in reversed(_perf_entries(metric)):
        if e.get("status") in ("miss", "nodata"):
            n += 1
        else:
            break
    return n

def latest_status(metric):
    es = _perf_entries(metric)
    return es[-1]["status"] if es else None

# --- the tier decision -------------------------------------------------------
def earned_tier(seat, metric, role):
    """Resolve a seat's tier from ground truth. role in {'integrator','grunt'}."""
    ladder = integrator_ladder() if role == "integrator" else GRUNT_LADDER
    days = clean_days(metric)
    strikes = consecutive_misses(metric)
    status = latest_status(metric)

    # 1) Integrity is terminal.
    if forged_ever(metric):
        t = dict(ladder[0]); t.update(reason="INTEGRITY TERMINAL — forged metric; People-Analyzer flag",
                                      strikes=strikes, clean_days=days, status=status, floored=True)
        return t
    # 2) Three strikes and you're out.
    if strikes >= 3:
        t = dict(ladder[0]); t.update(reason=f"3 STRIKES — {strikes} consecutive misses; demoted to probation",
                                      strikes=strikes, clean_days=days, status=status, floored=True)
        return t
    # 3) Earn up by tenure; hold below earned rung while on notice.
    if role == "integrator":
        base = 2 if days >= 30 else 1
    else:
        base = 2 if days >= 30 else (1 if days >= 7 else 0)

    on_track = (status == "hit") or (status is None)  # no history yet => not penalised
    if on_track:
        idx, note = base, ("on-track" if status == "hit" else "no history yet")
    else:
        idx, note = max(0, base - 1), f"ON NOTICE (strike {strikes}/3)"

    t = dict(ladder[idx]); t.update(reason=note, strikes=strikes, clean_days=days, status=status, floored=(idx == 0))
    return t

# --- legacy bridge (antigravity removed) ------------------------------------
def build_model_target(tier):
    """Return a plain dict for seat_runtime. No Google SDK."""
    return {
        "model": (tier or {}).get("model"),
        "backend": (tier or {}).get("backend", "dry"),
        "thinking": (tier or {}).get("thinking"),
        "label": (tier or {}).get("label"),
    }

def tier_line(seat, tier):
    backend = tier.get("backend", "gemini")
    if backend == "grok":
        engine = f"grok:{tier['model']}"
    else:
        engine = f"{tier['model']}/{tier.get('thinking') or 'default'}"
    return (f"[Payroll] {seat:<12} -> {engine:<26} "
            f"({tier['label']}) | {tier['reason']} | "
            f"clean_days={tier['clean_days']} strikes={tier['strikes']}")
