

这是本项目当前唯一推荐的迁移与启动目录。以后启动香橙派程序、打开 STM32 Keil 工程、烧录固件和查阅排错步骤，都从本目录取文件。

## 目录

* `01_OrangePi/FaceLockCar_NPU_20261026/`：香橙派人体检测、跟踪、中文 HUD、测距显示和 S1 舵机通信程序。
* `01_OrangePi/models_npu/`：板端 NPU 模型存放位置。详情课参考官方手册
* `02_STM32/STM32F103_SG90_VEHICLE_HOLD3S/`：完整 Keil 工程、源码、引脚配置文件和烧录产物。
* `03_接线参考/`：单电机验证版、四电机实战版及逐线核对图。


## 最常用文件

香橙派程序入口：`01_OrangePi/FaceLockCar_NPU_20261026/body_main.py`

香橙派启动脚本：`01_OrangePi/FaceLockCar_NPU_20261026/run_balanced.sh`

Keil 工程：`02_STM32/STM32F103_SG90_VEHICLE_HOLD3S/Project_VEHICLE.uvprojx`

STM32 烧录文件：`02_STM32/STM32F103_SG90_VEHICLE_HOLD3S/Objects/FaceLock_SG90.hex`

STM32 二进制文件：`02_STM32/STM32F103_SG90_VEHICLE_HOLD3S/Objects/FaceLock_SG90.bin`

#环境依赖
 板卡系统  本地镜像 `Orangepizero3w_1.0.2_ubuntu_jammy_desktop_xfce_linux5.15.147`，ARM64 |
Python  工程约定3.10～3.12；附带离线 NumPy wheel 仅适合CPython3.10 ARM64 |
Python包 `numpy==1.26.4`、`opencv-python==4.10.0.84`、`pyserial==3.5` |
MCU STM32F103C8T6，固件按8MHz HSE、72MHz主时钟配置 |
 编译  已有 ARM Compiler5 构建脚本与 Keil 工程；直接烧录已有HEX不要求重新编译 |

GUI和headless OpenCV二选一。登记需要图形界面；`requirements-headless.txt` 用于已登记后的无界面部署。不要把 Windows `.venv` 复制到 Linux。



## 当前边界

NPU 模型依赖 Orange Pi A733 的 VIPLite、`/dev/vipcore` 和匹配的 `yolov5.nb`。这些系统组件不能用 Windows 文件代替。STM32 使用 ST-Link 烧录；USB-TTL 只用于运行时 USART1 通信，不能拿 TTL 当作烧录入口。


##启动与排错指南

## 一、香橙派启动

### 1. 进入稳定版目录

    cd ~/FaceLockCar_NPU_20261026

如果板上目录名称不同，请把本目录中的 `01_OrangePi/FaceLockCar_NPU_20261026` 复制为该名称；

### 2. 启动前检查

    ls -l /dev/video*
    ls -l /dev/serial/by-id/
    fuser /dev/video0

确认摄像头存在、CH340/CH341 存在，并且没有另一个程序占用 `/dev/video0`。

### 3. 普通启动

    bash run_balanced.sh

该入口使用彩色 640×480、目标采集 30 FPS、人体 NPU 后端、自动单人锁定和原 S1 舵机协议。当前完整系统帧率必须以界面或日志实际测量为准，不能把 NPU 单项速度当作整机 FPS。

### 4. 带串口的调试启动

    bash run_debug.sh

调试日志固定写入：

    ~/FaceLockCar_NPU_20261026/logs/last_run.log

### 5. 只测试舵机链路

    .venv/bin/python tools/servo_link_test.py --port /dev/ttyUSB0 --pulse 1500 --seconds 3
    .venv/bin/python tools/servo_link_test.py --port /dev/ttyUSB0 --pulse 1450 --seconds 3
    .venv/bin/python tools/servo_link_test.py --port /dev/ttyUSB0 --pulse 1550 --seconds 3

测试前车轮悬空，确认舵机不会顶死。TTL 的 TX 接 STM32 PA10，RX 接 PA9，GND 共地，TTL VCC 不接；串口为 115200 8N1。

### 6. 只读测距遥测

    .venv/bin/python tools/distance_monitor.py --port /dev/ttyUSB0 --seconds 5

