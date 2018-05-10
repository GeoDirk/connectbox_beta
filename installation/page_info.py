# -*- coding: utf-8 -*-

"""
===========================================
  info_page.py
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

def mem_usage():
    return psutil.virtual_memory()

def get_connected_users():
    #iw dev wlan0 station dump | grep -c Station
    #result = subprocess.run(['iw', 'dev wlan0 station dump | grep -c Station'], stdout=subprocess.PIPE)
    #result.stdout.decode('utf-8')

    c = subprocess.run(['iw', 'dev', 'wlan0', 'station', 'dump'], stdout=subprocess.PIPE)
    connected_user_count = len([line for line in c.stdout.decode("utf-8").split('\n') if line.startswith("Station")])
    return "%s" % connected_user_count

def disk_usage(dir):
    return psutil.disk_usage(dir)

def network(iface):
    return psutil.net_io_counters(pernic=True)[iface]

def draw_page(device):
    # get an image
    dir_path = os.path.dirname(os.path.abspath(__file__))
    img_path =  dir_path + '/assets/info_page.png'
    #img_path = os.path.abspath('info_page.png')
    base = Image.open(img_path).convert('RGBA')
    fff = Image.new(base.mode, base.size, (255,) * 4)
    #background = Image.new("RGBA", device.size, "white")
    img = Image.composite(base, fff, base)

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', base.size, (255,255,255,0))

    # get a font
    font_path = os.path.abspath('connectbox.ttf')
    font20 = ImageFont.truetype(font_path, 22)
    font18 = ImageFont.truetype(font_path, 18)
    font14 = ImageFont.truetype(font_path, 14)
    # get a drawing context
    d = ImageDraw.Draw(txt)

    # uptime
    d.text((50, 0), uptime(), font=font18, fill="black")

    # connected users
    d.text((18, 21), get_connected_users(), font=font20, fill="black")
    
    # network stats
    try:
        stat = network('wlan0')       
        d.text((12, 41), "Tx%s" % bytes2human(stat.bytes_sent), font=font14, fill="black")
        d.text((12, 51), "Rx%s" % bytes2human(stat.bytes_recv), font=font14, fill="black")
    except KeyError:
        # no wifi enabled/available
        pass
    
    # memory usage
    usage = mem_usage()
    d.text((58, 35), "%s" % bytes2human(usage.used), font=font18, fill="black")
    d.text((58, 48), "%.0f%%" % (100 - usage.percent), font=font18, fill="black")
    
    # disk usage
    usage = disk_usage('/')
    d.text((91, 35), "%s" % bytes2human(usage.used), font=font18, fill="black") # <--TODO put in the right mount point
    d.text((91, 48), "%.0f%%" % usage.percent, font=font18, fill="black") # <--TODO put in the right mount point
     
    out = Image.alpha_composite(img, txt)
    device.display(out.convert(device.mode))

def main():
    device = get_device()
    while True:
        draw_page(device)
        time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass