# -*- coding: utf-8 -*-

"""Console script for neo_batterylevelshutdown."""

import logging

import axp209
import click

import neo_batterylevelshutdown.hats as hats
from .HAT_Utilities import setup_gpio_pin, readPin

PIN_LED = 6  # PA6 pin
PIN_PA1 = 1


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


def getHATVersion():
    if not neoHatIsPresent():
        logging.info("NEO HAT not detected")
        return hats.DummyHAT

    if not setup_gpio_pin(PIN_PA1, "in"):
        logging.info("NEO HAT not detected based on failed PA1 setup")
        return hats.DummyHAT

    try:
        axp = axp209.AXP209()
        axp.close()
        # AXP209 found... we have HAT from Q3Y2018 or later
        # Test PA1... LOW => Q4Y2018; HIGH => Q3Y2018
        if readPin(PIN_PA1) is False:
            logging.info("Q4Y2018 HAT Detected")
            return hats.q4y2018HAT
        else:
            logging.info("Q3Y2018 HAT Detected")
            return hats.q3y2018HAT
    except OSError:
        # There is no AXP209 on the Q12018 HAT
        logging.info("Q1Y2018 HAT Detected")
        return hats.q1y2018HAT
    except KeyboardInterrupt:
        pass

    return DummyHAT


@click.command()
@click.option('-v', '--verbose', is_flag=True, default=False)
def main(verbose):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    hat = getHATVersion()
    logging.info("starting main loop")
    hat().entryPoint()


if __name__ == "__main__":
    main()
