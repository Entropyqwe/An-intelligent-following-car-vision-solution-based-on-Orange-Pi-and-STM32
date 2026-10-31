# FaceLockCar 人脸编号锁定与电控数据输出

先插 USB 摄像头，完成电脑验证，再把整个目录复制到香橙派 Zero 3W。
模型已随工程提供，正常使用不用再次下载。运行不需要 PyTorch、CUDA 或 NPU。

## 人体检测与背影连续跟随

实现原理见 [算法说明](docs/ALGORITHM_GUIDE.md)，香橙派评估见 [部署评估](docs/DEPLOYMENT_ASSESSMENT.md)。

```powershell
.\.venv\Scripts\python.exe verify_models.py
.\.venv\Scripts\python.exe main.py --camera 1 --body
```

先用正脸登记并选择目标，连续确认后允许转身；人体漏检、重叠或关联不明确时立即停止，等待重新认脸。该模式是人体轨迹延续，不是凭任意背影识别身份。VS Code 新增“4 人脸与人体连续跟随 camera 1”。

**`--body` 输出 F2 协议，坐标始终来自人体框。** F2 在 F1 字段后追加 `source,face_age_ms`：source=0 无效、1 本帧人脸确认、2 人体连续关联；source=2 时 sim=-1000。接收端须支持 F2，并按人体框重新评估面积和纵向参数。普通人脸模式保持 F1。

新增 NanoDet ONNX 模型由 OpenCV CPU 推理，保留官方许可证，不需要新增 Python 依赖。香橙派尚未实测，先运行：

```bash
.venv/bin/python benchmark_vision.py --camera 0 --frames 300 --face-every 1
.venv/bin/python benchmark_vision.py --camera 0 --frames 300 --face-every 3 --output logs/benchmark_locked.json
.venv/bin/python main.py --camera 0 --body --no-show --target 1
```

基准不发送控制数据；不能用电脑 FPS 代替板上结果。原版人脸模式的说明如下。

## Windows 与 VS Code

推荐 Python 3.12。若已有 Python 3.13，另装 3.12，勿删除原版本。
从 python.org 下载 Python 3.12 的 Windows 安装程序，安装 Python Launcher。

