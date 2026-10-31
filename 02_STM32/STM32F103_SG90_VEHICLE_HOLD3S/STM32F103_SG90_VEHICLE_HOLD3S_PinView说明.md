# STM32F103_SG90_VEHICLE_HOLD3S 引脚查看配置

这个 `.ioc` 按车辆固件 `User/vehicle_hw.c` 和 `User/main.c` 整理，只用于 STM32CubeMX 直观看引脚。

| 引脚 | 用途 | 配置 |
|---|---|---|
| PA1 | SG90 舵机信号 | TIM2_CH2 PWM，50Hz，周期20000us |
| PA6 | TB6612 PWMA | TIM3_CH1 PWM |
| PA7 | TB6612 PWMB | TIM3_CH2 PWM |
| PA9 | TTL/香橙派发送 | USART1_TX，115200 8N1 |
| PA10 | TTL/香橙派接收 | USART1_RX，115200 8N1 |
| PB6 | HC-SR04 TRIG | GPIO输出 |
| PB7 | HC-SR04 ECHO | GPIO输入，必须是安全的3.3V电平 |
| PB8 | OLED SCL | 软件I²C GPIO输出 |
| PB9 | OLED SDA | 软件I²C GPIO输出 |
| PB10 | TB6612 STBY | GPIO输出 |
| PB12 | TB6612 AIN1 | GPIO输出 |
| PB13 | TB6612 AIN2 | GPIO输出 |
| PB14 | TB6612 BIN1 | GPIO输出 |
| PB15 | TB6612 BIN2 | GPIO输出 |
| PA13 | ST-LINK SWDIO | Serial Wire |
| PA14 | ST-LINK SWCLK | Serial Wire |
| PD0/PD1 | 外部高速晶振 | HSE |

注意：这是查看文件，不是 CubeMX HAL 重生成工程。不要点击 Generate Code 覆盖现有 Keil 工程。PB13/PB14/PB15 只有车辆 HOLD3S 工程才在固件中初始化，基础 SG90 工程不包含它们。
