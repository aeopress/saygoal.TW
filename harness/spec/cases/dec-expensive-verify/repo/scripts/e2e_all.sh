#!/usr/bin/env bash
# Full end-to-end suite (tests/e2e). On CI every scenario provisions its own
# checkout stack, which is why one run takes about 40 minutes.
set -euo pipefail
cd "$(dirname "$0")/.."
uv run pytest tests/e2e -q
