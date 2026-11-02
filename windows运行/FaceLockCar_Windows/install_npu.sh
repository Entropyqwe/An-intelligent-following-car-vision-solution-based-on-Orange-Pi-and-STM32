#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 - <<'PY'
import platform
from pathlib import Path
assert platform.machine() in ('aarch64','arm64'), 'Compile this bridge on the A733 board'
required=['/dev/vipcore','/usr/include/vip_lite.h','/usr/include/vip_lite_common.h',
          '/lib/libVIPhal.so','/lib/libNBGlinker.so','/opt/yolov5/model/yolov5.nb']
missing=[p for p in required if not Path(p).exists()]
if missing:raise SystemExit('Official A733 Linux SDK/runtime/model required: '+', '.join(missing))
PY
bash native/build.sh
.venv/bin/python - <<'PY'
import hashlib
from pathlib import Path
from vip_runtime import VipNetwork
model=Path('/opt/yolov5/model/yolov5.nb')
print('MODEL_SHA256',hashlib.sha256(model.read_bytes()).hexdigest())
network=VipNetwork(model)
try:
 print('INPUT',network.input_info.describe())
 for output in network.output_info:print('OUTPUT',output.describe())
finally:network.close()
PY
