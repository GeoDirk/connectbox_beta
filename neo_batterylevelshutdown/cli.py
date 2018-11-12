# -*- coding: utf-8 -*-

"""Console script for neo_batterylevelshutdown."""

import logging

import axp209
import click

from . import Q1Y2018_HAT
from . import Q3Y2018_HAT
from . import null_HAT
from .HAT_Utilities import setup_gpio_pin, readPin

PIN_LED = 6  # PA6 pin


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
        return null_HAT

    try:
        axp = axp209.AXP209()
        axp.close()
        logging.info("Q3Y2018 HAT Detected")
        return Q3Y2018_HAT
    except OSError:
        # There is no AXP209 on the Q12018 HAT
        logging.info("Q1Y2018 HAT Detected")
        return Q1Y2018_HAT
    except KeyboardInterrupt:
        pass

    return null_HAT


@click.command()
@click.option('-v', '--verbose', is_flag=True, default=False)
def main(verbose):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    hat = getHATVersion()
    logging.info("starting main loop")
    hat.entryPoint()


if __name__ == "__main__":
    main()
