# RATT Raspberry Pi Firmware

The firmware image for RATT is based on Yocto Poky, which builds a customized embedded Linux image specifically tailored for the RATT Raspberry Pi 0W.  The majority of what is built during this process is scaffolding (boot support, Linux OS, utilities, languages, support & configuration).

The core RATT application that controls access to the equipment as well as provides the GUI that the end user sees is written in Python3 and PyQt5/QML.  This runs on the target hardware, and can also be run on a desktop host for more rapid debug and feature development.

| Directory | Description |
| --------- | ----------- |
| [app/](app/) |RATT application, primarily written in Python3 and QML via PyQt5 |
| [yocto-build/](yocto-build/) |Yocto build directory for RATT |
| [meta-ratt/](meta-ratt/)   |Layer to build the RATT platform (submodule) |
| [meta-mender/](meta-mender/) |Layer to build and integrate the Mender OTA update mechanism (submodule) |
| [meta-jumpnow/](meta-jumpnow/) |Layer from jumpnowtek to help with Pi platform (submodule)|
| [config/](config/) |contains configuration R&D for the Pi platform (not used for Yocto build) |

**See [yocto-build/README.md](yocto-build/README.md) for step-by-step documentation on how to set up the build environment, build an image from scratch, and deploy it to an SD card.**

**See [app/README.md](app/README.md) for step-by-step instructions on how to run the app on a desktop host for development.**
