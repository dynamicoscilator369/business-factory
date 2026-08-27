"""Long-running Worker for PipelineWorkflow. Run this on a machine with the repo."""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from temporalio.worker import Worker

from kernel.temporal.activities import (
    build,
    distribute,
    sync,
    validate,
    write_handoff,
)
from kernel.temporal.client import connect_client, profile_name
from kernel.temporal.shared import TASK_QUEUE
from kernel.temporal.workflows import PipelineWorkflow


async def run_worker() -> None:
    client = await connect_client()
    print(
        f"Business Factory worker on task queue {TASK_QUEUE!r} "
        f"(env-config profile {profile_name()!r})"
    )
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[PipelineWorkflow],
        activities=[sync, build, validate, distribute, write_handoff],
        activity_executor=ThreadPoolExecutor(max_workers=8),
    )
    await worker.run()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
