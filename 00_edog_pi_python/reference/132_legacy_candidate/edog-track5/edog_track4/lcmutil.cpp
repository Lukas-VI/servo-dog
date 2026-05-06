#include "lcmutil.h"
#include "QDebug"

LcmUtil::LcmUtil() {
    if (!lcm.good())
        return;
}

void LcmUtil::send(float ForwardSpeed, float SideSpeed, float CircleSpeed, float RollAngle, float PitchAngle,
                   float Stand_height) {
    my_data.control_mode = 4;
    my_data.v_des[0] = ForwardSpeed;
    my_data.v_des[1] = SideSpeed;
    my_data.v_des[2] = CircleSpeed;
    my_data.rpy_des[0] = RollAngle;
    my_data.rpy_des[1] = PitchAngle;
    my_data.stand_height = Stand_height;
    lcm.publish("edogControlLcm", &my_data);
}

void LcmUtil::send(int control_mode) {
    switch (control_mode) {
        case stop:
            my_data.control_mode = 1;
            break;
//        case upstair:
//            my_data.control_mode = 2;
//            break;

        case lean:
            my_data.control_mode = 3;
            break;

//        case downstair:
//            my_data.control_mode = 5;
            break;
        case updais:
            my_data.control_mode = 6;
            break;
        case lean_left:
            my_data.control_mode=7;
            my_data.rpy_des[0]=0;  //判断是否使用动作
            my_data.v_des[0]=15;   //延时
            my_data.v_des[1]=20;   //逆时针
            my_data.v_des[2]=10;   //顺时针
            break;
        case lean_right:
            my_data.control_mode=8;
            my_data.rpy_des[0]=0;  //判断是否使用动作
            my_data.v_des[0]=15;   //延时
            my_data.v_des[1]=20;   //逆时针
            my_data.v_des[2]=10;   //顺时针
            break;
//        case leg_left:
//            my_data.control_mode=9;
//            break;
//        case leg_right:
//            my_data.control_mode=10;
//            break;

        default:
            my_data.control_mode = 1;
            break;
    }
    lcm.publish("edogControlLcm", &my_data);
}
