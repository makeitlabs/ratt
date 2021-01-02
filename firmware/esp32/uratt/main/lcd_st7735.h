#ifndef _LCD_ST7735_H
#define _LCD_ST7735_H


// bus speed for SPI clock
// works up to 20MHz on hand-wired prototype with logic analyzer connected
#define ONE_MHZ 1000000
#define LCD_SPI_BUS_SPEED (8 * ONE_MHZ)


// raft of defines from Adafruit library below
// some flags for initR() :(
#define INITR_GREENTAB 0x0
#define INITR_REDTAB   0x1
#define INITR_BLACKTAB   0x2

#define INITR_18GREENTAB    INITR_GREENTAB
#define INITR_18REDTAB      INITR_REDTAB
#define INITR_18BLACKTAB    INITR_BLACKTAB
#define INITR_144GREENTAB   0x1
#define INITR_MINI160x80 		0x04


#define ST7735_TFTWIDTH_80 80

#define ST7735_TFTWIDTH  128
#define ST7735_TFTWIDTH_128 128
#define ST7735_TFTHEIGHT_128 128
#define ST7735_TFTHEIGHT_144 128
#define ST7735_TFTHEIGHT_18  160
#define ST7735_TFTHEIGHT_160 160


#define ST7735_NOP     0x00
#define ST7735_SWRESET 0x01
#define ST7735_RDDID   0x04
#define ST7735_RDDST   0x09

#define ST7735_SLPIN   0x10
#define ST7735_SLPOUT  0x11
#define ST7735_PTLON   0x12
#define ST7735_NORON   0x13

#define ST7735_INVOFF  0x20
#define ST7735_INVON   0x21
#define ST7735_DISPOFF 0x28
#define ST7735_DISPON  0x29
#define ST7735_CASET   0x2A
#define ST7735_RASET   0x2B
#define ST7735_RAMWR   0x2C
#define ST7735_RAMRD   0x2E

#define ST7735_PTLAR   0x30
#define ST7735_COLMOD  0x3A
#define ST7735_MADCTL  0x36

#define ST7735_MADCTL_MY 0x80
#define ST7735_MADCTL_MX 0x40
#define ST7735_MADCTL_MV 0x20
#define ST7735_MADCTL_ML 0x10
#define ST7735_MADCTL_RGB 0x00

#define ST7735_FRMCTR1 0xB1
#define ST7735_FRMCTR2 0xB2
#define ST7735_FRMCTR3 0xB3
#define ST7735_INVCTR  0xB4
#define ST7735_DISSET5 0xB6

#define ST7735_PWCTR1  0xC0
#define ST7735_PWCTR2  0xC1
#define ST7735_PWCTR3  0xC2
#define ST7735_PWCTR4  0xC3
#define ST7735_PWCTR5  0xC4
#define ST7735_VMCTR1  0xC5

#define ST7735_RDID1   0xDA
#define ST7735_RDID2   0xDB
#define ST7735_RDID3   0xDC
#define ST7735_RDID4   0xDD

#define ST7735_PWCTR6  0xFC

#define ST7735_GMCTRP1 0xE0
#define ST7735_GMCTRN1 0xE1

// Color definitions
#define	ST7735_BLACK   0x0000
#define	ST7735_BLUE    0x001F
#define	ST7735_RED     0xF800
#define	ST7735_GREEN   0x07E0
#define ST7735_CYAN    0x07FF
#define ST7735_MAGENTA 0xF81F
#define ST7735_YELLOW  0xFFE0
#define ST7735_WHITE   0xFFFF

#define ST7735_MADCTL_BGR 0x08
#define ST7735_MADCTL_MH 0x04

typedef struct { // Data stored PER GLYPH
	uint16_t bitmapOffset;     // Pointer into GFXfont->bitmap
	uint8_t  width, height;    // Bitmap dimensions in pixels
	uint8_t  xAdvance;         // Distance to advance cursor (x axis)
	int8_t   xOffset, yOffset; // Dist from cursor pos to UL corner
} GFXglyph;

typedef struct { // Data stored for FONT AS A WHOLE:
	uint8_t  *bitmap;      // Glyph bitmaps, concatenated
	GFXglyph *glyph;       // Glyph array
	uint8_t   first, last; // ASCII extents
	uint8_t   yAdvance;    // Newline distance (y axis)
} GFXfont;



void lcd_init_hw(void);
void lcd_init(void);
void lcd_set_rotation(uint8_t m);
void lcd_fill_screen(uint16_t color);
void lcd_fill_rect(int16_t x, int16_t y, int16_t w, int16_t h, uint16_t color);
uint16_t lcd_rgb565(uint8_t r, uint8_t g, uint8_t b);
uint16_t lcd_rgb(uint8_t r, uint8_t g, uint8_t b);
void invertDisplay(uint8_t i);


void gfx_draw_circle(int16_t x0, int16_t y0, int16_t r, uint16_t color);
void gfx_draw_char(int16_t x, int16_t y, unsigned char c, uint16_t color, uint16_t bg, uint8_t size);
void gfx_write_string(uint16_t x, uint16_t y, char* str);
void gfx_write(uint8_t c);
void gfx_set_cursor(int16_t x, int16_t y);
int16_t gfx_get_cursor_x(void);
int16_t gfx_get_cursor_y(void);
void gfx_set_text_size(uint8_t s);
void gfx_set_text_color(uint16_t c);
void gfx_set_text_color_bg(uint16_t c, uint16_t b);
void gfx_set_text_wrap(uint8_t w);
void gfx_set_font(const GFXfont *f);

void gfx_load_rgb565_bitmap(int16_t x, int16_t y, int16_t w, int16_t h, char *filename);
void gfx_refresh();
void gfx_refresh_rect(int16_t x, int16_t y, int16_t w, int16_t h);



#endif
