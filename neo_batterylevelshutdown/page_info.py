# -*- coding: utf-8 -*-

"""
===========================================
  page_info.py
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

def bytes2human(n):
    """
    >>> bytes2human(10000)
    '9K'
    >>> bytes2human(100001221)
    '95M'
    """
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = int(float(n) / prefix[s])
            return '%s%s' % (value, s)
    return "%sB" % n

def uptime():
    # uptime
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    return "Up: %s" % (str(uptime).split('.')[0])

def get_connected_users():
    #iw dev wlan0 station dump | grep -c Station
    #result = subprocess.run(['iw', 'dev wlan0 station dump | grep -c Station'], stdout=subprocess.PIPE)
    #result.stdout.decode('utf-8')

    c = subprocess.run(['iw', 'dev', 'wlan0', 'station', 'dump'], stdout=subprocess.PIPE)
    connected_user_count = len([line for line in c.stdout.decode("utf-8").split('\n') if line.startswith("Station")])
    return "%s" % connected_user_count

def network(iface):
    return psutil.net_io_counters(pernic=True)[iface]

def draw_page(device):
    # get an image
    dir_path = os.path.dirname(os.path.abspath(__file__))
    img_path =  dir_path + '/assets/info_page.png'
    base = Image.open(img_path).convert('RGBA')
    fff = Image.new(base.mode, base.size, (255,) * 4)
    img = Image.composite(base, fff, base)

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', base.size, (255,255,255,0))

    # get a font
    font_path = os.path.abspath('connectbox.ttf')
    font20 = ImageFont.truetype(font_path, 26)
    font18 = ImageFont.truetype(font_path, 18)
    font14 = ImageFont.truetype(font_path, 14)
    # get a drawing context
    d = ImageDraw.Draw(txt)

    # uptime
    d.text((50, 0), uptime(), font=font18, fill="black")

    # connected users
    d.text((20, 30), get_connected_users(), font=font20, fill="black")
    
    # network stats
    try:
        stat = network('wlan0')       
        d.text((58, 35), "Tx: %s" % bytes2human(stat.bytes_sent), font=font18, fill="black")
        d.text((58, 47), "Rx: %s" % bytes2human(stat.bytes_recv), font=font18, fill="black")
    except KeyError:
        # no wifi enabled/available
        pass
         
    out = Image.alpha_composite(img, txt)
    device.display(out.convert(device.mode))

def main():
    device = get_device()
    draw_page(device)
    #while True:
    #    i = 1
    return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass