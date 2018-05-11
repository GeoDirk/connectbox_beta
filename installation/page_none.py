# -*- coding: utf-8 -*-

"""
===========================================
  page_none.py
  https://github.com/ConnectBox/NEO_BatteryLevelShutdown
  License: MIT
  Version 1.0
  GeoDirk - May 2018
===========================================
"""

import sys
from HAT_Utilities import get_device, display_settings


def draw_page(device):
    #turn off the OLED
    device.cleanup()

def main():
    device = get_device()
    draw_page(device)
    return
    

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass