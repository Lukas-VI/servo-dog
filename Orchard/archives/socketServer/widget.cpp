#include "widget.h"
#include "ui_widget.h"
#include <QNetworkInterface>
Widget::Widget(QWidget *parent)
    : QWidget(parent)
    , ui(new Ui::Widget)
{
    ui->setupUi(this);
    ui->lineEdit_low1->setText("0");
    ui->lineEdit_low2->setText("0");
    ui->lineEdit_low3->setText("0");
    ui->lineEdit_high1->setText("0");
    ui->lineEdit_high2->setText("0");
    ui->lineEdit_high3->setText("0");
    colorThreadhold[0]=1;//mode is set colorthreadhold
    initSocket();
}

Widget::~Widget()
{
    delete ui;
}
//receive Original image
void Widget::receive(){
    QByteArray ba;
    vector<unsigned char> data(50000);
    Mat image;
    while(udpSocket->hasPendingDatagrams())
    {
        ba.resize(udpSocket->pendingDatagramSize());
        udpSocket->readDatagram(ba.data(), ba.size());
        for(int i=0;i<ba.size();i++){
            data[i]=ba[i];
        }
        image = imdecode(data,IMREAD_COLOR);//图像解码
//        MatToQimageAndShowOriginal(image);
        imshow("原始图像",image);
        waitKey(1);
//        ui->receiveEdit->append(ba);
    }
}
//receive Binarization image
void Widget::receive2(){
    QByteArray ba;
    vector<unsigned char> data(50000);
    Mat image;
    while(udpSocket2->hasPendingDatagrams())
    {
        ba.resize(udpSocket2->pendingDatagramSize());
        udpSocket2->readDatagram(ba.data(), ba.size());
        for(int i=0;i<ba.size();i++){
            data[i]=ba[i];
        }
        image = imdecode(data,IMREAD_COLOR);//图像解码
//        MatToQimageAndShowBinarization(image);
        imshow("二值化后图像",image);
        waitKey(1);
//        ui->receiveEdit->append(ba);
    }
}
//receive first threadhold
void Widget::receive3(){
    QByteArray ba;
    unsigned char bb[6];
    while(udpSocket3->hasPendingDatagrams()){
        ba.resize(udpSocket3->pendingDatagramSize());
        udpSocket3->readDatagram(ba.data(), ba.size());
        for(int i=0;i<=5;i++){
            bb[i]=ba[i];
             colorThreadhold[i+1]=ba[i];
        }
        ui->horizontalSlider_low1->setValue(bb[0]);
        ui->horizontalSlider_low2->setValue(bb[1]);
        ui->horizontalSlider_low3->setValue(bb[2]);
        ui->horizontalSlider_high1->setValue(bb[3]);
        ui->horizontalSlider_high2->setValue(bb[4]);
        ui->horizontalSlider_high3->setValue(bb[5]);

    }
}
//receive Binarization image
void Widget::receive4(){
    QByteArray ba;
    vector<unsigned char> data(50000);
    Mat image;
    while(udpSocket4->hasPendingDatagrams())
    {
        ba.resize(udpSocket4->pendingDatagramSize());
        udpSocket4->readDatagram(ba.data(), ba.size());
        for(int i=0;i<ba.size();i++){
            data[i]=ba[i];
        }
        image = imdecode(data,IMREAD_COLOR);//图像解码
        imshow("循迹图像",image);
        waitKey(1);
    }
}
void Widget::initSocket(){
    QList<QHostAddress> list = QNetworkInterface::allAddresses();//所有地址的合集，其中list[2]为无线网卡地址
    udpSocket = new QUdpSocket(this);//套接字句柄
    udpSocket2= new QUdpSocket(this);
    udpSocket3= new QUdpSocket(this);
    udpSocket4= new QUdpSocket(this);
    udpSocket->bind(list[2], 30015);
    udpSocket2->bind(list[2], 30016);
    udpSocket3->bind(list[2], 30017);
    udpSocket4->bind(list[2], 30018);
    connect(udpSocket, SIGNAL(readyRead()), this, SLOT(receive()));
    connect(udpSocket2, SIGNAL(readyRead()), this, SLOT(receive2()));
    connect(udpSocket3, SIGNAL(readyRead()), this, SLOT(receive3()));
    connect(udpSocket4, SIGNAL(readyRead()), this, SLOT(receive4()));
}

void Widget::on_horizontalSlider_low1_valueChanged(int value)
{
    ui->lineEdit_low1->setText(QString::number(value));
    colorThreadhold[1]= value;
    udpSocket->writeDatagram(colorThreadhold,QHostAddress("192.168.12.1"),8000);
}

void Widget::on_horizontalSlider_low2_valueChanged(int value)
{
    ui->lineEdit_low2->setText(QString::number(value));
    colorThreadhold[2]= value;
    udpSocket->writeDatagram(colorThreadhold,QHostAddress("192.168.12.1"),8000);
}

void Widget::on_horizontalSlider_low3_valueChanged(int value)
{
    ui->lineEdit_low3->setText(QString::number(value));
    colorThreadhold[3]= value;
    udpSocket->writeDatagram(colorThreadhold,QHostAddress("192.168.12.1"),8000);
}

void Widget::on_horizontalSlider_high1_valueChanged(int value)
{
    ui->lineEdit_high1->setText(QString::number(value));
    colorThreadhold[4]= value;
    udpSocket->writeDatagram(colorThreadhold,QHostAddress("192.168.12.1"),8000);
}

void Widget::on_horizontalSlider_high2_valueChanged(int value)
{
    ui->lineEdit_high2->setText(QString::number(value));
    colorThreadhold[5]= value;
    udpSocket->writeDatagram(colorThreadhold,QHostAddress("192.168.12.1"),8000);
}

void Widget::on_horizontalSlider_high3_valueChanged(int value)
{
    ui->lineEdit_high3->setText(QString::number(value));
    colorThreadhold[6]= value;
    udpSocket->writeDatagram(colorThreadhold,QHostAddress("192.168.12.1"),8000);
}

void Widget::on_saveBtn_clicked()
{
    QByteArray msg;
    msg[0]=2;//2 is save;
    udpSocket->writeDatagram(msg,QHostAddress("192.168.12.1"),8000);
}

void Widget::on_sendBtn_clicked()
{
    int index; //0=yellow 1=blue 2=red 3=green 4=purple 5=brown 6=orange 7=pink  8=white  9=black
    index=ui->chooseBox->currentIndex();
    qDebug()<<"颜色:"<< ui->chooseBox->currentText()<<endl;
//    qDebug()<<"颜色:"<< index<<endl;
    QByteArray msg;
    msg[0]=0;//0 is color;
    msg[1]=index;
    qDebug()<<"颜色序号:"<<index<<endl;
    udpSocket->writeDatagram(msg,QHostAddress("192.168.12.1"),8000);
//   qDebug()<<"颜色序号:"<< msg[1]<<endl;

}
