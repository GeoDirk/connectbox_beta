# -*- coding: utf-8 -*-
"""
===========================================
  HAT_Utilities.py
  https://github.com/ConnectBox/NEO_BatteryLevelShutdown
  License: MIT
  Version 1.0
  GeoDirk - May 2018
===========================================
"""
import logging
import os
import time
import sys
import os.path
from luma.core import cmdline, error

LED_FLASH_DELAY_SEC = 0.1
GPIO_EXPORT_FILE = "/sys/class/gpio/export"

PIN_HIGH = "1"
PIN_LOW = "0"
PIN_LED = 6  # PA6 pin


def setup_gpio_pin(pinNum, direction):
    """Setup the GPIO Pin for operation in the system OS"""
    if not os.path.isfile(GPIO_EXPORT_FILE):
        logging.error("Unable to find GPIO export file: %s "
                      "Is GPIO_SYSFS active?", GPIO_EXPORT_FILE)
        return False

    # Has this pin been exported?
    pinPath = "/sys/class/gpio/gpio{}".format(pinNum)
    try:
        if not os.path.exists(pinPath):
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


def GetReleaseVersion():
    """Read the release version"""
    try:
        with open("/etc/connectbox-release", 'r') as release:
            return str(release.read())
    except OSError:
        logging.warn("Error reading release version")
    return "unknown"


def readPin(pinNum):
    """Read the value from some input pin"""
    logging.debug("Reading pin %s", pinNum)
    try:
        with open("/sys/class/gpio/gpio{}/value".format(pinNum), 'r') as pin:
            return str(pin.read(1)) == "1"
    except OSError:
        logging.warn("Error reading from pin %s", pinNum)
    return -1


def writePin(pinNum, value):
    try:
        with open("/sys/class/gpio/gpio{}/value".format(PIN_LED),
                  "w") as pin:
            pin.write(PIN_LOW)
    except OSError:
        logging.warn("Error writing to pin %s", PIN_LED)
        return False

    return True


def get_device(actual_args=None):
    """
    Create device from command-line arguments and return it.
    """
    # default to port 0 if nothing has been entered in as an argument
    if str(sys.argv[1:]) == '[]':
        sys.argv[1:] = ['--i2c-port', '0']

    if actual_args is None:
        # FIXME - hoist to cli
        actual_args = ['--i2c-port', '0']
    parser = cmdline.create_parser(description='luma.examples arguments')
    args = parser.parse_args(actual_args)

    if args.config:
        # load config from file
        config = cmdline.load_config(args.config)
        args = parser.parse_args(config + actual_args)

    # create device
    try:
        device = cmdline.create_device(args)
    except error.Error as e:
        parser.error(e)

    # print(display_settings(args))

    return device


def display_settings(args):
    """
    Display a short summary of the settings.
    :rtype: str
    """
    iface = ''
    display_types = cmdline.get_display_types()
    if args.display not in display_types['emulator']:
        iface = 'Interface: {}\n'.format(args.interface)

    return 'Display: {}\n{}Dimensions: {} x {}\n{}'.format(
        args.display, iface, args.width, args.height, '-' * 40)
