# i2c_lcd.py
from LCD_API import LcdApi  # capital letters must match the filename
from machine import I2C
from time import sleep_ms

MASK_RS = 0x01
MASK_RW = 0x02
MASK_E = 0x04
SHIFT_BACKLIGHT = 3
SHIFT_DATA = 4

class I2cLcd(LcdApi):
    """I2C LCD driver for ESP32 with PCF8574 backpack"""

    def __init__(self, i2c, i2c_addr, num_lines, num_columns):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.i2c.writeto(self.i2c_addr, bytearray([0]))
        sleep_ms(20)

        # Reset 3 times
        self.hal_write_init_nibble(LcdApi.LCD_FUNCTION_RESET)
        sleep_ms(5)
        self.hal_write_init_nibble(LcdApi.LCD_FUNCTION_RESET)
        sleep_ms(1)
        self.hal_write_init_nibble(LcdApi.LCD_FUNCTION_RESET)
        sleep_ms(1)
        # Put LCD into 4-bit mode
        self.hal_write_init_nibble(LcdApi.LCD_FUNCTION)

        # Initialize API
        LcdApi.__init__(self, num_lines, num_columns)

        # Set function
        cmd = LcdApi.LCD_FUNCTION
        if num_lines > 1:
            cmd |= LcdApi.LCD_FUNCTION_2LINES
        self.hal_write_command(cmd)

    # --- HAL implementations ---
    def hal_write_init_nibble(self, nibble):
        byte = ((nibble >> 4) & 0x0f) << SHIFT_DATA
        self.i2c.writeto(self.i2c_addr, bytearray([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytearray([byte]))

    def hal_backlight_on(self):
        byte = MASK_E | (1 << SHIFT_BACKLIGHT) if self.backlight else MASK_E
        self.i2c.writeto(self.i2c_addr, bytearray([byte]))

    def hal_backlight_off(self):
        self.i2c.writeto(self.i2c_addr, bytearray([0]))

    def hal_write_command(self, cmd):
        self._write_byte(cmd, rs=0)
        if cmd <= 3:
            sleep_ms(5)

    def hal_write_data(self, data):
        self._write_byte(data, rs=1)

    # --- low-level ---
    def _write_byte(self, byte, rs):
        high = ((byte >> 4) & 0x0F) << SHIFT_DATA
        low = (byte & 0x0F) << SHIFT_DATA
        backlight_bit = (1 << SHIFT_BACKLIGHT) if self.backlight else 0

        # Send high nibble
        self.i2c.writeto(self.i2c_addr, bytearray([high | backlight_bit | (MASK_RS if rs else 0) | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytearray([high | backlight_bit | (MASK_RS if rs else 0)]))

        # Send low nibble
        self.i2c.writeto(self.i2c_addr, bytearray([low | backlight_bit | (MASK_RS if rs else 0) | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytearray([low | backlight_bit | (MASK_RS if rs else 0)]))
