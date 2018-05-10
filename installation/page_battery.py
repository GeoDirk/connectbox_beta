# -*- coding: utf-8 -*-

"""
===========================================
  page_battery.py
  https://github.com/ConnectBox/NEO_BatteryLevelShutdown
  License: MIT
  Version 1.0
  GeoDirk - May 2018
===========================================
"""

import sys
import os.path
import time
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from luma.core import cmdline, error
from luma.core.render import canvas
import axp209

from HAT_Utilities import get_device, display_settings

def draw_page(device):
    # get an image
    dir_path = os.path.dirname(os.path.abspath(__file__))
    img_path =  dir_path + '/assets/battery_page.png'
    base = Image.open(img_path).convert('RGBA')
    fff = Image.new(base.mode, base.size, (255,) * 4)
    #background = Image.new("RGBA", device.size, "white")
    img = Image.composite(base, fff, base)

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', base.size, (255,255,255,0))

    # get a font
    font_path = os.path.abspath('connectbox.ttf')
    font18 = ImageFont.truetype(font_path, 18)
    # get a drawing context
    d = ImageDraw.Draw(txt)

    # draw text, full opacity
    axp = axp209.AXP209()
    d.text((12, 41), "%.1fmV" % axp.battery_voltage, font=font18, fill="black")
    d.text((58, 41), "%.2f" % axp.internal_temperature, font=font18, fill="black")
    d.text((95, 41), "%d%%" % axp.battery_gauge, font=font18, fill="black")
    axp.close()

    out = Image.alpha_composite(img, txt)
    device.display(out.convert(device.mode))

    '''
    #axp = axp209.AXP209()
    draw.text((14, 35), "%.1fmV" % axp.battery_voltage, font=font10, fill="white")
    draw.text((60, 35), "%.2f" % axp.internal_temperature, font=font10, fill="white")
    draw.text((92, 35), "%d%%" % axp.battery_gauge, font=font10, fill="white")

    print("internal_temperature: %.2fC" % axp.internal_temperature)
    print("battery_exists: %s" % axp.battery_exists)
    print("battery_charging: %s" % ("charging" if axp.battery_charging else "done"))
    print("battery_current_direction: %s" % ("charging" if axp.battery_current_direction else "discharging"))
    print("battery_voltage: %.1fmV" % axp.battery_voltage)
    print("battery_discharge_current: %.1fmA" % axp.battery_discharge_current)
    print("battery_charge_current: %.1fmA" % axp.battery_charge_current)
    print("battery_gauge: %d%%" % axp.battery_gauge)
    '''
    #axp.close()
 	
def main():
    device = get_device()
    while True:
        draw_page(device)
        time.sleep(10)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass