"""
===========================================
  stats_page.py
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
import json

from HAT_Utilities import get_device, display_settings

def readStatsJSON(dt_range):
    with open('/var/www/connectbox/connectbox_default/stats.top10.json') as json_file:  
        data = json.load(json_file)
        print('============================')
        print('     ' + dt_range)
        print('============================')
        for p in data[dt_range]:
            print('file: ' + p['resource'])
            print('count: ' + str(p['count']))
    print('')

'''
def draw_page():
    # get an image
    dir_path = os.path.dirname(os.path.abspath(__file__))
    img_path =  dir_path + '/assets/info_page.png'
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
    d.text((12, 41), "%.1f" % 3.7, font=font18, fill="black")
    d.text((58, 41), "%.1f" % 67.253, font=font18, fill="black")
    d.text((95, 41), "%d%%" % 76.35, font=font18, fill="black")
     
    out = Image.alpha_composite(img, txt)
    device.display(out.convert(device.mode))
'''
 	
def main():
    device = get_device()
    readStatsJSON('hour')
    readStatsJSON('day')
    readStatsJSON('week')
    readStatsJSON('month')
    readStatsJSON('year')

    #draw_page()
    #time.sleep(3)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass