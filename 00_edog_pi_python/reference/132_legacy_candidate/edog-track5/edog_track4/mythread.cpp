#include "mythread.h"
#include <QDebug>
extern int time_counter;

myThread::myThread()
{
    // timerId=startTimer(1000);
}
void myThread::setParameter(){
    //parameter=c;
}
void myThread::timerEvent(QTimerEvent *){
    ok=true;
    killTimer(timerId);
}
//设定停止标志位
void myThread::setStop(){
    continueFlag=false;
}
//状态时长设定线程，通过此线程可以更改每种状态持续的时间，并进行切换
void myThread::run(){
    while(continueFlag){
        switch(Mode){
            case residence:{//住户状态
                QThread::sleep(5);
//                Mode=track;
            break;
            }
//            case upstair:{//上楼梯状态
//                QThread::sleep(20);
////                Mode=track;
//            break;
//            }
            case track:{
                break;
            }
            case byroadA:{
                QThread::sleep(2);
                break;
            }
            case byroadB:{
                QThread::sleep(3);
                break;
            }
            case lean_left:{//住户状态
                QThread::sleep(6);
                break;
            }
            case lean_right:{//住户状态
                QThread::sleep(5);
                break;
            }
            case left:{
                QThread::sleep(10);
                break;
            }
            case right:{
                QThread::sleep(10);
                break;
            }
            case updais:{
                QThread::sleep(30);
                break;
            }case step:{
                QThread::sleep(10);
                break;
            }
            case null:{//无状态
                QThread::sleep(5);

            break;
            }
            default:
               QThread::msleep(10);
            break;
        }
    }
}
