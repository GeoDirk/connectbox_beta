# -*- coding: utf-8 -*-

from contextlib import contextmanager
import logging
import os
import os.path
import sys
import time
import threading
from axp209 import AXP209, AXP209_ADDRESS
from PIL import Image
import RPi.GPIO as GPIO  # pylint: disable=import-error
from .HAT_Utilities import get_device
from . import page_none
from . import page_main
from . import page_battery
from . import page_info
from . import page_stats
from . import page_memory
from . import page_battery_low


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
    logging.debug("sleeping for %.2f secs to guarantee min exec time", period)
    time.sleep(period)


class AbstractHAT:

    PIN_LED = PA6 = 12

    def __init__(self):
        GPIO.setup(self.PIN_LED, GPIO.OUT)

    @classmethod
    def shutdownDevice(cls):
        logging.info("Exiting for Shutdown")
        os.system("shutdown now")

    def shutdownDeviceCallback(self, channel):
        logging.debug("Triggering device shutdown based on edge detection "
                      "of GPIO %s.", channel)
        self.shutdownDevice()

    def blinkLED(self, times, flashDelay=0.3):
        for _ in range(0, times):
            GPIO.output(self.PIN_LED, GPIO.HIGH)
            time.sleep(flashDelay)
            GPIO.output(self.PIN_LED, GPIO.LOW)
            time.sleep(flashDelay)

    def solidLED(self):
        GPIO.output(self.PIN_LED, GPIO.LOW)


class DummyHAT(AbstractHAT):

    # pylint: disable=no-self-use
    # This is a standard interface - it's ok not to use self for a dummy impl
    def mainLoop(self):
        logging.info("There is no HAT, so there's nothing to do")


class q1y2018HAT(AbstractHAT):

    # Pin numbers from https://github.com/auto3000/RPi.GPIO_NP
    PIN_VOLT_3_0 = PG6 = 8
    PIN_VOLT_3_45 = PG7 = 10
    PIN_VOLT_3_71 = PG8 = 16
    PIN_VOLT_3_84 = PG9 = 18

    def __init__(self):
        logging.info("Initializing Pins")
        GPIO.setup(self.PIN_VOLT_3_0, GPIO.IN)
        GPIO.setup(self.PIN_VOLT_3_45, GPIO.IN)
        GPIO.setup(self.PIN_VOLT_3_71, GPIO.IN)
        GPIO.setup(self.PIN_VOLT_3_84, GPIO.IN)
        logging.info("Pin initialization complete")
        # The circuitry on the HAT triggers a shutdown of the 5V converter
        #  once battery voltage goes below 3.0V. It gives an 8 second grace
        #  period before yanking the power, so if we have a falling edge on
        #  PIN_VOLT_3_0, then we're about to get the power yanked so attempt
        #  a graceful shutdown immediately.
        GPIO.add_event_detect(self.PIN_VOLT_3_0, GPIO.FALLING,
                              callback=self.shutdownDeviceCallback)
        # We cannot perform edge detection on PG7, PG8 or PG9 because there
        #  is no hardware hysteresis built into those level detectors, so when
        #  charging, the charger chip causes edge transitions (mostly rising
        #  but there are also some falling) at a rate of tens per second which
        #  means the software (and thus the board) is consuming lots of CPU
        #  and thus the charge rate is slower.
        super().__init__()

    def mainLoop(self):
        """
        monitors battery voltage and shuts down the device when levels are low
        """
        logging.info("Starting Monitoring")
        while True:
            with min_execution_time(min_time_secs=5):
                if GPIO.input(self.PIN_VOLT_3_84):
                    logging.debug("Battery voltage > 3.84V i.e. > ~63%")
                    self.solidLED()
                    continue

                logging.debug("Battery voltage < 3.84V i.e. < ~63%")
                if GPIO.input(self.PIN_VOLT_3_71):
                    # Voltage above 3.71V
                    self.blinkLED(times=1)
                    continue

                logging.debug("Battery voltage < 3.71V i.e. < ~33%")
                if GPIO.input(self.PIN_VOLT_3_45):
                    # Voltage above 3.45V
                    self.blinkLED(times=2)
                    continue

                # If we're here, we can assume that PIN_VOLT_3_0 is high,
                #  otherwise we'd have triggered the falling edge detection
                #  on that pin, and we'd be in the process of shutting down
                #  courtesy of the callback.
                logging.info("Battery voltage < 3.45V i.e. < ~3%")
                self.blinkLED(times=3)


