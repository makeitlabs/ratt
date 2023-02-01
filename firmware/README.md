# RATT Raspberry Pi Firmware

The firmware image for RATT is based on Yocto Poky, which builds a customized embedded Linux image specifically tailored for the RATT Raspberry Pi 0W.  The majority of what is built during this process is scaffolding (boot support, Linux OS, utilities, languages, support & configuration).

| Directory | Description |
| --------- | ----------- |
| [yocto/](yocto/) |Yocto build and config directory for RATT |
| [raspbian/](raspbian/) |initial R&D for the platform on standard Raspbian (not used for Yocto build) |

**See [yocto/README.md](yocto/README.md) for step-by-step documentation on how to set up the build environment, build an image from scratch, and deploy it to an SD card.**

## RATT Application (GUI & Logic)

The "app" has been moved to its own repo, found here: [https://github.com/makeitlabs/ratt-app](https://github.com/makeitlabs/ratt-app)

