#include "lcmutil.h"
#include <QThread>
#include <stdio.h>
//#include <QDebug>
//#include <opencv2/opencv.hpp>
#include <vector>
#include <unistd.h>
#include <QDebug>
#include <QTime>
#include <sys/time.h>
#include <colorgroup.h>
#include <QTimer>
#include <pthread.h>
#include "mythread.h"
#include <QDir>
#include <wait.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <QThread>
#include "udputil.h"
#include "bridge.h"



//#define Bridge_flag 1  //0--手动干预，直行通过双边桥    1-- 直接识别蓝色然后二值化黑色条带

//using namespace cv;
using namespace std;
VideoCapture cap;//摄像头实例化
myThread mythread;//实例化计时线程
colorGroup colorgroup;//实例化色彩阈值类
LcmUtil *lcmutil;//创建lcm communication module
UdpUtil udpsocket;
QString residenceColor = "null";
QString nextColor = "green";


//图像处理
void imageProcess(Mat image);

//打印程序运行模式
void logMode(Mat image);

void track_run(int average);

int solve_avg(Mat matEdges);

float solve_ang(Mat matEdges);

void Color_deal(Mat img, int color);

void middle(int Avg);

void show_send_picture();

Mat get_edge(Mat img);
//程序入口
int main(int argc, char *argv[]) {
    //init lcm module
    lcmutil = new LcmUtil();
    //定义一幅图像
    Mat srcImage;
    /*以下程序用于根据输入参数的选择更改运行模式，以及选择是否将图像发送至上位机*/
    //according to the parameters passed in,choose mode
    //inputParameters1与inputParameters2是输入的两个参数
    QString inputParameters1;
    QString inputParameters2;
    bool flag = true;
    //无参数输入
    if (argc == 1) {
        printf("mode is stop\n");
        mythread.Mode = myThread::stop;
        residenceColor = "null";//"red";
    }
        //输入参数大于等于两个
    else if (argc >= 2) {
        inputParameters1 = argv[1];
        //track 模式
        if (inputParameters1 == "track") {
            printf("mode is track\n");
            printf("default residenceColor is null\n");
            mythread.Mode = myThread::track;
        } else if (inputParameters1 == "purple") {
            printf("mode is track\n");
            printf("input residenceColor is purple\n");
            mythread.Mode = myThread::track;
            residenceColor = "purple";
            nextColor = "green";
        } else if (inputParameters1 == "brown") {
            printf("mode is track\n");
            printf("input residenceColor is brown\n");
            mythread.Mode = myThread::track;
            residenceColor = "brown";
            nextColor = "green";
        } else if (inputParameters1 == "stop") {
            printf("mode is stop\n");
            mythread.Mode = myThread::stop;
        } else {
            mythread.Mode = myThread::track;
            printf("parameters error\n");
            printf("mode is track\n");
        }
        //输入第2个参数
        if (argc == 3) {
            inputParameters2 = argv[2];
            if (inputParameters2 == "showImage") {
                printf("start to show image\n");
                flag = true;
                udpsocket.start();//thread2
            }
        }
    }

    //识别id为0到3的设备序号，查看是否能打开对应的摄像头
    //打开摄像头
    for (int i = 0; i <= 3; i++) {
        cap.open(i);//open device
        if (!cap.isOpened()) {
            printf("打开摄像头失败:number=%d\n", i);
            if (i == 3)
                return 0;
        } else {
            printf("打开摄像头成功:number=%d\n", i);
            break;
        }
    }

    //计时线程开启
    mythread.start();
    //如下三行用于获取非阻塞获取键盘输入，中断程序的运行
    //get keyboard to stop program

    char buf[5] = {0};//keyboard buffer
    int attr = 1;
    ioctl(STDIN_FILENO, FIONBIO, &attr);//set non-blocking flag

    //主循环
    while (true) {
        cap >> srcImage;//读取当前帧
        if (!srcImage.empty()) {
            //进行图像处理
            imageProcess(srcImage);
            logMode(srcImage);//打印状态
            //show or send picture
            if (flag) {//
                colorgroup.showPicture(srcImage, 1);
                show_send_picture();
            }
        }
        //check any key ,then break out.
        //检测到键值，退出循环
        int len = read(STDIN_FILENO, &buf[0], 5);
        if (len > 0) {
            break;
        }
        //因为运动控制板最大接收频率14hz，故此处延迟70ms
        QThread::msleep(70);

    }
    mythread.setStop();
    QThread::msleep(200);
    lcmutil->send(LcmUtil::stop);
    printf("程序运行结束\n");
    cap.release();
    return 0;
}

