# OLED Testing

This installation directory contains everything you need to install the new version of the neo_batterylevelshutdown.py program.  The program will detect if you have the 100 Unit Run HAT or the new OLED HAT.  If the 100 Unit Run HAT, it will just run the program like normal.  It the OLED, then it will incorporate all the new code to display various messages onto the display.

To use:

First clone the repo
> git clone https://github.com/ConnectBox/NEO_BatteryLevelShutdown

Move into the repo
> cd NEO_BatteryLevelShutdown/

Switch branches to OLED_Testing branch
> git checkout -t origin/OLED_Testing

Get into the /installation directory
> cd installation/

Modify the script to be executable
> chmod 755 install_libraries.sh

Run the script
> ./install_libraries.sh

After the reboot, you'll need to drop back into the git directory structure
> cd NEO_BatteryLevelShutdown/installation/

Then run the program
> python3 neo_batterylevelshutdown.py

The unit is designed currently to use the Left and Middle buttons.  Right now, the Right button doesn't do anything
