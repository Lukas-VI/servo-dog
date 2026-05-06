#ifndef LCMUTIL_H
#define LCMUTIL_H
#include <lcm/lcm-cpp.hpp>
#include "edog_control_lcm.hpp"
class LcmUtil
{
public:
    enum controlMode{
        stop=1,//停止1
//        upstair,//上楼梯2
        lean,//快递3
        walk,//行走4
//        downstair,//下楼梯5
        updais,//6
        lean_left, //7
        lean_right,//8
//        leg_left,//9
//        leg_right,//10


    };
    LcmUtil();
//    void send(float ForwardSpeed,float SideSpeed,float CircleSpeed,float RollAngle,float PitchAngle);
    void send(float ForwardSpeed,float SideSpeed,float CircleSpeed,float RollAngle,float PitchAngle,float Stand_height);
    void send(int control_mode);
private:
    edog_control_lcm my_data;
    lcm::LCM lcm;
};

#endif // LCMUTIL_H
