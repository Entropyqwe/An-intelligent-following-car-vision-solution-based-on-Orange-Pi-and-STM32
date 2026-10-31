# 暗画面、噪点与真实720p采集

## 当前状态

2026-10-26恢复SSH后已同步720p参数和画质恢复脚本，板上31项测试通过，真实1280×720原图和遥测窗口均已验证。相机与窗口不再是640×480简单放大。板端图库和转向配置保留。

恢复gain=4、brightness=128、backlight_compensation=0、auto_exposure=3、exposure_dynamic_framerate=1后，当前墙面场景的720p原图均值约162/255，画面亮度恢复。此时自动曝光下480p与720p均实测约8.33FPS，显示当前相机曝光/输出速度限制。不能把画面变亮说成24FPS也已达成。仍有细粒噪点，不宣称已完全消除。

手动曝光测试得到更高采集率，但部分画面严重过曝，均值约253/255，**测试方案已撤回**，结束后恢复自动曝光；未把不合格图像当成优化结果。完整UI实测数据保存在板端logs/hd_quality_40s.json，截图/采集数据保存在logs/quality_1280x720.jpg、logs/quality_capture_report.json。

此前相机查询确认支持 MJPG 1280×720、640×480（驱动报告60FPS），YUYV 1280×720只报告10FPS。提升分辨率应使用MJPG，并实测帧率，不能把驱动报告值当作真实帧率。

## 曝光调整的更正

上一轮调试曾将gain从4提高到8、brightness从128提高到160、backlight_compensation从0提高到2，并关闭exposure_dynamic_framerate。画面效果没有充分验证，不能将这组值作为推荐默认值。先恢复本相机查询到的原始图像参数和自动曝光动态帧率，再比较固定场景的画质。

新脚本保存修改前状态，可恢复。先退出视觉程序，避免重复打开摄像头；新版文件已同步到板端：

```bash
cd ~/FaceLockCar_NPU_20261026
.venv/bin/python tools/camera_quality.py show
.venv/bin/python tools/camera_quality.py defaults
# 如需撤销本脚本的调整
# .venv/bin/python tools/camera_quality.py restore
```

`configure_board.py apply`也已改为默认允许动态曝光帧率。只有显式传`--fixed-frame-rate`才会关闭它。在暗处优先核验人脸可见程度与运动拖影，而非只看帧率。

## 720p先预览

快捷启动：`bash run_hd_preview.sh`。它会恢复已核对的相机默认画质，并启用720p相机及NPU预览；它不启用转向与串口。

```bash
cd ~/FaceLockCar_NPU_20261026
DISPLAY=:0 .venv/bin/python main.py --body --person-backend npu \
  --width 1280 --height 720 --window-width 980 --lock-mode auto --quiet-packets
```

这是摄像头实际采集1280×720。窗口为适配1024×768桌面可缩小显示，但原始处理帧保持720p。要看到像素更多的显示画面，需要桌面/VNC也支持更大的分辨率；仅放大640×480窗口不会增加原图细节。模型输入仍为640×640，人脸检测器默认224×224，不因提高采集尺寸自动变成720p推理。720p的采集、解码和绘制开销需重新测量，24FPS尚未保证。

**暂不启用转向。** 原相机HFOV来自640×480；1280×720改变画面比例，可能改变裁剪/视场。不能凭新宽度沿用原视场角并声称转向角度正确。720p联动前先核验视场或标定；提供该模式实测`--hfov`或匹配相机内参后方可启用`--steering`。原STM32、S1格式、心跳、PA9/PA10和PWM代码保持不变。

仍要直接使用此前标定与舵机链时，先保持640×480，用原命令并在恢复曝光后验证。不要将720p预览命令误认为完整舵机启动命令。
