#!/usr/bin/env bash
# Run pipeline for a business. Grok Bot Scout runs this on schedule.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
BUSINESS="${1:?Usage: run-pipeline.sh <business-id>}"
cd "$ROOT"
python3 main.py pipeline "$BUSINESS"