class Axp209HAT(AbstractHAT):
    SHUTDOWN_WARNING_PERIOD_SECS = 60
    BATTERY_CHECK_FREQUENCY_SECS = 30
    BATTERY_SHUTDOWN_THRESHOLD_PERC = 4

    def __init__(self):
        self.axp = AXP209()
        # no shutdown currently scheduled
        self.scheduledShutdownTime = 0
        # If we have a battery, perform a level check at our first chance but
        #  if we don't, never schedule the battery check (this assumes that
        #  the battery will never be plugged in after startup, which is a
        #  reasonable assumption for non-development situations)
        if self.axp.battery_exists:
            self.nextBatteryCheckTime = 0
        else:
            # Never schedule it...
            self.nextBatteryCheckTime = sys.maxsize
        super().__init__()

    def batteryLevelAbovePercent(self, level):
        logging.debug("Battery Level: %s%%", self.axp.battery_gauge)
        return self.axp.battery_gauge > level

    def mainLoop(self):
        while True:
            if time.time() > self.nextBatteryCheckTime:
                if self.batteryLevelAbovePercent(
                        self.BATTERY_SHUTDOWN_THRESHOLD_PERC):
                    logging.debug("Battery above warning level")
                    # If we have a pending shutdown, cancel it
                    if self.scheduledShutdownTime:
                        self.scheduledShutdownTime = 0
                else:
                    logging.debug("Battery below warning level")
                    # Schedule a shutdown time if we don't already have one
                    if not self.scheduledShutdownTime:
                        self.scheduledShutdownTime = \
                            time.time() + self.SHUTDOWN_WARNING_PERIOD_SECS

                self.nextBatteryCheckTime = \
                    time.time() + self.BATTERY_CHECK_FREQUENCY_SECS

            if self.scheduledShutdownTime and \
                    time.time() > self.scheduledShutdownTime:
                self.shutdownDevice()

            # Wait before next loop iteration
            time.sleep(1)

        return


