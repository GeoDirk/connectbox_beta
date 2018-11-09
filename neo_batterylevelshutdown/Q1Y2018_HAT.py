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
import logging
import os
import time
import threading
from .HAT_Utilities import setup_gpio_pin
from .HAT_Utilities import readPin
from .HAT_Utilities import blink_LEDxTimes

PIN_LED = 6  # PA6 pin
PIN_VOLT_3_0 = 198  # PG6 pin - shutdown within 10 seconds
PIN_VOLT_3_2 = 199  # PG7 pin - above 3.2V
PIN_VOLT_3_4 = 200  # PG8 pin - above 3.4V
PIN_VOLT_3_6 = 201  # PG9 pin - above 3.6V
LED_FLASH_DELAY_SEC = 0.1
GPIO_EXPORT_FILE = "/sys/class/gpio/export"

PIN_HIGH = "1"
PIN_LOW = "0"


def initializePins():
    logging.info("Intializing Pins")
    return setup_gpio_pin(PIN_LED, "out") and \
        setup_gpio_pin(PIN_VOLT_3_0, "in") and \
        setup_gpio_pin(PIN_VOLT_3_2, "in") and \
        setup_gpio_pin(PIN_VOLT_3_4, "in") and \
        setup_gpio_pin(PIN_VOLT_3_6, "in")


def monitorVoltageUntilShutdown():
    iIteration = 0
    threads = []
    bContinue = True
    logging.info("Starting Monitoring")
    while bContinue:
        # check if voltage is above 3.6V
        PIN_VOLT_ = readPin(PIN_VOLT_3_6)
        logging.debug("Value PIN_VOLT_3_6: %s", PIN_VOLT_)
        if PIN_VOLT_:
            try:
                with open("/sys/class/gpio/gpio{}/value".format(PIN_LED),
                          "w") as pin:
                    pin.write(PIN_LOW)
            except OSError:
                logging.warn("Error writing to pin %s", PIN_LED)
            time.sleep(9)
        else:
            # check if voltage is above 3.4V
            PIN_VOLT_ = readPin(PIN_VOLT_3_4)
            if PIN_VOLT_:
                t = threading.Thread(target=blink_LEDxTimes,
                                     args=(PIN_LED, 1,))
                threads.append(t)
                t.start()
                time.sleep(6)
            else:
                # check if voltage is above 3.2V
                PIN_VOLT_ = readPin(PIN_VOLT_3_2)
                if PIN_VOLT_:
                    t = threading.Thread(target=blink_LEDxTimes,
                                         args=(PIN_LED, 2,))
                    threads.append(t)
                    t.start()
                    time.sleep(4)
                else:
                    # check if voltage is above 3.0V
                    PIN_VOLT_ = readPin(PIN_VOLT_3_0)
                    if PIN_VOLT_:
                        t = threading.Thread(target=blink_LEDxTimes,
                                             args=(PIN_LED, 3,))
                        threads.append(t)
                        t.start()
                        # pin volage above 3V so reset iteration
                        iIteration = 0
                        time.sleep(4)
                    else:
                        # pin voltage is below 3V so we need to do a few
                        # iterations to make sure that we are still getting
                        # the same info each time
                        iIteration += 1
                        if iIteration > 3:
                            bContinue = False
                        else:
                            t = threading.Thread(target=blink_LEDxTimes,
                                                 args=(PIN_LED, 4,))
                            threads.append(t)
                            t.start()

        time.sleep(1)


def entryPoint():
    if not initializePins():
        logging.error("Errors during pin setup. Aborting")
        return False

    monitorVoltageUntilShutdown()
    logging.info("Exiting for Shutdown\n")
    os.system("shutdown now")
