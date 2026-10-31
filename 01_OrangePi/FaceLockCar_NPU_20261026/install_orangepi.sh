#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -c 'import sys,platform; assert (3,10)<=sys.version_info[:2]<=(3,12), "Python 3.10..3.12 required"; assert platform.machine() in ("aarch64","arm64"), "ARM64 required"'
if [ -d ../wheels ]; then
    python3 -c 'import sys; assert sys.version_info[:2]==(3,10), "Bundled offline wheels require Python 3.10; obtain matching ARM64 wheels for other versions"'
fi
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip libgl1 libglib2.0-0 libxcb-xinerama0 libxkbcommon-x11-0 v4l-utils
python3 -m venv .venv
if [ -d ../wheels ]; then
    .venv/bin/python -m pip install --no-index --find-links ../wheels -r requirements.txt
else
    .venv/bin/python -m pip install --only-binary=:all: -r requirements.txt
fi
.venv/bin/python -c 'import cv2; print("OpenCV",cv2.__version__,cv2.__file__); assert tuple(map(int,cv2.__version__.split(".")[:2]))>=(4,8)'
.venv/bin/python verify_models.py
