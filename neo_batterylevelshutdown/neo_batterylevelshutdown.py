# -*- coding: utf-8 -*-

"""
===========================================
  page_stats.py
  https://github.com/GeoDirk/NEO_BatteryLevelShutdown
  License: MIT
  Version 1.0
  GeoDirk - May 2018
===========================================
"""
import logging
import axp209

from . import Q1Y2018_HAT
from . import Q3Y2018_HAT
from .HAT_Utilities import setup_gpio_pin, readPin

PIN_LED = 6  # PA6 pin

#setup enums which define the various versions of HAT hardware
class HATtype:
    Q1Y2018, Q3Y2018 = range(2)

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
        axp.close()
        logging.info("Q3Y2018 Detected")
        return HATtype.Q3Y2018
    except OSError:
        logging.info("Q1Y2018 Detected")
        return  HATtype.Q1Y2018
    except KeyboardInterrupt:
        pass
    return  HATtype.Q1Y2018

def entryPoint():
    if not neoHatIsPresent():
        logging.info("NEO Hat not detected. No voltage detection possible. "
                     "Exiting.")
        return True

    hatType = checkForHATVersion()
    
    if hatType == HATtype.Q1Y2018:
        #100 Unit run HAT
        print("HATtype.Q1Y2018 Detected")
        Q1Y2018_HAT.entryPoint()
    elif hatType == HATtype.Q3Y2018:
        #OLED Version
        print("HATtype.Q3Y2018 Detected")
        Q3Y2018_HAT.entryPoint()
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

    """
    NOTES:

    Get number of active WiFi connections:
    iw dev wlan0 station dump | grep -c Station
    ================================
    Get shell command's output into Python:
    from:

    https://stackoverflow.com/questions/4760215/running-shell-command-from-python-and-capturing-the-output#4760517

    import subprocess
    result = subprocess.run(['ls', '-l'], stdout=subprocess.PIPE)
    result.stdout.decode('utf-8')
    ================================
    system uptime:

    uptime -p
    ================================
    axp = AXP209()
    print("internal_temperature: %.2fC" % axp.internal_temperature)
    print("battery_exists: %s" % axp.battery_exists)
    print("battery_charging: %s" % ("charging" if axp.battery_charging else "done"))
    print("battery_current_direction: %s" % ("charging" if axp.battery_current_direction else "discharging"))
    print("battery_voltage: %.1fmV" % axp.battery_voltage)
    print("battery_discharge_current: %.1fmA" % axp.battery_discharge_current)
    print("battery_charge_current: %.1fmA" % axp.battery_charge_current)
    print("battery_gauge: %d%%" % axp.battery_gauge)
    axp.close()
    ================================

    
    """
