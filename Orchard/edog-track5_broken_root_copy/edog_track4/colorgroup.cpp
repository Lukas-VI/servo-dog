#include "colorgroup.h"
#include <QFile>
#include <QDebug>
#include <QDir>
#include <QHostAddress>
#include <thread>
#include <QString>
#include <opencv2/imgcodecs.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/core.hpp>
#include <opencv2/opencv.hpp>
#define SERV_PORT   8000
colorGroup::colorGroup()
{
    QFile file(QDir::toNativeSeparators(QDir::currentPath()+"/"+"colorGroup.txt"));
   // QFile file("colorGroup.txt");
    if(!file.open(QIODevice::ReadWrite|QIODevice::Text)){
        qDebug()<<"未能成功读取颜色阈值"<<endl;
        return;
    }else{
        qDebug()<<"成功读取颜色阈值"<<endl;
    }
    //按行读取文本内的信息
    while(!file.atEnd()){
        QByteArray line = file.readLine();
        QString str(line);
        QStringList list=str.split(" ");

        if(list[0]=="yellow"){//黄色
            yellowMin.val[0]=list[1].toInt();
            yellowMin.val[1]=list[2].toInt();
            yellowMin.val[2]=list[3].toInt();
            yellowMax.val[0]=list[4].toInt();
            yellowMax.val[1]=list[5].toInt();
            yellowMax.val[2]=list[6].toInt();

        }else if(list[0]=="blue"){//蓝色
            blueMin.val[0]=list[1].toInt();
            blueMin.val[1]=list[2].toInt();
            blueMin.val[2]=list[3].toInt();
            blueMax.val[0]=list[4].toInt();
            blueMax.val[1]=list[5].toInt();
            blueMax.val[2]=list[6].toInt();

        }else if(list[0]=="red"){//红色
            redMin.val[0]=list[1].toInt();
            redMin.val[1]=list[2].toInt();
            redMin.val[2]=list[3].toInt();
            redMax.val[0]=list[4].toInt();
            redMax.val[1]=list[5].toInt();
            redMax.val[2]=list[6].toInt();

        }else if(list[0]=="green"){ //绿色
            greenMin.val[0]=list[1].toInt();
            greenMin.val[1]=list[2].toInt();
            greenMin.val[2]=list[3].toInt();
            greenMax.val[0]=list[4].toInt();
            greenMax.val[1]=list[5].toInt();
            greenMax.val[2]=list[6].toInt();

        }else if(list[0]=="purple"){//紫色
            purpleMin.val[0]=list[1].toInt();
            purpleMin.val[1]=list[2].toInt();
            purpleMin.val[2]=list[3].toInt();
            purpleMax.val[0]=list[4].toInt();
            purpleMax.val[1]=list[5].toInt();
            purpleMax.val[2]=list[6].toInt();

        }else if(list[0]=="brown"){//棕色
            brownMin.val[0]=list[1].toInt();
            brownMin.val[1]=list[2].toInt();
            brownMin.val[2]=list[3].toInt();
            brownMax.val[0]=list[4].toInt();
            brownMax.val[1]=list[5].toInt();
            brownMax.val[2]=list[6].toInt();

        }else if(list[0]=="orange"){//orange
            orangeMin.val[0]=list[1].toInt();
            orangeMin.val[1]=list[2].toInt();
            orangeMin.val[2]=list[3].toInt();
            orangeMax.val[0]=list[4].toInt();
            orangeMax.val[1]=list[5].toInt();
            orangeMax.val[2]=list[6].toInt();

        }else if(list[0]=="pink"){//pink
            pinkMin.val[0]=list[1].toInt();
            pinkMin.val[1]=list[2].toInt();
            pinkMin.val[2]=list[3].toInt();
            pinkMax.val[0]=list[4].toInt();
            pinkMax.val[1]=list[5].toInt();
            pinkMax.val[2]=list[6].toInt();

        }else if(list[0]=="white"){//white
            whiteMin.val[0]=list[1].toInt();
            whiteMin.val[1]=list[2].toInt();
            whiteMin.val[2]=list[3].toInt();
            whiteMax.val[0]=list[4].toInt();
            whiteMax.val[1]=list[5].toInt();
            whiteMax.val[2]=list[6].toInt();

        }else if(list[0]=="black"){//black
            blackMin.val[0]=list[1].toInt();
            blackMin.val[1]=list[2].toInt();
            blackMin.val[2]=list[3].toInt();
            blackMax.val[0]=list[4].toInt();
            blackMax.val[1]=list[5].toInt();
            blackMax.val[2]=list[6].toInt();
        }
    }
    //绑定当前的udp地址与端口
    udpsocket.bind(QHostAddress("192.168.12.1"),30014);
<<<<<<< HEAD

    //设置视频编码时的编码参数
    parameter.push_back(IMWRITE_JPEG_QUALITY);
    parameter.push_back(50);//进行50%的压缩
    }
