# ===== Imports =====
import network
import urequests as requests
import ubinascii
import ujson
import time
from machine import I2C, Pin
from I2C_LCD import I2cLcd  

# ===== WiFi Configuration =====

SSID = "ESP32-Hotspot"
PASSWORD = "*************"

# ===== LCD Configuration =====
I2C_SCL = 22
I2C_SDA = 21
I2C_ADDR = 0x27
LCD_ROWS = 2
LCD_COLS = 16

API_KEY = "********************"
API_SECRET = "********************"
USE_DEMO = False  
DOMAIN = "demo.trading212.com" if USE_DEMO else "live.trading212.com"
BASE_URL = f"https://{DOMAIN}/api/v0"

# ===== Functions =====

def connect_wifi():
    try:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        
        if not wlan.isconnected():
            print("Connecting to WiFi...")
            wlan.connect(SSID, PASSWORD)
            start = time.time()
            while not wlan.isconnected() and time.time() - start < 15:
                time.sleep(0.5)
                
        if wlan.isconnected():
            print("Connected! IP:", wlan.ifconfig()[0])
            return True
        
        else:
            print("Failed to connect WiFi")
            return False

    except:
        connect_wifi()

def test_connection():
    try:
        r = requests.get("http://example.com")
        if r.status_code == 200:
            print("Internet OK")
            return True
    except:
        pass
    
    return False

def fetch_portfolio():
    try:
        # Basic Auth header
        auth_bytes = "{}:{}".format(API_KEY, API_SECRET).encode()
        encoded_auth = ubinascii.b2a_base64(auth_bytes).decode().strip()
        headers = {
            "Authorization": "Basic {}".format(encoded_auth),
            "Accept": "application/json"
        }

        r = requests.get(BASE_URL + "/equity/portfolio", headers=headers)
        if r.status_code != 200:
            print("API error:", r.status_code)
            return []

        data = ujson.loads(r.text)
        simplified = []
        
        for p in data:
            total_value = p['quantity'] * p['currentPrice']
            simplified.append({
                'ticker': p['ticker'],
                'quantity': round(p['quantity'], 2),
                'currentPrice': round(p['currentPrice'], 2),
                'ppl': round(p['ppl'], 2),
                'totalValue': round(total_value, 2)
            })
        
        simplified.sort(key=lambda x: x['totalValue'], reverse=True)
        
        return simplified

    except Exception as e:
        print("Fetch error:", e)
        return []

def scroll_text(lcd, text, row=0, delay=0.4):
    text = text + " " * LCD_COLS
    for i in range(len(text) - LCD_COLS + 1):
        lcd.move_to(0, row)
        lcd.putstr(text[i:i+LCD_COLS])
        time.sleep(delay)

def display_portfolio(lcd, portfolio):
    if not portfolio:
        lcd.putstr("No data or error")
        time.sleep(5)
        return

    for stock in portfolio:
        arrow = '^ ' if stock['ppl'] >= 0 else 'v '
        
        line1 = f"{stock['ticker']} ${stock['currentPrice']}"
        line2 = f"{arrow}{stock['ppl']} T{stock['totalValue']}"

        lcd.move_to(0, 0)
        lcd.putstr("{:<{width}}".format(line1, width=LCD_COLS))

        lcd.move_to(0, 1)
        lcd.putstr("{:<{width}}".format(line2, width=LCD_COLS))

        time.sleep(60)

# ===== Main Program =====
if connect_wifi() and test_connection():
    i2c = I2C(scl=Pin(I2C_SCL), sda=Pin(I2C_SDA))
    lcd = I2cLcd(i2c, I2C_ADDR, LCD_ROWS, LCD_COLS)
    lcd.clear()
    lcd.putstr("WiFi connected")

    while True:
        portfolio = fetch_portfolio()
        display_portfolio(lcd, portfolio)
else:
    print("Cannot start program, WiFi/Internet error")
