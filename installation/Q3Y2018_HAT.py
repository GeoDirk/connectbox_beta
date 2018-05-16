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
import page_none
import page_main
import page_battery
import page_info
import page_stats
import page_memory


from enum import Enum

from HAT_Utilities import setup_gpio_pin, readPin, blink_LEDxTimes, get_device

class Pages:
    page_none, page_main, page_info, page_bat, page_memory, page_h1_stats, \
    page_h2_stats, page_d1_stats, page_d2_stats, page_w1_stats, page_w2_stats, \
    page_m1_stats, page_m2_stats = range(13)

PAGE_COUNT = 12 #range of Pages Class minus 1

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
    background = Image.new("RGBA", device.size, "black")
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
    bChange = False
    if L_Button == True:
        #move forward in the page stack
        if  curPage == PAGE_COUNT:
            curPage = 0
        else:
            curPage += 1
        bChange = True
    elif M_Button == True:
        #move backward in the page stack
        if  curPage == 0:
            curPage = PAGE_COUNT
        else:
            curPage -= 1
        bChange = True
    elif R_Button == True:
        #Right button - turn on/off display
        curPage = 0
        bChange = True

    if bChange == True:
        if  curPage == Pages.page_none:
            page_none.main()
        elif  curPage == Pages.page_main:
            page_main.main()
        elif curPage == Pages.page_info:
            page_info.main()
        elif curPage == Pages.page_bat:
            page_battery.main()            
        elif curPage == Pages.page_memory:
            page_memory.main()
        elif curPage == Pages.page_h1_stats:
            page_stats.main('hour', 1)
        elif curPage == Pages.page_h2_stats:
            page_stats.main('hour', 2)
        elif curPage == Pages.page_d1_stats:
            page_stats.main('day', 1)
        elif curPage == Pages.page_d2_stats:
            page_stats.main('day', 2)
        elif curPage == Pages.page_w1_stats:
            page_stats.main('week', 1)
        elif curPage == Pages.page_w2_stats:
            page_stats.main('week', 2)
        elif curPage == Pages.page_m1_stats:
            page_stats.main('month', 1)
        elif curPage == Pages.page_m2_stats:
            page_stats.main('month', 2)

    
    return curPage

def Main_Q3Y2018():
    """
    OLED Version of HAT Detected
    """    
    if not initializePins():
        logging.error("Errors during pin setup. Aborting")
        return False
    
    #draw the connectbox logo
    draw_logo()
    time.sleep(3)

    #set an OLED display timeout
    OLED_TIMEOUT = 20 #seconds
    timeout = int(round(time.time() * 1000))

    # start on the main page
    curPage = Pages.page_none
    page_none.main()
    #loop through the buttons looking for changes
    while True:
        L,M,R = CheckButtonState()
        if L + M + R > 0:
            #at least one button was pressed
            timeout = int(round(time.time() * 1000))
            curPage = ProcessButtons(curPage,L,M,R)
        else:
            #check for OLED timeout
            curTime = int(round(time.time() * 1000))
            if (curTime - timeout) > (OLED_TIMEOUT * 1000):
                #timeout hit reset the clock and clear the display
                timeout = int(round(time.time() * 1000))
                curPage = Pages.page_none
                page_none.main()

        time.sleep(0.4)
    return

def entryPoint():
    if not initializePins():
        logging.error("Errors during pin setup. Aborting")
        return False

    Main_Q3Y2018()
    logging.info("Exiting for Shutdown\n")
    #os.system("shutdown now") <-TODO enable for production
