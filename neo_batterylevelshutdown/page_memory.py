# -*- coding: utf-8 -*-

"""
===========================================
  page_memory.py
  https://github.com/ConnectBox/NEO_BatteryLevelShutdown
  License: MIT
  Version 1.0
  GeoDirk - May 2018
===========================================
"""

import sys
import os.path
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from .HAT_Utilities import get_device


try:
    import psutil
except ImportError:
    print("The psutil library was not found. "
          "Run 'sudo -H pip install psutil' to install it.")
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


def mem_usage():
    return psutil.virtual_memory()


def disk_usage(dir):
    return psutil.disk_usage(dir)


def cpu_usage():
    return psutil.cpu_percent(interval=0)


def network(iface):
    return psutil.net_io_counters(pernic=True)[iface]


def draw_page(device):
    # get an image
    dir_path = os.path.dirname(os.path.abspath(__file__))
    img_path = dir_path + '/assets/memory_page.png'
    base = Image.open(img_path).convert('RGBA')
    fff = Image.new(base.mode, base.size, (255,) * 4)
    img = Image.composite(base, fff, base)

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', base.size, (255, 255, 255, 0))

    # get a font
    font_path = dir_path + '/assets/connectbox.ttf'
    font18 = ImageFont.truetype(font_path, 18)
    # get a drawing context
    d = ImageDraw.Draw(txt)

    # cpu usage
    d.text((50, 1), "%.0f%%" % cpu_usage(), font=font18, fill="black")

    # memory usage
    usage = mem_usage()
    d.text((50, 21), "%.0f%%" %
           (100 - usage.percent), font=font18, fill="black")
    d.text((85, 21), "%s" % bytes2human(usage.used), font=font18, fill="black")

    # disk usage
    usage = disk_usage('/media/usb0')  # <--TODO put in the right mount point
    d.text((50, 42), "%.0f%%" % usage.percent, font=font18, fill="black")
    d.text((85, 42), "%s" % bytes2human(usage.used), font=font18, fill="black")

    out = Image.alpha_composite(img, txt)
    device.display(out.convert(device.mode))


def main():
    device = get_device()
    draw_page(device)
    # while True:
    #    i = 1
    return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
