Quick and test demonstrating both qt5 widgets rendering direct to linux framebuffer (/dev/fb1 SPI TFT) reacting to linux key events.

To build:

qmake ; make

To run:

> QT_QPA_PLATFORM=linuxfb:fb=/dev/fb1 ./qt5-keypad 

Or run as root and redirect output to /dev/tty1 to turn off blinking console cursor:

> QT_QPA_PLATFORM=linuxfb:fb=/dev/fb1 ./qt5-keypad > /dev/tty1
