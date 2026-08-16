"""Template pipeline — copy and replace each step for your business idea."""
from __future__ import annotations

import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3]))

from kernel.pipeline_base import PipelineBase  # noqa: E402


class Pipeline(PipelineBase):
    def sync(self) -> dict:
        # TODO: pull from APIs, scrape, read webhooks, etc.
        return {"status": "stub", "message": "Implement sync() for your data sources"}

    def build(self) -> dict:
        # TODO: site, report, inventory file, trading signals, etc.
        return {"status": "stub", "message": "Implement build() for your deliverable"}

    def validate(self) -> dict:
        # TODO: schema checks, lint, test gates
        return {"ok": True, "status": "stub"}

    def distribute(self) -> dict:
        # TODO: write outbox/, queue social posts, send emails
        outbox = self.root / "outbox"
        outbox.mkdir(exist_ok=True)
        return {"status": "stub", "outbox": str(outbox)}


if __name__ == "__main__":
    from kernel.business import load_pipeline

    p = load_pipeline("_template")
    print(p.run())
