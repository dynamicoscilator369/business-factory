"""Hugging Face Storage Bucket wiring — no live Hub login required."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kernel.hf_bucket import (  # noqa: E402
    bucket_uri,
    collect_artifact_paths,
    normalize_bucket_id,
    publish_business,
    resolve_bucket_id,
)


class TestBucketIdHelpers(unittest.TestCase):
    def test_normalize_strips_hf_uri_and_slashes(self):
        self.assertEqual(
            normalize_bucket_id("hf://buckets/you/factory/"),
            "you/factory",
        )
        self.assertEqual(normalize_bucket_id("you/factory"), "you/factory")

    def test_bucket_uri(self):
        self.assertEqual(
            bucket_uri("you/factory", "acme", "outbox"),
            "hf://buckets/you/factory/acme/outbox",
        )

    def test_resolve_prefers_hf_bucket_env(self):
        with patch.dict(os.environ, {"HF_BUCKET": "hf://buckets/you/new-bucket"}):
            self.assertEqual(resolve_bucket_id(), "you/new-bucket")

    def test_resolve_uses_manifest_when_env_unset(self):
        env = os.environ.copy()
        env.pop("HF_BUCKET", None)
        env.pop("HF_BUCKET_ID", None)
        with patch.dict(os.environ, env, clear=True):
            with patch("kernel.hf_bucket._newest_listed_bucket", return_value=None):
                self.assertEqual(
                    resolve_bucket_id({"storage": {"hf_bucket": "you/from-manifest"}}),
                    "you/from-manifest",
                )

    def test_resolve_uses_newest_listed_bucket(self):
        older = SimpleNamespace(
            id="you/old",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        newer = SimpleNamespace(
            id="you/new-bucket",
            created_at=datetime(2026, 8, 29, tzinfo=timezone.utc),
        )
        env = os.environ.copy()
        env.pop("HF_BUCKET", None)
        env.pop("HF_BUCKET_ID", None)
        with patch.dict(os.environ, env, clear=True):
            with patch("huggingface_hub.list_buckets", return_value=[older, newer]):
                self.assertEqual(resolve_bucket_id({}), "you/new-bucket")


class TestPublishArtifacts(unittest.TestCase):
    def test_collects_handoff_and_outbox_only_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".state").mkdir()
            (root / ".state" / "handoff.json").write_text("{}\n", encoding="utf-8")
            (root / "outbox").mkdir()
            artifacts = collect_artifact_paths(root)
        self.assertEqual(artifacts["files"], [".state/handoff.json"])
        self.assertEqual(artifacts["dirs"], ["outbox"])

    def test_publish_uploads_under_business_prefix(self):
        from kernel.business import load_pipeline

        load_pipeline("_template").run()
        adds: list = []
        syncs: list = []

        def fake_batch(bucket_id, add=None, **_kwargs):
            adds.append((bucket_id, list(add or [])))

        def fake_sync(source, dest, **_kwargs):
            syncs.append((source, dest))

        with patch.dict(os.environ, {"HF_BUCKET": "you/factory"}):
            with patch("huggingface_hub.batch_bucket_files", fake_batch):
                with patch("huggingface_hub.sync_bucket", fake_sync):
                    result = publish_business("_template")

        self.assertFalse(result["skipped"])
        self.assertEqual(result["bucket"], "you/factory")
        self.assertEqual(result["uri"], "hf://buckets/you/factory/_template")
        self.assertTrue(adds)
        self.assertEqual(adds[0][0], "you/factory")
        dests = [dest for _src, dest in adds[0][1]]
        self.assertIn("_template/.state/handoff.json", dests)
        self.assertTrue(any(dest.endswith("/_template/outbox") for _src, dest in syncs))

    def test_publish_skips_when_no_bucket_and_missing_ok(self):
        env = os.environ.copy()
        env.pop("HF_BUCKET", None)
        env.pop("HF_BUCKET_ID", None)
        with patch.dict(os.environ, env, clear=True):
            with patch("kernel.hf_bucket._newest_listed_bucket", return_value=None):
                result = publish_business("_template", missing_ok=True)
        self.assertTrue(result["skipped"])

    def test_source_has_no_hardcoded_token_or_bucket(self):
        text = (ROOT / "kernel" / "hf_bucket.py").read_text(encoding="utf-8")
        self.assertNotIn("hf_xxxxx", text)
        self.assertNotIn("HF_TOKEN=", text)
        self.assertNotIn("evanstewart90", text)
        self.assertNotIn("tmprl.cloud", text)


if __name__ == "__main__":
    unittest.main()
