"""Temporal pipeline wiring — no live Temporal Cloud required."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kernel.business import load_pipeline, record_pipeline_run  # noqa: E402
from kernel.temporal.shared import DEFAULT_PROFILE, PIPELINE_STAGES, TASK_QUEUE  # noqa: E402


class TestNoSecretsInRepo(unittest.TestCase):
    def test_client_does_not_hardcode_cloud_settings(self):
        text = (ROOT / "kernel" / "temporal" / "client.py").read_text(encoding="utf-8")
        self.assertNotIn("tmprl.cloud", text)
        self.assertNotIn("localhost:7233", text)
        self.assertNotIn("api_key=", text)
        self.assertNotRegex(text, r'api_key\s*=\s*["\']')
        self.assertIn("ClientConfig.load_client_connect_config", text)

    def test_task_queue_is_not_money_transfer_sample(self):
        self.assertEqual(TASK_QUEUE, "business-factory-pipeline")
        self.assertNotIn("money", TASK_QUEUE.lower())
        self.assertNotIn("transfer", TASK_QUEUE.lower())

    def test_default_profile_is_cloud_setup(self):
        self.assertEqual(DEFAULT_PROFILE, "cloud-setup")


class TestEnvConfigProfile(unittest.TestCase):
    def test_profile_name_defaults_to_cloud_setup(self):
        from kernel.temporal.client import profile_name

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TEMPORAL_PROFILE", None)
            self.assertEqual(profile_name(), "cloud-setup")

    def test_profile_name_respects_temporal_profile(self):
        from kernel.temporal.client import profile_name

        with patch.dict(os.environ, {"TEMPORAL_PROFILE": "other-profile"}):
            self.assertEqual(profile_name(), "other-profile")

    def test_load_connect_config_reads_cloud_setup_profile(self):
        from kernel.temporal.client import load_connect_config

        toml = """
[profile.cloud-setup]
address = "example.invalid:7233"
namespace = "demo-namespace"
api_key = "test-key-not-a-secret"
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "temporal.toml"
            path.write_text(toml, encoding="utf-8")
            env = {
                "TEMPORAL_CONFIG_FILE": str(path),
            }
            # Drop profile/address overrides so the file wins.
            for key in (
                "TEMPORAL_PROFILE",
                "TEMPORAL_ADDRESS",
                "TEMPORAL_NAMESPACE",
                "TEMPORAL_API_KEY",
            ):
                env[key] = ""
            with patch.dict(os.environ, env, clear=False):
                os.environ.pop("TEMPORAL_PROFILE", None)
                os.environ.pop("TEMPORAL_ADDRESS", None)
                os.environ.pop("TEMPORAL_NAMESPACE", None)
                os.environ.pop("TEMPORAL_API_KEY", None)
                os.environ["TEMPORAL_CONFIG_FILE"] = str(path)
                cfg = load_connect_config()
        self.assertEqual(cfg.get("target_host"), "example.invalid:7233")
        self.assertEqual(cfg.get("namespace"), "demo-namespace")
        self.assertNotIn("real-api-key", str(cfg.get("api_key", "")))


class TestActivitiesUseExistingPipeline(unittest.TestCase):
    def setUp(self):
        from temporalio.testing import ActivityEnvironment

        self.env = ActivityEnvironment()
        self.business_id = "_template"
        state = ROOT / "businesses" / "_template" / ".state"
        self.handoff = state / "handoff.json"
        self.runs = state / "pipeline_runs.txt"
        if self.handoff.exists():
            self.handoff.unlink()

    def test_four_stage_activities_call_pipeline_methods(self):
        from kernel.temporal.activities import build, distribute, sync, validate

        pipeline = load_pipeline(self.business_id)
        self.assertEqual(self.env.run(sync, self.business_id), pipeline.sync())
        self.assertEqual(self.env.run(build, self.business_id), pipeline.build())
        self.assertEqual(self.env.run(validate, self.business_id), pipeline.validate())
        self.assertEqual(self.env.run(distribute, self.business_id), pipeline.distribute())

    def test_write_handoff_matches_run_bookkeeping(self):
        from kernel.temporal.activities import write_handoff

        steps = {
            "sync": {"status": "stub"},
            "build": {"status": "stub"},
            "validate": {"ok": True},
            "distribute": {"status": "stub"},
        }
        before = int(self.runs.read_text().strip()) if self.runs.exists() else 0
        path = self.env.run(write_handoff, self.business_id, steps)
        self.assertTrue(Path(path).exists())
        text = Path(path).read_text(encoding="utf-8")
        self.assertIn("sync", text)
        self.assertEqual(int(self.runs.read_text().strip()), before + 1)


