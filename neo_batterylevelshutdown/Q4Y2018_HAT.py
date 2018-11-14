# -*- coding: utf-8 -*-

"""
===========================================
  Q4Y2018.py
  https://github.com/ConnectBox/NEO_BatteryLevelShutdown
  License: MIT
  Version 1.0
   DorJamJr - November 2018 
    from original Q32018.py code by GeoDirk - May 2018
===========================================
"""
import logging
import os
import time
import os.path
import axp209
from PIL import Image
from . import page_none
from . import page_main
from . import page_battery
from . import page_info
from . import page_stats
from . import page_memory
from . import page_battery_low

from .HAT_Utilities import setup_gpio_pin, readPin, get_device


class Pages:
    page_none, page_main, page_info, page_bat, page_memory, page_h1_stats, \
        page_h2_stats, page_d1_stats, page_d2_stats, page_w1_stats, \
        page_w2_stats, page_m1_stats, page_m2_stats = range(13)


PAGE_COUNT = 12  # range of Pages Class minus 1

# Common pins between HATs
PIN_LED = 6  # PA6 pin

# Q4Y2018 - AXP209/OLED (Anker) Unit run specific pins
PIN_L_BUTTON = 198  # PG6 left button
PIN_R_BUTTON = 199  # PG7 middle button

PIN_HIGH = "1"
PIN_LOW = "0"


def draw_logo():
    device = get_device()

    dir_path = os.path.dirname(os.path.abspath(__file__))
    img_path = dir_path + '/assets/connectbox_logo.png'
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
        setup_gpio_pin(PIN_R_BUTTON, "in")


def CheckButtonState():
    L_Button = not readPin(PIN_L_BUTTON)
    R_Button = not readPin(PIN_R_BUTTON)
    # print("L:%s R:%s" % (L_Button, R_Button))
    return L_Button, R_Button


def ProcessButtons(curPage, L_Button, R_Button):
    '''
    L botton is go back button
    R button is go forward button
    '''
    bChange = False
    if L_Button:
        # move forward in the page stack
        if curPage == PAGE_COUNT:
            curPage = 0
        else:
            curPage += 1
        bChange = True
    elif R_Button:
        # move backward in the page stack
        if curPage == 0:
            curPage = PAGE_COUNT
        else:
            curPage -= 1
        bChange = True

    if bChange:
        if curPage == Pages.page_none:
            page_none.main()
        elif curPage == Pages.page_main:
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


def CheckBatteryLevel(level):
    # open up the battery monitoring library
    axp = axp209.AXP209()
    logging.info("Battery Level: " + str(axp.battery_gauge) + "%")
    if axp.battery_gauge > level:
        axp.close()
        return True
    else:
        axp.close()
        return False


def BatteryPresent():
    # open up the battery monitoring library
    axp = axp209.AXP209()
    bRet = axp.battery_exists
    axp.close()
    return bRet


def Main_Q4Y2018():
    """
    OLED Version of HAT Detected
    """
    if not initializePins():
        logging.error("Errors during pin setup. Aborting")
        return False

    # draw the connectbox logo
    draw_logo()
    time.sleep(3)

    # set an OLED display timeout
    OLED_TIMEOUT = 20  # seconds
    timeout = int(round(time.time() * 1000))

    # start on the main page
    curPage = Pages.page_none
    page_none.main()
    # loop through the buttons looking for changes
    # and check the battery state
    iCheckBat = 0
    iShutdownTimer = 0
    bShutdownStart = False
    while True:
        L, R = CheckButtonState()
        if L + R > 0:
            # at least one button was pressed
            timeout = int(round(time.time() * 1000))
            curPage = ProcessButtons(curPage, L, R)
        else:
            # leave the battery shutdown page up if present
            if not bShutdownStart:
                # check for OLED timeout
                curTime = int(round(time.time() * 1000))
                if (curTime - timeout) > (OLED_TIMEOUT * 1000):
                    # timeout hit reset the clock and clear the display
                    timeout = int(round(time.time() * 1000))
                    curPage = Pages.page_none
                    page_none.main()

        time.sleep(0.4)

        # check the battery level
        iCheckBat += 1
        if iCheckBat > 70:  # 70 = ~30 seconds
            # check if battery present
            if BatteryPresent():
                logging.debug("Bat Loop\n")
                iCheckBat = 0
                if CheckBatteryLevel(4):  # 4 = 4% battery level
                    logging.debug("Battery Check TRUE\n")
                    bShutdownStart = False
                    iShutdownTimer = 0
                    # we are above the limit so reset display
                    if curPage != Pages.page_none:
                        curPage = Pages.page_none
                        page_none.main()
                else:
                    logging.debug("Battery Check FALSE\n")
                    # display battery low page
                    bShutdownStart = True
                    page_battery_low.main()

        # start a loop to see if we need to shutdown
        if bShutdownStart:
            iShutdownTimer += 1
            if iShutdownTimer > 140:  # 140 = ~60 seconds
                logging.info("Exiting for Shutdown\n")
                page_none.main()
                os.system("shutdown now")
    return


def entryPoint():
    if not initializePins():
        logging.error("Errors during pin setup. Aborting")
        return False

    Main_Q4Y2018()
    # If we were exiting the main loop on some battery-low signal,
    #  we'd have a logging statement and shutdown command here as
    #  we do with the Q1Y2018 HAT.
