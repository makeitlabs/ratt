#!/bin/sh
# put up some text in a specific spot on the screen that raspi2fb will "see"
# to inform user about app start/stop status
tput -T linux clear > /dev/tty1
tput -T linux civis > /dev/tty1
echo > /dev/tty1
echo "                                                       Starting RATT App" > /dev/tty1
echo "                                                         Please wait..." > /dev/tty1

