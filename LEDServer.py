'''
@Author: Chris Lockard
This program interacts with the pi's gpio pins, blinks leds and runs
a TCP server that communicates the boards status with a client.
'''

# Imports
import RPi.GPIO as gpio
from time import sleep
import threading as thread
import socket
import os


def button_press(light_pin, button_pin, sleep_time):
	'''
	Target function for whenever a button controlling an LED is
	pressed.
	
	Accepts the lights pin, button pin and sleep time for the led blink
	speed.
	'''
	# Tries to run
	try:
		# While loop to blink the led at the requested speed which
		# Should be input as half the desired speed
		while True:
			# Gets button state
			state = gpio.input(button_pin)
			# Blinks
			if state == False:
				gpio.output(light_pin, gpio.HIGH)
				sleep(sleep_time)
				gpio.output(light_pin, gpio.LOW)
				sleep(sleep_time)
			# Turns the LED off
			else:
				gpio.output(light_pin, gpio.LOW)
	# Except block to clean gpio if there are any errors and stop the
	# thread
	except:
		gpio.output(light_pin, False)
		gpio.cleanup()
		return False


def shutdown(button_pin3):
	'''
	Target function that will shut down the pi after three seconds of
	holding SW3.
	
	Accepts the pin for the third button.
	'''
	# Counts seconds
	sec_count = 0
	while True:
		button3_press = gpio.input(button_pin3)
		# If total seconds is greater than 2 (started at 0) shutdown the
		# pi
		if sec_count >= 2:
			print('Stutting down..')
			gpio.cleanup()
			# Python passes this command to a new terminal session
			os.system('shutdown -h now')
		if button3_press == False:
			# Increments the counter
			sec_count += 1
		if button3_press == True:
			# Returns counter to 0 if the button has been released
			sec_count = 0
		
		# Sleeps to add one second to the loop
		sleep(1)

		
def TCPserver(host, port, button_pin1, button_pin2, button_pin3):
	'''
	Target function that runs the TCP server.
	
	Accepts host, port and all button pins.
	'''
	# Creates socket
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
		sock.bind((host, port))
		sock.listen()
		conn, addr = sock.accept()
		# Carried out for a conneciton
		with conn:
			# While loop to determine the state of each button and carry
			# out its respective string formatting
			while True:
				button1_press = gpio.input(button_pin1)
				button2_press = gpio.input(button_pin2)
				button3_press = gpio.input(button_pin3)
					
				SW1_status, SW2_status = 'Released', 'Released'
				
				if button1_press == False:
					SW1_status = 'Pressed'
				if button2_press == False:
					SW2_status = 'Pressed'
				
				trans_string = r'{SW1: ' + SW1_status + ', SW2: ' + SW2_status + r'}'
				trans_string = trans_string.encode()
				
				if button3_press == False:
					trans_string = 'SW3 pressed, server shutting down..'.encode()
				
				conn.send(trans_string)
				# Receives ack from client
				data = conn.recv(1024)
				# Sleeps for 1 so that the message is received every 1
				# second
				sleep(1)
		
		# Closes socket when done		
		sock.close()
		

# Sets variables and starts threads when file is run
if __name__ == "__main__":
	gpio.setmode(gpio.BCM)
	gpio.setwarnings(False)
	
	# GPIO pins used
	lightR = 23
	lightG = 24
	button1 = 14
	button2 = 15
	button3 = 18

	gpio.setup((lightR, lightG), gpio.OUT)
	gpio.setup((button1, button2, button3), gpio.IN, pull_up_down=gpio.PUD_UP)

	# Starts the threads for each button
	T1 = thread.Thread(target=button_press, args=(lightR, button1, .5))
	T1.start()
	T2 = thread.Thread(target=button_press, args=(lightG, button2, .25))
	T2.start()
	T3 = thread.Thread(target=shutdown, args=(button3,))
	T3.start()

	try:
		# Starts the TCP server
		TCPserver('', 8888, button1, button2, button3)
	
	# Ensures that everything closes correctly if the program is closed
	except:
		gpio.output(lightR, False)
		gpio.output(lightG, False)
		gpio.cleanup()



	