class OledHAT(Axp209HAT):

    DISPLAY_TIMEOUT_SECS = 20
    # What to show after startup and blank screen
    STARTING_PAGE_INDEX = 0  # the main page

    def __init__(self):
        # Can't delegate the axp209 setup to the parent constructor because
        #  we need it now.
        self.axp = AXP209()
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
        # callbacks run in another thread, so we need to lock access to the
        #  current page variable as it can be modified from the main loop
        #  and from callbacks
        self.curPageLock = threading.Lock()
        # This is set in the start of the main loop anyway, but let's make
        #  sure it's defined for clarity's sake in the constructor
        self.curPage = self.STARTING_PAGE_INDEX
        super().__init__()
        # draw the connectbox logo
        self.draw_logo()
        # Blank the screen 3 seconds after showing the logo - that's long
        #  enough. While displayPowerOffTime is read and written from both
        #  callback threads and the main loop, there's no TOCTOU race
        #  condition because we're only ever setting an absolute value rather
        #  than incrementing i.e. we're not referencing the old value
        self.displayPowerOffTime = time.time() + 3

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

    def moveForward(self, channel):
        """callback for use on button press"""
        with self.curPageLock:
            logging.debug("Processing press on GPIO %s. Current page is %s",
                          channel, self.curPage)
            if self.curPage not in self.pages:
                # Always start with the starting page if the screen went off
                #  or if we were showing the low battery page
                self.curPage = self.pages[self.STARTING_PAGE_INDEX]
            else:
                # move forward in the page list
                # If we're at the end of the page list, go to the start
                if self.curPage == self.pages[-1]:
                    self.curPage = self.pages[0]
                else:
                    self.curPage = \
                        self.pages[self.pages.index(self.curPage) + 1]

            # draw the page while holding the lock, so that it doesn't change
            #  underneath us
            self.curPage.draw_page()
            logging.debug("Transitioned to page %s", self.curPage)

        # reset the display power off time
        self.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS

    def moveBackward(self, channel):
        """callback for use on button press"""
        with self.curPageLock:
            logging.debug("Processing press on GPIO %s. Current page is %s",
                          channel, self.curPage)
            if self.curPage not in self.pages:
                # Always start with the starting page if the screen went off
                #  or if we were showing the low battery page
                self.curPage = self.pages[self.STARTING_PAGE_INDEX]
            else:
                # move backwards in the page list
                # If we're at the start of the page list, go to the start
                if self.curPage == self.pages[0]:
                    self.curPage = self.pages[-1]
                else:
                    self.curPage = \
                        self.pages[self.pages.index(self.curPage) - 1]

            # draw the page while holding the lock, so that it doesn't change
            #  underneath us
            self.curPage.draw_page()
            logging.debug("Transitioned to page %s", self.curPage)

        # reset the display power off time
        self.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS

    def mainLoop(self):
        while True:
            if time.time() > self.displayPowerOffTime:
                # Power off the display
                if self.curPage != self.blank_page:
                    with self.curPageLock:
                        self.curPage = self.blank_page
                        self.curPage.draw_page()

            if time.time() > self.nextBatteryCheckTime:
                if self.batteryLevelAbovePercent(
                        self.BATTERY_SHUTDOWN_THRESHOLD_PERC):
                    logging.debug("Battery above warning level")
                    # If we have a pending shutdown, cancel it and blank the
                    #  display (at next chance) to hide the low battery warning
                    if self.scheduledShutdownTime:
                        self.scheduledShutdownTime = 0
                        self.displayPowerOffTime = 0
                else:
                    logging.debug("Battery below warning level")
                    # Schedule a shutdown time if we don't already have one
                    if not self.scheduledShutdownTime:
                        self.scheduledShutdownTime = \
                            time.time() + self.SHUTDOWN_WARNING_PERIOD_SECS
                        # Don't blank the display while we're in the warning
                        #  period so the low battery warning shows to the end
                        self.displayPowerOffTime = \
                            self.scheduledShutdownTime + 1
                        with self.curPageLock:
                            self.curPage = self.low_battery_page
                            self.curPage.draw_page()

                self.nextBatteryCheckTime = \
                    time.time() + self.BATTERY_CHECK_FREQUENCY_SECS

            if self.scheduledShutdownTime and \
                    time.time() > self.scheduledShutdownTime:
                self.shutdownDevice()

            # Wait before next loop iteration
            time.sleep(1)


class q3y2018HAT(OledHAT):

    # Pin numbers from https://github.com/auto3000/RPi.GPIO_NP
    PIN_L_BUTTON = PA1 = 22
    PIN_M_BUTTON = PG7 = 10
    PIN_R_BUTTON = PG8 = 16

    def __init__(self):
        GPIO.setup(self.PIN_L_BUTTON, GPIO.IN)
        GPIO.setup(self.PIN_M_BUTTON, GPIO.IN)
        GPIO.setup(self.PIN_R_BUTTON, GPIO.IN)
        GPIO.add_event_detect(self.PIN_L_BUTTON, GPIO.FALLING,
                              callback=self.moveForward,
                              bouncetime=125)
        GPIO.add_event_detect(self.PIN_M_BUTTON, GPIO.FALLING,
                              callback=self.moveBackward,
                              bouncetime=125)
        GPIO.add_event_detect(self.PIN_R_BUTTON, GPIO.FALLING,
                              callback=self.powerOffDisplay,
                              bouncetime=125)
        super().__init__()

    def powerOffDisplay(self, channel):
        """Turn off the display"""
        with self.curPageLock:
            logging.debug("Processing press on GPIO %s. Current page is %s",
                          channel, self.curPage)
            self.curPage = self.blank_page
            # draw the page while holding the lock, so that it doesn't change
            #  underneath us
            self.curPage.draw_page()
            logging.debug("Transitioned to page %s", self.curPage)
        # The display is already off... no need to set the power off time


