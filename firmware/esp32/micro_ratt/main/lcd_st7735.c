/*
  ST7735 128 x 160 SPI LCD code, integrated with ESP32 DMA SPI engine

  ported from Adafruit Arduino LCD and GFX libraries, and based on ESP-IDF SPI Master example
  by Steve Richardson (steve.richardson@makeitlabs.com)
  February 11, 2017

  see end of file for original copyright notices and other info
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_log.h"
#include "sdcard.h"
#include "driver/spi_master.h"
#include "soc/gpio_struct.h"
#include "driver/gpio.h"
#include "lcd_st7735.h"

// include standard font
#include "glcdfont.c"

static spi_device_handle_t m_spi;
static uint32_t colstart, rowstart;
static uint8_t  tabcolor;

static uint16_t _width;
static uint16_t _height;
static uint8_t rotation;

static uint16_t cursor_x;
static uint16_t cursor_y;
static uint16_t textcolor;
static uint16_t textbgcolor;
static uint8_t textsize;
static uint8_t wrap;
static GFXfont* gfxFont;


static const char *TAG = "lcd_st7735";

void lcd_init_common(const uint8_t *cmdList);
void lcd_initB(void);
void lcd_initR(uint8_t options);

void gfx_refresh();

uint16_t *m_frame_buf;
size_t m_frame_buf_size;

// Rather than a bazillion writecommand() and writedata() calls, screen
// initialization commands and arguments are organized in these tables
// stored in PROGMEM.  The table may look bulky, but that's mostly the
// formatting -- storage-wise this is hundreds of bytes more compact
// than the equivalent code.  Companion function follows.
#define DELAY 0x80
static const uint8_t
  Bcmd[] = {                  // Initialization commands for 7735B screens
    18,                       // 18 commands in list:
    ST7735_SWRESET,   DELAY,  //  1: Software reset, no args, w/delay
      50,                     //     50 ms delay
    ST7735_SLPOUT ,   DELAY,  //  2: Out of sleep mode, no args, w/delay
      255,                    //     255 = 500 ms delay
    ST7735_COLMOD , 1+DELAY,  //  3: Set color mode, 1 arg + delay:
      0x05,                   //     16-bit color
      10,                     //     10 ms delay
    ST7735_FRMCTR1, 3+DELAY,  //  4: Frame rate control, 3 args + delay:
      0x00,                   //     fastest refresh
      0x06,                   //     6 lines front porch
      0x03,                   //     3 lines back porch
      10,                     //     10 ms delay
    ST7735_MADCTL , 1      ,  //  5: Memory access ctrl (directions), 1 arg:
      0x08,                   //     Row addr/col addr, bottom to top refresh
    ST7735_DISSET5, 2      ,  //  6: Display settings #5, 2 args, no delay:
      0x15,                   //     1 clk cycle nonoverlap, 2 cycle gate
                              //     rise, 3 cycle osc equalize
      0x02,                   //     Fix on VTL
    ST7735_INVCTR , 1      ,  //  7: Display inversion control, 1 arg:
      0x0,                    //     Line inversion
    ST7735_PWCTR1 , 2+DELAY,  //  8: Power control, 2 args + delay:
      0x02,                   //     GVDD = 4.7V
      0x70,                   //     1.0uA
      10,                     //     10 ms delay
    ST7735_PWCTR2 , 1      ,  //  9: Power control, 1 arg, no delay:
      0x05,                   //     VGH = 14.7V, VGL = -7.35V
    ST7735_PWCTR3 , 2      ,  // 10: Power control, 2 args, no delay:
      0x01,                   //     Opamp current small
      0x02,                   //     Boost frequency
    ST7735_VMCTR1 , 2+DELAY,  // 11: Power control, 2 args + delay:
      0x3C,                   //     VCOMH = 4V
      0x38,                   //     VCOML = -1.1V
      10,                     //     10 ms delay
    ST7735_PWCTR6 , 2      ,  // 12: Power control, 2 args, no delay:
      0x11, 0x15,
    ST7735_GMCTRP1,16      ,  // 13: Magical unicorn dust, 16 args, no delay:
      0x09, 0x16, 0x09, 0x20, //     (seriously though, not sure what
      0x21, 0x1B, 0x13, 0x19, //      these config values represent)
      0x17, 0x15, 0x1E, 0x2B,
      0x04, 0x05, 0x02, 0x0E,
    ST7735_GMCTRN1,16+DELAY,  // 14: Sparkles and rainbows, 16 args + delay:
      0x0B, 0x14, 0x08, 0x1E, //     (ditto)
      0x22, 0x1D, 0x18, 0x1E,
      0x1B, 0x1A, 0x24, 0x2B,
      0x06, 0x06, 0x02, 0x0F,
      10,                     //     10 ms delay
    ST7735_CASET  , 4      ,  // 15: Column addr set, 4 args, no delay:
      0x00, 0x02,             //     XSTART = 2
      0x00, 0x81,             //     XEND = 129
    ST7735_RASET  , 4      ,  // 16: Row addr set, 4 args, no delay:
      0x00, 0x02,             //     XSTART = 1
      0x00, 0x81,             //     XEND = 160
    ST7735_NORON  ,   DELAY,  // 17: Normal display on, no args, w/delay
      10,                     //     10 ms delay
    ST7735_DISPON ,   DELAY,  // 18: Main screen turn on, no args, w/delay
      255 },                  //     255 = 500 ms delay

  Rcmd1[] = {                 // Init for 7735R, part 1 (red or green tab)
    15,                       // 15 commands in list:
    ST7735_SWRESET,   DELAY,  //  1: Software reset, 0 args, w/delay
      150,                    //     150 ms delay
    ST7735_SLPOUT ,   DELAY,  //  2: Out of sleep mode, 0 args, w/delay
      255,                    //     500 ms delay
    ST7735_FRMCTR1, 3      ,  //  3: Frame rate ctrl - normal mode, 3 args:
      0x01, 0x2C, 0x2D,       //     Rate = fosc/(1x2+40) * (LINE+2C+2D)
    ST7735_FRMCTR2, 3      ,  //  4: Frame rate control - idle mode, 3 args:
      0x01, 0x2C, 0x2D,       //     Rate = fosc/(1x2+40) * (LINE+2C+2D)
    ST7735_FRMCTR3, 6      ,  //  5: Frame rate ctrl - partial mode, 6 args:
      0x01, 0x2C, 0x2D,       //     Dot inversion mode
      0x01, 0x2C, 0x2D,       //     Line inversion mode
    ST7735_INVCTR , 1      ,  //  6: Display inversion ctrl, 1 arg, no delay:
      0x07,                   //     No inversion
    ST7735_PWCTR1 , 3      ,  //  7: Power control, 3 args, no delay:
      0xA2,
      0x02,                   //     -4.6V
      0x84,                   //     AUTO mode
    ST7735_PWCTR2 , 1      ,  //  8: Power control, 1 arg, no delay:
      0xC5,                   //     VGH25 = 2.4C VGSEL = -10 VGH = 3 * AVDD
    ST7735_PWCTR3 , 2      ,  //  9: Power control, 2 args, no delay:
      0x0A,                   //     Opamp current small
      0x00,                   //     Boost frequency
    ST7735_PWCTR4 , 2      ,  // 10: Power control, 2 args, no delay:
      0x8A,                   //     BCLK/2, Opamp current small & Medium low
      0x2A,
    ST7735_PWCTR5 , 2      ,  // 11: Power control, 2 args, no delay:
      0x8A, 0xEE,
    ST7735_VMCTR1 , 1      ,  // 12: Power control, 1 arg, no delay:
      0x0E,
    ST7735_INVOFF , 0      ,  // 13: Don't invert display, no args, no delay
    ST7735_MADCTL , 1      ,  // 14: Memory access control (directions), 1 arg:
      0xC8,                   //     row addr/col addr, bottom to top refresh
    ST7735_COLMOD , 1      ,  // 15: set color mode, 1 arg, no delay:
      0x05 },                 //     16-bit color

  Rcmd2green[] = {            // Init for 7735R, part 2 (green tab only)
    2,                        //  2 commands in list:
    ST7735_CASET  , 4      ,  //  1: Column addr set, 4 args, no delay:
      0x00, 0x02,             //     XSTART = 0
      0x00, 0x7F+0x02,        //     XEND = 127
    ST7735_RASET  , 4      ,  //  2: Row addr set, 4 args, no delay:
      0x00, 0x01,             //     XSTART = 0
      0x00, 0x9F+0x01 },      //     XEND = 159
  Rcmd2red[] = {              // Init for 7735R, part 2 (red tab only)
    2,                        //  2 commands in list:
    ST7735_CASET  , 4      ,  //  1: Column addr set, 4 args, no delay:
      0x00, 0x00,             //     XSTART = 0
      0x00, 0x7F,             //     XEND = 127
    ST7735_RASET  , 4      ,  //  2: Row addr set, 4 args, no delay:
      0x00, 0x00,             //     XSTART = 0
      0x00, 0x9F },           //     XEND = 159

  Rcmd2green144[] = {              // Init for 7735R, part 2 (green 1.44 tab)
    2,                        //  2 commands in list:
    ST7735_CASET  , 4      ,  //  1: Column addr set, 4 args, no delay:
      0x00, 0x00,             //     XSTART = 0
      0x00, 0x7F,             //     XEND = 127
    ST7735_RASET  , 4      ,  //  2: Row addr set, 4 args, no delay:
      0x00, 0x00,             //     XSTART = 0
      0x00, 0x7F },           //     XEND = 127

  Rcmd2green160x80[] = {            // 7735R init, part 2 (mini 160x80)
    2,                              //  2 commands in list:
    ST7735_CASET,   4,              //  1: Column addr set, 4 args, no delay:
      0x00, 0x00,                   //     XSTART = 0
      0x00, 0x4F,                   //     XEND = 79
    ST7735_RASET,   4,              //  2: Row addr set, 4 args, no delay:
      0x00, 0x00,                   //     XSTART = 0
      0x00, 0x9F },                 //     XEND = 159

  Rcmd3[] = {                 // Init for 7735R, part 3 (red or green tab)
    4,                        //  4 commands in list:
    ST7735_GMCTRP1, 16      , //  1: Magical unicorn dust, 16 args, no delay:
      0x02, 0x1c, 0x07, 0x12,
      0x37, 0x32, 0x29, 0x2d,
      0x29, 0x25, 0x2B, 0x39,
      0x00, 0x01, 0x03, 0x10,
    ST7735_GMCTRN1, 16      , //  2: Sparkles and rainbows, 16 args, no delay:
      0x03, 0x1d, 0x07, 0x06,
      0x2E, 0x2C, 0x29, 0x2D,
      0x2E, 0x2E, 0x37, 0x3F,
      0x00, 0x00, 0x02, 0x10,
    ST7735_NORON  ,    DELAY, //  3: Normal display on, no args, w/delay
      10,                     //     10 ms delay
    ST7735_DISPON ,    DELAY, //  4: Main screen turn on, no args w/delay
      100 };                  //     100 ms delay





void delay(int ms)
{
    TickType_t delay = ms / portTICK_PERIOD_MS;
    vTaskDelay(delay);
}

//This function is called (in irq context!) just before a transmission starts. It will
//set the D/C line to the value indicated in the user field.
void lcd_spi_pre_transfer_callback(spi_transaction_t *t)
{
    int dc=(int)t->user;
    gpio_set_level(LCD_PIN_DC, dc);
}


// set up GPIOs and reset the display, but don't initialize it yet
void lcd_init_hw(void)
{
    ESP_LOGI(TAG, "Initializing LCD control pins...");

    // these pins must be set to GPIO mode with gpio_config()
    gpio_config_t rst_cfg = {
        .pin_bit_mask = LCD_SEL_RST,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };

    gpio_config_t bckl_cfg = {
        .pin_bit_mask = LCD_SEL_BCKL,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };

    gpio_config_t dc_cfg = {
        .pin_bit_mask = LCD_SEL_DC,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };

    ESP_LOGI(TAG, "GPIO configuration...");
    gpio_config(&rst_cfg);
    gpio_config(&bckl_cfg);
    gpio_config(&dc_cfg);

    // Initialize the other GPIO
    gpio_set_direction(LCD_PIN_CS, GPIO_MODE_OUTPUT);

    ESP_LOGI(TAG, "Resetting display...");

    // Reset the display
    // toggle RST low to reset with CS low
    gpio_set_level(LCD_PIN_CS, 0);

    gpio_set_level(LCD_PIN_RST, 1);
    delay(50);
    gpio_set_level(LCD_PIN_RST, 0);
    delay(50);
    gpio_set_level(LCD_PIN_RST, 1);
    delay(50);
    gpio_set_level(LCD_PIN_CS, 1);

    ESP_LOGI(TAG, "LCD hardware initialized");
}

void lcd_init(void)
{
    ESP_LOGI(TAG, "Initializing SPI bus..");
    esp_err_t ret;
    spi_bus_config_t buscfg={
        .miso_io_num=LCD_PIN_MISO,
        .mosi_io_num=LCD_PIN_MOSI,
        .sclk_io_num=LCD_PIN_CLK,
        .quadwp_io_num=-1,
        .quadhd_io_num=-1
    };
    spi_device_interface_config_t devcfg={
        .clock_speed_hz=LCD_SPI_BUS_SPEED,      //SPI clock
        .mode=0,                                //SPI mode 0
        .spics_io_num=LCD_PIN_CS,               //CS pin
        .queue_size=32,                          //We want to be able to queue 16 transactions at a time
        .pre_cb=lcd_spi_pre_transfer_callback,  //Specify pre-transfer callback to handle D/C line
    };

    // init SPI bus
    ret=spi_bus_initialize(HSPI_HOST, &buscfg, 1);
    assert(ret==ESP_OK);

    // attach LCD to SPI bus
    ret=spi_bus_add_device(HSPI_HOST, &devcfg, &m_spi);
    assert(ret==ESP_OK);

    ESP_LOGI(TAG, "Initializing LCD...");

    // init LCD
    //lcd_initB();
    lcd_initR(INITR_MINI160x80);
    invertDisplay(1);

    // set rotation
    lcd_set_rotation(1);

    // init gfx routines
    gfx_set_text_wrap(1);
    gfx_set_text_size(1);

    m_frame_buf_size = (size_t)_width * (size_t)_height * sizeof(uint16_t);
    m_frame_buf = (uint16_t*) malloc(m_frame_buf_size);

    if (!m_frame_buf) {
        ESP_LOGE(TAG, "Can't alloc frame buffer of %zu bytes", m_frame_buf_size);
        return;
    }

    ESP_LOGI(TAG, "LCD Init complete, width=%d height=%d, frame buffer size=%zu", _width, _height, m_frame_buf_size);
}


void lcd_cmd(spi_device_handle_t spi, const uint8_t cmd)
{
    esp_err_t ret;
    spi_transaction_t t;
    memset(&t, 0, sizeof(t));       //Zero out the transaction
    t.length=8;                     //Command is 8 bits
    t.tx_buffer=&cmd;               //The data is the cmd itself
    t.user=(void*)0;                //D/C needs to be set to 0
    ret=spi_device_transmit(spi, &t);  //Transmit!
    assert(ret==ESP_OK);            //Should have had no issues.
}


void writecommand(uint8_t c)
{
    lcd_cmd(m_spi, c);
}


void lcd_data(spi_device_handle_t spi, const uint8_t *data, int len)
{
    esp_err_t ret;
    spi_transaction_t t;
    if (len==0) return;             //no need to send anything
    memset(&t, 0, sizeof(t));       //Zero out the transaction
    t.length=len*8;                 //Len is in bytes, transaction length is in bits.
    t.tx_buffer=data;               //Data
    t.user=(void*)1;                //D/C needs to be set to 1
    ret=spi_device_transmit(spi, &t);  //Transmit!
    assert(ret==ESP_OK);            //Should have had no issues.
}

void writedata(uint8_t c)
{
    lcd_data(m_spi, &c, sizeof(c));
}




// Companion code to the above tables.  Reads and issues
// a series of LCD commands stored in PROGMEM byte array.
void lcd_init_cmds(const uint8_t *addr)
{
    uint8_t  numCommands, numArgs;
    uint16_t ms;

    numCommands = *(addr++);      	// Number of commands to follow
    while(numCommands--) {      	// For each command...
        writecommand(*(addr++)); 	//   Read, issue command
        numArgs  = *(addr++);    	//   Number of args to follow
        ms       = numArgs & DELAY;     //   If hibit set, delay follows args
        numArgs &= ~DELAY;              //   Mask out delay bit
        while(numArgs--) {              //   For each argument...
            writedata(*(addr++));  	//     Read, issue argument
        }

        if(ms) {
            ms = *(addr++); 		// Read post-command delay time (ms)
            if(ms == 255) ms = 500;     // If 255, delay for 500 ms
            delay(ms);
        }
    }
}

// Initialization code common to both 'B' and 'R' type displays
void lcd_init_common(const uint8_t *cmdList)
{

  if(cmdList) lcd_init_cmds(cmdList);

  // Enable backlight
  gpio_set_level(LCD_PIN_BCKL, 1);
}

// Initialization for ST7735B screens
void lcd_initB(void)
{
  lcd_init_common(Bcmd);
}

// Initialization for ST7735R screens (green or red tabs)
void lcd_initR(uint8_t options)
{
    lcd_init_common(Rcmd1);
    if(options == INITR_GREENTAB) {
        lcd_init_cmds(Rcmd2green);
        colstart = 2;
        rowstart = 1;
    } else if(options == INITR_144GREENTAB) {
        _height = ST7735_TFTHEIGHT_144;
        lcd_init_cmds(Rcmd2green144);
        colstart = 2;
        rowstart = 3;
    } else if (options == INITR_MINI160x80) {
      _height = ST7735_TFTHEIGHT_160;
      _width = ST7735_TFTWIDTH_80;
      lcd_init_cmds(Rcmd2green160x80);
      colstart = 1;
      rowstart = 26;
    } else {
        // colstart, rowstart left at default '0' values
        lcd_init_cmds(Rcmd2red);
    }
    lcd_init_cmds(Rcmd3);

    // if black, change MADCTL color filter
    if (options == INITR_BLACKTAB || options == INITR_MINI160x80) {
        writecommand(ST7735_MADCTL);
        writedata(0xC0);
    }
    tabcolor = options;
}


void lcd_set_addr_window(uint8_t x0, uint8_t y0, uint8_t x1, uint8_t y1)
{
    uint8_t buf[4];

    writecommand(ST7735_CASET); // Column addr set

    buf[0] = 0x00;
    buf[1] = x0 + colstart; // XSTART
    buf[2] = 0x00;
    buf[3] = x1 + colstart; // XEND
    lcd_data(m_spi, buf, 4);

    writecommand(ST7735_RASET); // Row addr set

    buf[0] = 0x00;
    buf[1] = y0 + rowstart; // YSTART
    buf[2] = 0x00;
    buf[3] = y1 + rowstart; // YEND
    lcd_data(m_spi, buf, 4);

    writecommand(ST7735_RAMWR); // write to RAM
}

void lcd_draw_pixel(int16_t x, int16_t y, uint16_t color)
{
  if((x < 0) ||(x >= _width) || (y < 0) || (y >= _height)) return;

  m_frame_buf[((_height - y - 1) * _width) + x] = color;
}

void drawFastVLine(int16_t x, int16_t y, int16_t h, uint16_t color)
{
  // Rudimentary clipping
  if((x >= _width) || (y >= _height)) return;
  if((y+h-1) >= _height) h = _height-y;

  lcd_set_addr_window(x, y, x, y+h-1);

  while (h--)
      lcd_data(m_spi, (uint8_t*)&color, sizeof(color));
}


void drawFastHLine(int16_t x, int16_t y, int16_t w, uint16_t color)
{
  // Rudimentary clipping
  if((x >= _width) || (y >= _height)) return;
  if((x+w-1) >= _width)  w = _width-x;
  lcd_set_addr_window(x, y, x+w-1, y);

  while (w--)
      lcd_data(m_spi, (uint8_t*)&color, sizeof(color));

}


// fill a rectangle
void lcd_fill_rect(int16_t x, int16_t y, int16_t w, int16_t h, uint16_t color)
{
    // rudimentary clipping (drawChar w/big text requires this)
    if((x >= _width) || (y >= _height)) return;
    if((x + w - 1) >= _width)  w = _width  - x;
    if((y + h - 1) >= _height) h = _height - y;


    for(int iy=y+h-1; iy>=y; iy--) {
        for(int ix=x+w; ix>x; ix--) {
            m_frame_buf[((_height - iy-1) * _width) + ix - 1] = color;
        }
    }
}

void lcd_fill_screen(uint16_t color)
{
    lcd_fill_rect(0, 0,  _width, _height, color);
}


// Pass 8-bit (each) R,G,B, get back 16-bit packed color
uint16_t lcd_rgb565(uint8_t r, uint8_t g, uint8_t b)
{
    // do endian swap here for now -- this can definitely be more efficient
    uint16_t color = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
    return ((color & 0xFF) << 8) | ((color & 0xFF00) >> 8);
}

uint16_t lcd_rgb(uint8_t r, uint8_t g, uint8_t b)
{
    // do endian swap here for now -- this can definitely be more efficient
    uint16_t color = ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | (r >> 3);
    return ((color & 0xFF) << 8) | ((color & 0xFF00) >> 8);
}


void lcd_set_rotation(uint8_t m)
{
  uint8_t madctl = 0;

  rotation = m & 3; // can't be higher than 3

  // For ST7735 with GREEN TAB (including HalloWing)...
  if (tabcolor == INITR_144GREENTAB) {
    // ..._rowstart is 3 for rotations 0&1, 1 for rotations 2&3
    rowstart = (rotation < 2) ? 3 : 1;
  }

  switch (rotation) {
  case 0:
    if ((tabcolor == INITR_BLACKTAB) || (tabcolor == INITR_MINI160x80)) {
      madctl = ST7735_MADCTL_MX | ST7735_MADCTL_MY | ST7735_MADCTL_RGB;
    } else {
      madctl = ST7735_MADCTL_MX | ST7735_MADCTL_MY | ST7735_MADCTL_BGR;
    }

    if (tabcolor == INITR_144GREENTAB) {
      _height = ST7735_TFTHEIGHT_128;
      _width = ST7735_TFTWIDTH_128;
    } else if (tabcolor == INITR_MINI160x80) {
      _height = ST7735_TFTHEIGHT_160;
      _width = ST7735_TFTWIDTH_80;
    } else {
      _height = ST7735_TFTHEIGHT_160;
      _width = ST7735_TFTWIDTH_128;
    }
    //_xstart = _colstart;
    //_ystart = _rowstart;
    break;
  case 1:
    if ((tabcolor == INITR_BLACKTAB) || (tabcolor == INITR_MINI160x80)) {
      madctl = ST7735_MADCTL_MY | ST7735_MADCTL_MV | ST7735_MADCTL_RGB;
    } else {
      madctl = ST7735_MADCTL_MY | ST7735_MADCTL_MV | ST7735_MADCTL_BGR;
    }

    if (tabcolor == INITR_144GREENTAB) {
      _width = ST7735_TFTHEIGHT_128;
      _height = ST7735_TFTWIDTH_128;
    } else if (tabcolor == INITR_MINI160x80) {
      _width = ST7735_TFTHEIGHT_160;
      _height = ST7735_TFTWIDTH_80;
    } else {
      _width = ST7735_TFTHEIGHT_160;
      _height = ST7735_TFTWIDTH_128;
    }
    //_ystart = _colstart;
    //_xstart = _rowstart;
    break;
  case 2:
    if ((tabcolor == INITR_BLACKTAB) || (tabcolor == INITR_MINI160x80)) {
      madctl = ST7735_MADCTL_RGB;
    } else {
      madctl = ST7735_MADCTL_BGR;
    }

    if (tabcolor == INITR_144GREENTAB) {
      _height = ST7735_TFTHEIGHT_128;
      _width = ST7735_TFTWIDTH_128;
    } else if (tabcolor == INITR_MINI160x80) {
      _height = ST7735_TFTHEIGHT_160;
      _width = ST7735_TFTWIDTH_80;
    } else {
      _height = ST7735_TFTHEIGHT_160;
      _width = ST7735_TFTWIDTH_128;
    }
    //_xstart = _colstart;
    //_ystart = _rowstart;
    break;
  case 3:
    if ((tabcolor == INITR_BLACKTAB) || (tabcolor == INITR_MINI160x80)) {
      madctl = ST7735_MADCTL_MX | ST7735_MADCTL_MV | ST7735_MADCTL_RGB;
    } else {
      madctl = ST7735_MADCTL_MX | ST7735_MADCTL_MV | ST7735_MADCTL_BGR;
    }

    if (tabcolor == INITR_144GREENTAB) {
      _width = ST7735_TFTHEIGHT_128;
      _height = ST7735_TFTWIDTH_128;
    } else if (tabcolor == INITR_MINI160x80) {
      _width = ST7735_TFTHEIGHT_160;
      _height = ST7735_TFTWIDTH_80;
    } else {
      _width = ST7735_TFTHEIGHT_160;
      _height = ST7735_TFTWIDTH_128;
    }
    //_ystart = _colstart;
    //_xstart = _rowstart;
    break;
  }

  writecommand(ST7735_MADCTL);
  writedata(madctl);
}


void invertDisplay(uint8_t i)
{
    writecommand(i ? ST7735_INVON : ST7735_INVOFF);
}




// Draw a circle outline
void gfx_draw_circle(int16_t x0, int16_t y0, int16_t r, uint16_t color)
{
  int16_t f = 1 - r;
  int16_t ddF_x = 1;
  int16_t ddF_y = -2 * r;
  int16_t x = 0;
  int16_t y = r;

  lcd_draw_pixel(x0  , y0+r, color);
  lcd_draw_pixel(x0  , y0-r, color);
  lcd_draw_pixel(x0+r, y0  , color);
  lcd_draw_pixel(x0-r, y0  , color);

  while (x<y) {
    if (f >= 0) {
      y--;
      ddF_y += 2;
      f += ddF_y;
    }
    x++;
    ddF_x += 2;
    f += ddF_x;

    lcd_draw_pixel(x0 + x, y0 + y, color);
    lcd_draw_pixel(x0 - x, y0 + y, color);
    lcd_draw_pixel(x0 + x, y0 - y, color);
    lcd_draw_pixel(x0 - x, y0 - y, color);
    lcd_draw_pixel(x0 + y, y0 + x, color);
    lcd_draw_pixel(x0 - y, y0 + x, color);
    lcd_draw_pixel(x0 + y, y0 - x, color);
    lcd_draw_pixel(x0 - y, y0 - x, color);
  }
}

void gfx_write_string(uint16_t x, uint16_t y, char* str)
{
    gfx_set_cursor(x, y);
    for (unsigned int i=0; i<strlen(str); i++)
        gfx_write((uint8_t)str[i]);
}

void gfx_write(uint8_t c)
{
  if(!gfxFont) { // 'Classic' built-in font
    if(c == '\n') {
      cursor_y += textsize*8;
      cursor_x  = 0;
    } else if(c == '\r') {
      // skip em
    } else {
      if(wrap && ((cursor_x + textsize * 6) >= _width)) { // Heading off edge?
        cursor_x  = 0;            // Reset x to zero
        cursor_y += textsize * 8; // Advance y one line
      }
      gfx_draw_char(cursor_x, cursor_y, c, textcolor, textbgcolor, textsize);
      cursor_x += textsize * 6;
    }

  } else { // Custom font
    if(c == '\n') {
      cursor_x  = 0;
      cursor_y += (int16_t)textsize *
                  (uint8_t)gfxFont->yAdvance;
    } else if(c != '\r') {
      uint8_t first = gfxFont->first;
      if((c >= first) && (c <= (uint8_t)gfxFont->last)) {
        uint8_t   c2    = c - gfxFont->first;
        GFXglyph *glyph = &(((GFXglyph *)gfxFont->glyph)[c2]);
        uint8_t   w     = glyph->width,
                  h     = glyph->height;
        if((w > 0) && (h > 0)) { // Is there an associated bitmap?
          int16_t xo = (int8_t)glyph->xOffset; // sic
          if(wrap && ((cursor_x + textsize * (xo + w)) >= _width)) {
            // Drawing character would go off right edge; wrap to new line
            cursor_x  = 0;
            cursor_y += (int16_t)textsize *
                        (uint8_t)gfxFont->yAdvance;
          }
          gfx_draw_char(cursor_x, cursor_y, c, textcolor, textbgcolor, textsize);
        }
        cursor_x += glyph->xAdvance * (int16_t)textsize;
      }
    }
  }
}

// Draw a character
void gfx_draw_char(int16_t x, int16_t y, unsigned char c, uint16_t color, uint16_t bg, uint8_t size)
{

  if(!gfxFont) { // 'Classic' built-in font

    if((x >= _width)            || // Clip right
       (y >= _height)           || // Clip bottom
       ((x + 6 * size - 1) < 0) || // Clip left
       ((y + 8 * size - 1) < 0))   // Clip top
      return;

    for(int8_t i=0; i<6; i++ ) {
      uint8_t line;
      if(i < 5) line = *(font+(c*5)+i);
      else      line = 0x0;
      for(int8_t j=0; j<8; j++, line >>= 1) {
        if(line & 0x1) {
          if(size == 1) lcd_draw_pixel(x+i, y+j, color);
          else          lcd_fill_rect(x+(i*size), y+(j*size), size, size, color);
        } else if(bg != color) {
          if(size == 1) lcd_draw_pixel(x+i, y+j, bg);
          else          lcd_fill_rect(x+i*size, y+j*size, size, size, bg);
        }
      }
    }

  } else { // Custom font

    // Character is assumed previously filtered by write() to eliminate
    // newlines, returns, non-printable characters, etc.  Calling gfx_draw_char()
    // directly with 'bad' characters of font may cause mayhem!

    c -= gfxFont->first;
    GFXglyph *glyph  = &(((GFXglyph *)gfxFont->glyph)[c]);
    uint8_t  *bitmap = (uint8_t *)gfxFont->bitmap;

    uint16_t bo = glyph->bitmapOffset;
    uint8_t  w  = glyph->width,
        h  = glyph->height;
//             xa = glyph->xAdvance;
    int8_t   xo = glyph->xOffset,
             yo = glyph->yOffset;
    uint8_t  xx, yy, bits = 0, bit = 0;
    int16_t  xo16 = 0, yo16 = 0;

    if(size > 1) {
      xo16 = xo;
      yo16 = yo;
    }

    // Todo: Add character clipping here

    // NOTE: THERE IS NO 'BACKGROUND' COLOR OPTION ON CUSTOM FONTS.
    // THIS IS ON PURPOSE AND BY DESIGN.  The background color feature
    // has typically been used with the 'classic' font to overwrite old
    // screen contents with new data.  This ONLY works because the
    // characters are a uniform size; it's not a sensible thing to do with
    // proportionally-spaced fonts with glyphs of varying sizes (and that
    // may overlap).  To replace previously-drawn text when using a custom
    // font, use the getTextBounds() function to determine the smallest
    // rectangle encompassing a string, erase the area with lcd_fill_rect(),
    // then draw new text.  This WILL infortunately 'blink' the text, but
    // is unavoidable.  Drawing 'background' pixels will NOT fix this,
    // only creates a new set of problems.  Have an idea to work around
    // this (a canvas object type for MCUs that can afford the RAM and
    // displays supporting setAddrWindow() and pushColors()), but haven't
    // implemented this yet.

    for(yy=0; yy<h; yy++) {
      for(xx=0; xx<w; xx++) {
        if(!(bit++ & 7)) {
          bits = bitmap[bo++];
        }
        if(bits & 0x80) {
          if(size == 1) {
            lcd_draw_pixel(x+xo+xx, y+yo+yy, color);
          } else {
            lcd_fill_rect(x+(xo16+xx)*size, y+(yo16+yy)*size, size, size, color);
          }
        }
        bits <<= 1;
      }
    }

  } // End classic vs custom font

}


void gfx_set_cursor(int16_t x, int16_t y)
{
  cursor_x = x;
  cursor_y = y;
}

int16_t gfx_get_cursor_x(void)
{
  return cursor_x;
}

int16_t gfx_get_cursor_y(void)
{
  return cursor_y;
}

void gfx_set_text_size(uint8_t s)
{
  textsize = (s > 0) ? s : 1;
}

void gfx_set_text_color(uint16_t c)
{
  // For 'transparent' background, we'll set the bg
  // to the same as fg instead of using a flag
  textcolor = textbgcolor = c;
}

void gfx_set_text_color_bg(uint16_t c, uint16_t b)
{
  textcolor   = c;
  textbgcolor = b;
}

void gfx_set_text_wrap(uint8_t w)
{
  wrap = w;
}


void gfx_set_font(const GFXfont *f)
{
  if(f) {          // Font struct pointer passed in?
    if(!gfxFont) { // And no current font struct?
      // Switching from classic to new font behavior.
      // Move cursor pos down 6 pixels so it's on baseline.
      cursor_y += 6;
    }
  } else if(gfxFont) { // NULL passed.  Current font struct defined?
    // Switching from new to classic font behavior.
    // Move cursor pos up 6 pixels so it's at top-left of char.
    cursor_y -= 6;
  }
  gfxFont = (GFXfont *)f;
}


/*********************************************************
 * Not from Adafruit's GFX library below here
 *********************************************************/

