#ifndef VEHICLE_CONTROL_H
#define VEHICLE_CONTROL_H
#include <stdint.h>
#include "steering_protocol.h"

#define VEHICLE_STOP_MM 300u
#define VEHICLE_RELEASE_MM 350u
#define VEHICLE_DISTANCE_TIMEOUT_MS 250u
#define VEHICLE_VISUAL_TIMEOUT_MS 500u
#define MOTOR_MIN_DUTY 0u
#define MOTOR_FOLLOW_DUTY 300u
#define MOTOR_MAX_DUTY 700u

typedef enum {
    VEHICLE_SEARCH = 0,
    VEHICLE_TRACK_READY,
    VEHICLE_STOP_NEAR,
    VEHICLE_STOP_VISUAL,
    VEHICLE_STOP_SENSOR,
    VEHICLE_FAULT
} VehicleMode;

typedef struct {
    uint32_t distance_mm;
    uint32_t distance_ms;
    uint8_t distance_valid;
    uint8_t visual_valid;
    uint32_t visual_ms;
    uint16_t left_duty;
    uint16_t right_duty;
    VehicleMode mode;
} VehicleState;

void Vehicle_Init(VehicleState *s);
void Vehicle_SetDistance(VehicleState *s, uint32_t distance_mm,
                         uint8_t valid, uint32_t now_ms);
void Vehicle_SetVisual(VehicleState *s, const SteerPacket *packet,
                       uint32_t now_ms);
void Vehicle_Update(VehicleState *s, uint32_t now_ms);
uint8_t Vehicle_MotionAllowed(const VehicleState *s);
const char *Vehicle_ModeName(VehicleMode mode);

#endif
