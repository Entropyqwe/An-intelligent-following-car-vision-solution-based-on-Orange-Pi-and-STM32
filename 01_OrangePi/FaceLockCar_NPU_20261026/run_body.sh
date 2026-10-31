#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export DISPLAY="${DISPLAY:-:0}"
export QT_AUTO_SCREEN_SCALE_FACTOR=0
export QT_SCALE_FACTOR=1
export QT_FONT_DPI=96
# Tiny tracking matrices should not fan out across all CPU cores.
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
if fuser /dev/video0 >/dev/null 2>&1; then echo 'Camera busy: close the existing program.' >&2; exit 1; fi
.venv/bin/python tools/camera_quality.py defaults
v4l2-ctl -d /dev/video0 --set-ctrl=gamma=120,power_line_frequency=1
port='/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0'
options=()
if [[ -e "$port" ]]; then options+=(--port "$port"); fi
exec .venv/bin/python -u body_main.py "${options[@]}" "$@"
