"""Activities that call the existing per-business Pipeline methods."""
from __future__ import annotations

from temporalio import activity

from kernel.business import load_pipeline, record_pipeline_run
from kernel.temporal.shared import PIPELINE_STAGES


def _run_stage(business_id: str, stage: str) -> dict:
    if stage not in PIPELINE_STAGES:
        raise ValueError(f"Unknown pipeline stage: {stage}")
    pipeline = load_pipeline(business_id)
    activity.logger.info("pipeline %s %s", business_id, stage)
    result = getattr(pipeline, stage)()
    if not isinstance(result, dict):
        raise TypeError(f"{stage}() must return a dict, got {type(result).__name__}")
    return result


@activity.defn
def sync(business_id: str) -> dict:
    """Pull fresh data — ``Pipeline.sync``."""
    return _run_stage(business_id, "sync")


@activity.defn
def build(business_id: str) -> dict:
    """Turn data into the deliverable — ``Pipeline.build``."""
    return _run_stage(business_id, "build")


@activity.defn
def validate(business_id: str) -> dict:
    """Gate before ship — ``Pipeline.validate``."""
    return _run_stage(business_id, "validate")


@activity.defn
def distribute(business_id: str) -> dict:
    """Syndicate / outreach — ``Pipeline.distribute``."""
    return _run_stage(business_id, "distribute")


@activity.defn
def write_handoff(business_id: str, steps: dict) -> str:
    """Same bookkeeping as ``Pipeline.run()`` after the four stages succeed."""
    pipeline = load_pipeline(business_id)
    path = pipeline.write_handoff({"steps": steps})
    record_pipeline_run(business_id)
    return str(path)


STAGE_ACTIVITIES = (sync, build, validate, distribute)
