# Windows 视觉程序启动指南


记得改文件名！记得改文件名！记得改文件名！

## 1. 最快启动：双击

在文件资源管理器中打开：

```text
D:\新建文件夹 (7)\FaceLockCar_Windows
```

双击 `run_windows.cmd` 即可。

如果启动失败，保留报错窗口；不要反复安装，先按第 7 节排查。

## 2. 使用 CMD 启动（推荐）

按 `Win + R`，输入 `cmd`，回车。依次执行：

```cmd
cd /d "D:\新建文件夹 (7)\FaceLockCar_Windows"
run_windows.cmd
```

执行第一行后，命令行提示符应变成：

```text
D:\新建文件夹 (7)\FaceLockCar_Windows>
```

**CMD 从 C 盘进入 D 盘时必须使用 `cd /d`。** 单独使用 `cd` 不会切换当前盘符。

也可以跳过启动脚本，直接调用项目的 Python：

```cmd
cd /d "D:\新建文件夹 (7)\FaceLockCar_Windows"
".venv\Scripts\python.exe" -X utf8 -u body_main.py --person-backend cpu
```

CMD 中不要在 Python 命令前添加 `&`。

## 3. 使用 PowerShell 启动

如果打开的是 PowerShell，执行：

```powershell
Set-Location "D:\新建文件夹 (7)\FaceLockCar_Windows"
.\run_windows.cmd
```

直接调用 Python 的 PowerShell 写法为：

```powershell
Set-Location "D:\新建文件夹 (7)\FaceLockCar_Windows"
& ".\.venv\Scripts\python.exe" -X utf8 -u body_main.py --person-backend cpu
```

PowerShell 执行带引号的程序路径时使用 `&`。这与 CMD 的写法不同。

## 4. 启动后的操作

| 操作          | 作用              |
| ----------- | --------------- |
| `Q` 或 `Esc` | 退出程序            |
| `A`         | 切换自动 / 手动选择     |
| `U`         | 解除目标锁定，同时暂停自动选择 |
| 鼠标点击人体框     | 手动选择目标          |
| 数字键 `1`～`9` | 选择对应的可选目标编号     |

按键前先点击预览窗口，让窗口获得键盘焦点。

默认自动模式下，只有一个人体并连续确认后，会选择跟随槽位 `01`。出现多人时，单人槽位跟随会暂停，可点击人体框选择目标。槽位编号用于当前跟随，不代表永久身份；重新入镜后的 `01` 不保证是原来同一个人。

日常入口 `body_main.py` 不要求人脸登记。窗口标题已改成英文 `Body Tracking / Steering Guidance`；窗口内部使用中文。

## 5. 常用启动参数

以下命令在 CMD 中执行，先进入项目目录：

```cmd
cd /d "D:\新建文件夹 (7)\FaceLockCar_Windows"
```

### 更换摄像头

默认摄像头编号为 `0`。打不开时，可以尝试：

```cmd
run_windows.cmd --camera 1
```

如果电脑还有其他摄像头，可以继续尝试 `--camera 2`。

### 更换 Windows 摄像头接口

默认使用 DirectShow。打开失败或没有图像时，可以尝试 MSMF：

```cmd
run_windows.cmd --camera-backend msmf
```

参数可以组合使用：

```cmd
run_windows.cmd --camera 1 --camera-backend msmf
```

### 手动选择目标

```cmd
run_windows.cmd --lock-mode manual
```

启动后点击人体框选择目标。

### 调整分辨率

默认请求摄像头输出 `640×480`。摄像头支持时，可以使用：

```cmd
run_windows.cmd --width 1280 --height 720
```

摄像头必须支持请求的分辨率。720p 串口转向还需要适合该模式的视场角或相机标定参数，不能直接沿用不同镜头、不同画面比例的标定。

### 保存运行指标

运行 60 秒后退出，并保存处理帧率等指标：

```cmd
run_windows.cmd --max-seconds 60 --metrics-json logs\windows_60s.json
```