class q4y2018HAT(OledHAT):

    # Q4Y2018 - AXP209/OLED (Anker) Unit run specific pins
    # Pin numbers from https://github.com/auto3000/RPi.GPIO_NP
    PIN_L_BUTTON = PG6 = 8
    PIN_R_BUTTON = PG7 = 10
    PIN_AXP_INTERRUPT_LINE = PG8 = 16

    def __init__(self):
        GPIO.setup(self.PIN_L_BUTTON, GPIO.IN)
        GPIO.setup(self.PIN_R_BUTTON, GPIO.IN)
        GPIO.setup(self.PIN_AXP_INTERRUPT_LINE, GPIO.IN)
        GPIO.add_event_detect(self.PIN_L_BUTTON, GPIO.FALLING,
                              callback=self.moveForward,
                              bouncetime=125)
        GPIO.add_event_detect(self.PIN_R_BUTTON, GPIO.FALLING,
                              callback=self.moveBackward,
                              bouncetime=125)
        super().__init__()

        # Clear all IRQ Enable Control Registers. We may subsequently
        #  enable interrupts on certain actions below, but let's start
        #  with a known state for all registers.
        for ec_reg in (0x40, 0x41, 0x42, 0x43, 0x44):
            self.axp.bus.write_byte_data(AXP209_ADDRESS, ec_reg, 0x00)

        # Now all interrupts are disabled, clear the previous state
        self.clearAllPreviousInterrupts()

        # shutdown delay time to 3 secs (they delay before axp209 yanks power
        #  when it determines a shutdown is required) (default is 2 sec)
        hexval = self.axp.bus.read_byte_data(AXP209_ADDRESS, 0x32)
        hexval = hexval | 0x03
        self.axp.bus.write_byte_data(AXP209_ADDRESS, 0x32, hexval)

        # Enable interrupts when battery goes below LEVEL2 or when
        #  N_OE (the power switch) goes high
        self.axp.bus.write_byte_data(AXP209_ADDRESS, 0x43, 0x41)
        # We've masked all other interrupt sources for the AXP interrupt line
        #  so the desired action here is always to shutdown
        GPIO.add_event_detect(self.PIN_AXP_INTERRUPT_LINE, GPIO.FALLING,
                              callback=self.shutdownDeviceCallback)

    def clearAllPreviousInterrupts(self):
        """
        Reset interrupt state by writing a 1 to all bits of the state regs

        From the AXP209 datasheet:
        When certain events occur, AXP209 will inform the Host by pulling down
        the IRQ interrupt line, and the interrupt state will be stored in
        interrupt state registers (See registers REG48H, REG49H, REG4AH, REG4BH
        and REG4CH). The interrupt can be cleared by writing 1 to corresponding
        state register bit.

        Note that 0x4B is the only one that's enabled at this stage, but let's
        be thorough so that we don't need to change this if we start using the
        others.
        """
        # (IRQ status register 1-5)
        for stat_reg in (0x48, 0x49, 0x4A, 0x4B, 0x4C):
            self.axp.bus.write_byte_data(AXP209_ADDRESS, stat_reg, 0xFF)
        logging.debug("IRQ records cleared")
