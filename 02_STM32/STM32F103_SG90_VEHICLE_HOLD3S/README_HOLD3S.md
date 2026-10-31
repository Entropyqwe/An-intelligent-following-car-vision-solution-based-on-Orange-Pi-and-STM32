# 单人跟随配套：三秒舵机保持固件

本目录从 STM32F103_SG90_VEHICLE 复制；原工程保持不变。S1串口字段与校验不变，引脚不变。

- 有效视觉数据：转向跟踪；舵机PWM仍受1200–1800us协议限制，香橙派配置限制1300–1700us。
- 收到第一条视觉失效包时，立即清除跟踪有效性，电机停止；冻结当前已施加舵机脉宽，保持3000ms。
- 连续失效包不会刷新三秒计时；到期开始以有界速度回中，完成回中需要额外运动时间。
- 三秒内有效视觉恢复：按新指令继续转向。
- 串口超过500ms没有有效协议包：优先保护回中，不等待三秒。程序退出/USB拔出也最终走此保护。
- 舵机变化上限20us/20ms；原版为10us/20ms。
- OLED第一行新增HOLD / LOST；不是实测轮角反馈。测距遥测D1仍未实现。

烧录文件：`Objects/FaceLock_SG90.hex`。Keil入口：`Project_VEHICLE.uvprojx`，Target应为`FaceLock_SG90_VEHICLE_HOLD3S`。

已在2026-10-29完成ARMCC构建、实际C源码主机逻辑测试；未烧录到实物，未实测三秒保持。不要把这份HEX与旧目录同名HEX混淆。

主机测试可在有C编译器的平台执行：

```bash
cc -std=c99 -Wall -Wextra -Werror -IUser User/steering_protocol.c User/vehicle_control.c tests/hold3s_native_test.c -o hold3s_test
./hold3s_test
```

新固件先悬空车轮并断开驱动电机VM验舵机，确认左右不顶死后再考虑整车。超声波未到货，不做车辆前进测试。