void imageProcess(Mat image){
    Mat ZoomOutimage;
    Mat matHSV,Blurimage;
    static int time_counter = 0;
    int average = 0;
    resize(image,ZoomOutimage,Size(80,60));//改变图像尺寸为80*60

    /***********get edge value**********/

    cvtColor(ZoomOutimage,matHSV,COLOR_BGR2HSV,0);//HSV图
    medianBlur(matHSV,Blurimage,3);//中值滤波

    if(nextColor=="blue"){
        Color_deal(Blurimage,colorgroup.blue);//blue
    }else if(nextColor=="green"){
        Color_deal(Blurimage,colorgroup.green);//green
    }else if(nextColor=="purple"){
        qDebug() << "Purple nnnnn" << endl;
        Color_deal(Blurimage,colorgroup.purple);//purple
    }else if(nextColor=="brown"){
        Color_deal(Blurimage,colorgroup.brown);//brown
    }else if(nextColor=="null"){
        qDebug() << "Null: " << time_counter << endl;
        time_counter ++;
        if (time_counter > 10){
            nextColor = "brown";
            time_counter = 0;
        }
    }

    //the action of each thread defined here
    if (mythread.Mode == myThread::byroadA) {//left dash
        qDebug() << "TrackLeft" << endl;
        matHSV.setTo(cv::Scalar(0, 0, 0));
        nextColor = "null";
        lcmutil->send(0.60f, 0.00f, 0.20f, 0, 0, 148);
        QThread::sleep(1);
        mythread.Mode=myThread::track;

    }else if (mythread.Mode == myThread::byroadB) {
        qDebug() << "Right" << endl;
        nextColor = "purple";
        lcmutil->send(1.0f, 0.0f, -0.5f, 0, 0, 148);//右转
        QThread::sleep(1);
        mythread.Mode=myThread::track;

    }else if (mythread.Mode == myThread::track) {
        qDebug() << "TrackMode" << endl;
        average = solve_avg(matHSV);
        track_run(average);//边沿识别循迹

    }else if(mythread.Mode == myThread::lean_left){
        qDebug() << residenceColor<<"LLEFT\r" << endl;
        lcmutil->send(LcmUtil::lean_left);
        QThread::sleep(3);
        lcmutil->send(1.0f, 0.00f, -0.01*colorgroup.orangeMin[2], 0, 0, 140);
        sleep(colorgroup.orangeMax[2]);
        residenceColor == "purple";
        nextColor == "blue";
        mythread.Mode=myThread::track;

    }else if(mythread.Mode == myThread::lean_right){
        qDebug() << residenceColor<<"RRIGHT\r" << endl;
        lcmutil->send(LcmUtil::lean_right);
        sleep(3);
        lcmutil->send(1.0f, 0.1f, 0.10f, 0, 0, 140);
        sleep(2);
        residenceColor == "brown";
        nextColor == "blue";
        mythread.Mode=myThread::track;

    }else if(mythread.Mode == myThread::updais){
        qDebug() << "UP\r "<< endl;
//        middle(edgeMat);
        lcmutil->send(LcmUtil::updais);
        QThread::sleep(3);
        mythread.Mode=myThread::track;

    }else if(mythread.Mode == myThread::stop){
        qDebug() << "STOP "<< endl;

    }
}

void middle(int Avg){
    float side = 0;
    float yaw = 0;
    int d = 0;

    d = Avg - colorgroup.orangeMin[1];
    side = 0.001 * colorgroup.orangeMin[0] * d;
    yaw = 0.001 * colorgroup.orangeMax[0] * d;
    cout << " d: " << d << " s: " << side << " yaw: " << yaw << endl;
    lcmutil->send(0.0f, side, yaw, 0, 0, 140);
    sleep(0.5);
}

//循迹处理
void track_run(int average){
    cout << "AVG: " << average << endl;
    //中间循迹
    //mid 70
    if ((average > 70.0f) || (average < 5.0f)) { //直行
        lcmutil->send(0.001*colorgroup.pinkMin[2], 0, 0, 0, 0, colorgroup.pinkMax[2]);
//        qDebug() << "average<3.0 || average>77.0" << endl;
    //R 00
    } else if (average >= 65.0f) {
        lcmutil->send(0.001*colorgroup.pinkMin[2], -0.001*colorgroup.pinkMax[0], 0.001*colorgroup.yellowMax[0], 0, 0, colorgroup.pinkMax[2]);//右横移左转
//        qDebug() << "average>65.0" << endl;
    //R 30
    } else if (average >= 50.0f) {
        lcmutil->send(0.001*colorgroup.pinkMin[2], -0.001*colorgroup.pinkMin[0], 0.001*colorgroup.yellowMin[0], 0, 0, colorgroup.pinkMax[2]);//右横移左转
//        qDebug() << "average>48.0" << endl;

    //R 45
    } else if (average >= 30.0f) {
        lcmutil->send(0.001*colorgroup.pinkMin[2], 0.001*colorgroup.pinkMax[1], -0.001*colorgroup.yellowMax[1], 0, 0, colorgroup.pinkMax[2]);//左横移右转
//        qDebug() << "左横移右转" << endl;
    //L 45
    } else if (average <= 15.0f) {
        lcmutil->send(0.001*colorgroup.pinkMin[2], 0.001*colorgroup.pinkMin[1], -0.001*colorgroup.yellowMin[1], 0, 0, colorgroup.pinkMax[2]);//左横移右转
//        qDebug() << "左横移右转" << endl;
    //L 30
    } else {
        lcmutil->send(0.001*colorgroup.pinkMin[2], -0.0f, 0.05f, 0, 0, colorgroup.pinkMax[2]);//右横移左转
//        qDebug() << "Other" << endl;
    }
}

