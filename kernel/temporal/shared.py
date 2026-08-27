"""Shared Temporal names. No connection settings live here."""

# Default env-config profile in temporal.toml (see TEMPORAL_PROFILE).
DEFAULT_PROFILE = "cloud-setup"

# Dedicated queue — not the money-transfer sample's task queue.
TASK_QUEUE = "business-factory-pipeline"

PIPELINE_STAGES = ("sync", "build", "validate", "distribute")
