#!/bin/sh
echo "This script fixes the mac address of the unit thereby causing it to not"
echo "assign a new one and thereby forcing DHCP to issue a new IP address"

sed -i -e 's/allow-hotplug eth0/no-auto-down eth0/g' /etc/network/interfaces

sed -i -e 's/exit 0/#exit 0/g' /etc/rc.local 
echo "/sbin/ifconfig eth0 down" >> /etc/rc.local
echo "/sbin/ifconfig eth0 hw ether ca:07:59:65:16:ca" >> /etc/rc.local

# ifup here, instead of ifconfig, so we run the up-down scripts which
#  will give us an IP address (among other things)
echo "/sbin/ifup eth0" >> /etc/rc.local
echo "exit 0" >> /etc/rc.local
