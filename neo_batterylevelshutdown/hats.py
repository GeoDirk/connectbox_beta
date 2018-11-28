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
    logging.debug("sleeping for %s seconds to guarantee min exec time", period)
    time.sleep(period)


class AbstractHAT(object):

    # PA6 pin
    PIN_LED = 6  # PA6 pin

    def __init__(self):
        # Throw away the return value to allow pre-release hardware to be used
        self.initializePins()

    def initializePins(self):
        initialisationSuccess = True
        logging.info("Initializing Pins")
        # Fail if any of the pins can't be setup
        for pin, direction in self.pins_to_initialise:
            if not setup_gpio_pin(pin, direction):
                logging.warning("Unable to setup pin %s with direction %s",
                                pin, direction
                                )
                initialisationSuccess = False
        return initialisationSuccess

    def shutdownDevice(self):
        logging.info("Exiting for Shutdown")
        os.system("shutdown now")


class DummyHAT(AbstractHAT):
    pins_to_initialise = []

    def mainLoop(self):
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
                if readPin(self.PIN_VOLT_3_6):
                    # Voltage above 3.6V
                    # Show solid LED
                    writePin(self.PIN_LED, "0")
                    continue

                logging.debug("Battery voltage below 3.6V")
                if readPin(self.PIN_VOLT_3_4):
                    # Voltage above 3.4V
                    blink_LEDxTimes(self.PIN_LED, 1)
                    continue

                logging.debug("Battery voltage below 3.4V")
                if readPin(self.PIN_VOLT_3_2):
                    # Voltage above 3.2V
                    blink_LEDxTimes(self.PIN_LED, 2)
                    # Reset the low voltage loop counter in case we're
                    #  recovering from a below-3.0V situation
                    # XXX - if voltage transitions from 2.9->3.3 then this will
                    #       not be reset. Consider robustifying
                    lv_iterations_remaining = \
                        self.DEFAULT_LOW_VOLTAGE_ITERATIONS_BEFORE_SHUTDOWN
                    continue

                logging.info("Battery voltage below 3.2V")
                if readPin(self.PIN_VOLT_3_0):
                    # Voltage above 3.0V
                    blink_LEDxTimes(self.PIN_LED, 3)
                    # Given battery voltage is below 3.2V, we want to perform
                    #  a controlled shutdown so that the hardware cutoff is
                    #  not triggered (see below).
                    # We want to make sure we're really below 3.2V, so we read
                    #  on a few iterations to make sure that we are still
                    #  getting the same info each time before triggering
                    #  a controlled shutdown
                    if lv_iterations_remaining == 0:
                        logging.warning("Exiting main loop for shutdown")
                        # Time to shutdown
                        self.shutdownDevice()
                    else:
                        logging.info("Low voltage. %s loop(s) remaining",
                                     lv_iterations_remaining)
                        blink_LEDxTimes(self.PIN_LED, 4)
                        lv_iterations_remaining -= 1
                        continue

                logging.warning("Battery voltage below 3.0V")
                # The circuitry on the HAT triggers a shutdown of the 5V
                #  converter once battery voltage goes below 3.0V. It gives
                #  an 8 second grace period before yanking the power, so
                #  if we're here, then we're about to get the power yanked
                #  anyway so attempt a graceful shutdown immediately.
                logging.warning("Immediately exiting main loop for shutdown")
                self.shutdownDevice()


class Pages:
    page_none, page_main, page_info, page_bat, page_memory, page_h1_stats, \
        page_h2_stats, page_d1_stats, page_d2_stats, page_w1_stats, \
        page_w2_stats, page_m1_stats, page_m2_stats = range(13)


