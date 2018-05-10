# -*- coding: utf-8 -*-

"""
===========================================
  button_reader.py
  https://github.com/ConnectBox/NEO_BatteryLevelShutdown
  License: MIT
  Version 1.0
  GeoDirk - May 2018
===========================================
"""
import logging
import time
import threading

from HAT_Utilities import setup_gpio_pin, readPin, blink_LEDxTimes, get_device

# Common pins between HATs
PIN_LED = 6  # PA6 pin

# Q3Y2018 - OLED Unit run specific pins
PIN_L_BUTTON = 1  # PA1 left button
PIN_M_BUTTON = 199 # PG7 middle button
PIN_R_BUTTON = 200  # PG8 pin right button

def initializePins():
    logging.info("Intializing OLED HAT Pins")
    return setup_gpio_pin(PIN_LED, "out") and \
        setup_gpio_pin(PIN_L_BUTTON, "in") and \
        setup_gpio_pin(PIN_M_BUTTON, "in") and \
        setup_gpio_pin(PIN_R_BUTTON, "in")


def main():
    if not initializePins():
        logging.error("Errors during pin setup. Aborting")
        return False

    threads = []
    while True:
        L = not readPin(PIN_L_BUTTON)
        M = not readPin(PIN_M_BUTTON)
        R = not readPin(PIN_R_BUTTON)
        print("L:%s M:%s R:%s" % (L, M, R))

        if L == True:
            t = threading.Thread(target=blink_LEDxTimes, 
                args=(PIN_LED, 3,))
            threads.append(t)
            t.start()
        elif M == True:
            t = threading.Thread(target=blink_LEDxTimes, 
                args=(PIN_LED, 2,))
            threads.append(t)
            t.start()
        elif R == True:
            t = threading.Thread(target=blink_LEDxTimes, 
                args=(PIN_LED, 1,))
            threads.append(t)
            t.start()

        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass