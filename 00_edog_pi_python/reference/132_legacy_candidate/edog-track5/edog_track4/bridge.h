#ifndef BRIDGE_H
#define BRIDGE_H

#include <opencv2/opencv.hpp>
#include <QDebug>
using namespace cv;

bool judgmentLeft(Mat &image,int i,int j);
bool judgmentRight(Mat &image,int i,int j);
int getAverage(Mat &frame);


#endif // BRIDGE_H
