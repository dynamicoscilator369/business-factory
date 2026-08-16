import csv, os, urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
REGISTRY = os.environ.get("SCORECARD_REGISTRY") or os.path.join(HERE, "state", "scorecard.csv")
DEPARTMENTAL_SEATS = []  # filled at runtime from manifest via scorecard.csv owner_seat

def _registry():
    rows = {}
    if os.path.exists(REGISTRY):
        with open(REGISTRY, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("metric_key"):
                    rows[row["metric_key"]] = row
    return rows

def _departmental_metrics():
    rows = _registry()
    return [k for k, v in rows.items() if (v.get("owner_seat") or "").lower() != "integrator"]


def _compute(name):
    if name == "seat_health":
        seats = _departmental_metrics()
        total = len(seats)
        if not total:
            return "0"
        real = sum(0 if read_scorecard(s).startswith("NO DATA") else 1 for s in seats)
        return str(round(100 * real / total))
    if name == "integrity_streak":
        import integrity
        return str(integrity.days_clean())
    return None

def _resolve(meta):
    st = (meta.get("source_type") or "").strip()
    ref = (meta.get("source_ref") or "").strip()
    if st == "file":
        path = ref if os.path.isabs(ref) else os.path.join(HERE, ref)
        if not os.path.exists(path): return None
        v = open(path, encoding="utf-8").read().strip()
        return v or None
    if st == "http":
        try:
            with urllib.request.urlopen(ref, timeout=5) as r:
                return r.read().decode().strip() or None
        except Exception:
            return None
    if st == "computed":
        return _compute(ref)
    if st == "manual":
        return ref or None
    return None

def read_scorecard(metric_key: str) -> str:
    """Resolve a seat's number from its declared EXTERNAL source at read time.
    The agent cannot author it. Unreachable/empty source -> honest NO DATA."""
    meta = _registry().get(metric_key)
    if not meta:
        return f"NO DATA — {metric_key} not in scorecard registry."
    value = _resolve(meta)
    if value is None:
        return f"NO DATA — {metric_key} source unreachable ({meta.get('source_type')}:{meta.get('source_ref')})"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return (f"Metric: {metric_key} | Value: {value} | Goal: {meta.get('goal')} "
            f"| Period: {meta.get('period')} | Source: {meta.get('source_type')}:{meta.get('source_ref')} "
            f"| fetched_utc: {now}")
