#!/bin/sh
DEST_DIR="/u/rpi"
POKY="poky-sumo"
SOURCES_DIR="oe-sources"
TMP_DIR="tmp"

if [ ! -d "${DEST_DIR}/${SOURCES_DIR}" ]; then
    mkdir -p ${DEST_DIR}/${SOURCES_DIR}
    echo "Created ${DEST_DIR}/${SOURCES_DIR} directory for OpenEmbedded sources."
else
    echo "Good, you appear to have a sources directory at ${DEST_DIR}/${SOURCES_DIR}."
fi

if [ ! -d "${DEST_DIR}/${TMP_DIR}" ]; then
    mkdir -p ${DEST_DIR}/${TMP_DIR}
    echo "Created ${DEST_DIR}/${TMP_DIR} directory as a temporary build directory."
else
    echo "Good, you appear to have a temporary build directory at ${DEST_DIR}/${TMP_DIR}"
fi

if [ -d "${DEST_DIR}/${POKY}" ]; then
    echo "Not cloning ${POKY} because ${DEST_DIR}/${POKY} already exists - bailing out so you can sort it out."
    exit 1
else
    echo "Cloning ${POKY} into ${DEST_DIR}/${POKY}..."
    mkdir -p ${DEST_DIR}
    cd ${DEST_DIR}
    git clone -b sumo git://git.yoctoproject.org/poky.git ${POKY}
    cd ${POKY}
    echo "Cloning dependency directories..."
    git clone -b sumo git://git.openembedded.org/meta-openembedded
    git clone -b sumo https://github.com/meta-qt5/meta-qt5
    git clone -b sumo git://git.yoctoproject.org/meta-security
    git clone -b sumo git://git.yoctoproject.org/meta-raspberrypi
fi
 
