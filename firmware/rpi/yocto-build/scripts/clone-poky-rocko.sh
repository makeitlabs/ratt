#!/bin/sh
DEST_DIR="/u/rpi"

if [ -f "${DEST_DIR}/poky-rocko" ]; then
  echo "${DEST_DIR}/poky-rocko already exists, bailing out so you can sort it out"
  exit 1
else
  mkdir -p ${DEST_DIR}
  cd ${DEST_DIR}
  git clone -b rocko git://git.yoctoproject.org/poky.git poky-rocko
  cd poky-rocko
  git clone -b rocko git://git.openembedded.org/meta-openembedded
  git clone -b rocko https://github.com/meta-qt5/meta-qt5
  git clone -b rocko git://git.yoctoproject.org/meta-security
  git clone -b rocko git://git.yoctoproject.org/meta-raspberrypi
fi
 
