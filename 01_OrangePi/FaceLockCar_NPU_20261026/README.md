# Zero 3W A733：NPU 人像跟踪升级版

> 最新最低要求已改为彩色640×480、20FPS。启动用 `bash run_balanced.sh`，检测到USB-TTL时自动接入原S1串口。65秒完整实测约10.92FPS，**尚未通过20FPS与稳定跟踪验收**；NPU计算对照约23.21FPS不代表实机帧率。详见 [480p输出规格与验收报告](docs/480P_20FPS验收报告.md)。下方24FPS为之前目标和历史说明。

> 画质更正与720p新增选项见 [摄像头画质说明](docs/CAMERA_QUALITY.md)。720p及恢复画质代码已在2026-10-26恢复SSH后同步，板上31项测试通过。`bash run_hd_preview.sh`启用真实720p预览，当前自动曝光场景约8.34FPS，不能当作24FPS验收通过。原480p转向入口仍为`run_npu.sh`。

## 当前状态与入口

本目录是独立优化副本，原 `FaceLockCar`、`STM32F103_SG90` 目录保留。人体检测改用本板系统预装的 YOLOv5 NBG，通过 VIPLite 真实调用 A733 NPU；人脸检测和身份识别继续使用原 YuNet + SFace，CPU 与 NPU 对同一帧并行处理。

当前验收目标为完整流程稳定达到 24FPS，30FPS 为进一步优化目标。**截至最后一次可读日志，尚未完成“稳定锁定 + 完整 UI + 串口”的 24FPS 验收。** 不能用人体检测单项速度、相机帧率、无人画面帧率代替该验收。详细数据见 [验证报告](docs/NPU_VALIDATION.md)。

板上已部署目录：`/home/orangepi/FaceLockCar_NPU_20261026`。电脑源码目录：`E:\FaceLockCar_Project_20261025\src\FaceLockCar_Steering_Integration\FaceLockCar_NPU_20261026`。

**板上版本说明：**2026-10-26恢复SSH后已同步AUTO/MANUAL标签、JSON测速、画质设置、720p选项和测试，保留了板端图库和转向配置。板端真实NPU已运行，31项测试通过，完整锁定与24FPS组合验收仍未完成。

## 1. 环境与模型

实际检查到的环境：Orange Pi Zero3W / A733、4GB、Ubuntu 22.04、Linux 5.15.147-sun60iw2、Python 3.10.12、OpenCV 4.10.0、NumPy 1.26.4、pyserial 3.5。

NPU 所需文件来自这台板子的现有系统：

| 类型 | 路径 |
| --- | --- |
| 设备与内核模块 | `/dev/vipcore`，`vipcore` |
| 实际 SDK 头文件 | `/usr/include/vip_lite.h`、`/usr/include/vip_lite_common.h` |
| 运行库 | `/lib/libVIPhal.so`、`/lib/libNBGlinker.so` |
| 人体检测模型 | `/opt/yolov5/model/yolov5.nb` |
| 应用桥接库 | 本目录 `native/libfacelock_vip.so`，在板上编译 |

本次检查的 NBG SHA256：`6c6cb261f41fcc774134b90d0e1f2a17675cd6da1e8f1c6d2b61460cfd584158`。

该适配器仅支持已核对的模型契约：RGB uint8 CHW `(1,3,640,640)`，量化 scale=1/255、zero_point=0，三个 FP32 原始输出头 `(1,3,80,80,85)`、`(1,3,40,40,85)`、`(1,3,20,20,85)`。不能把任意 YOLO ONNX 或其他 `.nb` 直接替换进去。初始化会检查形状和输入量化参数；模型语义、anchors、类别顺序也必须匹配。

新板若缺少 SDK、内核驱动或模型，应按该板官方 Linux 手册安装匹配版本。本项目不捆绑替换内核驱动，不使用其他板 Android 环境的猜测头文件。`install_npu.sh` 只检查现有环境和编译应用桥接库，不下载系统 SDK。

这台板部署时复用了旧项目 `.venv` 与 `models` 的符号链接；`data/gallery.json`、`steering_config.json` 是独立副本。删除旧目录前先处理这些依赖。迁移到新板时，可使用已有 `install_orangepi.sh` 创建独立虚拟环境和安装固定版本依赖，然后编译 NPU 桥接库。不要同时安装多种 OpenCV Python 分发包。

```bash
cd ~/FaceLockCar_NPU_20261026
bash install_npu.sh
.venv/bin/python verify_models.py
.venv/bin/python -m unittest discover -s tests -v
```

## 2. 启动与操作

先运行预览，检查识别、偏角和帧率：

```bash
cd ~/FaceLockCar_NPU_20261026
bash run_npu.sh
```

`run_npu.sh` 默认 NPU 人体检测、S1 转向计算、自动选择、2 个 OpenCV 线程。没有 `--port` 时只记录和预览，不打开串口。现场曾比较 2、8 线程，优劣随负载变化，8 线程并未保证更快，可用 `--threads 8` 自行复测。

