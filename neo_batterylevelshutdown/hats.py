# -*- coding: utf-8 -*-

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


class AbstractHAT(object):
    def initializePins(self):
        initialisationSuccess = True
        logging.info("Intializing Pins")
        # Fail if any of the pins can't be setup
        for pin, direction in self.pins_to_initialise:
            if setup_gpio_pin(pin, direction):
                logging.error("Unable to setup pin %s with direction %s",
                              pin, direction
                              )
                initialisationSuccess = False
        return initialisationSuccess


class DummyHAT(AbstractHAT):
    def entryPoint(self):
        logging.info("There is no HAT, so there's nothing to do")


class q1y2018HAT(AbstractHAT):

    DEFAULT_LOW_VOLTAGE_ITERATIONS_BEFORE_SHUTDOWN = 3
    pins_to_initialise = [
        (PIN_LED, "out"),
        (PIN_VOLT_3_0, "in"),
        (PIN_VOLT_3_2, "in"),
        (PIN_VOLT_3_4, "in"),
        (PIN_VOLT_3_6, "in")
    ]

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
                    blink_LEDxTimes(PIN_LED, 4)

    def entryPoint(self):
        if not self.initializePins():
            logging.error("Errors during pin setup. Aborting")
            return False

        self.mainLoop()
        logging.info("Exiting for Shutdown")
        os.system("shutdown now")
