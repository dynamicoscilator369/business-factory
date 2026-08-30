"""Talent Bench Space — search the factory job-board demo."""
from __future__ import annotations

import json
from pathlib import Path

import spaces  # ZeroGPU: import before any CUDA-touching library
import gradio as gr

ROOT = Path(__file__).resolve().parent
JOBS_PATH = ROOT / "jobs.json" if (ROOT / "jobs.json").exists() else ROOT / "jobs.sample.json"
JOBS: list[dict] = json.loads(JOBS_PATH.read_text(encoding="utf-8"))

CSS = """
#col-container { max-width: 1100px; margin: 0 auto; }
.dark .gradio-container { color: var(--body-text-color); }
"""


def _blob(job: dict) -> str:
    return " ".join(
        [
            str(job.get("title", "")),
            str(job.get("summary", "")),
            str(job.get("category", "")),
            str(job.get("source", "")),
            str(job.get("region", "")),
            " ".join(job.get("verticals") or []),
            " ".join(job.get("tags") or []),
            " ".join(job.get("description") or []),
        ]
    ).lower()


def _pay(job: dict) -> str:
    lo, hi = job.get("payMin"), job.get("payMax")
    if not lo and not hi:
        return "—"
    unit = {"HOUR": "/hr", "MONTH": "/mo", "YEAR": "/yr"}.get(job.get("payUnit", "HOUR"), "")
    cur = {"USD": "$", "EUR": "€", "GBP": "£"}.get(job.get("currency", "USD"), "")
    if lo and hi and lo != hi:
        return f"{cur}{lo:g}–{hi:g}{unit}"
    return f"{cur}{(lo or hi):g}{unit}"


def _rows(jobs: list[dict]) -> list[list[str]]:
    rows = []
    for job in jobs:
        rows.append(
            [
                job.get("title", ""),
                job.get("source", ""),
                ", ".join(job.get("verticals") or []) or "—",
                job.get("region", "Worldwide"),
                _pay(job),
                job.get("applyUrl") or "",
            ]
        )
    return rows


@spaces.GPU(duration=15)
def _zerogpu_keepalive() -> None:
    """No-op so a free account can host this CPU demo on ZeroGPU."""
    return None


def search_jobs(query: str = "", source: str = "all", vertical: str = "all") -> tuple[list[list[str]], str]:
    """Filter Talent Bench listings by text, source, and vertical."""
    q = (query or "").strip().lower()
    hits = []
    for job in JOBS:
        if source != "all" and job.get("source") != source:
            continue
        verts = job.get("verticals") or []
        if vertical != "all" and vertical not in verts:
            continue
        if q and q not in _blob(job):
            continue
        hits.append(job)
    note = f"{len(hits)} listing{'s' if len(hits) != 1 else ''} · snapshot from the local Talent Bench folder"
    return _rows(hits), note


SOURCES = ["all", *sorted({str(j.get("source", "")) for j in JOBS if j.get("source")})]
VERTICALS = ["all", *sorted({v for j in JOBS for v in (j.get("verticals") or [])})]

with gr.Blocks(theme=gr.themes.Citrus(), css=CSS, title="Talent Bench") as demo:
    with gr.Column(elem_id="col-container"):
        gr.Markdown(
            """
# Talent Bench
Remote AI-training and music-production contracts — one board.

Demo of the **local** `businesses/examples/talent-bench` factory folder
(`sync → build → validate → distribute`). Listings below are a snapshot;
the live board is produced by the kernel pipeline.
"""
        )
        with gr.Row():
            query = gr.Textbox(
                label="Search",
                placeholder="turkish lyrics, DAW, coding…",
                scale=4,
            )
            source = gr.Dropdown(SOURCES, value="all", label="Source", scale=1)
            vertical = gr.Dropdown(VERTICALS, value="all", label="Vertical", scale=1)
        run = gr.Button("Search", variant="primary")
        status = gr.Markdown()
        table = gr.Dataframe(
            headers=["Title", "Source", "Verticals", "Region", "Pay", "Apply"],
            datatype=["str", "str", "str", "str", "str", "str"],
            wrap=True,
            interactive=False,
        )
        gr.Examples(
            examples=[
                ["turkish music"],
                ["video creator"],
                ["coding python"],
                ["DAW mix"],
            ],
            inputs=[query],
            outputs=[table, status],
            fn=search_jobs,
            cache_examples=True,
            cache_mode="lazy",
        )
        run.click(search_jobs, [query, source, vertical], [table, status])
        query.submit(search_jobs, [query, source, vertical], [table, status])
        demo.load(lambda: search_jobs(), outputs=[table, status])

if __name__ == "__main__":
    demo.launch(mcp_server=True)
