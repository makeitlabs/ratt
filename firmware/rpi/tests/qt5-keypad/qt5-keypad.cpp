
#include <QApplication>
#include <QPushButton>
#include <QWidget>
#include "win.h"

int main( int argc, char **argv )
{
    QApplication a( argc, argv );
    Win window;

    window.resize(160,128);
    window.show();
    
    return a.exec();
}
