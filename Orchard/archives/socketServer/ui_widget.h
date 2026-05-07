/********************************************************************************
** Form generated from reading UI file 'widget.ui'
**
** Created by: Qt User Interface Compiler version 5.10.0
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_WIDGET_H
#define UI_WIDGET_H

#include <QtCore/QVariant>
#include <QtWidgets/QAction>
#include <QtWidgets/QApplication>
#include <QtWidgets/QButtonGroup>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QGroupBox>
#include <QtWidgets/QHeaderView>
#include <QtWidgets/QLabel>
#include <QtWidgets/QLineEdit>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QSlider>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_Widget
{
public:
    QGroupBox *groupBox_3;
    QSlider *horizontalSlider_low1;
    QSlider *horizontalSlider_low2;
    QSlider *horizontalSlider_low3;
    QSlider *horizontalSlider_high1;
    QSlider *horizontalSlider_high2;
    QSlider *horizontalSlider_high3;
    QLineEdit *lineEdit_low1;
    QLineEdit *lineEdit_low2;
    QLineEdit *lineEdit_low3;
    QLineEdit *lineEdit_high1;
    QLineEdit *lineEdit_high2;
    QLineEdit *lineEdit_high3;
    QLabel *label;
    QLabel *label_2;
    QLabel *label_3;
    QLabel *label_5;
    QLabel *label_4;
    QLabel *label_6;
    QLabel *label_7;
    QLabel *label_8;
    QComboBox *chooseBox;
    QPushButton *saveBtn;
    QPushButton *sendBtn;

    void setupUi(QWidget *Widget)
    {
        if (Widget->objectName().isEmpty())
            Widget->setObjectName(QStringLiteral("Widget"));
        Widget->setEnabled(true);
        Widget->resize(950, 235);
        Widget->setMinimumSize(QSize(0, 0));
        groupBox_3 = new QGroupBox(Widget);
        groupBox_3->setObjectName(QStringLiteral("groupBox_3"));
        groupBox_3->setGeometry(QRect(40, 15, 751, 191));
        horizontalSlider_low1 = new QSlider(groupBox_3);
        horizontalSlider_low1->setObjectName(QStringLiteral("horizontalSlider_low1"));
        horizontalSlider_low1->setGeometry(QRect(60, 60, 240, 15));
        horizontalSlider_low1->setMaximum(255);
        horizontalSlider_low1->setOrientation(Qt::Horizontal);
        horizontalSlider_low2 = new QSlider(groupBox_3);
        horizontalSlider_low2->setObjectName(QStringLiteral("horizontalSlider_low2"));
        horizontalSlider_low2->setGeometry(QRect(60, 100, 240, 15));
        horizontalSlider_low2->setMaximum(255);
        horizontalSlider_low2->setOrientation(Qt::Horizontal);
        horizontalSlider_low3 = new QSlider(groupBox_3);
        horizontalSlider_low3->setObjectName(QStringLiteral("horizontalSlider_low3"));
        horizontalSlider_low3->setGeometry(QRect(60, 140, 240, 15));
        horizontalSlider_low3->setMaximum(255);
        horizontalSlider_low3->setOrientation(Qt::Horizontal);
        horizontalSlider_high1 = new QSlider(groupBox_3);
        horizontalSlider_high1->setObjectName(QStringLiteral("horizontalSlider_high1"));
        horizontalSlider_high1->setGeometry(QRect(430, 60, 240, 15));
        horizontalSlider_high1->setMaximum(255);
        horizontalSlider_high1->setOrientation(Qt::Horizontal);
        horizontalSlider_high2 = new QSlider(groupBox_3);
        horizontalSlider_high2->setObjectName(QStringLiteral("horizontalSlider_high2"));
        horizontalSlider_high2->setGeometry(QRect(430, 100, 240, 15));
        horizontalSlider_high2->setMaximum(255);
        horizontalSlider_high2->setOrientation(Qt::Horizontal);
        horizontalSlider_high3 = new QSlider(groupBox_3);
        horizontalSlider_high3->setObjectName(QStringLiteral("horizontalSlider_high3"));
        horizontalSlider_high3->setGeometry(QRect(430, 140, 240, 15));
        horizontalSlider_high3->setMaximum(255);
        horizontalSlider_high3->setOrientation(Qt::Horizontal);
        lineEdit_low1 = new QLineEdit(groupBox_3);
        lineEdit_low1->setObjectName(QStringLiteral("lineEdit_low1"));
        lineEdit_low1->setGeometry(QRect(310, 55, 41, 25));
        lineEdit_low2 = new QLineEdit(groupBox_3);
        lineEdit_low2->setObjectName(QStringLiteral("lineEdit_low2"));
        lineEdit_low2->setGeometry(QRect(310, 95, 41, 25));
        lineEdit_low3 = new QLineEdit(groupBox_3);
        lineEdit_low3->setObjectName(QStringLiteral("lineEdit_low3"));
        lineEdit_low3->setGeometry(QRect(310, 135, 41, 25));
        lineEdit_high1 = new QLineEdit(groupBox_3);
        lineEdit_high1->setObjectName(QStringLiteral("lineEdit_high1"));
        lineEdit_high1->setGeometry(QRect(690, 55, 41, 25));
        lineEdit_high2 = new QLineEdit(groupBox_3);
        lineEdit_high2->setObjectName(QStringLiteral("lineEdit_high2"));
        lineEdit_high2->setGeometry(QRect(690, 95, 41, 25));
        lineEdit_high3 = new QLineEdit(groupBox_3);
        lineEdit_high3->setObjectName(QStringLiteral("lineEdit_high3"));
        lineEdit_high3->setGeometry(QRect(690, 135, 41, 25));
        label = new QLabel(groupBox_3);
        label->setObjectName(QStringLiteral("label"));
        label->setGeometry(QRect(150, 40, 67, 16));
        label_2 = new QLabel(groupBox_3);
        label_2->setObjectName(QStringLiteral("label_2"));
        label_2->setGeometry(QRect(540, 40, 67, 17));
        label_3 = new QLabel(groupBox_3);
        label_3->setObjectName(QStringLiteral("label_3"));
        label_3->setGeometry(QRect(10, 59, 51, 16));
        label_5 = new QLabel(groupBox_3);
        label_5->setObjectName(QStringLiteral("label_5"));
        label_5->setGeometry(QRect(10, 98, 51, 16));
        label_4 = new QLabel(groupBox_3);
        label_4->setObjectName(QStringLiteral("label_4"));
        label_4->setGeometry(QRect(10, 135, 51, 20));
        label_6 = new QLabel(groupBox_3);
        label_6->setObjectName(QStringLiteral("label_6"));
        label_6->setGeometry(QRect(380, 59, 51, 16));
        label_7 = new QLabel(groupBox_3);
        label_7->setObjectName(QStringLiteral("label_7"));
        label_7->setGeometry(QRect(380, 98, 51, 16));
        label_8 = new QLabel(groupBox_3);
        label_8->setObjectName(QStringLiteral("label_8"));
        label_8->setGeometry(QRect(380, 135, 51, 20));
        chooseBox = new QComboBox(Widget);
        chooseBox->addItem(QString());
        chooseBox->addItem(QString());
        chooseBox->addItem(QString());
        chooseBox->addItem(QString());
        chooseBox->addItem(QString());
        chooseBox->addItem(QString());
        chooseBox->addItem(QString());
        chooseBox->addItem(QString());
        chooseBox->addItem(QString());
        chooseBox->addItem(QString());
        chooseBox->setObjectName(QStringLiteral("chooseBox"));
        chooseBox->setGeometry(QRect(820, 35, 101, 41));
        saveBtn = new QPushButton(Widget);
        saveBtn->setObjectName(QStringLiteral("saveBtn"));
        saveBtn->setGeometry(QRect(820, 165, 101, 41));
        sendBtn = new QPushButton(Widget);
        sendBtn->setObjectName(QStringLiteral("sendBtn"));
        sendBtn->setGeometry(QRect(820, 100, 101, 41));

        retranslateUi(Widget);

        QMetaObject::connectSlotsByName(Widget);
    } // setupUi

    void retranslateUi(QWidget *Widget)
    {
        Widget->setWindowTitle(QApplication::translate("Widget", "Widget", nullptr));
        groupBox_3->setTitle(QApplication::translate("Widget", "\350\260\203\350\212\202\351\230\210\345\200\274", nullptr));
        label->setText(QApplication::translate("Widget", "\344\275\216\351\230\210\345\200\274", nullptr));
        label_2->setText(QApplication::translate("Widget", "\351\253\230\351\230\210\345\200\274", nullptr));
        label_3->setText(QApplication::translate("Widget", "\351\200\232\351\201\223\344\270\200", nullptr));
        label_5->setText(QApplication::translate("Widget", "\351\200\232\351\201\223\344\272\214\n"
"", nullptr));
        label_4->setText(QApplication::translate("Widget", "\351\200\232\351\201\223\344\270\211", nullptr));
        label_6->setText(QApplication::translate("Widget", "\351\200\232\351\201\223\344\270\200", nullptr));
        label_7->setText(QApplication::translate("Widget", "\351\200\232\351\201\223\344\272\214", nullptr));
        label_8->setText(QApplication::translate("Widget", "\351\200\232\351\201\223\344\270\211", nullptr));
        chooseBox->setItemText(0, QApplication::translate("Widget", "yellow", nullptr));
        chooseBox->setItemText(1, QApplication::translate("Widget", "blue", nullptr));
        chooseBox->setItemText(2, QApplication::translate("Widget", "red", nullptr));
        chooseBox->setItemText(3, QApplication::translate("Widget", "green", nullptr));
        chooseBox->setItemText(4, QApplication::translate("Widget", "purple", nullptr));
        chooseBox->setItemText(5, QApplication::translate("Widget", "brown", nullptr));
        chooseBox->setItemText(6, QApplication::translate("Widget", "orange", nullptr));
        chooseBox->setItemText(7, QApplication::translate("Widget", "pink", nullptr));
        chooseBox->setItemText(8, QApplication::translate("Widget", "white", nullptr));
        chooseBox->setItemText(9, QApplication::translate("Widget", "black", nullptr));

        saveBtn->setText(QApplication::translate("Widget", "\344\277\235\345\255\230", nullptr));
        sendBtn->setText(QApplication::translate("Widget", "\347\241\256\345\256\232", nullptr));
    } // retranslateUi

};

namespace Ui {
    class Widget: public Ui_Widget {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_WIDGET_H
