# Platform Configs

This represents the initial R&D bringing up the RATT platform on Raspbian OS circa 2018.  Variations of these configs are used in current Yocto builds, but not directly.  The key elements such as device tree overlays, are "baked in" to Yocto recipes in meta-ratt.  This is kept for historical information, mainly.

boot/ - contains configs from the Raspberry Pi /boot directory
device-tree/ - contains custom device tree overlay files and a script to compile/install them

