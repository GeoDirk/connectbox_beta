# -*- coding: utf-8 -*-

"""
===========================================
  page_main.py
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
from datetime import datetime
import subprocess
import axp209

from HAT_Utilities import get_device, display_settings


try:
    import psutil
except ImportError:
    print("The psutil library was not found. Run 'sudo -H pip install psutil' to install it.")
    sys.exit()

def get_connected_users():
    #iw dev wlan0 station dump | grep -c Station
    #result = subprocess.run(['iw', 'dev wlan0 station dump | grep -c Station'], stdout=subprocess.PIPE)
    #result.stdout.decode('utf-8')

    c = subprocess.run(['iw', 'dev', 'wlan0', 'station', 'dump'], stdout=subprocess.PIPE)
    connected_user_count = len([line for line in c.stdout.decode("utf-8").split('\n') if line.startswith("Station")])
    return "%s" % connected_user_count

def draw_page(device):
    # get an image
    dir_path = os.path.dirname(os.path.abspath(__file__))
    img_path =  dir_path + '/assets/main_page.png'
    base = Image.open(img_path).convert('RGBA')
    fff = Image.new(base.mode, base.size, (255,) * 4)
    img = Image.composite(base, fff, base)

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', base.size, (255,255,255,0))

    # get a font
    font_path = os.path.abspath('connectbox.ttf')
    font30 = ImageFont.truetype(font_path, 28)
    font20 = ImageFont.truetype(font_path, 20)
    font14 = ImageFont.truetype(font_path, 14)

    # get a drawing context
    d = ImageDraw.Draw(txt)

    # ConnectBox Banner
    d.text((2, 0), 'ConnectBox', font=font30, fill="black")
    # Image version name/number
    d.text((41, 32), 'slimy frog', font=font14, fill="black")
    
    # connected users
    d.text((15, 35), get_connected_users(), font=font30, fill="black")

    #open up the battery monitoring library
    axp = axp209.AXP209()
    
    if not axp.power_input_status.acin_present:
        # not charging - cover up symbol
        d.rectangle((72, 48, 79, 61), fill="white") #charge symbol

    #draw battery fill lines
    if not axp.battery_exists:
        #cross out the battery
        d.line((46, 51, 65, 58), fill="black", width=2)
        d.line((46, 58, 65, 51), fill="black", width=2)
    else:
        #get the percent filled and draw a rectangle
        percent = axp.battery_gauge
        if percent > 0 and percent < 10:
            d.rectangle((46, 51, 48, 58), fill="black")
            d.text((51, 51), "!", font=font14, fill="black")
        elif  percent > 10:
            x = int((65 - 46) * (percent / 100)) + 46 #start of battery level= 20px, end = 38px
            #print("X:" + str(x))
            d.rectangle((46, 51, x, 58), fill="black")

       # percent charge left
    d.text((82,49), "%.0f%%" % axp.battery_gauge, font=font14, fill="black")

    axp.close()
     
    out = Image.alpha_composite(img, txt)
    device.display(out.convert(device.mode))

def main():
    device = get_device()
    draw_page(device)
    return
    

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass