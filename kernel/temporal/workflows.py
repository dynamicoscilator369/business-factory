"""Pipeline.run() as a Workflow: one Activity per stage so retries stay local."""
from __future__ import annotations

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from kernel.temporal.activities import (
        build,
        distribute,
        sync,
        validate,
        write_handoff,
    )

# Per-stage budget. Talent Bench's local run is ~90s; leave room for real syncs.
_STAGE_TIMEOUT = timedelta(minutes=30)
_HANDOFF_TIMEOUT = timedelta(minutes=2)
_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=2),
    maximum_attempts=5,
)


@workflow.defn
class PipelineWorkflow:
    """sync → build → validate → distribute, then write ``.state/handoff.json``.

    Each stage is its own Activity. A crash in distribute retries only
    distribute — earlier stages are not re-executed (withdraw-style isolation).
    Implementations stay on each business's ``pipeline/run.py``.
    """

    @workflow.run
    async def run(self, business_id: str) -> dict:
        steps: dict = {}
        steps["sync"] = await workflow.execute_activity(
            sync,
            business_id,
            start_to_close_timeout=_STAGE_TIMEOUT,
            retry_policy=_RETRY,
        )
        steps["build"] = await workflow.execute_activity(
            build,
            business_id,
            start_to_close_timeout=_STAGE_TIMEOUT,
            retry_policy=_RETRY,
        )
        steps["validate"] = await workflow.execute_activity(
            validate,
            business_id,
            start_to_close_timeout=_STAGE_TIMEOUT,
            retry_policy=_RETRY,
        )
        steps["distribute"] = await workflow.execute_activity(
            distribute,
            business_id,
            start_to_close_timeout=_STAGE_TIMEOUT,
            retry_policy=_RETRY,
        )
        handoff = await workflow.execute_activity(
            write_handoff,
            args=[business_id, steps],
            start_to_close_timeout=_HANDOFF_TIMEOUT,
            retry_policy=_RETRY,
        )
        return {**steps, "handoff": handoff}