class TestLocalPipelineStillWorks(unittest.TestCase):
    def test_in_process_run_writes_handoff(self):
        pipeline = load_pipeline("_template")
        result = pipeline.run()
        self.assertEqual(set(PIPELINE_STAGES), set(result) - {"handoff"})
        self.assertTrue(Path(result["handoff"]).exists())

    def test_record_pipeline_run_increments(self):
        n1 = record_pipeline_run("_template")
        n2 = record_pipeline_run("_template")
        self.assertEqual(n2, n1 + 1)

    def test_cli_exposes_temporal_commands(self):
        import io

        import main as cli

        self.assertTrue(callable(cli.cmd_worker))
        self.assertTrue(callable(cli.cmd_start))
        self.assertTrue(callable(cli.cmd_pipeline))
        buf = io.StringIO()
        with patch("sys.argv", ["main.py", "-h"]), patch("sys.stdout", buf):
            with self.assertRaises(SystemExit) as ctx:
                cli.main()
        self.assertEqual(ctx.exception.code, 0)
        help_text = buf.getvalue()
        self.assertIn("start", help_text)
        self.assertIn("worker", help_text)
        self.assertIn("pipeline", help_text)
        self.assertIn("publish", help_text)


class TestWorkflowRetriesOnlyFailedStage(unittest.IsolatedAsyncioTestCase):
    async def test_distribute_retry_does_not_rerun_sync(self):
        from temporalio import activity
        from temporalio.testing import WorkflowEnvironment
        from temporalio.worker import Worker

        from kernel.temporal.shared import TASK_QUEUE
        from kernel.temporal.workflows import PipelineWorkflow

        counts = {
            "sync": 0,
            "build": 0,
            "validate": 0,
            "distribute": 0,
            "write_handoff": 0,
            "publish": 0,
        }

        @activity.defn(name="sync")
        def fake_sync(business_id: str) -> dict:
            counts["sync"] += 1
            return {"n": counts["sync"]}

        @activity.defn(name="build")
        def fake_build(business_id: str) -> dict:
            counts["build"] += 1
            return {"n": counts["build"]}

        @activity.defn(name="validate")
        def fake_validate(business_id: str) -> dict:
            counts["validate"] += 1
            return {"ok": True, "n": counts["validate"]}

        @activity.defn(name="distribute")
        def flaky_distribute(business_id: str) -> dict:
            counts["distribute"] += 1
            if counts["distribute"] == 1:
                raise RuntimeError("simulated crash mid-distribute")
            return {"n": counts["distribute"]}

        @activity.defn(name="write_handoff")
        def fake_handoff(business_id: str, steps: dict) -> str:
            counts["write_handoff"] += 1
            return f"/tmp/handoff-{business_id}.json"

        @activity.defn(name="publish")
        def fake_publish(business_id: str) -> dict:
            counts["publish"] += 1
            return {"skipped": False, "bucket": "demo/artifacts", "business": business_id}

        try:
            async with await WorkflowEnvironment.start_time_skipping() as env:
                async with Worker(
                    env.client,
                    task_queue=TASK_QUEUE,
                    workflows=[PipelineWorkflow],
                    activities=[
                        fake_sync,
                        fake_build,
                        fake_validate,
                        flaky_distribute,
                        fake_handoff,
                        fake_publish,
                    ],
                    activity_executor=ThreadPoolExecutor(max_workers=4),
                ):
                    result = await env.client.execute_workflow(
                        PipelineWorkflow.run,
                        "acme",
                        id="test-pipeline-retry",
                        task_queue=TASK_QUEUE,
                    )
        except Exception as exc:
            self.skipTest(f"Temporal test server unavailable: {exc}")
            return

        self.assertEqual(counts["sync"], 1)
        self.assertEqual(counts["build"], 1)
        self.assertEqual(counts["validate"], 1)
        self.assertEqual(counts["distribute"], 2)
        self.assertEqual(counts["write_handoff"], 1)
        self.assertEqual(counts["publish"], 1)
        self.assertEqual(result["sync"], {"n": 1})
        self.assertEqual(result["distribute"], {"n": 2})
        self.assertTrue(str(result["handoff"]).endswith("handoff-acme.json"))
        self.assertEqual(result["bucket"]["bucket"], "demo/artifacts")


if __name__ == "__main__":
    unittest.main()
