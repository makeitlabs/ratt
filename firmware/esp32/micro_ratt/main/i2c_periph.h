/*--------------------------------------------------------------------------
  _____       ______________
 |  __ \   /\|__   ____   __|
 | |__) | /  \  | |    | |
 |  _  / / /\ \ | |    | |
 | | \ \/ ____ \| |    | |
 |_|  \_\/    \_\_|    |_|    ... RFID ALL THE THINGS!

 A resource access control and telemetry solution for Makerspaces

 Developed at MakeIt Labs - New Hampshire's First & Largest Makerspace
 http://www.makeitlabs.com/

 Copyright 2017-2020 MakeIt Labs

 Permission is hereby granted, free of charge, to any person obtaining a
 copy of this software and associated documentation files (the "Software"),
 to deal in the Software without restriction, including without limitation
 the rights to use, copy, modify, merge, publish, distribute, sublicense,
 and/or sell copies of the Software, and to permit persons to whom the
 Software is furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in
 all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

 --------------------------------------------------------------------------
 Author: Steve Richardson (steve.richardson@makeitlabs.com)
 -------------------------------------------------------------------------- */

#ifndef _I2C_PERIPH_H
#define _I2C_PERIPH_H

#define I2C_MASTER_SCL_IO    		22
#define I2C_MASTER_SDA_IO    		21
#define I2C_MASTER_NUM 			I2C_NUM_0
#define I2C_MASTER_TX_BUF_DISABLE	0
#define I2C_MASTER_RX_BUF_DISABLE   	0
#define I2C_MASTER_FREQ_HZ    	    	400000

#define WRITE_BIT  			I2C_MASTER_WRITE
#define READ_BIT   			I2C_MASTER_READ

#define ACK_CHECK_EN   			0x1
#define ACK_CHECK_DIS  			0x0

#define ACK_VAL    			0x0
#define NACK_VAL   			0x1


#define PCA9539_I2C_ADDR 		0x74

#define PCA9539_REG_IN0			0x00
#define PCA9539_REG_IN1			0x01
#define PCA9539_REG_OUT0		0x02
#define PCA9539_REG_OUT1		0x03
#define PCA9539_REG_INV0		0x04
#define PCA9539_REG_INV1		0x05
#define PCA9539_REG_CFG0		0x06
#define PCA9539_REG_CFG1		0x07


void i2c_init();
esp_err_t i2c_write(uint8_t addr, uint8_t* data_wr, size_t size);
esp_err_t i2c_read(uint8_t addr, uint8_t reg, uint8_t* data_rd, size_t size);

esp_err_t pca9539_read_in(uint8_t *in0, uint8_t *in1);
esp_err_t pca9539_write_out(uint8_t out0, uint8_t out1);
esp_err_t pca9539_cfg(uint8_t cfg0, uint8_t cfg1, uint8_t inv0, uint8_t inv1);

void i2c_test_task(void *pvParameters);

#endif
