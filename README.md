

这是本项目当前唯一推荐的迁移与启动目录。以后启动香橙派程序、打开 STM32 Keil 工程、烧录固件和查阅排错步骤，都从本目录取文件。

## 目录

* `01_OrangePi/FaceLockCar_NPU_20261026/`：香橙派人体检测、跟踪、中文 HUD、测距显示和 S1 舵机通信程序。
* `01_OrangePi/models_npu/`：板端 NPU 模型存放位置。当前电脑未能连接香橙派，`yolov5.nb` 需要按目录内说明从板端补入。
* `02_STM32/STM32F103_SG90_VEHICLE_HOLD3S/`：完整 Keil 工程、源码、引脚配置文件和烧录产物。
* `03_接线参考/`：单电机验证版、四电机实战版及逐线核对图。
* `04_测试记录/`：已完成的组件和跟踪验收记录。
* `05_校验/`：归档后生成的 SHA256 校验文件。

## 最常用文件

香橙派程序入口：`01_OrangePi/FaceLockCar_NPU_20261026/body_main.py`

香橙派启动脚本：`01_OrangePi/FaceLockCar_NPU_20261026/run_balanced.sh`

香橙派排错启动脚本：`01_OrangePi/FaceLockCar_NPU_20261026/run_debug.sh`

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


## 文档入口

1. 先读 `启动与排错指南.md`。
2. 需要烧录或换板时读 `STM32烧录与跨平台迁移指南.md`。
3. 需要确认版本和文件来源时读 `工程版本说明.md`。
4. 最后核对 `文件清单_SHA256.txt`。

## 当前边界

NPU 模型依赖 Orange Pi A733 的 VIPLite、`/dev/vipcore` 和匹配的 `yolov5.nb`。这些系统组件不能用 Windows 文件代替。STM32 使用 ST-Link 烧录；USB-TTL 只用于运行时 USART1 通信，不能拿 TTL 当作烧录入口。
