"""Business-aware L10 — seats loaded from manifest.json."""
from __future__ import annotations

import os

import integrity
import model_tiers as mt
import eos_protocol as ep
from agents import get_integrator_seat, get_departmental_seat


def _seats_from_manifest(manifest: dict):
    rows = []
    for s in manifest.get("seats", []):
        rows.append((s["name"], s["metric"], s["role"]))
    return rows


def _engine(tier):
    backend = (tier or {}).get("backend", "dry")
    if backend == "grok":
        return f"grok:{tier.get('model')}"
    return f"{tier.get('model')}/{tier.get('thinking') or 'default'}"


def price_payroll(seats):
    print("\n--- Payroll: right person / right seat / right TIER ---")
    tiers = {}
    for name, metric, role in seats:
        mt.record_performance(name, metric)
        tier = mt.earned_tier(name, metric, role)
        if not (os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")):
            tier = {**tier, "backend": "dry", "label": tier.get("label", "?") + " (dry)"}
        tiers[metric] = tier
        print("    " + mt.tier_line(name, tier))
    return tiers


async def run_l10_for_business(manifest: dict):
    business = manifest.get("name", manifest.get("id", "?"))
    seats = _seats_from_manifest(manifest)
    if not seats:
        raise ValueError("manifest.seats is empty")

    print(f"--- L10: {business} ---")
    backend = (os.environ.get("EOS_BACKEND") or "dry").lower()
    print(f"    EOS_BACKEND={backend}")

    payroll = price_payroll(seats)
    integrator_row = next((s for s in manifest["seats"] if s["role"] == "integrator"), manifest["seats"][0])
    int_metric = integrator_row["metric"]
    int_tier = payroll[int_metric]
    integrator = get_integrator_seat(tier=int_tier)

    grunts = [s for s in manifest["seats"] if s["role"] != "integrator"]
    grunt_seats = []
    for g in grunts:
        tier = payroll[g["metric"]]
        grunt_seats.append(
            get_departmental_seat(g["name"], g.get("responsibilities", "-"), g["metric"], tier=tier)
        )

    print("\n--- Scorecard Review ---")
    prompt = "Start the Level 10 meeting. Ask the first departmental seat to report using read_scorecard."
    resp = await integrator.chat(prompt)
    text = await resp.text()
    print(f"\n[Integrator]: {text[:500]}...")
    print("   " + ep.banner("Integrator", ep.route("Integrator", text)))

    handoff = os.environ.get("BUSINESS_ROOT", "") + "/.state/handoff.json"
    if os.path.exists(handoff):
        print(f"\n--- Pipeline handoff on disk: {handoff} ---")
