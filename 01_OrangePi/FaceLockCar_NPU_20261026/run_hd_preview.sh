#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export DISPLAY="${DISPLAY:-:0}"
.venv/bin/python tools/camera_quality.py defaults
exec .venv/bin/python main.py --body --person-backend npu --lock-mode auto \
  --width 1280 --height 720 --window-width 980 --quiet-packets "$@"
