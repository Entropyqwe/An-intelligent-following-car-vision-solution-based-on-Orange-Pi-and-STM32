# FaceLockCar 人体检测扩展部署评估

评估日期：2026 年 10 月 23 日。目标设备：用户确认的 Orange Pi Zero 3W A733；内存容量、系统版本、摄像头驱动及板上实测数据尚未提供。

## 修改前结论

**可以按 ARM64 Linux CPU 路线实现并准备部署验证；目前不能认定已经达到香橙派实时跟随要求。** 本次先采用 OpenCV Zoo 的 NanoDet Plus 人体检测，保留 YuNet 与 SFace。不引入 PyTorch，不依赖 NPU，不以电脑速度推算板子帧率。所有模型都由现有 OpenCV DNN 在 CPU 上运行，额外人体模型文件为 3,800,954 字节。模型文件大小不等于推理内存占用。

用户要求为：正脸确认指定身份，转身后连续跟随同一个人；遮挡或混淆时停止并重新认脸。实现采用保守关联，不把任意 person 检测当作身份识别，也不承诺纯背影重新入镜时能认出特定身份。

| 项目 | 修改前判断 | 板上验收条件 |
| --- | --- | --- |
| 模型和运行时 | 官方 ONNX 加现有 OpenCV 4.10 CPU，可避免新增深度学习框架 | ARM64 环境成功安装固定版本依赖，全部模型通过哈希校验 |
| 摄像头 | 继续使用 Linux V4L2 | 单独运行 camera_check.py，能够持续获得新帧 |
| 吞吐和延迟 | 有望用于低速原型，尚无 A733 实测依据 | 真实相机与实际人数下测量总耗时、端到端帧龄及 P95；新帧应明显快于 400 ms 超时门限 |
| 内存和热稳定性 | 尚未测得 | 持续运行至少 10 分钟，无内存不足或明显降频，给系统和串口保留余量 |
| 背影身份延续 | 只能从已认脸并绑定的人体连续延续 | 转身、遮挡、交叉、离开重入分别验证；失配必须停止并重认脸 |
| NPU | 不作为本次部署前提 | 未来单独确认 SDK、驱动、算子支持和量化后准确率，不可直接套用 RKNN |

本次采用同步人体检测，每个处理帧都重新检测人体。人脸识别可在人体连续锁定时每三帧执行一次，减轻 SFace 负担；确认和丢失重认阶段每帧执行。独立 10 Hz 数据发送线程不是 10 FPS 视觉推理。

## 为什么暂不替换为 YOLO

NanoDet 的优势是沿用现有 OpenCV、固定官方模型、额外模型小、部署改动少。这是本项目的工程选择，**不代表已经证明 NanoDet 比所有 YOLO 更快或更准确**。该模型仍计算 COCO 多类别，只在后处理中保留 person；过滤类别不会把神经网络计算量缩减到单类别模型。

YOLO 可以作为人体检测器，也适合后续扩展物体类别。标准 person 检测不提供已登记人脸身份；即使启用跟踪，track ID 也是一段视频内的轨迹编号，不等于持久化人员编号。仍需保留人脸核验及丢失重认策略。Ultralytics 官方 ARM 部署指南推荐评估 NCNN 等导出格式；其 Raspberry Pi 5 的数据不能视为 Zero 3W 的测试结果。

若本次板上实测不足，优先在相同摄像头、人数、输入尺寸、延迟统计和召回要求下比较 NanoDet OpenCV 与 YOLO nano 的 NCNN 导出。先在电脑导出，再复制模型和推理所需依赖到板上。只有 CPU 路线确实不满足需求，再单独开展 A733 NPU 适配。

## 依据与限制

- OpenCV 官方 YuNet 与 SFace 教程：<https://docs.opencv.org/4.x/d0/dd4/tutorial_dnn_face.html>。
- NanoDet 官方固定源码与 Apache 2.0 许可证：<https://github.com/opencv/opencv_zoo/tree/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/object_detection_nanodet>。本次模型使用此提交的 2022nov FP32 版本。
- Ultralytics ARM CPU 部署与基准：<https://docs.ultralytics.com/guides/raspberry-pi/>。
- Ultralytics 跟踪与 ReID：<https://docs.ultralytics.com/modes/track/>。
- VeriSilicon TIM-VX 的部署依赖说明：<https://github.com/VeriSilicon/TIM-VX>。它不证明当前板上已经安装可用的 NPU 环境。

官方板卡详情页在本次检索中未能正常读取；本评估不据此猜测内存、NPU 驱动可用性或实时帧率。最终可部署性需在用户这块板上执行随工程提供的 benchmark_vision.py 并完成现场场景测试。
