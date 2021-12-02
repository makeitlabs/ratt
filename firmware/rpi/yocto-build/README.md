# Building RATT Image with Yocto/OpenEmbedded and Mender

Based on http://www.jumpnowtek.com/rpi/Raspberry-Pi-Systems-with-Yocto.html
Mender info at https://docs.mender.io/

Updated November 2021 for Ubuntu 20.04 build host & Yocto Poky Dunfell

## Pre-requisites

Set up an [Ubuntu 20.04 LTS](https://ubuntu.com/download/desktop) virtual machine.  Make sure you allocate at least 100GB for disk storage.  If you are  doing a lot of building, you will want this located on an SSD on your VM host.  You will also want to give the Virtual Machine as much RAM (16GB+) and CPU cores (4+) as you can spare.  I run with 16GB RAM and 12 cores dedicated to the VM for faster builds.

### Install some pre-requisites for building:

    sudo apt install build-essential chrpath diffstat gawk libncurses5-dev python3-distutils texinfo git

### Ensure 'dash' shell is disabled on Ubuntu:
    sudo dpkg-reconfigure dash

Choose "No" to dash when prompted.


### Clone the RATT repo from GitHub

Some directories have fixed paths with `${HOME}` references for the Yocto build, so it is necessary to clone it into your home directory, i.e. `~/ratt` - do not place it inside of other directories or in other locations.

Start out in your home directory.

    cd ~

You can clone using the GitHub URL if you aren't planning on committing changes back to the repository.

    git clone --recurse-submodules -j8 https://github.com/makeitlabs/ratt.git

If you use SSH for GitHub authentication and plan to commit changes back to the repository, clone using the following command line:

    git clone --recurse-submodules -j8 git@github.com:makeitlabs/ratt


### Set up a work directory in `/u` (with `/tmp`-like permissions)

    sudo mkdir /u
    sudo chmod 777 /u
    sudo chmod o+t /u

### Set up Yocto Poky

[Poky](https://www.yoctoproject.org/software-item/poky/) is the name of the reference distribution of the Yocto Project.  Dunfell is the long term support branch that RATT is based on as of late 2021, and was released in April of 2020.  See https://wiki.yoctoproject.org/wiki/Releases for info on Yocto releases.

I've included a script to do the dirty work of cloning Yocto, using specific pinned versions so that anyone building a RATT image in the future will get the same end result.  The script will also set up a couple of directories in `/u/rpi` that the build process will use for the downloaded sources cache as well as the temporary build directory where the image will be built.

    ~/ratt/firmware/rpi/yocto-build/scripts/setup-poky-build.sh

This script will take a couple minutes to run, as it fetches a lot of data.
   

## Building

### Source the yocto environment before running bitbake

    source ~/ratt/firmware/rpi/yocto-build/scripts/build-env.sh

_Ignore the common suggested build target text that is displayed here, as we don't build those targets for RATT._

### Start a build of the RATT image

    bitbake ratt-image

_Wait a long time..._  3+ hours typically.  More RAM, faster disk, and faster cores will help, but it builds a lot of stuff so it simply takes a while.  Yocto Project does a good job at determining deltas and dependencies, so subsequent builds of small changes are comparably much quicker.

## Mounting Image on Loop Filesystem

The Linux loop filesystem can be used to mount the four partitions of a RATT SD image (boot, rootfs1, rootfs2, and data).  This allows exploration and modification of the contents of the SD image, which will be saved back to the monolithic SD image once unmounted.  When the image is later copied to a physical SD card, those changes will persist.  Generally speaking, only changes to the data partition should be made.  This partition is intended to persist across Mender system updates, and is used to contain configuration information specific to that node.  If you find you need to make changes to the contents of the data or boot partitions, it's generally more appropriately done as a Yocto recipe.  The only exception might be provisioning (e.g. copying certificates), but, again, these should generally be placed on the data partition as it will persist across future updates.

To make this process easier, I created the `sdimg_util.sh` script.  It makes mounting and unmounting loop filesystems easier.

To get started, you first must create the mount points.

     ~/ratt/firmware/rpi/yocto-build/scripts/sdimg_util.sh create
   
Once created, you may mount a previously created SD image using the following command:

     ~/ratt/firmware/rpi/yocto-build/scripts/sdimg_util.sh mount

You can then browse and manipulate the files contained in the image via the mount points in `/mnt/sdimg`.  Once done, you must unmount the SD image using the command:

     ~/ratt/firmware/rpi/yocto-build/scripts/sdimg_util.sh umount

In particular, make sure you remember to unmount before doing another `bitbake` build.

### Image Configuration

The most critical thing to configure in a RATT SD image is the wireless network configuration.  As long as a RATT node can get onto the network, you can later SSH into it to provision it with node-specific configuration, certificates, etc.  All other forms of login are disabled in the image by default, so that's why it's critical to perform this step.  Wireless network config is done via the `wpa_supplicant.conf` file, which lives in the `/data/etc` directory on the RATT image.  This allows the configuration to persist across Mender updates, which would normally overwrite/swap the root filesystems that contain `/etc`.

A template for this file is included in `~/ratt/firmware/rpi/yocto-build/scripts/templates/etc/wpa_supplicant.conf-example`.  Copy this file to `wpa_supplicant.conf` in the same directory, and edit it to set your SSID and PSK for your wireless network.  You can configure multiple networks if you want.  Note that there is a `.gitignore` file in this directory which will ignore the copied file, so you don't accidentally commit it with passwords visible.

Check through the `templates` directory to see what other files may be configured for an image.  Anything that is provided as an `-example` can be copied to the same filename, sans `-example` and it will be copied to the data filesystem in the next step.

The `sdimg_util.sh` script has a function to copy the template files to the mounted SD image.  First mount the SD image, per instructions in the last section.  Then run the following commmand:

    ~/ratt/firmware/rpi/yocto-build/scripts/sdimg_util.sh template

The script will check that the SD image is mounted before it copies.  It will copy all files from the templates directory tree that aren't ending in `-example` and aren't `.gitignore`, so be careful what files you leave around in there.

## Copy Image to SD Card

If you had the SD image mounted with the loop filesystem, be sure to first unmount, following the directions above.

### Find the SD Card Device

Insert the SD card into your USB reader, and make sure the USB device is attached to the Virtual Machine.  If you're using VirtualBox be sure to install the extensions and configure your VM for xHCI USB so you can get the fastest copy possible.

Run the following:

    ~/ratt/firmware/rpi/yocto-build/scripts/sdimg_util.sh findsd

Example output is as follows:

    Here are your disk devices...

    NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
    sda      8:0    0  100G  0 disk 
    ├─sda1   8:1    0  512M  0 part /boot/efi
    ├─sda2   8:2    0    1K  0 part 
    └─sda5   8:5    0 99.5G  0 part /
    sdc      8:32   1 14.9G  0 disk 
    └─sdc1   8:33   1  3.7G  0 part /media/steve/rootfs
    
    Your SD card may be:
    /dev/sdc  14.9G disk

In the above example, `/dev/sdc` is the SD card device.  Be sure you have the correct device if you're at all unsure, and note that it may change if your system configuration changes!  You can potentially lose data by overwriting your hard disk image if you specify the wrong device for the next step!

### Write the Image

Run the following command (substituting your actual SD card device for `/dev/sdX`):

    ~/ratt/firmware/rpi/yocto-build/scripts/sdimg_util.sh write /dev/sdX
    
Note: This can be pretty slow to finish (5-10 minutes depending on speed of your card and reader/writer).  Wait for the activity LED to stop blinking on your card reader before you remove the card, even if the script says it has completed.


### Test the Image

  * Place the SD card into the Raspberry Pi 0W on the RATT.
  * You may wish to connect an HDMI monitor (via mini-HDMI cable) to see the diagnostics display.
  * Apply 5V power to the RATT board.
  * HDMI Display should show some U-Boot messages, and then proceed to load the kernel.
  * Several seconds later, the RATT LCD will power up and show white at first, then a boot splash progress screen with a RATT logo.
  * First boot on a fresh card is slower than normal boot, since some things are initialized during this step.
  * Eventually a message that the RATT app is loading will be shown, and then the RATT app GUI will be displayed.
  * Hold down the BLUE button for a few seconds.  This will cause some info to be displayed, such as current WiFi AP and IP address.
  * Assuming it is on the network, you can SSH in for configuration or testing.  The default login is `root` password `raspberry`.  Provisioning scripts should disable this and install SSH keys instead.  Note that SSH tends to be slow when connecting, especially the first time.
  


# Yocto / OpenEmbedded References

## Writing Recipes

  * http://www.yoctoproject.org/docs/current/dev-manual/dev-manual.html#new-recipe-writing-a-new-recipe
  * https://wiki.yoctoproject.org/wiki/Building_your_own_recipes_from_first_principles
  * http://www.embeddedlinux.org.cn/OEManual/directories_installation.html
  * http://www.embeddedlinux.org.cn/OEManual/recipes_directories.html
  * https://elinux.org/Bitbake_Cheat_Sheet
  
  
