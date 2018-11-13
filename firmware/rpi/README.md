| Directory | Description |
| --------- | ----------- |
| [app/](app/)         |RATT core application, primarily written in Python and QML via PyQt5 |
| [config/](config/)      |contains configuration details for the Pi platform |
| meta-mender/ |Layer to build and integrate the Mender OTA update mechanism (submodule) |
| meta-ratt/   |Layer to build the overall platform (submodule) |
| [tests/](tests/)       |Test framework (tbd) |
| [yocto-build/](yocto-build/) |Yocto build directory for RATT |
 
See [yocto-build README](yocto-build/README.md) for documentation on how to set up the build environment and build an image from scratch.
