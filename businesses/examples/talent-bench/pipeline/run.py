"""Talent Bench pipeline — Mercor/Outlier/DataAnnotation job board."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from kernel.pipeline_base import PipelineBase  # noqa: E402


class Pipeline(PipelineBase):
    def _run(self, script: str) -> None:
        env = os.environ.copy()
        if os.environ.get("MERCOR_REFERRAL_CODE") or os.environ.get("SITE_BASE_URL"):
            subprocess.run(["bash", "apply-secrets.sh"], cwd=self.root, check=True, env=env)
        subprocess.run([sys.executable, script], cwd=self.root, check=True, env=env)

    def sync(self) -> dict:
        self._run("sync.py")
        jobs = json.loads((self.root / "jobs.json").read_text(encoding="utf-8"))
        state_path = self.root / ".state" / "sync-state.json"
        added = removed = 0
        if state_path.exists():
            st = json.loads(state_path.read_text(encoding="utf-8"))
            hist = st.get("history", [])
            added = sum(1 for h in hist if h.get("event") == "added")
            removed = sum(1 for h in hist if h.get("event") == "removed")
        count = len(jobs)
        (self.root / ".state" / "job_count.txt").write_text(str(count), encoding="utf-8")
        return {"jobs": count, "added": added, "removed": removed}

    def build(self) -> dict:
        self._run("build.py")
        n = (self.root / "site" / "index.html").read_text(encoding="utf-8").count('class="card"')
        return {"site": str(self.root / "site"), "cards": n}

    def validate(self) -> dict:
        self._run("validate.py")
        return {"ok": True}

    def distribute(self) -> dict:
        self._run("distribute.py")
        today = date.today().isoformat()
        outbox = self.root / "outbox" / today
        posts = len(list(outbox.rglob("*.txt"))) if outbox.exists() else 0
        return {"outbox": str(outbox), "posts": posts}

    def write_handoff(self, extra: dict | None = None) -> Path:
        today = date.today().isoformat()
        jobs = []
        if (self.root / "jobs.json").exists():
            jobs = json.loads((self.root / "jobs.json").read_text(encoding="utf-8"))
        turkey = [
            {"id": j["id"], "title": j["title"]}
            for j in jobs
            if "turkey" in j.get("verticals", [])
            or "turkish" in j.get("title", "").lower()
            or j.get("region", "").lower() == "turkey"
        ]
        return super().write_handoff({
            **(extra or {}),
            "totalJobs": len(jobs),
            "turkeyJobs": turkey,
            "outboxDir": f"outbox/{today}",
            "postizQueue": f"outbox/{today}/postiz-queue.json",
        })
