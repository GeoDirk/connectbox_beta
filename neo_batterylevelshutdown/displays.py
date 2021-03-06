# -*- coding: utf-8 -*-

import logging
import os
import threading
from PIL import Image
from .HAT_Utilities import get_device
from . import page_none
from . import page_main
from . import page_battery
from . import page_info
from . import page_stats
from . import page_memory
from . import page_battery_low
from . import page_display_image

class DummyDisplay:

    def __init__(self, powerManagementDevice):
        pass

    def moveForward(self):
        pass

    def moveBackward(self):
        pass

    def powerOffDisplay(self):
        pass

    def showLowBatteryWarning(self):
        pass

    def hideLowBatteryWarning(self):
        pass

    def drawLogo(self):
        # should this be exposed publicly, or should it be private and
        #  simply called in the constructor or via some standard interface?
        pass


class OLED:

    # What to show after startup and blank screen
    STARTING_PAGE_INDEX = 0  # the main page

    def __init__(self, powerManagementDevice):
        # rename this.... perhaps it doesn't even need to be stored
        self.axp = powerManagementDevice
        self.display_device = get_device()
        self.blank_page = page_none.PageBlank(self.display_device)
        self.low_battery_page = \
            page_battery_low.PageBatteryLow(self.display_device)
        self.statusPages = [
            page_main.PageMain(self.display_device, self.axp),
            page_info.PageInfo(self.display_device),
            page_battery.PageBattery(self.display_device, self.axp),
            page_memory.PageMemory(self.display_device),
            page_stats.PageStats(self.display_device, 'hour', 1),
            page_stats.PageStats(self.display_device, 'hour', 2),
            page_stats.PageStats(self.display_device, 'day', 1),
            page_stats.PageStats(self.display_device, 'day', 2),
            page_stats.PageStats(self.display_device, 'week', 1),
            page_stats.PageStats(self.display_device, 'week', 2),
            page_stats.PageStats(self.display_device, 'month', 1),
            page_stats.PageStats(self.display_device, 'month', 2),
            page_display_image.PageDisplayImage(self.display_device, 'show_admin.png'),
        ]
        self.adminPages = [
            page_display_image.PageDisplayImage(self.display_device, 'copy_from_usb.png'),
            page_display_image.PageDisplayImage(self.display_device, 'erase_folder.png'),
            page_display_image.PageDisplayImage(self.display_device, 'exit.png'),  # MUST be last item in list
        ]
        self.adminPageNames = [
            'copy_from_usb',
            'erase_folder',
            'exit'
        ]

        self.pages = self.statusPages
        self.pageStack = 'status'

        self._curPage = self.pages[self.STARTING_PAGE_INDEX]
        # callbacks run in another thread, so we need to lock access to the
        #  current page variable as it can be modified from the main loop
        #  and from callbacks
        self._curPageLock = threading.Lock()
        # draw the connectbox logo - classes containing an OLED display
        #  manage timeouts and timed display power-downs, so we leave that
        #  as an exercise for anyone using this class
        self.drawLogo()

    def getAdminPageName(self):
        try:
            return  self.adminPageNames[self.adminPages.index(self._curPage)]
        except:
            return ''

    def checkIfLastPage(self):
        return True if self._curPage == self.pages[-1] else False

    def showRemoveUsbPage(self):
        with self._curPageLock:
            logging.debug("Showing remove usb page")
            self._curPage = page_display_image.PageDisplayImage(self.display_device, 'remove_usb.png')
            self._curPage.draw_page()

    def showNoUsbPage(self):
        with self._curPageLock:
            logging.debug("Showing no usb page")
            self._curPage = page_display_image.PageDisplayImage(self.display_device, 'error_no_usb.png')
            self._curPage.draw_page()

    def showNoSpacePage(self):
        with self._curPageLock:
            logging.debug("Showing no space page")
            self._curPage = page_display_image.PageDisplayImage(self.display_device, 'error_no_space.png')
            self._curPage.draw_page()

    def showWaitPage(self):
        with self._curPageLock:
            logging.debug("Showing wait page")
            self._curPage = page_display_image.PageDisplayImage(self.display_device, 'wait.png')
            self._curPage.draw_page()

    def showConfirmPage(self):
        with self._curPageLock:
            logging.debug("Showing confirm choice page")
            self.pageStack = 'confirm'
            self._curPage = page_display_image.PageDisplayImage(self.display_device, 'confirm.png')
            self._curPage.draw_page()

    def showSuccessPage(self):
        with self._curPageLock:
            logging.debug("Showing success page")
            self._curPage = page_display_image.PageDisplayImage(self.display_device, 'success.png')
            self._curPage.draw_page()

    def showErrorPage(self):
        with self._curPageLock:
            logging.debug("Showing error page")
            self._curPage = page_display_image.PageDisplayImage(self.display_device, 'error.png')
            self._curPage.draw_page()

    def switchPages(self):
        '''
        This method is to switch between the original stack of pages referred to as status pages and the new stack
        of pages referred to as admin pages.  This is based upon the variable pageStack.
        :return: Nothing
        '''
        with self._curPageLock:
            logging.debug("Previous page stack: {}".format(self.pageStack))
            self.pages = self.statusPages if self.pageStack == 'admin' else self.adminPages
            self.pageStack = 'status' if self.pageStack == 'admin' else 'admin'
            logging.debug("Current page stack: {}".format(self.pageStack))
            self._curPage = self.pages[0]

            # draw the page while holding the lock, so that it doesn't change
            #  underneath us
            self._curPage.draw_page()
            logging.debug("Transitioned to page %s", self._curPage)

    def moveForward(self):
        with self._curPageLock:
            logging.debug("Current page is %s", self._curPage)
            if self._curPage not in self.pages:
                # Always start with the starting page if the screen went off
                #  or if we were showing the low battery page
                self._curPage = self.pages[self.STARTING_PAGE_INDEX]
            else:
                # move forward in the page list
                # If we're at the end of the page list, go to the start
                if self._curPage == self.pages[-1]:
                    self._curPage = self.pages[0]
                else:
                    self._curPage = \
                        self.pages[self.pages.index(self._curPage) + 1]

            # draw the page while holding the lock, so that it doesn't change
            #  underneath us
            self._curPage.draw_page()
            logging.debug("Transitioned to page %s", self._curPage)

    def moveBackward(self):
        with self._curPageLock:
            logging.debug("Current page is %s", self._curPage)
            if self._curPage not in self.pages:
                # Always start with the starting page if the screen went off
                #  or if we were showing the low battery page
                self._curPage = self.pages[self.STARTING_PAGE_INDEX]
            else:
                # move backwards in the page list
                # If we're at the start of the page list, go to the start
                if self._curPage == self.pages[0]:
                    self._curPage = self.pages[-1]
                else:
                    self._curPage = \
                        self.pages[self.pages.index(self._curPage) - 1]

            # draw the page while holding the lock, so that it doesn't change
            #  underneath us
            self._curPage.draw_page()
            logging.debug("Transitioned to page %s", self._curPage)

    def showLowBatteryWarning(self):
        if self._curPage == self.low_battery_page:
            # nothing to do
            return

        with self._curPageLock:
            logging.debug("Current page is %s", self._curPage)
            self._curPage = self.low_battery_page
            self._curPage.draw_page()
            logging.debug("Transitioned to page %s", self._curPage)

    def hideLowBatteryWarning(self):
        if self._curPage == self.low_battery_page:
            self.powerOffDisplay()

    def powerOffDisplay(self):
        if self._curPage == self.blank_page:
            # nothing to do
            return 

        with self._curPageLock:
            logging.debug("Current page is %s", self._curPage)
            self._curPage = self.blank_page
            self._curPage.draw_page()
            logging.debug("Transitioned to page %s", self._curPage)

    # Ideally this should be a page, like the low battery page
    def drawLogo(self):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        img_path = dir_path + '/assets/connectbox_logo.png'
        logo = Image.open(img_path).convert("RGBA")
        fff = Image.new(logo.mode, logo.size, (255,) * 4)
        background = Image.new("RGBA", self.display_device.size, "black")
        posn = ((self.display_device.width - logo.width) // 2, 0)
        img = Image.composite(logo, fff, logo)
        background.paste(img, posn)
        self.display_device.display(
            background.convert(self.display_device.mode)
        )