int solve_avg(Mat matEdges){
    int number = 0;
    int average = 0;
    int sum = 0;
    int position[100] = {0};

    for (int i = 59; i > 0; i--) {//行
        for (int j = 79; j > 0; j--) {
            if (matEdges.at<uchar>(i, j) == 255) {//像素点是白色
                position[i] = j;
                break;
            } else {
                position[i] = 0;
            }
        }
    }

    average = 0;
    number = 0;
    sum = 0;
    for (int i = 0; i < matEdges.rows - 1; i++) {//59
        if ((position[i] < (position[i + 1] + 5)) &&
            (position[i] > (position[i + 1] - 5)) &&
            (position[i] != 0)) {
            sum = sum + position[i];
            number++;
        }
    }
    if (sum == 0) {
        average = 80;
    } else {
        average = sum / number;
    }
    return average;
}

float solve_ang(Mat matEdges){
    int sum_m = 0;
    int sum_i = 0;
    int con = 0;
    int av_m, av_i;
    int L_xx,L_yy,L_xy;
    float re[2] = {0};
    //变量初始化
    av_m = 0; //X的平均值
    av_i = 0; //Y的平均值
    L_xx = 0; //Lxx
    L_yy = 0; //Lyy
    L_xy = 0; //Lxy

    int m_position[100] = {0}, r_position[100] = {0};
//    Mat img_Thr_O, gray;

//    inRange(mat,colorgroup.blackMin,colorgroup.blackMax,transfered_black);//输出图像为单通道二值图

//    Canny(transfered_black,matEdges,150,255,3,true);//canny边缘检测

    for (int i = 59; i > 0; i--) {//行
        for (int j = 79; j > 0; j--) {
            if (matEdges.at<uchar>(i, j) == 255) {//像素点是白色
                r_position[i] = j;
                break;
            } else {
                r_position[i] = 0;
            }
            for (int m = 0; m < 80; m ++) {
                if ((matEdges.at<uchar>(i, j) == 255) && (m != j)) {//像素点是白色
                    m_position[i] = int((m + j) / 2);
                    con ++;
                    sum_m += m_position[i];
                    sum_i += i;
                    break;
                }else {
                    m_position[i] = 0;
                }
            }
        }
        av_m = sum_m/con;
        av_i = sum_i/con;
    }


    for(int i = 0; i < 60; i++) //计算Lxx、Lyy和Lxy
    {
        L_xx += (i-av_m)*(i-av_m);
        L_yy += (m_position[i]-av_i)*(m_position[i]-av_i);
        L_xy += (i-av_m)*(m_position[i]-av_i);
    }

    re[0] = L_xy/L_xx; //斜率
    re[1] = av_i-L_xy*av_m/L_xx; //截距

    return re[0];
}
//颜色识别处理
void Color_deal(Mat img, int color) {
    Mat transformImage;

    int number1 = 0;
    switch (color) {
        case colorgroup.blue: //blue  ---上高台
            inRange(img, colorgroup.blueMin, colorgroup.blueMax, transformImage);//输出图像为单通道二值图
            for (int i = 0; i <= 59; i++) {//列
                for (int j = 0; j <= 79; j++) {//行
                    if (transformImage.at<uchar>(i, j) == 255) {
                        number1++;
                        break;
                    }
                }
            }
            qDebug() << "BLUE:" << number1 << endl;
            if (number1 >= 13) {
                qDebug() << "find BLUE";
                nextColor = "green";
                mythread.Mode = myThread::updais;
            }
        break;

        case colorgroup.red://red --
            inRange(img, colorgroup.redMin, colorgroup.redMax, transformImage);//输出图像为单通道二值图
            for (int i = 0; i <= 59; i++) {//列
                for (int j = 0; j <= 79; j++) {//行
                    if (transformImage.at<uchar>(i, j) == 255) {
                        number1++;
                        break;
                    }
                }
            }
            qDebug() << "RED:" << number1 << endl;
            if (number1 >= 15) {
                qDebug() << "find RED";
                mythread.Mode = myThread::byroadB;
                nextColor = "purple";
            }
        break;

        case colorgroup.brown://brown -- 送快递2
            inRange(img, colorgroup.brownMin, colorgroup.brownMax, transformImage);//输出图像为单通道二值图
            for (int i = 0; i <= 59; i++) {//列
                for (int j = 0; j <= 79; j++) {//行
                    if (transformImage.at<uchar>(i, j) == 255) {
                        number1++;
                        break;
                    }
                }
            }
            qDebug() << "BROWN:" << number1 << endl;
            if (number1 >= 25) {
                qDebug() << "find BROWN";
                nextColor = "blue";
                mythread.Mode = myThread::lean_left;
                residenceColor = "purple";                
            }
        break;

        case colorgroup.purple://purple -- 送快递1
            inRange(img, colorgroup.purpleMin, colorgroup.purpleMax, transformImage);//输出图像为单通道二值图
            for (int i = 0; i <= 59; i++) {//列
                for (int j = 0; j <= 79; j++) {//行
                    if (transformImage.at<uchar>(i, j) == 255) {
                        number1++;
                        break;
                    }
                }
            }
            qDebug() << "PURPLE:" << number1 << endl;
            if (number1 >= 19) {
                qDebug() << "find PURPLE";
                residenceColor = "brown";
                nextColor = "blue";
                mythread.Mode = myThread::lean_right;
            }
        break;


        case colorgroup.green://green --
            inRange(img, colorgroup.greenMin, colorgroup.greenMax, transformImage);//输出图像为单通道二值图
            for (int i = 0; i <= 59; i++) {//列
                for (int j = 0; j <= 79; j++) {//行
                    if (transformImage.at<uchar>(i, j) == 255) {
                        number1++;
                        break;
                    }
                }
            }
            qDebug() << "GREEN:" << number1 << endl;
            if (number1 >= 16) {
                qDebug() << "find GREEN";
                if (residenceColor=="brown"){
                    nextColor == "null";
                    mythread.Mode = myThread::byroadA;
                }else if (residenceColor=="purple"){
                    nextColor == "purple";
                    mythread.Mode = myThread::byroadB;
//                mythread.Mode = myThread::step;
                }
            }
        break;

    }
}