void gfx_refresh()
{
    esp_err_t ret;
    spi_transaction_t t;

    lcd_set_addr_window(0, 0, _width-1, _height-1);

    // zero out the transaction
    memset(&t, 0, sizeof(t));
    // transaction length is in bits.
    t.length = (_width * sizeof(uint16_t)) * 8;
    // DC set to 1
    t.user=(void*)1;

    for (int y=_height-1; y>=0; y--) {
        // data buffer
        t.tx_buffer = (uint8_t*)&m_frame_buf[y * _width];
        // transmit
        ret=spi_device_transmit(m_spi, &t);
        assert(ret==ESP_OK);
    }
}

void gfx_refresh_rect(int16_t x, int16_t y, int16_t w, int16_t h)
{
    esp_err_t ret;
    spi_transaction_t t;

    lcd_set_addr_window(x, y, x+w-1, y+h-1);

    // zero out the transaction
    memset(&t, 0, sizeof(t));
    // transaction length is in bits.
    t.length = (w * sizeof(uint16_t)) * 8;
    // DC set to 1
    t.user=(void*)1;

    for (int iy=y; iy<y+h-1; iy++) {
        // data buffer
        t.tx_buffer = (uint8_t*)&m_frame_buf[((_height - iy - 1) * _width) + x];
        // transmit
        ret=spi_device_transmit(m_spi, &t);
        assert(ret==ESP_OK);
    }
}


