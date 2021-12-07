#!/bin/bash

# Yocto+Mender sd image mounting/unmounting utility using loop filesystems
# Steve Richardson (steve.richardson@makeitlabs.com)
# December 2018
#

SDIMG="${HOME}/yocto-ratt/tmp/deploy/images/raspberrypi0-wifi/ratt-image-raspberrypi0-wifi.sdimg"

PART_BOOTFS=1
PART_ROOT1FS=2
PART_ROOT2FS=3
PART_DATAFS=4

MOUNT_PT="/mnt/sdimg"
MOUNT_BOOTFS="${MOUNT_PT}/bootfs"
MOUNT_ROOT1FS="${MOUNT_PT}/rootfs1"
MOUNT_ROOT2FS="${MOUNT_PT}/rootfs2"
MOUNT_DATAFS="${MOUNT_PT}/datafs"

LOOP_BOOTFS="/dev/loop1"
LOOP_ROOT1="/dev/loop2"
LOOP_ROOT2="/dev/loop3"
LOOP_DATAFS="/dev/loop4"

create_mountpoints()
{
    
    if [ ! -d ${MOUNT_PT} ]; then
	U=${USER}
	sudo mkdir ${MOUNT_PT}
	sudo chown ${U}:${U} ${MOUNT_PT}
	mkdir ${MOUNT_BOOTFS}
	mkdir ${MOUNT_ROOT1FS}
	mkdir ${MOUNT_ROOT2FS}
	mkdir ${MOUNT_DATAFS}

	echo "Created mount points in ${MOUNT_PT}:"
	ls -al ${MOUNT_PT}
    else
	echo "${MOUNT_PT} already exists, exiting."
    fi
}

show_parts()
{
    IMG=$1

    fdisk -l -u ${IMG} | grep "${IMG}[0-9]"
    echo ---
}

get_part_start()
{
    IMG=$1
    PART=$2

    echo `fdisk -o Device,Start -l -u ${IMG} | grep "${IMG}${PART}" | awk -F " " '{print $2}'`
}

get_part_size()
{
    IMG=$1
    PART=$2

    echo `fdisk -o Device,Sectors -l -u ${IMG} | grep "${IMG}${PART}" | awk -F " " '{print $2}'`
}

mount_part()
{
    IMG=$1
    PART=$2
    MOUNTPOINT=$3
    LOOPDEV=$4

    START=$( get_part_start ${SDIMG} $PART )
    SIZE=$( get_part_size ${SDIMG} $PART )

    echo mounting ${IMG}${PART} to ${MOUNTPOINT}
    echo "  Start ${START}"
    echo "   Size ${SIZE}"
    echo "   Loop ${LOOPDEV}"
    sudo umount ${MOUNTPOINT} 2> /dev/null
    sudo mount -o loop,offset=$((512*${START})),sizelimit=$((512*${SIZE})) ${IMG} ${MOUNTPOINT} -o loop=${LOOPDEV}
    df -h ${MOUNTPOINT}
    echo ---
}

umount_part()
{
    MOUNTPOINT=$1
    echo "unmounting ${MOUNTPOINT}"
    sudo umount ${MOUNTPOINT} 2> /dev/null
}

mount_parts()
{
    show_parts ${SDIMG}

    mount_part ${SDIMG} ${PART_BOOTFS} ${MOUNT_BOOTFS} ${LOOP_BOOTFS}
    mount_part ${SDIMG} ${PART_ROOT1FS} ${MOUNT_ROOT1FS} ${LOOP_ROOT1FS}
    mount_part ${SDIMG} ${PART_ROOT2FS} ${MOUNT_ROOT2FS} ${LOOP_ROOT2FS}
    mount_part ${SDIMG} ${PART_DATAFS} ${MOUNT_DATAFS} ${LOOP_DATAFS}
}

umount_parts()
{
    umount_part ${MOUNT_BOOTFS}
    umount_part ${MOUNT_ROOT1FS}
    umount_part ${MOUNT_ROOT2FS}
    umount_part ${MOUNT_DATAFS}
}

copy_template_data()
{
    if /usr/bin/mountpoint -q ${MOUNT_DATAFS} ; then
	SCRIPT_RELATIVE_DIR=$(dirname "${BASH_SOURCE[0]}")
	cd $SCRIPT_RELATIVE_DIR/../templates
	if [ $? -ne 0 ]; then
	    echo "Aborted."
	    exit 1
	fi
	find . \( ! -name "*-example" \) \( ! -name ".gitignore" \) -type f | sudo cpio -vdump ${MOUNT_DATAFS}
	sudo chown --quiet --recursive root:root ${MOUNT_DATAFS}/home/root
	sudo chmod --quiet --recursive og-rwx ${MOUNT_DATAFS}/home/root/.ssh
    else
	echo "please first run '$0 mount' to mount the SD image partitions before copying template data"
    fi
}

find_sd()
{
    echo "Here are your disk devices..."
    echo
    lsblk --include 8
    echo
    echo "Your SD card may be:"
    lsblk --include 8 --fs --output RM,HOTPLUG,PATH,SIZE,TYPE|grep disk|grep "1       1"|cut -c 12-
}

umount_sdparts()
{
    umount_part ${SDCARD}${PART_BOOTFS}
    umount_part ${SDCARD}${PART_ROOT1FS}
    umount_part ${SDCARD}${PART_ROOT2FS}
    umount_part ${SDCARD}${PART_DATAFS}
}

dd_image_to_sd()
{
    echo "Copying ${SDIMG} to ${SDCARD}... This will take a while, please wait."
    /usr/bin/time -f "\tcopy took %E" sudo dd if=${SDIMG} of=${SDCARD} bs=8M status=progress
}

if [ "$1" = "create" ]; then
    create_mountpoints
elif [ "$1" = "mount" ]; then
    if [ "X$2" != "X" ]; then
	SDIMG=$2
    fi

    echo SDIMG=${SDIMG}

    if [ -f ${SDIMG} ]; then
	mount_parts
    else
	echo "${SDIMG} does not exist."
    fi
elif [ "$1" = "umount" ]; then
    umount_parts
elif [ "$1" = "template" ]; then
    copy_template_data
elif [ "$1" = "findsd" ]; then
    find_sd
elif [ "$1" = "write" ]; then

    if [ "X$2" != "X" ]; then
	SDCARD=$2
    fi

    if [[ ! -b ${SDCARD} ]]; then
	echo "${SDCARD} is not a block device.  Exiting."
	exit 1
    fi

    lsblk ${SDCARD}
    echo
    
    echo -ne "\e[1;31mAre you sure you want to write to ${SDCARD}?  \e[5;7mAll contents will be destroyed!\e[0m "
    read -p " (y/n)? " -r
    echo    
    if [[ ! $REPLY =~ ^[Yy]$ ]]
    then
	exit 1
    fi

    umount_parts
    umount_sdparts
    dd_image_to_sd

    echo "Finished copy.  Please wait for activity LED to stop blinking on card writer before removing card."
    
else
    echo $0
    echo
    echo "Usage:"
    echo "      create -- create mount point directories in ${MOUNT_PT}"
    echo "      mount [ path/to/file.sdimg, default=${SDIMG} ] -- mount SD image to ${MOUNT_PT} using loop filesystem"
    echo "      umount -- unmount SD image from ${MOUNT_PT}"
    echo "      template -- copy config templates to ${MOUNT_DATAFS}"
    echo "      findsd -- try to locate SD card device"
    echo "      write [ /dev/sdX ] -- write SD image to SD card"

fi


