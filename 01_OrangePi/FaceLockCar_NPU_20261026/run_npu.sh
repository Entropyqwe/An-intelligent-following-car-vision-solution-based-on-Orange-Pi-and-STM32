#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export DISPLAY="${DISPLAY:-:0}"
exec .venv/bin/python main.py --body --steering --person-backend npu --lock-mode auto --threads 2 --quiet-packets "$@"
