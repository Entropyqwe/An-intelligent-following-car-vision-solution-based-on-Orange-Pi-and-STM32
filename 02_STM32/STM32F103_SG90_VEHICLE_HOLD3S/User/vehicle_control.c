#include "vehicle_control.h"

void Vehicle_Init(VehicleState *s) {
    s->distance_mm=0; s->distance_ms=0; s->distance_valid=0;
    s->visual_valid=0; s->visual_ms=0;
    s->left_duty=0; s->right_duty=0; s->mode=VEHICLE_SEARCH;
}

void Vehicle_SetDistance(VehicleState *s, uint32_t distance_mm,
                         uint8_t valid, uint32_t now_ms) {
    s->distance_mm=distance_mm; s->distance_valid=valid; s->distance_ms=now_ms;
}

void Vehicle_SetVisual(VehicleState *s, const SteerPacket *packet,
                       uint32_t now_ms) {
    s->visual_valid=(uint8_t)(packet && packet->valid);
    s->visual_ms=now_ms;
}

void Vehicle_Update(VehicleState *s, uint32_t now_ms) {
    uint8_t visual_ok=s->visual_valid &&
        (uint32_t)(now_ms-s->visual_ms)<VEHICLE_VISUAL_TIMEOUT_MS;
    uint8_t distance_ok=s->distance_valid &&
        (uint32_t)(now_ms-s->distance_ms)<VEHICLE_DISTANCE_TIMEOUT_MS;
    if(!visual_ok) {
        s->left_duty=0; s->right_duty=0; s->mode=VEHICLE_STOP_VISUAL;
        return;
    }
    if(!distance_ok) {
        s->left_duty=0; s->right_duty=0; s->mode=VEHICLE_STOP_SENSOR;
        return;
    }
    if(s->distance_mm<=VEHICLE_STOP_MM) {
        s->left_duty=0; s->right_duty=0; s->mode=VEHICLE_STOP_NEAR;
        return;
    }
    s->left_duty=MOTOR_FOLLOW_DUTY; s->right_duty=MOTOR_FOLLOW_DUTY;
    s->mode=VEHICLE_TRACK_READY;
}

uint8_t Vehicle_MotionAllowed(const VehicleState *s) {
    return s->mode==VEHICLE_TRACK_READY;
}

const char *Vehicle_ModeName(VehicleMode mode) {
    switch(mode) {
    case VEHICLE_TRACK_READY:return "TRACK_READY";
    case VEHICLE_STOP_NEAR:return "STOP_NEAR";
    case VEHICLE_STOP_VISUAL:return "STOP_VISUAL";
    case VEHICLE_STOP_SENSOR:return "STOP_SENSOR";
    case VEHICLE_FAULT:return "FAULT";
    default:return "SEARCH";
    }
}
