import os
import time
import datetime

###===========================================
###  GLOBALS
###===========================================
pinLED = 6 #PA6 pin
pinVolt3_0 = 198  #PG6 pin - shutdown within 10 seconds
pinVolt3_2 = 199  #PG7 pin - above 3.2V
pinVolt3_4 = 200  #PG8 pin - above 3.4V
pinVolt3_6 = 201  #PG9 pin - above 3.6V

delay_sec = 0.1 #delay in LED flash

###===========================================
###  Setup the GPIO Pin for operation
###  in the system OS
###===========================================
def setup_gpio_pin(pinNum, direction):
	#check if file exists or not
	path = "/sys/class/gpio/gpio" + str(pinNum)
	if not os.path.isfile(path):
		#function for telling the system that it needs to create a
		#gpio pin for use
		try:
			os.system("echo {} > /sys/class/gpio/export".format(pinNum))
			os.system("echo \"" + direction + "\" > /sys/class/gpio/gpio{}/direction".format(pinNum))
		except:
			print("Error reading Pin {} value".format(str(pinNum)))

###===========================================
###  Blink the LED a certain number of times
###===========================================
def blink_LEDxTimes(pinNum, times):
	times = times * 2	#need to account for going on/off as two cycles
	bVal = True
	for num in range(0, times):
		if bVal:
			os.system("echo 1 > /sys/class/gpio/gpio" + str(pinNum) + "/value")
		else:
			os.system("echo 0 > /sys/class/gpio/gpio" + str(pinNum) + "/value")
		time.sleep(delay_sec)
		bVal = not bVal #toggle boolean
	#make sure that we turn the LED off
	os.system("echo 0 > /sys/class/gpio/gpio" + str(pinNum) + "/value")

###===========================================
###  Read the value from some input pin
###===========================================
def readPin(pinNum):
	try:
		sRet = os.popen("cat /sys/class/gpio/gpio" + str(pinNum) + "/value").read()
		if sRet == "1\n":
			return True
		else:
			return False
	except:
		print("Error reading Pin " + str(pinNum) + " Values")

###===========================================
###  Program entry point
###===========================================
if __name__ == "__main__":
	DEBUG = 1

	print("Intializing Pins\n")
	print("Pin: LED")
	setup_gpio_pin(pinLED, "out")
	print("Pin: PG6 3.0V")
	setup_gpio_pin(pinVolt3_0, "in")
	print("Pin: PG7 3.2V")
	setup_gpio_pin(pinVolt3_2, "in")
	print("Pin: PG8 3.4V")
	setup_gpio_pin(pinVolt3_4, "in")
	print("Pin: PG9 3.6V\n")
	setup_gpio_pin(pinVolt3_6, "in")

	print("Starting Monitoring")
	iIteration = 0
	bContinue = True
	while bContinue:
		#check if voltage is above 3.6V
		pinVolt = readPin(pinVolt3_6)
		if pinVolt:
			blink_LEDxTimes(6, 1)
		else:
			#check if voltage is above 3.4V
			pinVolt = readPin(pinVolt3_4)
			if pinVolt:
				blink_LEDxTimes(6, 2)
			else:
				#check if voltage is above 3.2V
				pinVolt = readPin(pinVolt3_2)
				if pinVolt:
					blink_LEDxTimes(6, 3)
				else:
					#check if voltage is above 3.0V
					pinVolt = readPin(pinVolt3_0)
					if pinVolt:
						#pin voltage is below 3V so we need to do a few iterations to make sure that we
						#are still getting the same info each time
						iIteration += 1
						if iIteration > 3:
							bContinue = False
						else:
							blink_LEDxTimes(6, 4)
					else:
						#pin volage above 3V so reset iteration
						iIteration = 0

		time.sleep(1)

	print("Exiting for Shutdown\n")
