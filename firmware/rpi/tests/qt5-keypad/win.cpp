#include <QDebug>
#include "win.h"

// quick and dirty test to show qt reacting to key events
// steve.richardson@makeitlabs.com

Win::Win(QWidget* parent) :
    QWidget(parent)

{
    escWidget = new QLabel(QString("\u21ba"), this);
    escWidget->move(0, 100);
    escWidget->resize(40,27);
    escWidget->setFrameStyle(QFrame::Panel | QFrame::Raised);
    escWidget->setAlignment(Qt::AlignHCenter | Qt::AlignVCenter);
    downWidget = new QLabel(QString("\u25bc"), this);
    downWidget->move(40, 100);
    downWidget->resize(40,27);
    downWidget->setFrameStyle(QFrame::Panel | QFrame::Raised);
    downWidget->setAlignment(Qt::AlignHCenter | Qt::AlignVCenter);
    upWidget = new QLabel(QString("\u25b2"), this);
    upWidget->move(80, 100);
    upWidget->resize(40,27);
    upWidget->setFrameStyle(QFrame::Panel | QFrame::Raised);
    upWidget->setAlignment(Qt::AlignHCenter | Qt::AlignVCenter);
    enterWidget = new QLabel(QString("\u23ce"), this);
    enterWidget->move(120,100);
    enterWidget->resize(40,27);
    enterWidget->setFrameStyle(QFrame::Panel | QFrame::Raised);
    enterWidget->setAlignment(Qt::AlignHCenter | Qt::AlignVCenter);
}

Win::~Win()
{
    escWidget->deleteLater();
    downWidget->deleteLater();
    upWidget->deleteLater();
    enterWidget->deleteLater();
}


void Win::keyPressEvent(QKeyEvent* event)
{
    qDebug() << "key press code=" << event->key();

    switch (event->key()) {
    case Qt::Key_Escape:
        escWidget->setLineWidth(4);
        break;
    case Qt::Key_Down:
        downWidget->setLineWidth(4);
        break;
    case Qt::Key_Up:
        upWidget->setLineWidth(4);
        break;
    case Qt::Key_Return:
        enterWidget->setLineWidth(4);
        break;
    }
        
}

void Win::keyReleaseEvent(QKeyEvent* event)
{
    qDebug() << "key release code=" << event->key();

    switch (event->key()) {
    case Qt::Key_Escape:
        escWidget->setLineWidth(2);
        break;
    case Qt::Key_Down:
        downWidget->setLineWidth(2);
        break;
    case Qt::Key_Up:
        upWidget->setLineWidth(2);
        break;
    case Qt::Key_Return:
        enterWidget->setLineWidth(2);
        break;
    }
        
}

