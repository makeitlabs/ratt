# Building RATT Image with Yocto/OpenEmbedded

Based on http://www.jumpnowtek.com/rpi/Raspberry-Pi-Systems-with-Yocto.html

## Pre-requisites

Start with Ubuntu 16.04.3 LTS image running in a virtual machine.

### Set up a work directory in `/u` (with `/tmp`-like permissions)

    mkdir /u
    chmod 777 /u
    chmod o+t /u

### Install some pre-requisites for building:

    sudo apt install build-essential chrpath diffstat gawk libncurses5-dev texinfo python2.7 git

### Ensure python2.7 has links (16.04.3 had them already):

    steve@ubuntu:~$ ls -al /usr/bin/python
    lrwxrwxrwx 1 root root 9 Feb  8 05:47 /usr/bin/python -> python2.7
    steve@ubuntu:~$ ls -al /usr/bin/python2
    lrwxrwxrwx 1 root root 9 Feb  8 05:47 /usr/bin/python2 -> python2.7
    steve@ubuntu:~$

### Ensure 'dash' is disabled on Ubuntu:
    sudo dpkg-reconfigure dash

Choose No to dash when prompted.

### Clone the RATT repo

Some directories have fixed paths with `${HOME}` references for the Yocto build, so it is necessary to clone it into your home directory, i.e. `~/ratt` - do not place it inside of other directories or in other locations.

    cd ~
    git clone https://github.com/makeitlabs/ratt.git

### Make a local clone of the Yocto poky-rocko branch from github

I've included a script to do the dirty work in `~/ratt/firmware/rpi/yocto-build/scripts/clone-poky-rocko.sh`

### Check that the meta-ratt submodule was initialized

Some versions of git will not automatically initialize submodules.  If `~/ratt/firmware/rpi/meta-ratt` is empty after your initial git clone, do this:

    cd ~/ratt/firmware/rpi
    git submodule update --init --recursive

### Make a central directory for downloaded source files:

    mkdir /u/rpi/oe-sources
    
_Note that this location is controlled with the variable `DL_DIR` in `~/ratt/firmware/rpi/yocto-build/conf/local.conf`_

### Set up a temporary build directory for Yocto

    mkdir /u/rpi/tmp

_Note that this location is controlled with the variable `TMPDIR` in `~/ratt/firmware/rpi/yocto-build/conf/local.conf`_

## Building

### Source the yocto environment before running bitbake

    source /u/rpi/poky-rocko/oe-init-build-env ~/ratt/firmware/rpi/yocto-build

_Ignore the common target text that is spit out here - we don't build those targets._

### Start a build of the RATT image

    bitbake ratt-image

_Wait a long time... 2-3 hours typically_

## Copying to SD Card

Insert the SD card into your reader, and make sure the USB device is attached to the Virtual Machine.

### Find the device with a combination of dmesg/lsblk

    steve@ubuntu:~/rpi/meta-rpi/scripts$ lsblk
    NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
    sdf      8:80   1  3.7G  0 disk
    ├─sdf1   8:81   1   64M  0 part 
    └─sdf2   8:82   1  3.6G  0 part 
    sr0     11:0    1 1024M  0 rom  
    sda      8:0    0  100G  0 disk 
    ├─sda2   8:2    0    1K  0 part 
    ├─sda5   8:5    0    8G  0 part [SWAP]
    └─sda1   8:1    0   92G  0 part /

_SD device is /dev/sdf in the above example, but it may appear in a different place on your machine_

### Make Partitions

Use the meta-rpi script to make the two necessary partitions on the SD card (need to know device above)

    cd ~/ratt/firmware/rpi/meta-rpi/scripts
    sudo ./mk2parts.sh sdf

### Make a temporary mount point

Some of the utility scripts have this mount point hard coded, so make sure it exists.

    sudo mkdir /media/card

### Copy boot partition:

_Note, replace `sdf` with your actual SD card device, and be careful!_

    source ~/ratt_card_env.sh
    ./copy_boot.sh sdf

### Copy root filesystem:

_Note, replace `sdf` with your actual SD card device, and be careful!_

    ./copy_rootfs.sh sdf ratt ratt-test

This script takes several args:
    copy_rootfs.sh [SD device] [image name minus the -image] [hostname]


Note: This can be pretty slow to finish (minutes to potentially tens of minutes depending on quality of card).


