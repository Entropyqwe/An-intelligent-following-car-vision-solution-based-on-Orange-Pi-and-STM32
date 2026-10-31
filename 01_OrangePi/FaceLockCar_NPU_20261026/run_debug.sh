#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
export DISPLAY="${DISPLAY:-:0}"
export QT_AUTO_SCREEN_SCALE_FACTOR=0
export QT_SCALE_FACTOR=1
export QT_FONT_DPI=96
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1

log="logs/last_run.log"
mkdir -p logs
echo "[$(date '+%F %T')] 启动视觉程序，日志：$log" | tee "$log"
if fuser /dev/video0 >/dev/null 2>&1; then
  echo "错误：/dev/video0 已被其他程序占用。先执行：pkill -f body_main.py" | tee -a "$log"
  read -r -p '按回车关闭...' _
  exit 2
fi

port=''
for candidate in /dev/serial/by-id/* /dev/ttyUSB* /dev/ttyACM*; do
  if [[ -e "$candidate" ]]; then port="$candidate"; break; fi
done
if [[ -z "$port" ]]; then
  echo '错误：没有找到 USB-TTL/CH340。' | tee -a "$log"
  read -r -p '按回车关闭...' _
  exit 2
fi
echo "串口：$port；115200 8N1" | tee -a "$log"

set +e
.venv/bin/python -u body_main.py \
  --person-backend npu --lock-mode auto --single-person-slot on \
  --threads 2 --width 640 --height 480 --camera-fps 30 \
  --port "$port" "$@" 2>&1 | tee -a "$log"
rc=${PIPESTATUS[0]}
echo "[$(date '+%F %T')] 程序结束，退出码：$rc" | tee -a "$log"
echo "查看完整日志：$PWD/$log"
read -r -p '程序已结束，按回车关闭此窗口...' _
exit "$rc"
