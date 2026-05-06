
#include "bridge.h"


bool judgmentLeft(Mat &image,int i,int j){
    if((int)image.at<uchar>(i,j)==0){
        if((int)image.at<uchar>(i,j+3)==255&&(int)image.at<uchar>(i,j+5)==255)
            return true;
        else
            return false;
    }else if((int)image.at<uchar>(i,j)==255&&j==0){
        if((int)image.at<uchar>(i,j+3)==255&&(int)image.at<uchar>(i,j+5)==255)
            return true;
        else
            return false;
    }else{
        return false;
    }
}
bool judgmentRight(Mat &image,int i,int j){
    if((int)image.at<uchar>(i,j)==0){
        if((int)image.at<uchar>(i,j-3)==255&&(int)image.at<uchar>(i,j-5)==255)
            return true;
        else
            return false;
    }else if((int)image.at<uchar>(i,j)==255&&j==79){
        if((int)image.at<uchar>(i,j-3)==255&&(int)image.at<uchar>(i,j-5)==255)
            return true;
        else
            return false;
    }else{
        return false;
    }
}

int getAverage(Mat &frame){
    int average=40;//中线均值
    int number=0;
    int value[150]={0};//存储每个点对应的x轴对应的值
    float sum=0;
    int left[480]={0};//存储左侧边缘
    float middle[480]={0};//存储中线
    int right[480]={0};//存储右侧边缘

    //提取赛道左侧边缘
//    qDebug()<<"frame:" << frame.rows  <<endl;
    for(int i=0;i<frame.rows;i++){//
        for(int j=0;j<frame.cols-3;j++){//-3
            if(judgmentLeft(frame,i,j)){
                if(j==0)
                    left[i]=1;//
                else
                    left[i]=j;

                break;
            }
        }
    }
    //提取赛道右侧边缘
    for(int i=0;i<frame.rows;i++){
        for(int j=frame.cols-1;j>=3;j--){//-1
            if(judgmentRight(frame,i,j)){
                right[i]=j;
                break;
            }
        }
    }

    //提取中线,并将中线绘制到图上
    number=0;
//    for(int i=0;i<(frame.rows/2.0);i++){
//        if((left[i]<(left[i+1]+4))&&(left[i]>(left[i+1]-4))&&(left[i]!=0))
//            if((right[i]<(right[i+1]+4))&&(right[i]>(right[i+1]-4))&&(right[i]!=0)){
//                middle[i]=(left[i]+right[i])/2.0;
//                frame.at<uchar>(i,(int)middle[i])=0;
//                value[number]=middle[i];
//                number++;
//                 qDebug()<<"number:" << number  <<endl;
//            }
//    }
    //计算中线平均值
//    qDebug()<<"number:" << number  <<endl;
    sum=0;
    if(number!=0){
        for(int i=0;i<number;i++){
            sum=sum+value[i];
        }
//        qDebug()<<"sum:" << sum  <<endl;
        average=sum/number;
        qDebug()<<"averageMID:" << average  <<endl;
        //限幅
        if(average<=80&&average>=0){

        }else{
            average=0;//40;
        }
    }
    return average;
}
