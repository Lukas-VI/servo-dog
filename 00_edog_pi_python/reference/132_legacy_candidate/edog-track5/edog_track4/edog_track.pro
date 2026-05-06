QT += network
QT -= gui

CONFIG += c++11 console
CONFIG -= app_bundle

# The following define makes your compiler emit warnings if you use
# any feature of Qt which as been marked deprecated (the exact warnings
# depend on your compiler). Please consult the documentation of the
# deprecated API in order to know how to port your code away from it.
DEFINES += QT_DEPRECATED_WARNINGS

# You can also make your code fail to compile if you use deprecated APIs.
# In order to do so, uncomment the following line.
# You can also select to disable deprecated APIs only up to a certain version of Qt.
#DEFINES += QT_DISABLE_DEPRECATED_BEFORE=0x060000    # disables all the APIs deprecated before Qt 6.0.0

SOURCES += main.cpp \
    lcmutil.cpp \
    colorgroup.cpp \
    mythread.cpp \
    udputil.cpp \
    bridge.cpp

HEADERS += \
    lcmutil.h \
    colorgroup.h \
    mythread.h \
    udputil.h \
    bridge.h
#导入lcm 的库
INCLUDEPATH += ./LCM
INCLUDEPATH += /usr/local/include
LIBS += -L/usr/local/lib/ -llcm
#导入opencv 的库
INCLUDEPATH += /usr/local/include
LIBS += /usr/local/lib/libopencv_videoio.so \
    -lopencv_core \
    -lopencv_features2d \
    -lopencv_flann \
    -lopencv_highgui \
    -lopencv_imgproc \
    -lopencv_ml \
    -lopencv_objdetect \
    -lopencv_photo \
    -lopencv_stitching \
    -lopencv_video

LIBS +=/usr/local/lib/libopencv_core.so
LIBS +=/usr/local/lib/libopencv_imgcodecs.so
