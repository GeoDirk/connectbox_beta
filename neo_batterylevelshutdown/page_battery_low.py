# -*- coding: utf-8 -*-

"""
===========================================
  page_battery_low.py
  https://github.com/ConnectBox/NEO_BatteryLevelShutdown
  License: MIT
  Version 1.0
  GeoDirk - May 2018
===========================================
"""

import os.path
from PIL import Image
from .HAT_Utilities import get_device


def draw_page(device):
    dir_path = os.path.dirname(os.path.abspath(__file__))

    img_path = dir_path + '/assets/battery_low.png'

    base = Image.open(img_path).convert('RGBA')
    fff = Image.new(base.mode, base.size, (255,) * 4)
    img = Image.composite(base, fff, base)

    device.display(img.convert(device.mode))


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
