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

from HAT_Utilities import get_device, display_settings


try:
    import psutil
except ImportError:
    print("The psutil library was not found. Run 'sudo -H pip install psutil' to install it.")
    sys.exit()

def draw_page(device):
    # get an image
    dir_path = os.path.dirname(os.path.abspath(__file__))
    img_path =  dir_path + '/assets/main_page.png'
    #img_path = os.path.abspath('info_page.png')
    base = Image.open(img_path).convert('RGBA')
    fff = Image.new(base.mode, base.size, (255,) * 4)
    #background = Image.new("RGBA", device.size, "white")
    img = Image.composite(base, fff, base)

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', base.size, (255,255,255,0))

    # get a font
    font_path = os.path.abspath('connectbox.ttf')
    font30 = ImageFont.truetype(font_path, 28)

    # get a drawing context
    d = ImageDraw.Draw(txt)

    # uptime
    d.text((2, 0), 'ConnectBox', font=font30, fill="black")
     
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