| 操作 | 行为 |
| --- | --- |
| 启动默认 AUTO | 唯一已登记人脸与孤立人体明确对应时，自动选择 ID；随后仍需原跟踪器连续确认 |
| N | 仅一张足够大且清楚的人脸时，显式录入 8 个样本；不会自动登记陌生人 |
| 点击头框、1～9 | 手动选择已登记 ID |
| A | 自动/手动切换，保留当前选择 |
| U | 解除选择并暂停自动选择，防止立刻锁回 |
| Q / Esc | 退出；原发送逻辑会发送无效回中包 |

自动模式不会在多人候选中任意挑选，不会因当前目标丢失就切换到另一个 ID。目标转身后允许原人体连续关联；漏检、重叠、身份冲突、关联歧义时保持原停止逻辑。UNKNOWN 的含义是尚未通过身份匹配，并不代表人体检测失效。

只使用手动选择：

```bash
bash run_npu.sh --lock-mode manual
```

有明确已登记 ID 后无窗口运行：

```bash
.venv/bin/python main.py --body --steering --person-backend npu \
  --no-show --target 1 --quiet-packets
```

ID 1 必须真实存在于本板独立图库中。默认 `--face-size 224`；小脸或远距离漏检时可设 320，会增加 CPU 工作量。160 仅用于比较性能和召回，不能默认认为效果相同。`--face-every 3` 仅在成功锁定人体后生效，未锁定仍逐帧核验人脸。

## 3. 界面

摄像头区域不拉伸，保留头部框、人体角框；身份 ID 与相似度写在头框内部，不再绘制第三个标号框。中心只保留小准星，不绘制全高蓝线。右侧为深色遥测风格信息区，没有使用 SpaceX 标志。

FPS / PROCESSED 是真实处理帧率；CAM 是主机采集统计；FACE 是身份核验频率。FACE/BODY ms 是处理耗时，二者并行，不能简单相加视作总耗时。AGE 是主机接收到图像后的帧龄，不是摄像头曝光到舵机的完整端到端延迟。

水平偏角来自原 `Steering.bearing`，单位度，使用人体框中心和原相机参数。它是目标视线偏角，不是测得的车轮转角。串口区显示发送状态，`#A1` 也不是舵机轴位置传感器反馈。

跳帧期间的头框可使用最多 0.25 秒光流做显示补偿。补偿结果不进入控制，不刷新身份确认时间，也不产生新的有效人体观察。

## 4. 板端配置与可逆调整

检查当前设置：

```bash
.venv/bin/python tools/check_npu.py
.venv/bin/python tools/configure_board.py show
```

现场检查发现本相机 `exposure_dynamic_framerate=1`。已临时设为 0，以避免曝光策略主动降低帧率；仍需保证照明。V4L2 的控件名称是本次相机返回的名称，其他相机若不支持，脚本将报错，不猜测控件。

本次调试前原值：相机动态帧率 1，CPU policy0、policy6 governor 均为 `ondemand`。现场临时改为动态帧率 0、CPU `performance`，没有安装永久开机服务。NPU 原本已经是 performance / 1008000000Hz，没有超频。

以后复现时可先保存并应用设置：

```bash
# 只调整相机；先保存原值到 logs/board_settings_before.json
.venv/bin/python tools/configure_board.py apply
# 可选 CPU 性能模式；增加功耗，需观察散热，未证明必然改善 SFace 耗时
sudo .venv/bin/python tools/configure_board.py apply --cpu-performance
# 恢复脚本保存的原值
sudo .venv/bin/python tools/configure_board.py restore
```

本次临时调整发生于上述通用脚本创建之前，原状态另保存在板端 `logs/camera_control_before.txt`、`logs/cpu_governors_before.json`。如果通用脚本尚未保存本次最初状态，可按已记录原值回退：

```bash
v4l2-ctl -d /dev/video0 --set-ctrl=exposure_dynamic_framerate=1
printf ondemand | sudo tee /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
printf ondemand | sudo tee /sys/devices/system/cpu/cpufreq/policy6/scaling_governor
```

## 5. 完整流程测速

确保没有另一个程序占用相机，人物正常入镜并完成登记/锁定。以下命令**没有串口**：

```bash
cd ~/FaceLockCar_NPU_20261026
bash run_npu.sh --max-seconds 60 --metrics-json logs/full_pipeline_60s.json
cat logs/full_pipeline_60s.json
```

比较时记录：光照、是否检测到脸、是否锁定、人物数量、UI 开关、分辨率、线程数、人脸尺寸、valid_percent。`steady_wall_fps` 扣除前 2 秒预热，按真实墙钟时间计算；持续有效跟踪时才可评价跟踪目标。图像重复刷新不增加算法处理帧数。