/* load a raw 565 bitmap file from sd card  .. must be in a very specific format and size
 * TODO: not very robust, needs lots of cleanup.  just a proof of concept for now.
 *
 * preprocess images using imagemagick for resizing/scaling and ffmpeg for 565 conversion...
 *
 * resize to 128x160 - ( force to fit with \! ):
 * convert myimage.jpg -resize 128x160\! myimage-scaled.bmp
 *
 * convert to rgb565be (big endian) using ffmpeg:
 * ffmpeg -vcodec bmp -i myimage-scaled.bmp -vcodec rawvideo -f rawvideo -pix_fmt rgb565be myimage.raw
 *
 * copy file to SD card
 *
 */
void gfx_load_rgb565_bitmap(int16_t x, int16_t y, int16_t w, int16_t h, char *filename)
{
    int r;
    uint8_t buf[128*2];

    lcd_set_addr_window(0, 0, x+w-1, y+h-1);

    ESP_LOGI(TAG, "taking sdcard mutex...");
    xSemaphoreTake(g_sdcard_mutex, portMAX_DELAY);

    FILE *f = fopen(filename, "r");

    if (!f) {
        ESP_LOGE(TAG, "can't open filename %s", filename);
        return;
    }

    do {
        r = fread(buf, sizeof(buf), 1, f);
        if (r)
            lcd_data(m_spi, buf, sizeof(buf));
    } while (!feof(f));


    fclose(f);

    xSemaphoreGive(g_sdcard_mutex);
    ESP_LOGI(TAG, "gave sdcard mutex...");
}

