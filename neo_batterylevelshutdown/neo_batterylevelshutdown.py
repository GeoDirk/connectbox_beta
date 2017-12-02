# -*- coding: utf-8 -*-

"""
===========================================
  blinkLED.py
  https://github.com/GeoDirk/NEO_BatteryLevelShutdown
  License: MIT
  Version 1.0
===========================================
"""
import os
import time
import threading


PIN_LED = 6  # PA6 pin
PIN_VOLT_3_0 = 198  # PG6 pin - shutdown within 10 seconds
PIN_VOLT_3_2 = 199  # PG7 pin - above 3.2V
PIN_VOLT_3_4 = 200  # PG8 pin - above 3.4V
PIN_VOLT_3_6 = 201  # PG9 pin - above 3.6V
LED_FLASH_DELAY_SEC = 0.1


def setup_gpio_pin(pinNum, direction):
    """Setup the GPIO Pin for operation in the system OS"""
    # check if file exists or not
    path = "/sys/class/gpio/gpio" + str(pinNum)
    if not os.path.isfile(path):
        # function for telling the system that it needs to create a
        # gpio pin for use
        try:
            os.system("echo {} > /sys/class/gpio/export".format(pinNum))
            os.system("echo \"" + direction +
                      "\" > /sys/class/gpio/gpio{}/direction".format(pinNum))
        except:
            print("Error reading Pin {} value".format(str(pinNum)))
    return


def blink_LEDxTimes(pinNum, times):
    """Blink the LED a certain number of times"""
    times = times * 2  # need to account for going on/off as two cycles
    bVal = True
    for _ in range(0, times):
        if bVal:
            os.system("echo 0 > /sys/class/gpio/gpio" + str(pinNum) + "/value")
        else:
            os.system("echo 1 > /sys/class/gpio/gpio" + str(pinNum) + "/value")
        time.sleep(LED_FLASH_DELAY_SEC)
        bVal = not bVal  # toggle boolean
    # make sure that we turn the LED off
    os.system("echo 1 > /sys/class/gpio/gpio" + str(pinNum) + "/value")
    return


def readPin(pinNum):
    """Read the value from some input pin"""
    try:
        sRet = os.popen("cat /sys/class/gpio/gpio" +
                        str(pinNum) + "/value").read()
        if sRet == "1\n":
            return True
        else:
            return False
    except:
        print("Error reading Pin " + str(pinNum) + " Values")
    return


def entryPoint():
    DEBUG = 1

    print("Intializing Pins\n")
    print("Pin: LED")
    setup_gpio_pin(PIN_LED, "out")
    print("Pin: PG6 3.0V")
    setup_gpio_pin(PIN_VOLT_3_0, "in")
    print("Pin: PG7 3.2V")
    setup_gpio_pin(PIN_VOLT_3_2, "in")
    print("Pin: PG8 3.4V")
    setup_gpio_pin(PIN_VOLT_3_4, "in")
    print("Pin: PG9 3.6V\n")
    setup_gpio_pin(PIN_VOLT_3_6, "in")

    print("Starting Monitoring")
    iIteration = 0
    threads = []
    bContinue = True
    while bContinue:
        # check if voltage is above 3.6V
        PIN_VOLT_ = readPin(PIN_VOLT_3_6)
        if PIN_VOLT_:
            os.system("echo 1 > /sys/class/gpio/gpio" +
                      str(PIN_LED) + "/value")
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

    print("Exiting for Shutdown\n")
    os.system("shutdown now")