class OledHAT(AbstractHAT):

    SHUTDOWN_WARNING_PERIOD_SECS = 60
    BATTERY_CHECK_FREQUENCY_SECS = 30
    BATTERY_SHUTDOWN_THRESHOLD_PERC = 4
    DISPLAY_TIMEOUT_SECS = 20
    # What to show after startup and blank screen
    STARTING_PAGE_INDEX = 0  # the main page

    def __init__(self):
        self.axp = axp209.AXP209()
        self.display_device = get_device()
        self.blank_page = page_none.PageBlank(self.display_device)
        self.low_battery_page = \
            page_battery_low.PageBatteryLow(self.display_device)
        self.pages = [
            page_main.PageMain(self.display_device, self.axp),
            page_info.PageInfo(self.display_device),
            page_battery.PageBattery(self.display_device, self.axp),
            page_memory.PageMemory(self.display_device),
            page_stats.PageStats(self.display_device, 'hour', 1),
            page_stats.PageStats(self.display_device, 'hour', 2),
            page_stats.PageStats(self.display_device, 'day', 1),
            page_stats.PageStats(self.display_device, 'day', 2),
            page_stats.PageStats(self.display_device, 'week', 1),
            page_stats.PageStats(self.display_device, 'week', 2),
            page_stats.PageStats(self.display_device, 'month', 1),
            page_stats.PageStats(self.display_device, 'month', 2),
        ]
        self.curPage = self.blank_page
        super().__init__()

    def draw_logo(self):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        img_path = dir_path + '/assets/connectbox_logo.png'
        logo = Image.open(img_path).convert("RGBA")
        fff = Image.new(logo.mode, logo.size, (255,) * 4)
        background = Image.new("RGBA", self.display_device.size, "black")
        posn = ((self.display_device.width - logo.width) // 2, 0)
        img = Image.composite(logo, fff, logo)
        background.paste(img, posn)
        self.display_device.display(
            background.convert(self.display_device.mode)
        )

    def batteryLevelAbovePercent(self, level):
        logging.debug("Battery Level: " + str(self.axp.battery_gauge) + "%")
        return self.axp.battery_gauge > level

    def BatteryPresent(self):
        return self.axp.battery_exists

    def mainLoop(self):
        # draw the connectbox logo
        self.draw_logo()
        time.sleep(3)

        # no shutdown currently scheduled
        scheduledShutdownTime = 0
        # set an OLED display timeout
        displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS
        nextBatteryCheckTime = time.time() + self.BATTERY_CHECK_FREQUENCY_SECS

        # blank the screen given we've shown the logo for long enough
        self.curPage = self.blank_page
        self.curPage.draw_page()
        # loop through the buttons looking for changes
        # and check the battery state
        while True:
            buttonState = self.CheckButtonState()
            if sum(buttonState) > 0:
                # at least one button was pressed
                self.ProcessButtons(*buttonState)
                self.curPage.draw_page()
                # reset the display power off time
                displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS

            if time.time() > displayPowerOffTime:
                # Power off the display
                if self.curPage != self.blank_page:
                    self.curPage = self.blank_page
                    self.curPage.draw_page()

            time.sleep(0.4)

            if time.time() > nextBatteryCheckTime and self.BatteryPresent():
                if self.batteryLevelAbovePercent(
                        self.BATTERY_SHUTDOWN_THRESHOLD_PERC):
                    logging.debug("Battery above warning level")
                    # If we have a pending shutdown, cancel it and blank
                    #  the display to hide the low battery warning
                    if scheduledShutdownTime:
                        scheduledShutdownTime = 0
                        self.curPage = self.blank_page
                        self.curPage.draw_page()
                else:
                    logging.debug("Battery below warning level")
                    # Schedule a shutdown time if we don't already have one
                    if not scheduledShutdownTime:
                        scheduledShutdownTime = \
                            time.time() + self.SHUTDOWN_WARNING_PERIOD_SECS
                        # Don't blank the display while we're in the warning
                        #  period so the low battery warning shows to the end
                        displayPowerOffTime = scheduledShutdownTime + 1
                        self.curPage = self.low_battery_page
                        self.curPage.draw_page()

                nextBatteryCheckTime = \
                    time.time() + self.BATTERY_CHECK_FREQUENCY_SECS

            if scheduledShutdownTime and time.time() > scheduledShutdownTime:
                self.blank_page.draw_page()
                self.shutdownDevice()

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

    def ProcessButtons(self, L_Button, M_Button, R_Button):
        '''
        L botton is go back button
        M button is go forward button
        R button turns off display
        '''
        logging.debug("Processing buttons. Current page is %s", self.curPage)
        if self.curPage not in self.pages:
            # Always start with the starting page if the screen went off
            #  or if we were showing the low battery page
            self.curPage = self.pages[self.STARTING_PAGE_INDEX]

        if L_Button:
            # move forward in the page stack
            # If we're at the end of the page list. Go to the start
            if self.curPage == self.pages[-1]:
                self.curPage = self.pages[0]
            else:
                self.curPage = self.pages[self.pages.index(self.curPage) + 1]
        elif M_Button:
            # move backward in the page stack
            if self.curPage == self.pages[0]:
                self.curPage = self.pages[-1]
            else:
                self.curPage = self.pages[self.pages.index(self.curPage) - 1]
        elif R_Button:
            # Right button - turn on/off display
            self.curPage = self.blank_page

        logging.debug("Transitioning to page %s", self.curPage)
        # Page is actually drawn in the calling function


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
        super().__init__()

    def CheckButtonState(self):
        L_Button = not readPin(self.PIN_L_BUTTON)
        R_Button = not readPin(self.PIN_R_BUTTON)
        logging.debug("Button state L:%s R:%s",
                      L_Button, R_Button)
        return L_Button, R_Button

    def ProcessButtons(self, L_Button, R_Button):
        '''
        L botton is go forward button
        R button is go back button
        '''
        logging.debug("Processing buttons. Current page is %s", self.curPage)
        if self.curPage not in self.pages:
            # Always start with the starting page if the screen went off
            #  or if we were showing the low battery page
            self.curPage = self.pages[self.STARTING_PAGE_INDEX]

        if L_Button:
            # move forward in the page stack
            # If we're at the end of the page list. Go to the start
            if self.curPage == self.pages[-1]:
                self.curPage = self.pages[0]
            else:
                self.curPage = self.pages[self.pages.index(self.curPage) + 1]
        elif R_Button:
            # move backward in the page stack
            if self.curPage == self.pages[0]:
                self.curPage = self.pages[-1]
            else:
                self.curPage = self.pages[self.pages.index(self.curPage) - 1]

        logging.debug("Transitioning to page %s", self.curPage)
        # Page is actually drawn in the calling function
