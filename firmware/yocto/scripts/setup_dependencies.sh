#!/bin/sh
DEST_DIR="${HOME}/yocto-ratt"
RELEASE="dunfell"

HASH_POKY="0839888394a6e42e96f9f0d201376eb38bc79b24"
HASH_META_OPENEMBEDDED="7889158dcd187546fc5e99fd81d0779cad3e8d17"
HASH_META_QT5="b4d24d70aca75791902df5cd59a4f4a54aa4a125"
HASH_META_SECURITY="b76698c788cb8ca632077a972031899ef15025d6"
HASH_META_RASPBERRYPI="934064a01903b2ba9a82be93b3f0efdb4543a0e8"
HASH_META_JUMPNOW="b3995636741be0d219a50035c98ded8b48590888"
HASH_META_MENDER="045cfcfc3649b0505cee0b56af8946ef692cd67d"

POKY="poky-${RELEASE}"
SOURCES_DIR="oe-sources"
TMP_DIR="tmp"

clone_hash()
{
    GIT=$1
    DEST=$2
    REV=$3

    git clone -b ${RELEASE} --single-branch ${GIT} ${DEST}
    pushd .
    cd ${DEST}
    git -c advice.detachedHead=false checkout ${REV}
    popd
}

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
    clone_hash "git://git.yoctoproject.org/poky.git" ${POKY} ${HASH_POKY}
    
    cd ${POKY}
    echo "Cloning dependency directories..."
    clone_hash "git://git.openembedded.org/meta-openembedded" meta-openembedded ${HASH_META_OPENEMBEDDED}
    clone_hash "https://github.com/meta-qt5/meta-qt5" meta-qt5 ${HASH_META_QT5}
    clone_hash "git://git.yoctoproject.org/meta-security" meta-security ${HASH_META_SECURITY}
    clone_hash "git://git.yoctoproject.org/meta-raspberrypi" meta-raspberrypi ${HASH_META_RASPBERRYPI}
    clone_hash "https://github.com/jumpnow/meta-jumpnow" meta-jumpnow ${HASH_META_JUMPNOW}
    clone_hash "https://github.com/mendersoftware/meta-mender" meta-mender ${HASH_META_MENDER}
fi
 