=======
    //设置视频编码时的编码参数
    parameter.push_back(IMWRITE_JPEG_QUALITY);
    parameter.push_back(50);//进行50%的压缩
}
>>>>>>> ae1e708 (addd)

    //将当前的阈值信息保存到文本文档内
    void colorGroup::save(){
        qDebug()<<"save successful"<<endl;
        QFile file(QDir::toNativeSeparators(QDir::currentPath()+"/"+"colorGroup.txt"));
        if(! file.open(QIODevice::ReadWrite|QIODevice::Text)){
            qDebug()<<"未能成功写入"<<endl;
            return;
        }
        QString dataAll="";
        QString dataline="";
        //save yellow
        dataline.append("yellow ");
        for(int i=0;i<=2;i++)
            dataline.append(QString::number(yellowMin.val[i])+" ");
        for(int i=0;i<=1;i++)
            dataline.append(QString::number(yellowMax.val[i])+" ");
        dataline.append(QString::number(yellowMax.val[2])+"\n");
        dataAll.append(dataline);
        dataline.clear();
        //save blue
        dataline.append("blue ");
        for(int i=0;i<=2;i++)
            dataline.append(QString::number(blueMin.val[i])+" ");
        for(int i=0;i<=1;i++)
            dataline.append(QString::number(blueMax.val[i])+" ");
        dataline.append(QString::number(blueMax.val[2])+"\n");
        dataAll.append(dataline);
        dataline.clear();

        //save red
        dataline.append("red ");
        for(int i=0;i<=2;i++)
            dataline.append(QString::number(redMin.val[i])+" ");
        for(int i=0;i<=1;i++)
            dataline.append(QString::number(redMax.val[i])+" ");
        dataline.append(QString::number(redMax.val[2])+"\n");
        dataAll.append(dataline);
        dataline.clear();

        //save green
        dataline.append("green ");
        for(int i=0;i<=2;i++)
            dataline.append(QString::number(greenMin.val[i])+" ");
        for(int i=0;i<=1;i++)
            dataline.append(QString::number(greenMax.val[i])+" ");
        dataline.append(QString::number(greenMax.val[2])+"\n");
        dataAll.append(dataline);
        dataline.clear();

        //save purple
        dataline.append("purple ");
        for(int i=0;i<=2;i++)
            dataline.append(QString::number(purpleMin.val[i])+" ");
        for(int i=0;i<=1;i++)
            dataline.append(QString::number(purpleMax.val[i])+" ");
        dataline.append(QString::number(purpleMax.val[2])+"\n");
        dataAll.append(dataline);
        dataline.clear();

        //save brown
        dataline.append("brown ");
        for(int i=0;i<=2;i++)
            dataline.append(QString::number(brownMin.val[i])+" ");
        for(int i=0;i<=1;i++)
            dataline.append(QString::number(brownMax.val[i])+" ");
        dataline.append(QString::number(brownMax.val[2])+"\n");
        dataAll.append(dataline);
        dataline.clear();

        //save orange
        dataline.append("orange ");
        for(int i=0;i<=2;i++)
            dataline.append(QString::number(orangeMin.val[i])+" ");
        for(int i=0;i<=1;i++)
            dataline.append(QString::number(orangeMax.val[i])+" ");
        dataline.append(QString::number(orangeMax.val[2])+"\n");
        dataAll.append(dataline);
        dataline.clear();

        //save pink
        dataline.append("pink ");
        for(int i=0;i<=2;i++)
            dataline.append(QString::number(pinkMin.val[i])+" ");
        for(int i=0;i<=1;i++)
            dataline.append(QString::number(pinkMax.val[i])+" ");
        dataline.append(QString::number(pinkMax.val[2])+"\n");
        dataAll.append(dataline);
        dataline.clear();

        //save white
        dataline.append("white ");
        for(int i=0;i<=2;i++)
            dataline.append(QString::number(whiteMin.val[i])+" ");
        for(int i=0;i<=1;i++)
            dataline.append(QString::number(whiteMax.val[i])+" ");
        dataline.append(QString::number(whiteMax.val[2])+"\n");
        dataAll.append(dataline);
        dataline.clear();

        //save black
        dataline.append("black ");
        for(int i=0;i<=2;i++)
            dataline.append(QString::number(blackMin.val[i])+" ");
        for(int i=0;i<=1;i++)
            dataline.append(QString::number(blackMax.val[i])+" ");
        dataline.append(QString::number(blackMax.val[2])+"\n");
        dataAll.append(dataline);
        dataline.clear();

        qDebug()<<dataAll<<endl;
        file.close();
        file.open(QIODevice::WriteOnly|QIODevice::Truncate);
        QTextStream in(&file);//写入
        in << dataAll ;
        file.close();
        qDebug()<<"save successful"<<endl;
    }

    void colorGroup::showPicture(Mat &im,int de){
        image=im;
        destination=de;
    }

    //执行图像发送（或者在当前界面显示图像）线程
    void colorGroup::run(){
        if(ifRunContinueFlag){
            Mat ZoomOutimage;
            Mat Blurimage,matEdges;
<<<<<<< HEAD
            Mat transformImage;
            Mat matHSV, WebStream;
            Mat transfered_black;
            Mat img_Thr_O,gary;
            resize(image,ZoomOutimage,Size(70,60));
            resize(image,WebStream,Size(70,60));

            cvtColor(ZoomOutimage,matHSV,COLOR_BGR2HSV,0);//HSV图
            cvtColor(ZoomOutimage,gary,COLOR_BGR2GRAY,0);//HSV图

            medianBlur(matHSV,Blurimage,3);//中值滤波


            threshold(gary, img_Thr_O, 0, 255, THRESH_BINARY | THRESH_OTSU);    // 大津法自动寻求全局阈值。
            inRange(img_Thr_O,blackMin,blackMax,transfered_black);//输出图像为单通道二值图
=======
            Mat transformImage;/*,matGrey;*/
            Mat matHSV, WebStream;
            Mat transfered_black;
            resize(image,ZoomOutimage,Size(70,60));
            resize(image,WebStream,Size(70,60));
            cvtColor(ZoomOutimage,matHSV,COLOR_BGR2HSV,0);//HSV图
    //        cvtColor(ZoomOutimage,matGrey,COLOR_BGR2GRAY,0);//灰度图
            medianBlur(matHSV,Blurimage,3);//中值滤波
            inRange(Blurimage,blackMin,blackMax,transfered_black);//输出图像为单通道二值图

    //        medianBlur(matHSV,matBlur,5);//中值滤波
>>>>>>> ae1e708 (addd)
            Canny(transfered_black,matEdges,150,255,3,true);//canny边缘检测

    //sim the color mask img
            switch (color) {
                case Color::yellow:
                    inRange(Blurimage,yellowMin,yellowMax,transformImage);//输出图像为单通道二值图
                break;
                case Color::blue:
                    inRange(Blurimage,blueMin,blueMax,transformImage);//输出图像为单通道二值图
                break;
                case Color::red:
                    inRange(Blurimage,redMin,redMax,transformImage);//输出图像为单通道二值图
                break;
                case Color::green:
                    inRange(Blurimage,greenMin,greenMax,transformImage);//输出图像为单通道二值图
                break;
                case Color::purple:
                    inRange(Blurimage,purpleMin,purpleMax,transformImage);//输出图像为单通道二值图
                break;
                case Color::brown:
                    inRange(matHSV,brownMin,brownMax,transformImage);//输出图像为单通道二值图
                break;
                case Color::orange:
                    inRange(Blurimage,orangeMin,orangeMax,transformImage);//输出图像为单通道二值图
                break;
                case Color::pink:
                    inRange(Blurimage,pinkMin,pinkMax,transformImage);//输出图像为单通道二值图
                break;
                case Color::white:
                    inRange(Blurimage,whiteMin,whiteMax,transformImage);//输出图像为单通道二值图
                break;
                case Color::black:
                    inRange(Blurimage,blackMin,blackMax,transformImage);//输出图像为单通道二值图
                break;
            }
            if(destination==0){
                imshow("原图",ZoomOutimage);
                waitKey(1);
                imshow("二值图像",transformImage);
                waitKey(1);
                imshow("循迹图像",matEdges);
                waitKey(1);

            }else if(destination==1){
                imencode(".jpg",Blurimage,data_encode,parameter);
                for (unsigned int i = 0; i < data_encode.size(); i++){
                    msg[i] = data_encode[i];
                }
                udpsocket.writeDatagram(msg, QHostAddress("192.168.12.209"), 30015);
                imencode(".jpg",transformImage,data_encode,parameter);
                for (unsigned int i = 0; i < data_encode.size(); i++){
                    msg[i] = data_encode[i];
                }
                udpsocket.writeDatagram(msg, QHostAddress("192.168.12.209"), 30016);

                imencode(".jpg",matEdges,data_encode,parameter);
                for (unsigned int i = 0; i < data_encode.size(); i++){
                    msg[i] = data_encode[i];
                }
                udpsocket.writeDatagram(msg, QHostAddress("192.168.12.209"), 30018);
            }
        }
    }

    //发送当前的阈值信息到上位机
    void colorGroup::sendColorThreadhold(){
        switch (color) {
            case Color::yellow://yellow
                for(int i=0;i<3;i++)
                    msg[i]=yellowMin.val[i];
                for(int i=0;i<3;i++)
                    msg[i+3]=yellowMax.val[i];
            break;
            case Color::blue://blue
                for(int i=0;i<3;i++)
                    msg[i]=blueMin.val[i];
                for(int i=0;i<3;i++)
                    msg[i+3]=blueMax.val[i];
            break;
            case Color::red://red
                for(int i=0;i<3;i++)
                    msg[i]=redMin.val[i];
                for(int i=0;i<3;i++)
                    msg[i+3]=redMax.val[i];
            break;
            case Color::green://green
                for(int i=0;i<3;i++)
                    msg[i]=greenMin.val[i];
                for(int i=0;i<3;i++)
                    msg[i+3]=greenMax.val[i];
            break;
            case Color::purple://purple
                for(int i=0;i<3;i++)
                    msg[i]=purpleMin.val[i];
                for(int i=0;i<3;i++)
                    msg[i+3]=purpleMax.val[i];
            break;
            case Color::brown://brown
                for(int i=0;i<3;i++)
                    msg[i]=brownMin.val[i];
                for(int i=0;i<3;i++)
                    msg[i+3]=brownMax.val[i];
            break;
            case Color::orange://orange
                for(int i=0;i<3;i++)
                    msg[i]=orangeMin.val[i];
                for(int i=0;i<3;i++)
                    msg[i+3]=orangeMax.val[i];
            break;
            case Color::pink://pink
                for(int i=0;i<3;i++)
                    msg[i]=pinkMin.val[i];
                for(int i=0;i<3;i++)
                    msg[i+3]=pinkMax.val[i];
            break;
            case Color::white://white
                for(int i=0;i<3;i++)
                    msg[i]=whiteMin.val[i];
                for(int i=0;i<3;i++)
                    msg[i+3]=whiteMax.val[i];
            break;
            case Color::black://black
                for(int i=0;i<3;i++)
                    msg[i]=blackMin.val[i];
                for(int i=0;i<3;i++)
                    msg[i+3]=blackMax.val[i];
            break;
        }
        udpsocket.writeDatagram(msg, QHostAddress("192.168.12.209"), 30017);
    }

    //选择当前的颜色
    void colorGroup::chooseColor(int number){
        switch (number) {
            case 0:
                color=Color::yellow;
            break;
            case 1:
                color=Color::blue;
            break;
            case 2:
                color=Color::red;
            break;
            case 3:
                color=Color::green;
            break;
            case 4:
                color=Color::purple;
            break;
            case 5:
                color=Color::brown;
            break;
            case 6:
                color=Color::orange;
            break;
            case 7:
                color=Color::pink;
            break;
            case 8:
                color=Color::white;
            break;
            case 9:
                color=Color::black;
            break;
        }
    }
    //设置颜色的阈值
    void colorGroup::setColorThreadhold(QByteArray colorarray){
        switch (color) {
            case Color::yellow:
                for(int i=0;i<=2;i++)
                    yellowMin.val[i]=colorarray[i];
                for(int i=0;i<=2;i++)
                    yellowMax.val[i]=colorarray[i+3];
            break;
            case Color::blue:
                for(int i=0;i<=2;i++)
                    blueMin.val[i]=colorarray[i];
                for(int i=0;i<=2;i++)
                    blueMax.val[i]=colorarray[i+3];
            break;
            case Color::red:
                for(int i=0;i<=2;i++)
                    redMin.val[i]=colorarray[i];
                for(int i=0;i<=2;i++)
                    redMax.val[i]=colorarray[i+3];
            break;
            case Color::green:
                for(int i=0;i<=2;i++)
                    greenMin.val[i]=colorarray[i];
                for(int i=0;i<=2;i++)
                    greenMax.val[i]=colorarray[i+3];
            break;
            case Color::purple:
                for(int i=0;i<=2;i++)
                    purpleMin.val[i]=colorarray[i];
                for(int i=0;i<=2;i++)
                    purpleMax.val[i]=colorarray[i+3];
            break;
            case Color::brown:
                for(int i=0;i<=2;i++)
                    brownMin.val[i]=colorarray[i];
                for(int i=0;i<=2;i++)
                    brownMax.val[i]=colorarray[i+3];
            break;
            case Color::orange:
                for(int i=0;i<=2;i++)
                    orangeMin.val[i]=colorarray[i];
                for(int i=0;i<=2;i++)
                    orangeMax.val[i]=colorarray[i+3];
            break;
            case Color::pink:
                for(int i=0;i<=2;i++)
                   pinkMin.val[i]=colorarray[i];
                for(int i=0;i<=2;i++)
                   pinkMax.val[i]=colorarray[i+3];
            break;
            case Color::white:
                for(int i=0;i<=2;i++)
                    whiteMin.val[i]=colorarray[i];
                for(int i=0;i<=2;i++)
                    whiteMax.val[i]=colorarray[i+3];
            break;
            case Color::black:
                for(int i=0;i<=2;i++)
                   blackMin.val[i]=colorarray[i];
                for(int i=0;i<=2;i++)
                   blackMax.val[i]=colorarray[i+3];
            break;
        }
    }
