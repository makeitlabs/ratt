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
