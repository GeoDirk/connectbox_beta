# -*- coding: utf-8 -*-

"""
===========================================
  blinkLED.py
  https://github.com/GeoDirk/NEO_BatteryLevelShutdown
  License: MIT
  Version 1.0
===========================================
"""
import logging
import os
import time
import threading


PIN_LED = 6  # PA6 pin
PIN_VOLT_3_0 = 198  # PG6 pin - shutdown within 10 seconds
PIN_VOLT_3_2 = 199  # PG7 pin - above 3.2V
PIN_VOLT_3_4 = 200  # PG8 pin - above 3.4V
PIN_VOLT_3_6 = 201  # PG9 pin - above 3.6V
LED_FLASH_DELAY_SEC = 0.1
GPIO_EXPORT_FILE = "/sys/class/gpio/export"

PIN_HIGH = "1"
PIN_LOW = "0"

def setup_gpio_pin(pinNum, direction):
    """Setup the GPIO Pin for operation in the system OS"""
    if not os.path.isfile(GPIO_EXPORT_FILE):
        logging.warn("Unable to find GPIO export file: %s "
                     "Is GPIO_SYSFS active?", GPIO_EXPORT_FILE)
        return False

    # Has this pin been exported?
    pinPath = "/sys/class/gpio/gpio{}".format(pinNum)
    if not os.path.isfile(pinPath):
        try:
            # Export pin for access
            with open(GPIO_EXPORT_FILE, "w") as f:
                f.write(pinNum)
            # Configure the pin direction
            with open(os.path.join(pinPath, "direction")) as f:
                f.write(direction)
        except OSError:
            logging.warn("Error setting up GPIO pin %s", pinNum)
            return False

    return True


def blink_LEDxTimes(pinNum, times):
    """Blink the LED a certain number of times"""
    try:
        with open("/sys/class/gpio/gpio{}/value".format(pinNum), "w") as pin:
            for _ in range(0, times):
                pin.write(PIN_LOW)
                time.sleep(LED_FLASH_DELAY_SEC)
                pin.write(PIN_HIGH)
                time.sleep(LED_FLASH_DELAY_SEC)

            # make sure that we turn the LED off
            pin.write(PIN_HIGH)
    except OSError:
        logging.warn("Error writing to pin {}".format(pinNum))
        return False
    return True


def readPin(pinNum):
    """Read the value from some input pin"""
    try:
        with open("/sys/class/gpio/gpio{}/value".format(pinNum)) as pin:
            return pin.read(1) == 1
    except OSError:
        logging.warn("Error reading from pin {}".format(pinNum))

    return -1


def entryPoint():
    logging.info("Intializing Pins")
    logging.debug("Pin: LED")
    setup_gpio_pin(PIN_LED, "out")
    logging.debug("Pin: PG6 3.0V")
    setup_gpio_pin(PIN_VOLT_3_0, "in")
    logging.debug("Pin: PG7 3.2V")
    setup_gpio_pin(PIN_VOLT_3_2, "in")
    logging.debug("Pin: PG8 3.4V")
    setup_gpio_pin(PIN_VOLT_3_4, "in")
    logging.debug("Pin: PG9 3.6V")
    setup_gpio_pin(PIN_VOLT_3_6, "in")

    logging.info("Starting Monitoring")
    iIteration = 0
    threads = []
    bContinue = True
    while bContinue:
        # check if voltage is above 3.6V
        PIN_VOLT_ = readPin(PIN_VOLT_3_6)
        if PIN_VOLT_:
            try:
                with open("/sys/class/gpio/gpio{}/value".format(PIN_LED)) as pin:
                    pin.write(PIN_HIGH)
            except OSError:
                logging.warn("Error writing to pin {}".format(PIN_LED))
            time.sleep(9)
        else:
            # check if voltage is above 3.4V
            PIN_VOLT_ = readPin(PIN_VOLT_3_4)
            if PIN_VOLT_:
                t = threading.Thread(target=blink_LEDxTimes,
                                     args=(PIN_LED, 1,))
                threads.append(t)
                t.start()
                time.sleep(9)
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

    logging.info("Exiting for Shutdown\n")
    os.system("shutdown now")
