# -*- coding: utf-8 -*-

"""
===========================================
  Q32018.py
  https://github.com/ConnectBox/NEO_BatteryLevelShutdown
  License: MIT
  Version 1.0
  GeoDirk - May 2018
===========================================
"""
import logging
import os
import time
import threading
import sys
import os.path
from PIL import Image
from PIL import ImageFont
from luma.core import cmdline, error
from luma.core.render import canvas
import axp209
import subprocess
import page_main
import page_battery
import page_info
import page_stats


from enum import Enum

from HAT_Utilities import setup_gpio_pin, readPin, blink_LEDxTimes, get_device

class Pages:
    page_main, page_bat, page_info, page_stats = range(4)

# Common pins between HATs
PIN_LED = 6  # PA6 pin

# Q3Y2018 - OLED Unit run specific pins
PIN_L_BUTTON = 1  # PA1 left button
PIN_M_BUTTON = 199 # PG7 middle button
PIN_R_BUTTON = 200  # PG8 pin right button

PIN_HIGH = "1"
PIN_LOW = "0"

def draw_logo():
    device = get_device()

    img_path = os.path.abspath('connectbox_logo.png')
    logo = Image.open(img_path).convert("RGBA")
    fff = Image.new(logo.mode, logo.size, (255,) * 4)
    background = Image.new("RGBA", device.size, "white")
    posn = ((device.width - logo.width) // 2, 0)
    img = Image.composite(logo, fff, logo)
    background.paste(img, posn)
    device.display(background.convert(device.mode))

def initializePins():
    logging.info("Intializing OLED HAT Pins")
    return setup_gpio_pin(PIN_LED, "out") and \
        setup_gpio_pin(PIN_L_BUTTON, "in") and \
        setup_gpio_pin(PIN_M_BUTTON, "in") and \
        setup_gpio_pin(PIN_R_BUTTON, "in")

def CheckButtonState():
    L_Button = not readPin(PIN_L_BUTTON)
    M_Button = not readPin(PIN_M_BUTTON)
    R_Button = not readPin(PIN_R_BUTTON)
    #print("L:%s M:%s R:%s" % (L_Button, M_Button, R_Button))
    return L_Button, M_Button, R_Button

def ProcessButtons(curPage,L_Button,M_Button,R_Button):
    '''
    L botton is go back button
    M button is go forward button
    R button is ???
    '''
    print('ProcessButton.0:' + str(curPage))
    print("L:%s M:%s R:%s" % (L_Button, M_Button, R_Button))

    bChange = False
    if L_Button == True:
        #move forward in the page stack
        if  curPage == Pages.page_main:
            curPage = curPage + 1
        bChange = True
    elif M_Button == True:
        #move forward in the page stack
        bChange = True
    elif R_Button == True:
        #Right button - unknown yet what to do
        bChange = True

    if bChange == True:
        print('ProcessButton.bChange=true')
        if  curPage == Pages.page_main:
            page_main.main()
        elif curPage == Pages.page_bat:
            page_battery.main()
        elif curPage == Pages.page_info:
            page_info.main()
        elif curPage == Pages.page_stats:
            page_stats.main()
    
    print('ProcessButton.1:' + str(curPage))
    return curPage

def Main_Q3Y2018():
    """
    OLED Version of HAT Detected
    """    
    if not initializePins():
        logging.error("Errors during pin setup. Aborting")
        return False

    draw_logo()
    time.sleep(3)

    # start on the main page
    curPage = Pages.page_main
    page_main.main()
    #loop through the buttons looking for changes
    while True:
        L,M,R = CheckButtonState()
        curPage = ProcessButtons(curPage,L,M,R)
        print('Main_Q3Y2018.0:' + str(curPage))
        print('-----------------------')
        time.sleep(2)

    return

def entryPoint():
    if not initializePins():
        logging.error("Errors during pin setup. Aborting")
        return False

    Main_Q3Y2018()
    logging.info("Exiting for Shutdown\n")
    #os.system("shutdown now") <-TODO enable for production