/*==============================================================*/

/*
  Based in part on Adafruit_ST7735.cpp
  from https://github.com/adafruit/Adafruit-ST7735-Library
  **************************************************
  This is a library for the Adafruit 1.8" SPI display.

This library works with the Adafruit 1.8" TFT Breakout w/SD card
  ----> http://www.adafruit.com/products/358
The 1.8" TFT shield
  ----> https://www.adafruit.com/product/802
The 1.44" TFT breakout
  ----> https://www.adafruit.com/product/2088
as well as Adafruit raw 1.8" TFT display
  ----> http://www.adafruit.com/products/618

  Check out the links above for our tutorials and wiring diagrams
  These displays use SPI to communicate, 4 or 5 pins are required to
  interface (RST is optional)
  Adafruit invests time and resources providing this open source code,
  please support Adafruit and open-source hardware by purchasing
  products from Adafruit!

  Written by Limor Fried/Ladyada for Adafruit Industries.
  MIT license, all text above must be included in any redistribution
 ****************************************************/

/*
  Based in part on Adafruit_GFX.cpp
  https://github.com/adafruit/Adafruit-GFX-Library

This is the core graphics library for all our displays, providing a common
set of graphics primitives (points, lines, circles, etc.).  It needs to be
paired with a hardware-specific library for each display device we carry
(to handle the lower-level functions).

Adafruit invests time and resources providing this open source code, please
support Adafruit & open-source hardware by purchasing products from Adafruit!

Copyright (c) 2013 Adafruit Industries.  All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
- Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
*/


/*
  Based in part on ESP-IDF spi_master.c example
  from https://github.com/espressif/esp-idf/tree/master/examples/peripherals/spi_master

  SPI Master example

   This example code is in the Public Domain (or CC0 licensed, at your option.)

   Unless required by applicable law or agreed to in writing, this
   software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
   CONDITIONS OF ANY KIND, either express or implied.
*/
