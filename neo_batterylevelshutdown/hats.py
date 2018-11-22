# -*- coding: utf-8 -*-

from contextlib import contextmanager
import logging
import os
import os.path
import time
import axp209
from .HAT_Utilities import setup_gpio_pin
from .HAT_Utilities import readPin
from .HAT_Utilities import writePin
from .HAT_Utilities import get_device
from .HAT_Utilities import blink_LEDxTimes
from PIL import Image
from . import page_none
from . import page_main
from . import page_battery
from . import page_info
from . import page_stats
from . import page_memory
from . import page_battery_low

# Common
GPIO_EXPORT_FILE = "/sys/class/gpio/export"

PAGE_COUNT = 12  # range of Pages Class minus 1


# Q3Y2018 - OLED Unit run specific pins

PIN_HIGH = "1"
PIN_LOW = "0"


@contextmanager
def min_execution_time(min_time_secs):
    """
    Runs the logic within the context handler for at least min_time_secs

    This function will sleep in order to pad out the execution time if the
    logic within the context handler finishes early
    """
    start_time = time.monotonic()
    yield
    duration = time.monotonic() - start_time
    # If the function has run over the min execution time, don't sleep
    period = max(0, min_time_secs - duration)
    logging.debug("sleeping for %s seconds", period)
    time.sleep(period)


class AbstractHAT(object):

    PIN_LED = 6  # PA6 pin

    def initializePins(self):
        initialisationSuccess = True
        logging.info("Intializing Pins")
        # Fail if any of the pins can't be setup
        for pin, direction in self.pins_to_initialise:
            if not setup_gpio_pin(pin, direction):
                logging.warning("Unable to setup pin %s with direction %s",
                                pin, direction
                                )
                initialisationSuccess = False
        return initialisationSuccess

    def entryPoint(self):
        # Throw away the return value to allow pre-release hardware to be used
        self.initializePins()
        self.mainLoop()
        logging.info("Exiting for Shutdown")
        os.system("shutdown now")


class DummyHAT(AbstractHAT):
    def entryPoint(self):
        logging.info("There is no HAT, so there's nothing to do")


class q1y2018HAT(AbstractHAT):

    DEFAULT_LOW_VOLTAGE_ITERATIONS_BEFORE_SHUTDOWN = 3
    PIN_VOLT_3_0 = 198  # PG6 pin - shutdown within 30 seconds
    PIN_VOLT_3_2 = 199  # PG7 pin - above 3.2V
    PIN_VOLT_3_4 = 200  # PG8 pin - above 3.4V
    PIN_VOLT_3_6 = 201  # PG9 pin - above 3.6V

    def __init__(self):
        self.pins_to_initialise = [
            (self.PIN_LED, "out"),
            (self.PIN_VOLT_3_0, "in"),
            (self.PIN_VOLT_3_2, "in"),
            (self.PIN_VOLT_3_4, "in"),
            (self.PIN_VOLT_3_6, "in")
        ]
        super().__init__()

    def mainLoop(self):
        """
        monitors battery voltage and shuts down the device when levels are low
        """
        lv_iterations_remaining = \
            self.DEFAULT_LOW_VOLTAGE_ITERATIONS_BEFORE_SHUTDOWN
        logging.info("Starting Monitoring")
        while True:
            with min_execution_time(min_time_secs=10):
                # check if voltage is above 3.6V
                if readPin(self.PIN_VOLT_3_6):
                    # Show solid LED
                    writePin(self.PIN_LED, "0")
                    continue

                # check if voltage is above 3.4V
                if readPin(self.PIN_VOLT_3_4):
                    blink_LEDxTimes(self.PIN_LED, 1)
                    continue

                # check if voltage is above 3.2V
                if readPin(self.PIN_VOLT_3_2):
                    blink_LEDxTimes(self.PIN_LED, 2)
                    continue

                # check if voltage is above 3.0V
                if readPin(self.PIN_VOLT_3_0):
                    blink_LEDxTimes(self.PIN_LED, 3)
                    # pin voltage above 3V so reset iteration
                    # XXX - if voltage transitions from 2.9->3.3 then this will
                    #       not be reset. Consider robustifying
                    lv_iterations_remaining = \
                        self.DEFAULT_LOW_VOLTAGE_ITERATIONS_BEFORE_SHUTDOWN
                    continue

                # pin voltage is below 3V so we need to do a few
                # iterations to make sure that we are still getting
                # the same info each time
                lv_iterations_remaining -= 1
                if lv_iterations_remaining == 0:
                    # Time to shutdown
                    break
                else:
                    blink_LEDxTimes(self.PIN_LED, 4)


class Pages:
    page_none, page_main, page_info, page_bat, page_memory, page_h1_stats, \
        page_h2_stats, page_d1_stats, page_d2_stats, page_w1_stats, \
        page_w2_stats, page_m1_stats, page_m2_stats = range(13)


