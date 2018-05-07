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
import sys
import os.path
from PIL import Image
from PIL import ImageFont
from luma.core import cmdline, error
from luma.core.render import canvas
import axp209

# Common pins between HATs
PIN_LED = 6  # PA6 pin

# Q1Y2018 - 100 Unit run specific pins
PIN_VOLT_3_0 = 198  # PG6 pin - shutdown within 10 seconds
PIN_VOLT_3_2 = 199  # PG7 pin - above 3.2V
PIN_VOLT_3_4 = 200  # PG8 pin - above 3.4V
PIN_VOLT_3_6 = 201  # PG9 pin - above 3.6V

# Q3Y2018 - 100 Unit run specific pins
PIN_L_BUTTON = 1  # PA1 left button
PIN_M_BUTTON = 199 # PG7 middle button
PIN_R_BUTTON = 200  # PG8 pin right button

LED_FLASH_DELAY_SEC = 0.1
GPIO_EXPORT_FILE = "/sys/class/gpio/export"

PIN_HIGH = "1"
PIN_LOW = "0"

#setup enums which define the various versions of HAT hardware
def enum(**named_values):
     return type('Enum', (), named_values)

HATtype = enum(Q1Y2018='100unitrun', Q3Y2018='OLED N')
_HATtype = HATtype.Q1Y2018


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

def initializePins_OLED():
    logging.info("Intializing OLED HAT Pins")
    return setup_gpio_pin(PIN_LED, "out") and \
        setup_gpio_pin(PIN_L_BUTTON, "in") and \
        setup_gpio_pin(PIN_M_BUTTON, "in") and \
        setup_gpio_pin(PIN_R_BUTTON, "in") and \
        setup_gpio_pin(PIN_VOLT_3_6, "in")  # <-- check this pin

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


def Main_Q1Y2018():
    """
    100 Unit Run HAT Detected
    """    
    if not initializePins():
        logging.error("Errors during pin setup. Aborting")
        return False

    monitorVoltageUntilShutdown()
    return

def Main_Q3Y2018():
    """
    OLED Version of HAT Detected
    """    
    if not initializePins_OLED():
        logging.error("Errors during pin setup. Aborting")
        return False

    draw_logo()
    time.sleep(5)

    while True:
       draw_text(device)

    return

def get_device(actual_args=None):
    
    """
    Create device from command-line arguments and return it.
    """
    if actual_args is None:
        actual_args = sys.argv[1:]
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

    print(display_settings(args))

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

def draw_logo():
    img_path = os.path.abspath('connectbox_logo.png')
    logo = Image.open(img_path).convert("RGBA")
    fff = Image.new(logo.mode, logo.size, (255,) * 4)
    background = Image.new("RGBA", device.size, "white")
    posn = ((device.width - logo.width) // 2, 0)
    img = Image.composite(logo, fff, logo)
    background.paste(img, posn)
    device.display(background.convert(device.mode))

def draw_text(device):
    # use custom font
    font_path = os.path.abspath('connectbox.ttf')
    font30 = ImageFont.truetype(font_path, 30)
    font10 = ImageFont.truetype(font_path, 14)
	
    with canvas(device) as draw:
        draw.text((0, 0), 'ConnectBox', font=font30, fill="white")
        draw.text((0, 30), 'http://www.', font=font10, fill="white")
        draw.text((0, 40), 'connectbox.technology', font=font10, fill="white")

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

def checkForHATVersion():
    """
    We need to define which HAT is on the unit.  If this is a HAT from the
    2017Q3 run, then it will fail with the OLED test.
    """
    try:
        axp = axp209.AXP209()
        _HATtype = HATtype.Q3Y2018
    except OSError as e:
        _HATtype = HATtype.Q1Y2018
    except KeyboardInterrupt:
        pass


def entryPoint():
    if not neoHatIsPresent():
        logging.info("NEO Hat not detected. No voltage detection possible. "
                     "Exiting.")
        return True

    checkForHATVersion()
    
    if _HATtype == HATtype.Q1Y2018:
        #100 Unit run HAT
        print("HATtype.Q1Y2018 Detected")
        Main_Q1Y2018()
    elif _HATtype == HATtype.Q3Y2018:
        #OLED Version
        print("HATtype.Q3Y2018 Detected")
        Main_Q3Y2018()
    else:
        print("No HATtype Determined")
        pass

    logging.info("Exiting for Shutdown\n")
    #os.system("shutdown now")  # <--todo remove this for production


if __name__ == "__main__":
    try:
        entryPoint()
    except KeyboardInterrupt:
        pass