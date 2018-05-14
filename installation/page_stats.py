"""
===========================================
  stats_page.py
  https://github.com/ConnectBox/NEO_BatteryLevelShutdown
  License: MIT
  Version 1.0
  GeoDirk - May 2018
===========================================
"""

import sys
import os.path
import time
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from luma.core import cmdline, error
from luma.core.render import canvas
import json
import re

from HAT_Utilities import get_device, display_settings

def readStatsJSON(dt_range):
    with open('/var/www/connectbox/connectbox_default/stats.top10.json') as json_file:  
        data = json.load(json_file)
        print('============================')
        print('     ' + dt_range)
        print('============================')
        for p in data[dt_range]:
            print('file: ' + p['resource'])
            print('count: ' + str(p['count']))
    print('')


def draw_page(device, dt_range, page_num):
    # get an image
    dir_path = os.path.dirname(os.path.abspath(__file__))
    img_path =  dir_path + '/assets/stats_h_page.png'
    if dt_range == 'hour':
        img_path =  dir_path + '/assets/stats_h_page.png'
    elif dt_range == 'day':
        img_path =  dir_path + '/assets/stats_d_page.png'
    elif dt_range == 'week':
        img_path =  dir_path + '/assets/stats_w_page.png'
    elif dt_range == 'month':
        img_path =  dir_path + '/assets/stats_m_page.png'
    elif dt_range == 'year':
        img_path =  dir_path + '/assets/stats_y_page.png'                
    base = Image.open(img_path).convert('RGBA')
    fff = Image.new(base.mode, base.size, (255,) * 4)
    img = Image.composite(base, fff, base)

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', base.size, (255,255,255,0))

    # get a font
    font_path = os.path.abspath('connectbox.ttf')
    font20 = ImageFont.truetype(font_path, 22)
    font10 = ImageFont.truetype(font_path, 12)
    # get a drawing context
    d = ImageDraw.Draw(txt)

    # draw text, full opacity
    with open('/var/www/connectbox/connectbox_default/stats.top10.json') as json_file:  
        data = json.load(json_file)
        y = 0
        count = 0
        
        if page_num == 1:
            d.text((107, 18), 'p1', font=font20, fill="black")
        else:    
            d.text((107, 18), 'p2', font=font20, fill="black")

        #check to see if we have data or not
        for p in data[dt_range]:            
            if 'resource' in p.keys():
                #cover up the unhappy face
                d.rectangle((25, 1, 75, 128), fill="white")

        for p in data[dt_range]: 
            media = p['resource'].rsplit('/',1)[1]
            if page_num == 1:
                #trim out directories
                d.text((2, y), '(%s) %s'%(str(p['count']),media), font=font10, fill="black")
                y += 12
                count += 1
                if count == 5:
                    break
            else:
                #trim out directories
                count += 1
                if count > 5:
                    d.text((2, y), '(%s) %s'%(str(p['count']),media), font=font10, fill="black")
                    y += 12
     
    out = Image.alpha_composite(img, txt)
    device.display(out.convert(device.mode))
 	
def main(dt_range, pagenum):
    device = get_device()
    #readStatsJSON('hour')
    #readStatsJSON('day')
    #readStatsJSON('week')
    #readStatsJSON('month')
    #readStatsJSON('year')

    draw_page(device, dt_range, pagenum)
    #while True:
    #    i = 1
    return

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

'''
#triggers the log to refresh
sudo logrotate /etc/logrotate.hourly.conf
'''