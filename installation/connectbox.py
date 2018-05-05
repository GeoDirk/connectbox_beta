#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014-17 Richard Hull and contributors
# See LICENSE.rst for details.
# PYTHON_ARGCOMPLETE_OK

"""
Display the ConnectBox logo (loads image as .png).
"""
import sys
import os.path
import time
from PIL import Image
from PIL import ImageFont
from luma.core import cmdline, error
from luma.core.render import canvas

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
		
def main():
    draw_logo()
    time.sleep(5)

    while True:
       draw_text(device)


if __name__ == "__main__":
    try:
        device = get_device()
        main()
    except KeyboardInterrupt:
        pass
