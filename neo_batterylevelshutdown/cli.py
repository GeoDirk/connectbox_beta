# -*- coding: utf-8 -*-

"""Console script for neo_batterylevelshutdown."""

import logging
import click
from . import neo_batterylevelshutdown


@click.command()
@click.option('-v', '--verbose', is_flag=True, default=False)
def main(verbose):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    neo_batterylevelshutdown.entryPoint()


if __name__ == "__main__":
    main()
