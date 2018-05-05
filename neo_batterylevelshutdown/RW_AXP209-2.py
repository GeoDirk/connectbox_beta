#!/usr/bin/python

# Nice summary of smbus commands at: 
#    http://wiki.erazor-zone.de/wiki:linux:python:smbus:doc
#
# Need the following before using commands...
import smbus
import time

# Then need to create a smbus object like...
bus = smbus.SMBus(0)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

# Then we can use smbus commands like... (prefix commands with "bus.") 
#
# read_byte(dev)     / reads a byte from specified device
# write_byte(dev,val)   / writes value val to device dev, current register
# read_byte_data(dev,reg) / reads byte from device dev, register reg
# write_byte_data(dev,reg,val) / write byte val to device dev, register reg 
#

# Start building the interactive menuing...

dev_i2c = 0x34 # for AXP209 = 0x34

def batteryVoltage():
   datH = bus.read_byte_data(dev_i2c,0x78)
   time.sleep (0.05)
   datL = bus.read_byte_data(dev_i2c,0x79)
   time.sleep (0.05)
   dat = datH * 16 + datL
   return (dat * 0.0011)

def batteryCharge():
   datH = bus.read_byte_data(dev_i2c,0x7A)
   time.sleep(0.05)
   datL = bus.read_byte_data(dev_i2c,0x7B)
   time.sleep(0.05)
   dat = datH * 16 +datL
   return (dat + 0.0005)

def batteryDischarge():
   bus.write_byte_data(dev_i2c,0x82,0xC3)
   time.sleep(0.05)
   datH = bus.read_byte_data(dev_i2c,0x7C)
   time.sleep(0.05)
   datL = bus.read_byte_data(dev_i2c,0x7D)
   time.sleep(0.05)
   dat = datH * 32 + datL
   return (dat * 0.0005)

def ipsoutVoltage():
   datH = bus.read_byte_data(dev_i2c,0x7E)
   time.sleep(0.05)
   datL = bus.read_byte_data(dev_i2c,0x7f)
   time.sleep(0.05)
   dat = datH * 16 + datL
   return (dat * 0.0011)

def chipTemp():
   datH = bus.read_byte_data(dev_i2c,0x5E)
   time.sleep(0.05)
   datL = bus.read_byte_data(dev_i2c,0x5F)
   time.sleep(0.05)
   dat = datH * 16 + datL
   return (dat * 0.1 - 144.7)

# Give some instructions:
print "\n\nRW_AXP209.py tool instuctions\n"
print "You can choose to either Read [R] or Write [W] a register in the AXP209"
print "You will be asked for the register address (in HEX) and, (if doing a"
print "write) the data to be written (also in HEX)."
print "Written data will be verified with an automatic read following the write"
print "and the success or failure will be noted along with the read data."
print "\nType an X to exit the program.\n\n"
print "\nTyping an S will give a summary of some interesting information.\n"

while True:
   action = raw_input("Would you like to [R]ead, [W]rite or E[X]it?  ")
   if ((action == "R") or (action == "r")):
      hexreg = raw_input("Enter the register you want to READ (HEX): ")
      hexreg = int(hexreg,16)

      hexval = bus.read_byte_data(dev_i2c, hexreg)
      print ("Value at register %s is %s\n\n" % (format(hexreg, '#02X') , format(hexval, '#02X')))

   elif ((action == "W") or (action == "w")):
      hexreg = raw_input("Enter the register to which you want to WRITE (HEX): ")
      hexreg = int(hexreg,16)
      hexval = raw_input("Enter the value to WRITE (HEX): ")
      hexval = int(hexval,16)
      bus.write_byte_data(dev_i2c, hexreg, hexval)
      newdata = bus.read_byte_data(dev_i2c, hexreg)
      print ("Value at register %s now is %s" % (format(hexreg,'#02X'),format(newdata, '#02X')))
      if newdata == hexval:
         print "SUCCESS!\n\n"
      else:
         print "Write did not succeed...\n\n" 
   
   elif ((action == "S") or (action == "s")):
      print ("IPS_OUT voltage reads:     %2.3f V" % ipsoutVoltage())
      time.sleep(1)
      print ("Battery voltage reads:     %2.3f V" % batteryVoltage())
      time.sleep(1)
      print ("Battery charge current:    %2.3f A" % batteryCharge())
      time.sleep(1)
      print ("Battery discharge current: %2.3f A" % batteryDischarge())
      time.sleep(1)
      print ("Chip temperature:          %3.1f C" % chipTemp())
      print

   elif ((action == "X") or (action == "x")):
      break

   

