"""Base class every business pipeline implements."""
from __future__ import annotations

import json
import pathlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone


class PipelineBase(ABC):
    """Override sync/build/distribute for your business idea."""

    def __init__(self, root: pathlib.Path, manifest: dict):
        self.root = root
        self.manifest = manifest
        self.state_dir = root / ".state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def write_handoff(self, extra: dict | None = None) -> pathlib.Path:
        handoff = {
            "business": self.manifest["id"],
            "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "manifest": self.manifest.get("name"),
            **(extra or {}),
        }
        path = self.state_dir / "handoff.json"
        path.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
        return path

    @abstractmethod
    def sync(self) -> dict:
        """Pull fresh data from external sources. Return summary dict."""

    @abstractmethod
    def build(self) -> dict:
        """Turn synced data into deployable artifacts."""

    @abstractmethod
    def distribute(self) -> dict:
        """Generate syndication / outreach copy."""

    def validate(self) -> dict:
        """Optional — override if your business has validation gates."""
        return {"ok": True, "skipped": True}

    def run(self) -> dict:
        results = {}
        for step in ("sync", "build", "validate", "distribute"):
            fn = getattr(self, step)
            results[step] = fn()
        handoff_path = self.write_handoff({"steps": results})
        results["handoff"] = str(handoff_path)
        return results
