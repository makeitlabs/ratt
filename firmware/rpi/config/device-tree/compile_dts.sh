#!/bin/sh

# MakeIt Labs RATT: RFID All The Things
# steve.richardson@makeitlabs.com
# -----------------------------------------------------------------
# build device tree overlay files for RATT platform


DTBO_DIR=/boot/overlays

run_dtc()
{
    DTS_FILE=$1.dts
    DTBO_FILE=$DTBO_DIR/$1.dtbo

    echo "Compiling $DTS_FILE => $DTBO_FILE"
    sudo dtc -W no-unit_address_vs_reg -@ -I dts -O dtb -o $DTBO_FILE $DTS_FILE
    file $DTBO_FILE
    echo "---"
}
    
    
###

run_dtc ratt-lcd
run_dtc ratt-keypad
run_dtc ratt-ioexpander
