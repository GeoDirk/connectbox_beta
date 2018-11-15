# -*- coding: utf-8 -*-

"""
===========================================
  Q12018.py
  https://github.com/ConnectBox/NEO_BatteryLevelShutdown
  License: MIT
  Version 1.0
  GeoDirk - May 2018
===========================================
"""
from contextlib import contextmanager
import logging
import os
import time
from .HAT_Utilities import setup_gpio_pin
from .HAT_Utilities import readPin
from .HAT_Utilities import writePin
from .HAT_Utilities import blink_LEDxTimes

PIN_LED = 6  # PA6 pin
PIN_VOLT_3_0 = 198  # PG6 pin - shutdown within 30 seconds
PIN_VOLT_3_2 = 199  # PG7 pin - above 3.2V
PIN_VOLT_3_4 = 200  # PG8 pin - above 3.4V
PIN_VOLT_3_6 = 201  # PG9 pin - above 3.6V
GPIO_EXPORT_FILE = "/sys/class/gpio/export"


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


def initializePins():
    logging.info("Intializing Pins")
    return setup_gpio_pin(PIN_LED, "out") and \
        setup_gpio_pin(PIN_VOLT_3_0, "in") and \
        setup_gpio_pin(PIN_VOLT_3_2, "in") and \
        setup_gpio_pin(PIN_VOLT_3_4, "in") and \
        setup_gpio_pin(PIN_VOLT_3_6, "in")


def mainLoop():
    """
    monitors battery voltage and shuts down the device when levels are low
    """
    iIteration = 0
    logging.info("Starting Monitoring")
    while True:
        with min_execution_time(min_time_secs=10):
            # check if voltage is above 3.6V
            if readPin(PIN_VOLT_3_6):
                # Show solid LED
                writePin(PIN_LED, "0")
                continue

            # check if voltage is above 3.4V
            if readPin(PIN_VOLT_3_4):
                blink_LEDxTimes(PIN_LED, 1)
                continue

            # check if voltage is above 3.2V
            if readPin(PIN_VOLT_3_2):
                blink_LEDxTimes(PIN_LED, 2)
                continue

            # check if voltage is above 3.0V
            if readPin(PIN_VOLT_3_0):
                blink_LEDxTimes(PIN_LED, 3)
                # pin voltage above 3V so reset iteration
                # XXX - if voltage transitions from 2.9->3.3 then this will
                #       not be reset. Consider robustifying
                iIteration = 0
                continue

            # pin voltage is below 3V so we need to do a few
            # iterations to make sure that we are still getting
            # the same info each time
            iIteration += 1
            if iIteration > 3:
                # Time to shutdown
                break
            else:
                blink_LEDxTimes(PIN_LED, 4)


def entryPoint():
    if not initializePins():
        logging.error("Errors during pin setup. Aborting")
        return False

    mainLoop()
    logging.info("Exiting for Shutdown")
    os.system("shutdown now")
