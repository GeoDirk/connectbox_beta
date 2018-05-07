#!/bin/bash

cd ~
echo " "
echo "Checking for apt locks"
## check if DPKG database is locked
dpkg -i /dev/zero 2>/dev/null
if [ "$?" -eq 2 ]; then
    echo "-->dpkg database is locked by a system upgrade. Try again later..."
	exit 0
fi
echo "-->No lock in place...continuing with install"


sudo apt-get install python3-dev python3-pip libfreetype6-dev libjpeg-dev build-essential i2c-tools -y
sudo -H pip3 install --upgrade pip
sudo -H pip3 install --upgrade pip setuptools
sudo -H pip3 install smbus2
sudo -H pip3 install axp209
#sometimes problems with installing the next command with the d/l of pillow
#it can KILL the process and mess up the full install
sudo -H pip3 install --upgrade luma.oled


#add in I2C overlay
sed -i '/overlays=usbhost0 usbhost1 usbhost2 usbhost3/c\overlays=usbhost0 usbhost1 usbhost2 usbhost3 i2c0' /boot/armbianEnv.txt


#download example files
wget https://raw.githubusercontent.com/GeoDirk/NEO_OLED_Setup/master/neo_batterylevelshutdown.py
wget https://raw.githubusercontent.com/GeoDirk/NEO_OLED_Setup/master/connectbox_logo.png
wget https://raw.githubusercontent.com/GeoDirk/NEO_OLED_Setup/master/connectbox.ttf

echo " "
echo "Please restart to implement changes!"
echo "  _____  ______  _____ _______       _____ _______ "
echo " |  __ \|  ____|/ ____|__   __|/\   |  __ \__   __|"
echo " | |__) | |__  | (___    | |  /  \  | |__) | | |   "
echo " |  _  /|  __|  \___ \   | | / /\ \ |  _  /  | |   "
echo " | | \ \| |____ ____) |  | |/ ____ \| | \ \  | |   "
echo " |_|  \_\______|_____/   |_/_/    \_\_|  \_\ |_|   "
echo " "
echo "Please restart to implement changes!"
echo "To Restart type sudo reboot"

echo "To finish changes, we will reboot the NEO."
echo "Pi must reboot for changes and updates to take effect."
echo "If you need to abort the reboot, press Ctrl+C.  Otherwise, reboot!"
echo "Rebooting in 5 seconds!"
sleep 1
echo "Rebooting in 4 seconds!"
sleep 1
echo "Rebooting in 3 seconds!"
sleep 1
echo "Rebooting in 2 seconds!"
sleep 1
echo "Rebooting in 1 seconds!"
sleep 1
echo "Rebooting now!  "
sleep 1
sudo reboot