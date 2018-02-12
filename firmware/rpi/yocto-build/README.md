# Building RATT Image with Yocto/OpenEmbedded

Based on http://www.jumpnowtek.com/rpi/Raspberry-Pi-Systems-with-Yocto.html

## Pre-requisites

Start with Ubuntu 16.04.3 LTS image running in a virtual machine.  Make sure you have enough disk space (at LEAST 50GB, preferably more).  If you are
doing a lot of building, you will want this on fast disk (SSD).  You will also want to give the Virtual Machine a lot of RAM and CPU cores if you can.
I run with 16GB and 12 cores dedicated to the VM for faster builds.

### Set up a work directory in `/u` (with `/tmp`-like permissions)

    sudo mkdir /u
    sudo chmod 777 /u
    sudo chmod o+t /u

### Install some pre-requisites for building:

    sudo apt install build-essential chrpath diffstat gawk libncurses5-dev texinfo python2.7 git

### Ensure python2.7 has links (16.04.3 had them already):

    steve@ubuntu:~$ ls -al /usr/bin/python
    lrwxrwxrwx 1 root root 9 Feb  8 05:47 /usr/bin/python -> python2.7
    steve@ubuntu:~$ ls -al /usr/bin/python2
    lrwxrwxrwx 1 root root 9 Feb  8 05:47 /usr/bin/python2 -> python2.7

### Ensure 'dash' is disabled on Ubuntu:
    sudo dpkg-reconfigure dash

Choose No to dash when prompted.

### Clone the RATT repo from github

Some directories have fixed paths with `${HOME}` references for the Yocto build, so it is necessary to clone it into your home directory, i.e. `~/ratt` - do not place it inside of other directories or in other locations.

    cd ~
    git clone https://github.com/makeitlabs/ratt.git

### Check that the `meta-ratt` submodule was initialized

Some versions of git will not automatically initialize submodules.  If `~/ratt/firmware/rpi/meta-ratt` is empty after your initial git clone, do this:

    cd ~/ratt/firmware/rpi
    git submodule update --init --recursive

_The `meta-ratt` is included as a submodule because it's forked from the `meta-rpi` project and for ease of maintainance I want to keep it
separate from the rest of RATT._  `meta-ratt` is essentially the layer that defines how to build Yocto exactly for our RATT platform.  It
stands on the shoulders of a lot of work from others for Raspberry Pi compatibility, and makes only specific tweaks where necessary to adjust
the build to our needs.

### Make a local clone of the Yocto poky-rocko branch from github

Poky is the name of the reference build of Yocto Project.  Rocko is the branch that RATT is based on, and was released in October of 2017.
See https://www.yoctoproject.org/downloads/core/rocko24 for more info about the specific release.

I've included a script to do the dirty work of cloning Poky-Rocko.

    ~/ratt/firmware/rpi/yocto-build/scripts/clone-poky-rocko.sh

**TODO: Maybe adjust the script to tie to specific SHAs for poky-rocko and its dependencies so we're not chasing updates.**

### Make a central directory for downloaded source files

The build system will download sources and keep them around so they don't have to be re-downloaded every time you build.  This directory is configurable,
but for simplicity we fix it at `/u/rpi/oe-sources`.  Make sure this directory exists.

    mkdir -p /u/rpi/oe-sources
    
_Note that this location is controlled with the variable `DL_DIR` in `~/ratt/firmware/rpi/yocto-build/conf/local.conf` - don't change it unless you know what you're doing._

### Set up a temporary build directory for Yocto

The build system uses a lot of temporary space for the build.

    mkdir -p /u/rpi/tmp

_Note that this location is controlled with the variable `TMPDIR` in `~/ratt/firmware/rpi/yocto-build/conf/local.conf` - don't change it unless you know what you're doing._

## Building

### Source the yocto environment before running bitbake

    source /u/rpi/poky-rocko/oe-init-build-env ~/ratt/firmware/rpi/yocto-build

_Ignore the common suggested build target text that is spit out here - we don't build those targets._

### Start a build of the RATT image

    bitbake ratt-image

_Wait a long time..._  2-3 hours typically.  More RAM, faster disk, and more/faster cores will help but it's building a lot of stuff.  Yocto Project does a good job at determining deltas and dependencies, so subsequent builds of small changes are comparably much smaller.

## Copying to SD Card

Insert the SD card into your USB reader, and make sure the USB device is attached to the Virtual Machine.

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


