"""Start a PipelineWorkflow for a business id."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from kernel.temporal.client import connect_client, profile_name
from kernel.temporal.shared import TASK_QUEUE
from kernel.temporal.workflows import PipelineWorkflow


def workflow_id_for(business_id: str) -> str:
    safe = business_id.replace("/", "_")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"pipeline-{safe}-{stamp}"


async def start_pipeline(business_id: str) -> dict:
    client = await connect_client()
    wf_id = workflow_id_for(business_id)
    handle = await client.start_workflow(
        PipelineWorkflow.run,
        business_id,
        id=wf_id,
        task_queue=TASK_QUEUE,
    )
    print(
        f"Started PipelineWorkflow {handle.id} on {TASK_QUEUE!r} "
        f"(profile {profile_name()!r}). Waiting for result…"
    )
    result = await handle.result()
    return result


def main(business_id: str) -> dict:
    return asyncio.run(start_pipeline(business_id))


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Start a business pipeline Workflow")
    parser.add_argument("business", help="Business id (folder under businesses/)")
    args = parser.parse_args()
    print(json.dumps(main(args.business), indent=2, default=str))
