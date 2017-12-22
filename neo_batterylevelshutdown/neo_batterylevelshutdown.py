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
        logging.error("Unable to find GPIO export file: %s "
                      "Is GPIO_SYSFS active?", GPIO_EXPORT_FILE)
        return False

    # Has this pin been exported?
    pinPath = "/sys/class/gpio/gpio{}".format(pinNum)
    if not os.path.isfile(pinPath):
        try:
            # Export pin for access - once we have HATs for wider testing
            #  turn this echo into the regular python open and write pattern
            os.system("echo {} > /sys/class/gpio/export".format(pinNum))
            logging.info("Completed export of GPIO pin %s", pinNum)
            # Configure the pin direction
            with open(os.path.join(pinPath, "direction"), 'w') as f:
                f.write(direction)
            logging.info("Completed setting direction GPIO pin %s to %s",
                         pinNum, direction)
        except OSError:
            logging.error("Error setting up GPIO pin %s", pinNum)
            return False

    return True


def blink_LEDxTimes(pinNum, times):
    """Blink the LED a certain number of times"""
    pinFile = "/sys/class/gpio/gpio{}/value".format(pinNum)
    try:
        for _ in range(0, times):
            with open(pinFile, "w") as pin:
                pin.write(PIN_HIGH)
            time.sleep(LED_FLASH_DELAY_SEC)
            with open(pinFile, "w") as pin:
                pin.write(PIN_LOW)
            time.sleep(LED_FLASH_DELAY_SEC)
    except OSError:
        logging.warn("Error writing to pin %s", pinNum)
        return False
    return True


def readPin(pinNum):
    """Read the value from some input pin"""
    logging.info("Reading pin %s", pinNum)
    try:
        with open("/sys/class/gpio/gpio{}/value".format(pinNum), 'r') as pin:
            return str(pin.read(1)) == "1"
    except OSError:
        logging.warn("Error reading from pin %s", pinNum)
    return -1


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
        logging.info("Value PIN_VOLT_3_6: %s", PIN_VOLT_)
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


def neoHatIsPresent():
    """
    As PA6 is set to be a pulldown resistor on system startup by the
    pa6-pulldown.service, and the HAT sets PA6 HIGH, so we check the
    value of PA6, knowing non-HAT NEOs will read LOW.

    We assume the HAT is not present if we're unable to setup the pin
    or read from it. That's the safe option and means that we won't
    immediately shutdown devices that don't have a HAT if we've incorrect
    detected the presence of a HAT
    """
    return setup_gpio_pin(PIN_LED, "in") and readPin(PIN_LED) is True


def entryPoint():
    if not neoHatIsPresent():
        logging.info("NEO Hat not detected. No voltage detection possible. "
                     "Exiting.")
        return True

    if not initializePins():
        logging.error("Errors during pin setup. Aborting")
        return False

    monitorVoltageUntilShutdown()
    logging.info("Exiting for Shutdown\n")
    os.system("shutdown now")
