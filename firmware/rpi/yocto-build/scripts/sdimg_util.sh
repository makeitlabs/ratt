#!/bin/sh

# Yocto+Mender sd image mounting/unmounting utility using loop filesystems
# Steve Richardson (steve.richardson@makeitlabs.com)
# December 2018
#

SDIMG="/u/rpi/tmp/deploy/images/raspberrypi0-wifi/ratt-image-raspberrypi0-wifi.sdimg"

PART_BOOTFS=1
PART_ROOT1FS=2
PART_ROOT2FS=3
PART_DATAFS=4

MOUNT_BOOTFS="/mnt/sdimg/bootfs"
MOUNT_ROOT1FS="/mnt/sdimg/rootfs1"
MOUNT_ROOT2FS="/mnt/sdimg/rootfs2"
MOUNT_DATAFS="/mnt/sdimg/datafs"

LOOP_BOOTFS="/dev/loop1"
LOOP_ROOT1="/dev/loop2"
LOOP_ROOT2="/dev/loop3"
LOOP_DATAFS="/dev/loop4"

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

if [ "$1" = "mount" ]; then
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
elif [ "$1" = "write" ]; then

    if [ "X$2" != "X" ]; then
	SDCARD=$2
    fi

    if [[ ! -b ${SDCARD} ]]; then
	echo "${SDCARD} is not a block device.  Exiting."
	exit 1
    fi
    
    read -p "Are you sure you want to write to ${SDCARD}?  All contents will be destroyed!  (y/n)? " -n 1 -r
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
    echo "      mount [path/to/file.sdimg, default=${SDIMG}]"
    echo "      umount"
    echo "      write [/dev/sdX, where X is letter of SD card drive]"

fi


