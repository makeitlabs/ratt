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

// control PCA9539 16-bit I2C I/O expander using the ESP32 I2C master capability
// 2017FEB18 Steve Richardson (steve.richardson@makeitlabs.com)
// based on ESP-IDF i2c example

#include "esp_log.h"
#include "esp_system.h"
#include <driver/i2c.h>
#include "i2c_periph.h"

static const char *TAG = "i2c_periph";


void i2c_init()
{
    int i2c_master_port = I2C_MASTER_NUM;
    i2c_config_t conf;
    conf.mode = I2C_MODE_MASTER;
    conf.sda_io_num = I2C_MASTER_SDA_IO;
    conf.sda_pullup_en = GPIO_PULLUP_ENABLE;
    conf.scl_io_num = I2C_MASTER_SCL_IO;
    conf.scl_pullup_en = GPIO_PULLUP_ENABLE;
    conf.master.clk_speed = I2C_MASTER_FREQ_HZ;
    i2c_param_config(i2c_master_port, &conf);
    i2c_driver_install(i2c_master_port, conf.mode, I2C_MASTER_RX_BUF_DISABLE, I2C_MASTER_TX_BUF_DISABLE, 0);

    ESP_LOGI(TAG, "i2c master initialized");


    int ret = pca9539_cfg(0x00, 0x00, 0x00, 0x00);

    if (ret == ESP_FAIL) {
        ESP_LOGE(TAG, "error configuring PCA9539 io expander");
    } else {
        ESP_LOGI(TAG, "configured PCA9539 io expander");
    }
}


esp_err_t i2c_write(uint8_t addr, uint8_t* data_wr, size_t size)
{
    i2c_cmd_handle_t link = i2c_cmd_link_create();
    i2c_master_start(link);
    i2c_master_write_byte(link, ( addr << 1 ) | WRITE_BIT, ACK_CHECK_EN);
    i2c_master_write(link, data_wr, size, ACK_CHECK_EN);
    i2c_master_stop(link);
    esp_err_t ret = i2c_master_cmd_begin(I2C_MASTER_NUM, link, 1000 / portTICK_RATE_MS);
    i2c_cmd_link_delete(link);
    return ret;
}


esp_err_t i2c_read(uint8_t addr, uint8_t reg, uint8_t* data_rd, size_t size)
{
    i2c_cmd_handle_t link = i2c_cmd_link_create();
    i2c_master_start(link);
    i2c_master_write_byte(link, ( addr << 1 ) | WRITE_BIT, ACK_CHECK_EN);
    i2c_master_write(link, &reg, 1, ACK_CHECK_EN);

    i2c_master_write_byte(link, ( addr << 1 ) | READ_BIT, ACK_CHECK_EN);
    if (size > 1)
        i2c_master_read(link, data_rd, size - 1, ACK_VAL);

    i2c_master_read_byte(link, data_rd + size - 1, NACK_VAL);

    i2c_master_stop(link);
    esp_err_t ret = i2c_master_cmd_begin(I2C_MASTER_NUM, link, 1000 / portTICK_RATE_MS);
    i2c_cmd_link_delete(link);
    return ret;
}


esp_err_t pca9539_read_in(uint8_t *in0, uint8_t *in1)
{
    uint8_t buf[2];
    esp_err_t ret;

    ret = i2c_read(PCA9539_I2C_ADDR, PCA9539_REG_IN0, buf, 2);
    if (ret != ESP_FAIL) {
        *in0 = buf[0];
        *in1 = buf[1];
    }
    return ret;
}

esp_err_t pca9539_write_out(uint8_t out0, uint8_t out1)
{
    uint8_t buf[3];

    buf[0] = PCA9539_REG_OUT0;
    buf[1] = out0;
    buf[2] = out1;

    return i2c_write(PCA9539_I2C_ADDR, buf, 3);
}

esp_err_t pca9539_cfg(uint8_t cfg0, uint8_t cfg1, uint8_t inv0, uint8_t inv1)
{
    uint8_t buf[3];
    esp_err_t ret;

    buf[0] = PCA9539_REG_CFG0;
    buf[1] = cfg0;
    buf[2] = cfg1;
    ret = i2c_write(PCA9539_I2C_ADDR, buf, 3);

    if (ret == ESP_FAIL)
        return ret;

    buf[0] = PCA9539_REG_INV0;
    buf[1] = inv0;
    buf[2] = inv1;
    ret = i2c_write(PCA9539_I2C_ADDR, buf, 3);

    return ret;
}


void i2c_test_task(void *pvParameters)
{
    uint8_t counter=0;
    while(1) {
        int ret = pca9539_write_out(counter, 0xFF - counter);
        counter++;

        if (ret == ESP_FAIL) {
            ESP_LOGE(TAG, "pca9539_write_out() error");
        } else {
            ESP_LOGI(TAG, "pca9539 wrote %X / %X", counter, 0xFF - counter);
        }

        vTaskDelay(500/portTICK_PERIOD_MS);
    }

}
