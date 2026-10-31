#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export DISPLAY="${DISPLAY:-:0}"
export QT_AUTO_SCREEN_SCALE_FACTOR=0
export QT_SCALE_FACTOR=1
export QT_FONT_DPI=96
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1

if fuser /dev/video0 >/dev/null 2>&1; then
  echo '摄像头正在被其他程序占用，请先退出旧预览。' >&2
  exit 1
fi

if command -v v4l2-ctl >/dev/null 2>&1; then
  v4l2-ctl -d /dev/video0 --set-ctrl=gamma=120,power_line_frequency=1 || true
fi

args=(--person-backend npu --lock-mode auto --single-person-slot on
      --threads 2 --width 640 --height 480 --camera-fps 30)
port=''
for candidate in /dev/serial/by-id/* /dev/ttyUSB* /dev/ttyACM*; do
  if [[ -e "$candidate" ]]; then
    port="$candidate"
    break
  fi
done
if [[ -z "$port" ]]; then
  echo '错误：没有找到 USB-TTL/CH340，串口未打开；请先接好 TTL 后再启动。' >&2
  exit 2
fi
echo "串口已选择：$port，参数：115200 8N1；PA9/PA10 使用 S1 协议。" >&2
args+=(--port "$port")

# The distance channel is asynchronous (#D1 every 200 ms).  Keep the
# read-only monitor available for diagnosis, but do not run it here because
# it would compete for the same UART as the S1 control process.

exec .venv/bin/python -u body_main.py "${args[@]}" "$@"