看到连续 `#D1` 且 `valid=1`，才说明 STM32 已经把有效 HC-SR04 距离送到香橙派。测距失败时先检查 PB6 TRIG、PB7 ECHO、分压、VCC、GND 和超声波前方是否无遮挡。

## 二、STM32 烧录

1. 关闭香橙派视觉程序，避免运行时串口干扰。
2. 用 ST-Link 接 STM32 的 SWDIO、SWCLK、GND、3.3V/目标电压；NRST 可不接，但接上更利于复位和连接。
3. 用 Keil 打开 `02_STM32/STM32F103_SG90_VEHICLE_HOLD3S/Project_VEHICLE.uvprojx`。
4. 也可以直接用 ST-Link Utility、STM32CubeProgrammer 或 Keil 烧录：

    02_STM32/STM32F103_SG90_VEHICLE_HOLD3S/Objects/FaceLock_SG90.hex

5. `.bin` 用于支持二进制烧录的软件；`.hex` 通常更方便直接烧录。
6. SHA256 文件只用于校验，不需要烧录进 STM32。
7. 烧录完成后断开 ST-Link 的调试线（至少不要让它继续给舵机供电），再接 USB-TTL 做运行时通信测试。

## 三、故障定位顺序

### 没有窗口或程序立即退出

    cat logs/last_run.log

* `Camera is in use`：执行 `pkill -f body_main.py`，关闭旧预览后重试。
* `Camera failed`、`VIDIOC_REQBUFS errno=19`：USB 摄像头或 USB Hub 掉线。重新插拔摄像头，换数据线和 USB 口，保证 Hub 有稳定供电。
* `BodyHUD.render() got an unexpected keyword argument`：源码文件版本混用。必须把本归档中的整个 `FaceLockCar_NPU_20261026` 目录整体覆盖到板端，不能只替换单个 `main.py`。
* `No module named cv2/serial`：在本目录执行 `install_orangepi.sh`，再使用 `.venv/bin/python` 启动。

### 找不到摄像头

    lsusb
    v4l2-ctl --list-devices

摄像头和 CH340 不要同时依赖一个供电不足的 Hub。香橙派使用稳定 5V/3A；不要用香橙派 USB 给舵机或电机供电。

### 找不到串口或舵机没有反应

    ls -l /dev/serial/by-id/
    dmesg | tail -n 50

* CH340/CH341 必须出现在 USB 列表中。
* 串口 TX/RX 必须交叉连接：TTL TX→PA10，TTL RX→PA9。
* 必须共地；TTL VCC 不接。
* 确认烧录的是本归档的 `FaceLock_SG90.hex`，不是旧版同名文件。
* `valid=0` 时舵机回中属于保护行为；人在中心附近时也可能约为 1500 微秒。

### 没有 `#D1` 或距离无效

检查 STM32 是否为本归档车辆版工程，HC-SR04 是否接 PB6/PB7，ECHO 是否经过分压进入 3.3V GPIO。只有 `#A1` 没有 `#D1`，通常表示舵机协议链路正常但车辆版测距固件、接线或传感器链路仍有问题。

### USB 摄像头和 CH340 同时消失

内核日志出现 `USB disconnect`、`uvcvideo ... -19` 或 `ch341-uart disconnected` 时，先处理硬件供电和接触，不要先改算法。软件包含重连逻辑，但不能修复掉电、接触不良或 Hub 过流。

## 四、日志和回退

运行 CSV 通常在 `logs/body_*.csv`。查看 `valid`、`bearing_mdeg`、`servo_us`、`age_ms`：

* 人在中心：偏角接近 0，舵机约 1500 微秒。
* 目标有效且偏左/偏右：偏角变号，舵机脉宽向对应方向变化。
* 丢失目标：停止有效转向并回中。

不要同时启动旧版和本稳定版；两者会争抢摄像头和串口。需要回退时，停止当前程序，使用旧目录运行原命令即可，STM32 不需要重复烧录

在香橙派中启动视觉程序：cd ~/FaceLockCar_NPU_20261026
bash run_balanced.sh
联动程序：cd ~/FaceLockCar_NPU_20261026
bash run_debug.sh
STM32烧录使用：E:\FaceLockCar_CURRENT_STABLE\02_STM32\STM32F103_SG90_VEHICLE_HOLD3S\Objects\FaceLock_SG90.hex
