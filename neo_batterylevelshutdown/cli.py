# -*- coding: utf-8 -*-

"""Console script for neo_batterylevelshutdown."""

import click
import neo_batterylevelshutdown


@click.command()
def main(args=None):
    neo_batterylevelshutdown.entryPoint()


if __name__ == "__main__":
    main()