在 VS Code 用“文件 → 打开文件夹”打开 **FaceLockCar**，打开终端执行：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe verify_models.py
.\.venv\Scripts\python.exe camera_check.py --camera 0
.\.venv\Scripts\python.exe main.py --camera 0
```

摄像头 0 无法打开就改成 1。不要同时运行检测程序和摄像头验证程序。
Ctrl+Shift+P → Python: Select Interpreter → 选择此工程 `.venv\Scripts\python.exe`。
之后可在“运行和调试”中选预设按 F5。
不使用 `Activate.ps1`，避免 PowerShell 脚本执行策略问题。

## 登记与锁定

1. 一次只让一个人正脸入镜，脸框至少约 70×70 像素。
2. 点击画面使窗口获得焦点，按 **N**，稍微转动头部，采集 8 个特征样本。
3. 首次保存为 ID 1，下一人登记为 ID 2，以此类推。ID 保存于 `data/gallery.json`。
4. 登记后自动选择该 ID；等待连续 3 帧识别通过，显示 **LOCKED**。
5. 多人进入时，鼠标点击已登记的人脸框锁定；1～9 键也可切换到对应 ID。
6. **U** 解除锁定；**Q** 或 Esc 退出。未登记的人显示 Unknown，不自动成为目标。
7. 再次登记已认出的 ID 会补充该 ID 的样本；若误显示 Unknown，不要盲目重复登记，以免同一人生成新编号。

锁定是“固定目标编号 + 连续身份验证”，不会因目标消失而自动选择最大脸或最近的人。
短时丢失即输出 valid=0；同 ID 重新出现后需连续 3 帧确认。
没有启用活体检测；照片也可能被识别。遮挡、背面、快速移动与脸小会失效。
这是实验原型，不承诺所有情况下绝不换 ID。

## 数据输出

屏幕坐标原点为左上角。cx、cy、bw、bh、area 为 0～1000 千分数。
ex、ey 约 -1000～1000，ex<0 左，ex>0 右；ey>0 下。
direction=-1/0/1 为左/居中/右，必须先检查 valid。
face area 不是米数，也不能凭它保证跟随距离。

串口 115200 8N1，10 Hz，ASCII，以 LF 换行结束：

```text
@F1,seq,valid,target_id,cx,cy,ex,ey,bw,bh,area,det,sim,direction,age_ms*XX\n
```

`XX` 为从 `F` 到 `age_ms` 最后一位之间所有 ASCII 字节异或，含逗号，不含 @、*、换行。
seq 每发送一包加 1；sim 为余弦相似度×1000，det 为人脸检测分数×1000。
age_ms 为主机收到当前图像到发送的时间；并非传感器真实曝光延迟。
数据超过默认 400 ms 自动 valid=0、位置清零；target_id 继续保留。
10 Hz 是发送频率，不代表算法每秒识别 10 帧。
日志每次运行保存在 `logs/run_*.csv`，无原始人脸照片；gallery 保存人脸特征。

```powershell
.\.venv\Scripts\python.exe main.py --camera 0 --port COM3
```

电控接收端必须拼接完整行、核对版本/字段数/校验和/字段范围；valid=0 时停止跟随。
超过 500 ms 没有合法新数据时停止跟随（起步调试值，最终由电控按车速调整）。
解析后 ex 可作为转向闭环误差输入，方向正负号和 PID 参数由电控实车验证。
程序不输出电机 PWM，不控制电机，不提供可靠测距。

## 香橙派命令

详见单独 Word 文档。需 Zero 3W **A733** 专用 Ubuntu/Debian arm64 系统，不能刷旧 Zero 3 镜像。
在板子上重新创建环境，不能复制 Windows 的 .venv。

```bash
cd ~/FaceLockCar
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python verify_models.py
.venv/bin/python camera_check.py --camera 0
.venv/bin/python main.py --camera 0
# Registered ID 1, running without a display:
.venv/bin/python main.py --camera 0 --no-show --target 1 --port /dev/ttyUSB0
```

板子的 Python 需为 3.10～3.12；已有版本不兼容时按 Word 排错，不要直接在车上源码编译。
初版采用 CPU；NPU 不会自动加速这些 OpenCV 接口。
多人越多，SFace 计算次数越多；最多处理面积最大的 5 张脸。
若慢到 age_ms 超时，默认不输出有效控制位置，应先测性能和减少人数。

## 验证

```bash
python -m unittest discover -s tests -v
python verify_models.py
```

首轮实机测试：分别登记两人，单人离开再进入、两人交换左右、目标被遮挡、拔摄像头、拔串口。
验收看是否保持目标编号以及异常时 valid=0，先架空车轮联调。

## 文件

- `main.py`：摄像头、界面、登记、锁定、串口和日志。
- `vision.py`：YuNet + SFace 模型推理。
- `core.py`：编号库、连续确认、坐标和带校验的数据包。
- `camera_check.py`：插入摄像头后先运行。
- `serial_monitor.py`：在接收端电脑解析协议的参考程序。
- `models/`：已校验 SHA256 的原始模型及各自许可证。
- `data/gallery.json`：首次登记后生成；想保留编号要随工程迁移。
- `logs/`：坐标数据，给电控做曲线和控制参数分析。

## 来源

OpenCV 官方人脸教程：https://docs.opencv.org/4.x/d0/dd4/tutorial_dnn_face.html
YuNet：https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet
SFace：https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface
模型来源提交：48b10fa505aeb51fbd127fc60a5c660040e823b7。
YuNet 使用 2023mar OpenCV 4.x 模型；SFace 使用 2021dec ONNX。
YuNet MIT 许可证与 SFace Apache 2.0 许可证保留在 models 中。
相似度默认 0.45 和身份分差 0.05 是原型参数，需要用登记者实测调整；模型公开基准不是你摄像头上的准确率保证。
