#ifndef COLORGROUP_H
#define COLORGROUP_H
#include <opencv2/opencv.hpp>
#include <QByteArray>
#include <QVector>
#include <QUdpSocket>
#include <QThread>
using namespace cv;
using namespace std;

class colorGroup : public QThread
{
public:
    enum Color{
        yellow,
        blue,
        red,
        green,
        purple,
        brown,
        orange,
        pink,
        white,
        black,

    };
public:
    colorGroup();
    //黄色//
    Scalar yellowMin=Scalar(0,184,136);
    Scalar yellowMax=Scalar(136,255,255);
    //蓝色//
    Scalar blueMin=Scalar(0,96,0);
    Scalar blueMax=Scalar(244,195,105);
    //红色//
    Scalar redMin=Scalar(0,0,128);
    Scalar redMax=Scalar( 105,180,255);
    //绿色
    Scalar greenMin=Scalar(0,0,0);
    Scalar greenMax=Scalar(98,116,114);
    //紫色//
    Scalar purpleMin=Scalar(177,0,0);
    Scalar purpleMax=Scalar(255,99,255);
    //棕色//
    Scalar brownMin=Scalar(32,61,84);
    Scalar brownMax=Scalar(91,255,138);
    //orange
    Scalar orangeMin=Scalar(0,0,255);
    Scalar orangeMax=Scalar(255,255,255);
    //pink
    Scalar pinkMin=Scalar(76,69,153);
    Scalar pinkMax=Scalar(167,177,255);
    //white
    Scalar whiteMin=Scalar(0,0,75);
    Scalar whiteMax=Scalar(255,255,255);
    //black
    Scalar blackMin=Scalar(0,0,0);
    Scalar blackMax=Scalar(86,255,222);
public:
    void save();
    void showPicture(Mat &image,int destination);
    void sendColorThreadhold();
    void chooseColor(int number);
    void setColorThreadhold(QByteArray colorarray);
    void run();
    bool ifRunContinueFlag=false;
private:
    QByteArray msg;
    QUdpSocket udpsocket;
    vector<uchar> data_encode;
    vector<int> parameter;
    int color=yellow;
    Mat image;
    int destination=0;
};

#endif // COLORGROUP_H
