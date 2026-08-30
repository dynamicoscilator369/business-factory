"""Publish pipeline artifacts to a Hugging Face Storage Bucket.

No bucket id, token, or username is hardcoded. Resolution order:

1. ``HF_BUCKET`` / ``HF_BUCKET_ID`` (``namespace/name`` or ``hf://buckets/...``)
2. ``manifest.storage.hf_bucket``
3. The newest bucket returned by ``list_buckets()`` when logged in
   (the usual case after creating one new bucket on the Hub)
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from kernel.business import business_root, load_manifest

_FILE_ARTIFACTS = (".state/handoff.json", "jobs.json", "scorecard.csv")
_DIR_ARTIFACTS = ("outbox", "site")


def normalize_bucket_id(raw: str) -> str:
    value = raw.strip()
    for prefix in ("hf://buckets/", "hf://bucket/"):
        if value.startswith(prefix):
            value = value[len(prefix) :]
            break
    return value.strip("/")


def resolve_bucket_id(manifest: dict | None = None) -> str | None:
    raw = os.environ.get("HF_BUCKET") or os.environ.get("HF_BUCKET_ID")
    if not raw and manifest:
        raw = (manifest.get("storage") or {}).get("hf_bucket")
    if raw:
        return normalize_bucket_id(str(raw))
    return _newest_listed_bucket()


def bucket_uri(bucket_id: str, *parts: str) -> str:
    suffix = "/".join(p.strip("/") for p in parts if p)
    base = f"hf://buckets/{normalize_bucket_id(bucket_id)}"
    return f"{base}/{suffix}" if suffix else base


def _newest_listed_bucket() -> str | None:
    try:
        from huggingface_hub import list_buckets
    except ImportError:
        return None
    try:
        buckets = list(list_buckets())
    except Exception:
        return None
    if not buckets:
        return None

    def _created(bucket: Any) -> datetime:
        created = getattr(bucket, "created_at", None)
        if created is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        if created.tzinfo is None:
            return created.replace(tzinfo=timezone.utc)
        return created

    newest = max(buckets, key=_created)
    return getattr(newest, "id", None)


def collect_artifact_paths(root: Path) -> dict[str, list[str]]:
    files = [rel for rel in _FILE_ARTIFACTS if (root / rel).is_file()]
    dirs = [rel for rel in _DIR_ARTIFACTS if (root / rel).is_dir()]
    return {"files": files, "dirs": dirs}


def publish_business(business_id: str, *, missing_ok: bool = False) -> dict:
    """Upload handoff / outbox / site (and jobs.json if present) for one business."""
    manifest = load_manifest(business_id)
    bucket_id = resolve_bucket_id(manifest)
    if not bucket_id:
        if missing_ok:
            return {
                "skipped": True,
                "reason": "No Hugging Face bucket. Set HF_BUCKET=namespace/name "
                "or run `hf auth login` so the newest bucket can be used.",
            }
        raise RuntimeError(
            "No Hugging Face bucket configured. Set HF_BUCKET=namespace/name "
            "(or manifest.storage.hf_bucket), and authenticate with HF_TOKEN "
            "or `hf auth login`. Do not put tokens in this repo."
        )

    try:
        from huggingface_hub import batch_bucket_files, sync_bucket
    except ImportError as exc:
        raise RuntimeError(
            "huggingface_hub>=1.5.0 is required to publish to a Storage Bucket. "
            "Install with: pip install -r requirements.txt"
        ) from exc

    root = business_root(business_id)
    artifacts = collect_artifact_paths(root)
    uploaded: list[str] = []

    adds: list[tuple[str, str]] = []
    for rel in artifacts["files"]:
        dest = f"{business_id}/{rel}"
        adds.append((str(root / rel), dest))
        uploaded.append(dest)
    if adds:
        batch_bucket_files(bucket_id, add=adds)

    for rel in artifacts["dirs"]:
        dest_uri = bucket_uri(bucket_id, business_id, rel)
        sync_bucket(str(root / rel), dest_uri, quiet=True)
        uploaded.append(f"{business_id}/{rel}/")

    return {
        "skipped": False,
        "bucket": bucket_id,
        "uri": bucket_uri(bucket_id, business_id),
        "url": f"https://huggingface.co/buckets/{bucket_id}",
        "uploaded": uploaded,
    }