//显示发送图片
void show_send_picture() {

    //first  parameter is imput image
    //second parameter is output destination
    //second parameter is 0 ,output destination is native computer
    //second parameter is 1 ,output destination is upper computer
    colorgroup.start();//thread1
    if (udpsocket.ifReceiveInfoFlag != 0) {
        switch (udpsocket.ifReceiveInfoFlag) {
            case 1://choose color and return this color threadhold
                std::cout << "choose color and return this color threadhold" << std::endl;
                colorgroup.chooseColor(udpsocket.color);
                colorgroup.sendColorThreadhold();
                colorgroup.ifRunContinueFlag = true;
                break;
            case 2://set color threadhold
                std::cout << "set color threadhold" << std::endl;
                colorgroup.setColorThreadhold(udpsocket.colorThreadhold);
                break;
            case 3://save color threadhold
                std::cout << "save color threadhold" << std::endl;
                colorgroup.save();
                break;
        }
        udpsocket.ifReceiveInfoFlag = 0;
        }
   }

//print current modesss
void logMode(Mat &image) {
    Mat ZoomOutimage,matEdges;
    Mat transfered_black;
    static int count = 0;
    int average = 0;
    float k = 0;
    count++;

    resize(image, ZoomOutimage, Size(80,60));//改变图像尺寸为80*60
    inRange(ZoomOutimage, colorgroup.blackMin, colorgroup.blackMax, transfered_black);//输出图像为单通道二值图
    Canny(transfered_black, matEdges, 150, 255, 3, true);//canny边缘检测

    if (1 == 1) {
        switch (mythread.Mode) {
            case myThread::residence:
                cout << "Mode:" << "residence" << endl;
                break;
            case myThread::track:
                cout << "Mode:" << "track" << endl;
                break;
            case myThread::lean_left:
                cout<<"Mode:"<<"lean_left"<<endl;
                break;
            case myThread::lean_right:
                cout<<"Mode:"<<"lean_right"<<endl;
                break;
            case myThread::updais:
                cout<<"Mode:"<<"updais"<<endl;
                break;
            case myThread::stop:
                cout << "Mode:" << "stop" << endl;
                average = solve_avg(matEdges);
                k =solve_ang(matEdges);
                cout << "AVG: " << average << " ANG; " << k << endl;
                if((average>65) | (average<55)){
//                    middle(average);
                }

                break;


        }
//        qDebug() << "nextColor:" << nextColor << endl;
//        qDebug()<<"residenceColor"<<residenceColor<<endl;
    }
}