如果不需要预览窗口：

```cmd
run_windows.cmd --no-show --max-seconds 60 --metrics-json logs\windows_headless_60s.json
```

指标保存在项目目录下的 `logs` 文件夹中。Windows 测量结果反映本机运行情况，不代表香橙派 NPU 的性能。

## 6. 连接 STM32（可选）

不填写 `--port` 时，程序不会打开串口。

先接好 USB-TTL，在 CMD 中查看端口列表：

```cmd
cd /d "D:\新建文件夹 (7)\FaceLockCar_Windows"
".venv\Scripts\python.exe" -m serial.tools.list_ports
```

假设实际端口为 `COM5`：

```cmd
run_windows.cmd --port COM5
```

将 `COM5` 替换为设备实际端口号。通信沿用原项目的 S1 协议，串口参数为 `115200、8N1`。用 USB-TTL 时，TX 接 STM32 PA10、RX 接 PA9、GND 共地，TTL 信号电平使用 3.3V；沿用原项目已验证的独立供电接法。

首次联调先架空车轮，确认舵机方向和失去目标后的行为。换摄像头后，需要核对 `steering_config.json` 中的视场角或相机标定。窗口里的偏角是目标视线偏角；超声波距离来自 STM32 回传，不是视觉估算的目标距离。

## 7. 常见问题

| 现象                                  | 原因与处理                                                                       |
| ----------------------------------- | --------------------------------------------------------------------------- |
| `run_windows.cmd` 不是内部或外部命令         | 当前目录不对。在 CMD 中先执行 `cd /d "D:\新建文件夹 (7)\FaceLockCar_Windows"`。               |
| `此时不应有 &`                           | 在 CMD 中粘贴了 PowerShell 命令。移除 Python 路径前的 `&`。                                |
| 找不到 `.venv\Scripts\python.exe`      | 目录不对，或当前副本尚未安装环境。先确认目录；当前 D 盘副本已安装。                                         |
| `setup_windows.ps1` 不存在             | 从错误的目录执行了相对路径。先进入包含该脚本的项目目录。                                                |
| `py` 无法识别                           | 没有 Python Launcher。当前电脑日常启动不需要它；重建环境时通过 `-PythonExe` 指定真实解释器路径。             |
| 摄像头打不开或没有图像                         | 关闭占用相机的程序，确认 Windows 允许桌面应用访问摄像头，尝试 `--camera 1` 或 `--camera-backend msmf`。 |
| `Camera returned ... requested ...` | 摄像头不支持请求的分辨率。先恢复 `640×480`。                                                 |
| 窗口标题乱码                              | 关闭旧程序，再启动修改后的 D 盘版本；标题已改成英文。                                                |
| 检测到人但没锁定                            | 等待连续确认；检查是否多人、目标是否过小或位于画面边缘，也可点击人体框手动选择。                                    |
| 串口无法打开                              | 核对实际 COM 号、USB-TTL 驱动，并关闭占用该端口的串口助手或其他程序。                                   |

如果仍然失败，保留从启动命令到最后一行的完整报错，便于判断是在解释器、模型、摄像头还是串口阶段失败。

## 8. 重建环境（只在需要时执行）

当前这台电脑不需要重复安装。本节用于换电脑，或重新解压后没有 `.venv` 的情况。

安装 64 位 Python 3.12，并包含 Python Launcher 后，在 CMD 中执行：

```cmd
cd /d "D:\新建文件夹 (7)\FaceLockCar_Windows"
powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
```

没有 `py` 启动器时，指定真实 Python 路径。下面路径仅为示例，必须替换为本机实际安装位置：

```cmd
powershell -ExecutionPolicy Bypass -File "D:\新建文件夹 (7)\FaceLockCar_Windows\setup_windows.ps1" -PythonExe "C:\Python312\python.exe"
```

安装脚本会创建环境、安装依赖并检查随附的模型。安装成功后再执行 `run_windows.cmd`。
