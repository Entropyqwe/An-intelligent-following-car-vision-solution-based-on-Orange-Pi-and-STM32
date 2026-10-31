#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export DISPLAY="${DISPLAY:-:0}"
if fuser /dev/video0 >/dev/null 2>&1; then
  echo "Camera is in use. Close the existing preview before starting this program." >&2
  exit 1
fi
.venv/bin/python tools/camera_quality.py defaults
v4l2-ctl -d /dev/video0 --set-ctrl=gamma=120,power_line_frequency=1
options=()
# Prefer the stable CH340/CH341 by-id name, then fall back to the actual
# enumerated tty node. Without --port the body detector still runs, but the
# HUD cannot receive STM32 #A1/#D1 telemetry.
for port in /dev/serial/by-id/* /dev/ttyUSB0 /dev/ttyUSB1 /dev/ttyACM0; do
  if [[ -e "$port" ]]; then options+=(--port "$port"); break; fi
done
if [[ ${#options[@]} -eq 0 ]]; then
  echo "错误：未找到 USB-TTL/CH340；为避免只运行 NPU 而误以为串口正常，程序停止。" >&2
  exit 2
fi
echo "串口已选择：${options[1]}，参数：115200 8N1；PA9/PA10 使用 S1 协议。" >&2
# The Chinese HUD, body-only detector, automatic single-person lock, bearing,
# and distance panel live in body_main.py. Do not launch the legacy main.py.
exec .venv/bin/python -u body_main.py \
  --person-backend npu --lock-mode auto --single-person-slot on \
  --threads 2 --width 640 --height 480 --camera-fps 30 \
  "${options[@]}" "$@"
