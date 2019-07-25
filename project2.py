import RPi.GPIO as gpio
from time import sleep, time
from gpiozero import DistanceSensor
import threading as thread

def RGB_setup(red, green, blue):
	'''
	Simply sets up the gpio pins for the colors
	'''
	gpio.setup((red, green, blue), gpio.OUT)
	return True

def change_color(distance, red, green, blue):
	'''
	Function to change the color of RGB led based on distance
	'''
	if distance > 20:
		red_dc, green_dc, blue_dc = 100, 0, 0
	
	elif distance <= 20 and distance >= 17:
		red_dc, green_dc, blue_dc = 100, 15, 0
		
	elif distance < 17 and distance >= 13:
		red_dc, green_dc, blue_dc = 100, 50, 0
	
	elif distance < 13 and distance >= 10:
		red_dc, green_dc, blue_dc = 25, 100, 0
	
	elif distance < 10 and distance >= 7:
		red_dc, green_dc, blue_dc = 25, 100, 50
		
	elif distance < 7 and distance > 3:
		red_dc, green_dc, blue_dc = 25, 25, 100
	
	elif distance <= 3 and distance > 0:
		red_dc, green_dc, blue_dc = 100, 0, 100	
	
	else:
		red_dc, green_dc, blue_dc = 0, 0, 100
	
	red.ChangeDutyCycle(red_dc)
	blue.ChangeDutyCycle(blue_dc)
	green.ChangeDutyCycle(green_dc)
	
	
	return distance, (red_dc, blue_dc)


def read_distance(trig, echo, red, green, blue):
	'''
	Target function for the ultrasonic sensor thread. Based on the
	value of the programs mode, it will determine weather or not to
	print/change the hue of the led.
	'''
	while True:
			sleep(.5)
			gpio.output(trig, True)
			sleep(0.00001)
			gpio.output(trig, False)

			while gpio.input(echo)==0:
				pulse_start = time()

			while gpio.input(echo)==1:
				pulse_end = time()

			pulse_duration = (pulse_end - pulse_start)*1000000

			distance = pulse_duration/58.0
			distance = round(distance, 2)
			
			if mode == 'Monitor':
				change_color(distance, RED, GREEN, BLUE)
				print(distance)
				
			elif mode == 'Monitor&Record':
				change_color(distance, RED, GREEN, BLUE)
				print(distance)
				# something here to write to the file
			
			elif mode == 'Record':
				# something here to write to the file
				red.ChangeDutyCycle(0)
				blue.ChangeDutyCycle(0)
				green.ChangeDutyCycle(0)
	

def led_controller(led):
	'''
	Target function that controls the led based on the mode.
	'''		
	while True:
		if mode == 'Monitor':
			gpio.output(led, False)
		elif mode == 'Monitor&Record':
			gpio.output(led, True)
		elif mode == 'Record':
			sleep(.5)
			gpio.output(led, False)
			sleep(.5)
			gpio.output(led, True)

def binary_conversion(pot1, pot2, pot3, pot4):
	'''
	Converts the pot binary value to int
	'''
	binary = ''.join(
		(str(gpio.input(pot1)),str(gpio.input(pot2)),
		str(gpio.input(pot3)),str(gpio.input(pot4)))
	)
	return int(binary, 2)
	

def pot_reader(pot1, pot2, pot3, pot4, buzzer):
	'''
	Target funciton to control the pot funcitonality based on the mode
	'''
	pass

if __name__ == '__main__':
	# Constants for pin values
	red = 5
	green = 6
	blue = 13
	led = 14
	buzzer = 18
	button = 16
	trig = 25
	echo = 24

	# These are actually in the wrong order, but I didnt want to change
	pot1 = 7
	pot2 = 8
	pot3 = 9
	pot4 = 11
	freq = 100
	
	# Board settings
	gpio.setmode(gpio.BCM)
	gpio.setwarnings(False)
	
	# GPIO setup
	RGB_setup(red, green, blue)
	gpio.setup((pot1, pot2, pot3, pot4), gpio.IN)
	gpio.setup(button, gpio.IN, pull_up_down=gpio.PUD_UP)
	gpio.setup((led, buzzer), gpio.OUT)
	gpio.setup(echo, gpio.IN)
	gpio.setup(trig, gpio.OUT, initial=gpio.LOW)
	
	# PWM setup
	RED = gpio.PWM(red, freq)
	GREEN = gpio.PWM(green, freq)
	BLUE = gpio.PWM(blue, freq)
	BUZZ = gpio.PWM(buzzer, freq)
	
	# Starting the PWM at duty cycles of 0
	BUZZ.start(0)
	RED.start(0)
	BLUE.start(0)
	GREEN.start(0)
	
	# Initial mode
	mode = 'Monitor'
	
	# Instantiates and runs the ultra sonic sensor thread
	ultra_thread = thread.Thread(target=read_distance, args=(trig, echo, RED, GREEN, BLUE,))
	ultra_thread.start()
	
	# Instantiates and runs the led indicator thread
	led_thread = thread.Thread(target=led_controller, args=(led,))
	led_thread.start()
	
	# Instantiates and runs the pot thread
	# Side note, the pot is on the 5v channel so it will already be
	# collecting data at the start of the thread
	pot_thread = thread.Thread(target=pot_reader)
	
	
	try:
		time_count = 0
		while True:
			#pot_reader(pot1, pot2, pot3, pot4)
			
			if gpio.input(button) == False:
				time_count += 1
			else:
				if time_count < 2:
					time_count = 0
				elif mode == 'Monitor':
					if time_count >= 2 and time_count < 5:
						mode = 'Monitor&Record'
						time_count = 0
					elif time_count >= 5:
						mode = 'Record'
						time_count = 0
				elif mode == 'Monitor&Record':
					if time_count >= 2 and time_count < 5:
						mode = 'Monitor'
						time_count = 0
					elif time_count >= 5:
						mode = 'Record'
						time_count = 0
				elif mode == 'Record':
					if time_count >= 2 and time_count < 5:
						mode = 'Monitor&Record'
						time_count = 0
					elif time_count >= 5:
						mode = 'Monitor'
						time_count = 0
			
			print(mode)
				
			sleep(1)
	except KeyboardInterrupt:
		gpio.cleanup()
