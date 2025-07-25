import hid
import time
import threading
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem as item

running = True

class HyperXBatteryReader:
    def __init__(self, vendor_id=0x03f0, product_id=0x05b7):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.device = None
        self.request = bytes([0x66, 0x89] + [0x00] * 62)

    def connect(self):
        devices = hid.enumerate()
        for d in devices:
            if d['vendor_id'] == self.vendor_id and d['product_id'] == self.product_id:
                self.device = hid.device()
                self.device.open_path(d['path'])
                return True
        return False

    def read_battery(self):
        try:
            self.device.write(self.request)
            time.sleep(0.1)
            self.device.set_nonblocking(1)
            for _ in range(50):
                data = self.device.read(64)
                if data and data[0] == 0x66 and data[1] == 0x89: # (66 battery, 89 level value (possibly)) (self.request)
                                                                 # could be device specific, but i found this using 
                                                                 # wireshark. im not a reverse engineer. 
                                                                 # i just fucked around and found out and got lucky
                    return data[4]
                time.sleep(0.01)
        except:
            return None

    def close(self):
        if self.device:
            self.device.close()

def get_battery_status():
    reader = HyperXBatteryReader()
    if reader.connect():
        percent = reader.read_battery()
        reader.close()
        return percent
    return None


def render_text_icon(text):
    image = Image.new('RGB', (16, 16), color='black')
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", 10)
    except:
        font = ImageFont.load_default()
    
    text = text[:3]
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # centering
    x = (16 - text_width) // 2 - bbox[0]
    y = (16 - text_height) // 2 - bbox[1]

    draw.text((x, y), text, font=font, fill="white")
    return image


def update_icon(icon):
    while True:
        percent = get_battery_status()
        if percent is not None and 0 <= percent <= 100:
            icon.icon = render_text_icon(str(percent))
            icon.title = f"HyperX Battery: {percent}%"
        else:
            icon.icon = render_text_icon("N/A")
            icon.title = "HyperX Battery: N/A"
        time.sleep(30)
        
def quit_program(icon, item):
    global running
    running = False
    icon.stop()

def setup_tray():
    icon = pystray.Icon("hyperx_battery")
    icon.icon = render_text_icon("...")
    icon.title = "HyperX Battery"
    icon.menu = pystray.Menu(item("Quit", quit_program))
    threading.Thread(target=update_icon, args=(icon,), daemon=True).start()
    icon.run()

if __name__ == "__main__":
    setup_tray()