class OledHAT(AbstractHAT):

    def __init__(self):
        self.axp = axp209.AXP209()

    @staticmethod
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

    def TransitionPage(self, bChange, newPage):
        if bChange:
            if newPage == Pages.page_none:
                page_none.main()
            elif newPage == Pages.page_main:
                page_main.main(self.axp)
            elif newPage == Pages.page_info:
                page_info.main()
            elif newPage == Pages.page_bat:
                page_battery.main(self.axp)
            elif newPage == Pages.page_memory:
                page_memory.main()
            elif newPage == Pages.page_h1_stats:
                page_stats.main('hour', 1)
            elif newPage == Pages.page_h2_stats:
                page_stats.main('hour', 2)
            elif newPage == Pages.page_d1_stats:
                page_stats.main('day', 1)
            elif newPage == Pages.page_d2_stats:
                page_stats.main('day', 2)
            elif newPage == Pages.page_w1_stats:
                page_stats.main('week', 1)
            elif newPage == Pages.page_w2_stats:
                page_stats.main('week', 2)
            elif newPage == Pages.page_m1_stats:
                page_stats.main('month', 1)
            elif newPage == Pages.page_m2_stats:
                page_stats.main('month', 2)

        return newPage

    def batteryLevelAbovePercent(self, level):
        logging.info("Battery Level: " + str(self.axp.battery_gauge) + "%")
        return self.axp.battery_gauge > level

    def BatteryPresent(self):
        return self.axp.battery_exists

    def mainLoop(self):
        # draw the connectbox logo
        self.draw_logo()
        time.sleep(3)

        # set an OLED display timeout
        OLED_TIMEOUT = 20  # seconds
        timeout = int(round(time.time() * 1000))

        # start with a blank page
        curPage = Pages.page_none
        page_none.main()
        # loop through the buttons looking for changes
        # and check the battery state
        iCheckBat = 0
        iShutdownTimer = 0
        bShutdownStart = False
        while True:
            buttonState = self.CheckButtonState()
            if sum(buttonState) > 0:
                # at least one button was pressed
                timeout = int(round(time.time() * 1000))
                changed, newPage = self.ProcessButtons(curPage, *buttonState)
                curPage = self.TransitionPage(changed, newPage)
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
                if self.BatteryPresent():
                    logging.debug("Bat Loop\n")
                    iCheckBat = 0
                    if self.batteryLevelAbovePercent(4):
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
                    # exit to trigger a shutdown
                    page_none.main()
                    break
        return


class q3y2018HAT(OledHAT):

    PIN_L_BUTTON = 1  # PA1 left button
    PIN_M_BUTTON = 199  # PG7 middle button
    PIN_R_BUTTON = 200  # PG8 pin right button

    def __init__(self):
        self. pins_to_initialise = [
            (self.PIN_LED, "out"),
            (self.PIN_L_BUTTON, "in"),
            (self.PIN_M_BUTTON, "in"),
            (self.PIN_R_BUTTON, "in")
        ]
        super().__init__()

    def CheckButtonState(self):
        L_Button = not readPin(self.PIN_L_BUTTON)
        M_Button = not readPin(self.PIN_M_BUTTON)
        R_Button = not readPin(self.PIN_R_BUTTON)
        logging.debug("Button state L:%s M:%s R:%s",
                      L_Button, M_Button, R_Button)
        return L_Button, M_Button, R_Button

    def ProcessButtons(self, curPage, L_Button, M_Button, R_Button):
        '''
        L botton is go back button
        M button is go forward button
        R button is ???
        '''
        bChange = False
        if L_Button:
            # move forward in the page stack
            if curPage == PAGE_COUNT:
                curPage = 0
            else:
                curPage += 1
            bChange = True
        elif M_Button:
            # move backward in the page stack
            if curPage == 0:
                curPage = PAGE_COUNT
            else:
                curPage -= 1
            bChange = True
        elif R_Button:
            # Right button - turn on/off display
            curPage = 0
            bChange = True

        return bChange, curPage


class q4y2018HAT(OledHAT):

    # Q4Y2018 - AXP209/OLED (Anker) Unit run specific pins
    PIN_L_BUTTON = 198  # PG6 left button
    PIN_R_BUTTON = 199  # PG7 middle button

    def __init__(self):
        self. pins_to_initialise = [
            (self.PIN_LED, "out"),
            (self.PIN_L_BUTTON, "in"),
            (self.PIN_R_BUTTON, "in")
        ]

    def CheckButtonState(self):
        L_Button = not readPin(self.PIN_L_BUTTON)
        R_Button = not readPin(self.PIN_R_BUTTON)
        logging.debug("Button state L:%s R:%s",
                      L_Button, R_Button)
        return L_Button, R_Button

    def ProcessButtons(self, curPage, L_Button, R_Button):
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

        return bChange, curPage
