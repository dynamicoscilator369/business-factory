"""Load a business module from businesses/<id>/ or businesses/examples/<id>/."""
from __future__ import annotations

import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUSINESSES = ROOT / "businesses"


def _iter_business_dirs():
    for p in sorted(BUSINESSES.iterdir()):
        if p.is_dir() and p.name == "examples":
            for ex in sorted(p.iterdir()):
                if ex.is_dir() and (ex / "manifest.json").exists():
                    yield f"examples/{ex.name}", ex
            continue
        if p.is_dir() and not p.name.startswith("_") and (p / "manifest.json").exists():
            yield p.name, p


def list_businesses() -> list[str]:
    return [bid for bid, _ in _iter_business_dirs()]


def business_root(business_id: str) -> pathlib.Path:
    path = BUSINESSES / business_id
    if not path.exists():
        raise FileNotFoundError(f"No business at businesses/{business_id}")
    return path


def load_manifest(business_id: str) -> dict:
    path = business_root(business_id) / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_pipeline(business_id: str):
    run_path = business_root(business_id) / "pipeline" / "run.py"
    if not run_path.exists():
        raise FileNotFoundError(f"No pipeline at {run_path}")
    spec = importlib.util.spec_from_file_location(
        f"biz_{business_id.replace('/', '_')}_pipeline", run_path
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    if not hasattr(mod, "Pipeline"):
        raise AttributeError(f"{run_path} must define class Pipeline")
    return mod.Pipeline(business_root(business_id), load_manifest(business_id))
