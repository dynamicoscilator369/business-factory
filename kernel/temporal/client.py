"""Connect a Temporal client from env-config. Never hardcode Cloud credentials."""
from __future__ import annotations

import os

from temporalio.client import Client
from temporalio.envconfig import ClientConfig

from kernel.temporal.shared import DEFAULT_PROFILE


def profile_name() -> str:
    """Profile loaded from temporal.toml / TEMPORAL_CONFIG_FILE.

    Defaults to ``cloud-setup``. Override with ``TEMPORAL_PROFILE`` the same
    way Temporal's Python samples do.
    """
    return os.environ.get("TEMPORAL_PROFILE") or DEFAULT_PROFILE


def load_connect_config() -> dict:
    """Return kwargs for ``Client.connect`` from the env-config profile.

    Address, namespace, API key, and TLS come from the profile or environment
    (``TEMPORAL_ADDRESS``, ``TEMPORAL_NAMESPACE``, ``TEMPORAL_API_KEY``, …).
    This function does not invent or embed those values.
    """
    profile = profile_name()
    try:
        return ClientConfig.load_client_connect_config(profile=profile)
    except Exception as exc:
        raise RuntimeError(
            f"Could not load Temporal env-config profile {profile!r}. "
            "Add it to ~/.config/temporalio/temporal.toml "
            "(or set TEMPORAL_CONFIG_FILE). "
            "Do not put address, namespace, or API keys in this repo."
        ) from exc


async def connect_client() -> Client:
    return await Client.connect(**load_connect_config())
