/* VEHICLE variant. Original S1/PA1/PA9/PA10 path is retained.
 * USART1 PA10 RX, PA9 TX, 115200 8N1. OLED PB8/PB9 as original diagram.
 * Visual loss: motor invalid immediately; servo holds 3s then centers.
 * Serial link loss: 500ms center protection retained. S1 wire format unchanged.
 */
#include "stm32f10x.h"
#include "OLED.h"
#include "steering_protocol.h"
#include "vehicle_control.h"
#include "vehicle_hw.h"
#include <stdio.h>
#include <string.h>

#define RX_SIZE 256u
#define ENABLE_OLED 1
static volatile uint32_t milliseconds;
static volatile uint16_t rx_head,rx_tail;
static volatile uint8_t rx_overflow;
static volatile uint8_t rx_data[RX_SIZE];
static SteerState control;
static VehicleState vehicle;

void SysTick_Handler(void) { ++milliseconds; }
void USART1_IRQHandler(void) {
    uint32_t sr=USART1->SR;
    if(sr&(USART_SR_RXNE|USART_SR_ORE|USART_SR_FE|USART_SR_NE)) {
        uint8_t c=(uint8_t)USART1->DR;
        if(sr&(USART_SR_ORE|USART_SR_FE|USART_SR_NE)) { rx_overflow=1; return; }
        if(sr&USART_SR_RXNE) {
            uint16_t next=(rx_head+1u)&(RX_SIZE-1u);
            if(next==rx_tail) rx_overflow=1;
            else { rx_data[rx_head]=c; rx_head=next; }
        }
    }
}
static void Serial_Init(void) {
    GPIO_InitTypeDef g; USART_InitTypeDef u; NVIC_InitTypeDef n;
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA|RCC_APB2Periph_USART1,ENABLE);
    g.GPIO_Pin=GPIO_Pin_9; g.GPIO_Mode=GPIO_Mode_AF_PP; g.GPIO_Speed=GPIO_Speed_50MHz;
    GPIO_Init(GPIOA,&g);
    g.GPIO_Pin=GPIO_Pin_10; g.GPIO_Mode=GPIO_Mode_IPU; GPIO_Init(GPIOA,&g);
    USART_StructInit(&u); u.USART_BaudRate=115200;
    u.USART_Mode=USART_Mode_Rx|USART_Mode_Tx; USART_Init(USART1,&u);
    n.NVIC_IRQChannel=USART1_IRQn; n.NVIC_IRQChannelPreemptionPriority=1;
    n.NVIC_IRQChannelSubPriority=0; n.NVIC_IRQChannelCmd=ENABLE; NVIC_Init(&n);
    USART_ITConfig(USART1,USART_IT_RXNE,ENABLE); USART_Cmd(USART1,ENABLE);
}
static void Send(const char *s) {
    while(*s) {while(USART_GetFlagStatus(USART1,USART_FLAG_TXE)==RESET){} USART_SendData(USART1,(uint8_t)*s++);}
}
static void PWM_Init_Safe(void) {
    GPIO_InitTypeDef g; TIM_TimeBaseInitTypeDef t; TIM_OCInitTypeDef o;
    RCC_ClocksTypeDef clocks; uint32_t timer_clock;
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA,ENABLE);
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM2,ENABLE);
    g.GPIO_Pin=GPIO_Pin_1; g.GPIO_Mode=GPIO_Mode_AF_PP; g.GPIO_Speed=GPIO_Speed_50MHz;
    GPIO_Init(GPIOA,&g);
    RCC_GetClocksFreq(&clocks); timer_clock=clocks.PCLK1_Frequency;
    if(clocks.PCLK1_Frequency!=clocks.HCLK_Frequency) timer_clock*=2;
    TIM_TimeBaseStructInit(&t); t.TIM_Prescaler=(uint16_t)(timer_clock/1000000u-1u);
    t.TIM_Period=19999; TIM_TimeBaseInit(TIM2,&t);
    TIM_OCStructInit(&o); o.TIM_OCMode=TIM_OCMode_PWM1;
    o.TIM_OutputState=TIM_OutputState_Enable; o.TIM_OCPolarity=TIM_OCPolarity_High;
    o.TIM_Pulse=STEER_CENTER_US; TIM_OC2Init(TIM2,&o);
    TIM_OC2PreloadConfig(TIM2,TIM_OCPreload_Enable); TIM_ARRPreloadConfig(TIM2,ENABLE);
    TIM_GenerateEvent(TIM2,TIM_EventSource_Update); TIM_Cmd(TIM2,ENABLE);
}
static void Watchdog_Init(void) {
    IWDG_WriteAccessCmd(IWDG_WriteAccess_Enable);
    IWDG_SetPrescaler(IWDG_Prescaler_64); IWDG_SetReload(1250);
    IWDG_ReloadCounter(); IWDG_Enable(); /* ~2s nominal LSI; timing varies. */
}
int main(void) {
    char line[128],reply[96]; uint16_t used=0,applied=1500,demand;
    uint32_t last_pwm=0,last_display=0,last_telemetry=0,good=0,bad=0;
    uint8_t collecting=0; SteerPacket packet;
    SystemCoreClockUpdate(); NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);
    PWM_Init_Safe();
    #if ENABLE_OLED
    OLED_Init(); OLED_Clear(); OLED_ShowString(1,1,"FaceLock S1");
    #endif
    SysTick_Config(SystemCoreClock/1000u); Serial_Init(); Watchdog_Init();
    Vehicle_Init(&vehicle);
    VehicleHw_Init();
    Send("#READY,S1,HOLD3S,PA1,115200\n");
    while(1) {
        if(rx_overflow) {
            __disable_irq(); rx_tail=rx_head; rx_overflow=0; __enable_irq();
            collecting=0; used=0; control.tracking=0; control.holding=0; control.demand=1500;
            vehicle.visual_valid=0;
        }
        while(rx_tail!=rx_head) {
            char c=(char)rx_data[rx_tail]; rx_tail=(rx_tail+1u)&(RX_SIZE-1u);
            if(c=='@') { collecting=1; used=0; }
            if(!collecting) continue;
            if(used>=sizeof(line)-1) {collecting=0; used=0; ++bad; continue;}
            line[used++]=c;
            if(c=='\n') {
                line[used]='\0'; collecting=0;
                if(Steer_Parse(line,&packet)) {
                    uint8_t was_tracking=control.tracking;
                    Steer_Accept(&control,&packet,milliseconds); ++good;
                    /* Freeze the last applied pulse, not a demand still slewing. */
                    if(was_tracking && !packet.valid && control.holding)
                        control.demand=applied;
                    Vehicle_SetVisual(&vehicle,&packet,milliseconds);
                    /* A1 is diagnostic telemetry, no checksum: never a control input. */
                    sprintf(reply,"#A1,%lu,%u,%u,%ld\n",(unsigned long)packet.seq,
                            packet.valid,packet.servo_us,(long)packet.bearing_mdeg);
                    Send(reply);
                } else ++bad;
                used=0;
            }
        }
        Vehicle_Update(&vehicle,milliseconds);
        VehicleHw_UltrasonicTask(milliseconds,&vehicle);
        Vehicle_Update(&vehicle,milliseconds);
        VehicleHw_ApplyMotors(&vehicle);
        /* Read-only distance telemetry for the Orange Pi HUD. S1 control
         * packets and their checksum/fields remain unchanged. */
        if((uint32_t)(milliseconds-last_telemetry)>=200u) {
            char distance_line[64];
            last_telemetry=milliseconds;
            sprintf(distance_line,"#D1,%lu,%u,%s\n",
                    (unsigned long)vehicle.distance_mm,
                    vehicle.distance_valid,
                    Vehicle_ModeName(vehicle.mode));
            Send(distance_line);
        }
        demand=Steer_Demand(&control,milliseconds);
        if((uint32_t)(milliseconds-last_pwm)>=20u) {
            last_pwm=milliseconds;
            /* Bounded 20us/20ms = 1000us/s; pulse limits stay unchanged. */
            if(applied<demand) applied+=(demand-applied>20u)?20u:demand-applied;
            else if(applied>demand) applied-=(applied-demand>20u)?20u:applied-demand;
            TIM_SetCompare2(TIM2,applied);
        }
        #if ENABLE_OLED
        if((uint32_t)(milliseconds-last_display)>=200u) {
            last_display=milliseconds;
            OLED_ShowString(1,1,control.tracking?"TRACKING S1     ":
                            (control.holding?"HOLD / LOST     ":"CENTER / LOST   "));
            OLED_ShowString(2,1,"PWM:"); OLED_ShowNum(2,5,applied,4);
            OLED_ShowString(3,1,"OK:"); OLED_ShowNum(3,4,good%100000,5);
            OLED_ShowString(4,1,"BAD:"); OLED_ShowNum(4,5,bad%100000,5);
        }
        #endif
        IWDG_ReloadCounter();
    }
}
