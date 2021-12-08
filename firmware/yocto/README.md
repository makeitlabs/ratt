# Building RATT Image with Yocto/OpenEmbedded and Mender

Based on http://www.jumpnowtek.com/rpi/Raspberry-Pi-Systems-with-Yocto.html
Mender info at https://docs.mender.io/

Updated November 2021 for Ubuntu 20.04 build host & Yocto Poky Dunfell

## Pre-requisites

Set up an [Ubuntu 20.04 LTS](https://ubuntu.com/download/desktop) virtual machine.  Make sure you allocate at least 100GB for disk storage.  If you are  doing a lot of building, you will want this located on an SSD on your VM host.  You will also want to give the Virtual Machine as much RAM (16GB+) and CPU cores (4+) as you can spare.  I run with 16GB RAM and 12 cores dedicated to the VM for faster builds.

You can, of course, do this on an Ubuntu install on bare metal as well.  This may be more performant, depending on your hardware.

### Install some pre-requisites for building:

    sudo apt install build-essential chrpath diffstat gawk libncurses5-dev python3-distutils texinfo git

### Ensure 'dash' shell is disabled on Ubuntu:
    sudo dpkg-reconfigure dash

Choose "No" to dash when prompted.


### Clone the RATT Repository from GitHub

Some directories have fixed paths with `${HOME}` references for the Yocto build, so it is necessary to clone it into your home directory, i.e. `~/ratt` - do not place it inside of other directories or in other locations. (N.B. this has hopefully been fixed - but for the sake of consistency this document refers to `~/ratt`)

Start out in your home directory.

    cd ~

You can clone using the GitHub URL if you aren't planning on committing changes back to the repository.

    git clone --recurse-submodules -j8 https://github.com/makeitlabs/ratt.git

If you use SSH for GitHub authentication and plan to commit changes back to the repository, clone using the following command line:

    git clone --recurse-submodules -j8 git@github.com:makeitlabs/ratt

### Set up Dependencies

[Poky](https://www.yoctoproject.org/software-item/poky/) is the name of the reference distribution of the Yocto Project.  Dunfell is the long term support branch that RATT is based on as of late 2021, and was released in April of 2020.  See https://wiki.yoctoproject.org/wiki/Releases for info on Yocto releases.

I've included a script to do the dirty work of cloning Yocto and other required layers, using specific pinned versions so that anyone building a RATT image in the future will get the same end result.  The script will create `~/yocto-ratt/` and set up a couple of directories that the build process will use for the downloaded sources cache as well as the temporary build directory where the image will be built.

    ~/ratt/firmware/yocto/scripts/setup_dependencies.sh

This script will take a little bit to run, as it fetches a lot of data.  When it's finished, you should have all the required dependencies in `~/yocto-ratt/poky-dunfell/`.  At the present time, there is no (easy, flexible) way to change this path.

## Image Configuration (Templating)

_Templating_ is the name I made up for a process that overlays config files over the completed root filesystem image, to allow default configuration of a node for a specific environment.  Not every system setting can be changed this way, but RATT is built in such a way that the most critical ones can.

Persistent configs live in the `/data/etc` directory on the RATT target.  This allows the configuration to persist across Mender updates, which would normally overwrite the root filesystems that contain `/etc` (and others), during an update.

The templates tree lives in `~ratt/firmware/yocto/templates` and is a duplication of the structure of the target's `/data` directory.

A bitbake step that runs after the root filesystem has been created is responsible for the templating.  It will copy all files from the templates directory tree that aren't ending in `-example` and aren't `.gitignore`, so be careful what extra files you leave around in the templates directory, as they will end up on the target image.

The `.gitignore` file in the templates directory which will ignore non-example files, so you don't accidentally commit those and expose sensitive data.  However it means you might lose critical config data if you delete your repository, so be careful!

### Configure Wireless (Required!)

The most important thing to configure is the wireless network configuration.  As long as a RATT node can get onto the network, you can later SSH into it to provision it with node-specific configuration, certificates, etc.  All other forms of login are disabled in the image by default, so that's why it's critical to perform this step.

A template for this file is included in `~/ratt/firmware/yocto/templates/etc/wpa_supplicant.conf-example`.  Copy this file to `wpa_supplicant.conf` in the same directory, and edit it to set your SSID and PSK for your wireless network.  You can configure multiple networks if you want.

### Configure SSH Key (Required!)

The default RATT image does not enable a password for the `root` account (it is locked via `usermod`).  Thus, to SSH into the unit, you will need to set up an SSH key as a template.

You _can_ use your public SSH key from your personal user account, but it's generally better to create a key specifically for accessing the device.  This step will create a single key that will allow you to log into all devices running this image.  Later provisioning steps will use this key, and may optionally replace it with a key unique for the node, rather than having all devices share a common key.

To create a key, run (replace `id_ratt` with a more sensible name if you like):

    ssh-keygen -f ~/.ssh/id_ratt

You may specify a passphrase for added security if you wish, though I generally don't bother.  Once completed, this will create `~/.ssh/id_ratt` and `~/.ssh/id_ratt.pub` files.

Now you need to create a template for `/data/home/root/.ssh/authorized_keys`.

You must copy it, as the templating process won't copy links:

    cp ~/.ssh/id_ratt ~/ratt/firmware/yocto/templates/home/root/.ssh/authorized_keys

Lastly, set up your `~/.ssh/config` file to include an entry for ratt.  You probably do not yet know the IP address of the RATT, so you may need to revisit this to edit later.  If you have several RATTs, you'll make entries for each of them.

    Host ratt
	    HostName 192.168.0.154
    	User root
    	IdentityFile id_ratt

### Configure Other Items

To see all of the example files that you can potentially configure, you can run the following command from inside of the `templates` directory.

    find . -name "*-example"

Anything that is provided as an `-example` can be copied to the same filename, sans `-example` and it will be copied to the data filesystem in the next step.

Including, but not limited to:
* `templates/etc/ntp.conf-example`
* `templates/etc/hosts-example`

## Building

Now we're ready to start the build process.  Hope your CPU cores and RAM are ready for a workout!

### Source the yocto environment before running bitbake

    . ~/ratt/firmware/yocto/scripts/build-env.sh

This will set up your environment for Yocto, as well as put `~/ratt/firmware/yocto/scripts/` into your path, which contains a number of useful scripts to ease the build and deployment process.

### Start a build of the RATT image

#### RATT build wrapper script

For standard everyday builds, I wrote a build wrapper script called `baker`, that performs some necessary steps like creating a unique Mender artifact name before each build.  I recommend using this script for most builds.

    baker build

This will start a standard build with a uniquely named Mender artifact based on the date and time.

_Wait a long time..._  3+ hours for a typical full build, on a decently-equipped VM.  Running the host OS natively on a fast SSD can significantly improve times, as VM's tend not to have the best I/O performance.  Bitbake does a good job at determining deltas and dependencies, so subsequent builds of small changes are comparably much quicker.

#### Using standard Yocto tools

Standard Yocto/OE build tools like `bitbake` can also be used directly.  These tools will mostly be used during development to perform various lower-level tasks.  e.g.:

    bitbake ratt-image

or:

    bitbake -c cleansstate ratt-app
    
## Copy Image to SD Card

Once the build is finished, you're ready to write to a physical SD card for use in the RATT.

### Find the SD Card Device

Insert the SD card into your USB reader, and make sure the USB device is attached to the Virtual Machine, or plugged into your physical machine.  If you're using VirtualBox be sure to install the extensions and configure your VM for xHCI USB so you can get the fastest copy possible.

I created a helper script called `imgfeast` that helps perform various tasks associated with SD card images.  Run the following to find the SD card device:

    imgfeast findsd

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

    imgfeast write /dev/sdX

The script will prompt you to be sure you want to write to the device.  Answer 'y' and press enter to continue.  This can be pretty slow to finish (5-10 minutes depending on speed of your card and reader/writer).  Wait for the activity LED to stop blinking on your card reader before you remove the card, even if the script says it has completed.

### Test the Image

  * Place the SD card into the Raspberry Pi 0W on the RATT.
  * You may wish to connect an HDMI monitor (via mini-HDMI cable) to see the diagnostics display.
  * Apply 5V power to the RATT board.
  * HDMI Display should show some U-Boot messages, and then proceed to load the kernel.
  * Shortly after powerup, the RATT LCD will show white at first, then a boot splash progress screen with a RATT logo.
  * First boot on a fresh card is slower than normal boot, since some things are initialized during this step.
  * Eventually a message that the RATT app is loading will be shown, and then the RATT app GUI will be displayed.
  * Hold down the BLUE button for a few seconds.  This will cause some info to be displayed, including current IP address.
  * Assuming it is on the network, you can SSH in for configuration or testing.  You will use the name that you configured in your `~/.ssh/config` file as the host to connect to.  Make sure the correct IP address is in the config, and that it's pointing to the correct SSH key.  Note that SSH tends to be slow on the single-core Pi 0W when connecting, especially the first time.

## Mounting Image on Loop Filesystem

The Linux loop filesystem can be used to mount the four partitions of a RATT SD image (boot, rootfs1, rootfs2, and data).  This allows exploration and modification of the contents of the SD image, which will be saved back to the monolithic SD image once unmounted.  When the image is later copied to a physical SD card, those changes will persist.  Generally speaking, only changes to the data partition should be made.  This partition is intended to persist across Mender system updates, and is used to contain configuration information specific to that node.  If you find you need to make changes to the contents of the root or boot partitions, it's generally more appropriately done as a recipe.  And if you want to consistently apply changes to the data partition, it's most easily done as a template (see previous section).

To get started, you first must create the mount points.

     imgfeast create

Once created, you may mount a previously created SD image using the following command:

     imgfeast mount

You can then browse and manipulate the files contained in the image via the mount points in `/mnt/sdimg`.  Once done, you must unmount the SD image using the command:

     imgfeast umount

In particular, make sure you remember to unmount before doing another `bitbake` build.

### Re-apply the Templates to the SD Image

The `imgfeast` script has a function to copy the template files to the mounted SD image, similar to how it happens in the bitbake process.  This is useful for quickly updating the template files on an already-built SD image, without running the slower bitbake process (~5 minutes).  First mount the SD image, per instructions in the loop filesystem section.  Then run the following commmand:

    imgfeast template

The script will check that the SD image is mounted before it copies.

# Yocto / OpenEmbedded References

  * http://www.yoctoproject.org/docs/current/dev-manual/dev-manual.html#new-recipe-writing-a-new-recipe
  * https://wiki.yoctoproject.org/wiki/Building_your_own_recipes_from_first_principles
  * http://www.embeddedlinux.org.cn/OEManual/directories_installation.html
  * http://www.embeddedlinux.org.cn/OEManual/recipes_directories.html
  * https://elinux.org/Bitbake_Cheat_Sheet