NPU 单项测速及紧凑/完整输出一致性：

```bash
.venv/bin/python tools/benchmark_npu.py --image logs/person_validation.jpg \
  --threshold 0.25 --require-person --frames 100
```

0.25 是一次正例对照的诊断阈值，主程序仍默认 0.45。正例图片必须包含人；空结果的一致不能代替正例验证。该脚本打印的是人体检测单项速度，不是完整系统 FPS。

## 6. STM32 与舵机兼容

本次保持原 `core.py`、`body_tracker.py`、`steering.py`、`Output` 类和全部 STM32 工程文件不变。人体检测器继续输出原格式 `[{box:(x,y,w,h), score:...}]`；新自动选择只选择 ID，实际锁定与连续关联仍由原跟踪器判断。

| 项目 | 原参数，保持不变 |
| --- | --- |
| UART | 115200，8N1，10Hz 独立心跳 |
| 数据包 | `@S1,seq,valid,target_id,bearing_mdeg,servo_us,age_ms,source*XX\n` |
| 校验 | 包体 ASCII 字节逐个 XOR |
| 有效观察最大年龄 | 400ms |
| MCU 无合法包超时 | 500ms 请求回中 |
| 舵机信号 | PA1 / TIM2_CH2，50Hz |
| USART1 | PA9=TX、PA10=RX |
| 中位 | 1500µs |
| 本板原应用脉宽范围 | 1300～1700µs |

USB-TTL TX 接 PA10，RX 接 PA9，GND 共地；TTL VCC 不接。TTL 信号电平应为 3.3V，舵机和 STM32 沿用此前验证的供电接法；本次没有验证 USB-TTL 可给舵机供电，也没有改供电设计。相机应固定朝前，舵机控制前轮。

接回硬件后先退出视觉程序，使用原测试工具验证 1500、1450、1550µs。每条命令结束时发送无效回中包：

```bash
.venv/bin/python tools/servo_link_test.py --port /dev/ttyUSB0 --pulse 1500 --seconds 3
.venv/bin/python tools/servo_link_test.py --port /dev/ttyUSB0 --pulse 1450 --seconds 3
.venv/bin/python tools/servo_link_test.py --port /dev/ttyUSB0 --pulse 1550 --seconds 3
```

确认没有机械卡滞且方向正确后，再启动视觉联动：

```bash
bash run_npu.sh --port /dev/ttyUSB0
```

查看运行 CSV 的 `valid`、`bearing_mdeg`、`servo_us`、`age_ms`；人在中心应接近 0° / 1500µs，左右偏移对应角度变号和脉宽两侧变化。失去有效目标应请求回中。实际方向由原配置 `servo_direction` 决定，勿仅凭画面镜像判断接线。当前仍待接回 USB-TTL/STM32 完成本次升级实物联调。

## 7. 结构与选型

| 文件 | 责任 |
| --- | --- |
| `main.py` | 同帧并行、交互、采集、原控制链调度 |
| `native/vip_bridge.c` | 使用板上 SDK 头文件的 C ABI，常驻网络、缓存同步、紧凑候选 |
| `vip_runtime.py` | ctypes 调用自有 ABI，线程归属检查 |
| `yolo_npu.py` | 官方系统模型预处理、YOLOv5 person 解码和 NMS |
| `inference_worker.py` | 一帧在途，NPU 构造/推理/销毁在同一线程 |
| `vision.py` | CPU YuNet/SFace，保留身份匹配语义 |
| `selection.py` | 自动 ID 选择；保留手动覆盖 |
| `hud.py`、`display_faces.py` | 遥测 UI、仅供显示的短时头框补偿 |
| `core.py`、`body_tracker.py`、`steering.py` | 原控制与协议实现，未修改 |

接入 YOLO 的理由是这块 A733 已有匹配的 640 输入 NBG，可以直接使用 NPU，避免继续用 CPU NanoDet 占用身份识别资源。4GB 内存不是本次主要耗时来源；更大的 YOLO 也不会自动更快。未盲目增加模型或承诺 YOLOv8/YOLO11 可直接运行。SFace 的 NPU 迁移需要匹配转换工具、校准、精度验证，本次没有伪称已迁移。

显式 CPU 对照：`--person-backend cpu`。NPU 缺失或执行失败时默认报错停止，不静默回退并继续显示 NPU 字样。

## 8. 回退

退出新程序后从原目录运行原启动命令即可，无需重刷 STM32：

```bash
cd ~/FaceLockCar_Steering_Integration/FaceLockCar
# 使用此前已经验证的原命令与参数
```

不要同时运行新旧程序争抢摄像头或串口。原项目和新副本的图库独立，新录入人员不会自动同步回原图库。源码可上传 GitHub，但排除 `.venv`、日志、图库、私人截图、板端密码、编译出来的 `.so`；系统模型和 SDK 应按其原许可与获取说明处理。
