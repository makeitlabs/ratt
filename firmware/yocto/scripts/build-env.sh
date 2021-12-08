# from bash: . build-env.sh
[[ ! "${BASH_SOURCE[0]}" != "${0}" ]] && echo "script ${BASH_SOURCE[0]} must be sourced, like this: " && echo ". ${BASH_SOURCE[0]}" && echo && exit 1

SCRIPT_DIR="$(dirname "$(realpath "$BASH_SOURCE")")"

info() {
    echo "You can now run one of the following commands:"
    echo
    echo "baker build                Use script to start a RATT build (standard builds)."
    echo "bitbake ratt-image         Do a build using raw tools (development)."
    echo
    echo "imgfeast write /dev/sdX    Use script to write SD card image to physical card"
    echo
    echo "imgfeast mount             mount SD card image to devhost using loop fs"
    echo "imgfeast umount            unmount SD card image from devhost"
    echo "imgfeast create            create mount points for loop fs (do once)"
    echo
}

if [ -z "${RATT_BUILD_ENV}" ]; then
    source ~/yocto-ratt/poky-dunfell/oe-init-build-env ${SCRIPT_DIR}/../ > /dev/null

    if [ $? -eq 0 ] ; then
	echo "*** RATT Yocto build environment now configured."

	export PATH=${SCRIPT_DIR}:${PATH}
	export RATT_BUILD_ENV=1

	info
    fi
else
    echo "*** RATT Yocto build environment already configured previously."
    cd ${SCRIPT_DIR}/../

    info
fi
