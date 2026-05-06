#ifndef MYTHREAD_H
#define MYTHREAD_H
#include <QThread>
#include <iostream>
class myThread:public QThread
{
public:
    enum Mode{
        stop=1,//停止
        track,//循迹
        residence,//住户
//        upstair,//上楼梯
//        downstair,//下楼梯
//        Bridge,//双边桥6
        updais,//上高台
        step,
        byroadA,        //分岔路A
        byroadB,        //分岔路B
        left,
        right,

        lean_left,
        lean_right,
        leg_left,
        leg_right,
        null


    };
    myThread();
    void setParameter();
    void timerEvent(QTimerEvent *);
    void setStop();
    void run() override;
    int  Process=1;

    bool ok=true;
    int timerId;
    int Mode=track;
    bool continueFlag=true;
};

#endif // MYTHREAD_H
