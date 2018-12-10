import numpy as np
import cv2
import os
import sys
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

#Cascade Settings
faceCascade = cv2.CascadeClassifier('/home/pi/Desktop/122/py_servo_facetracker/haarcascade_frontalface_alt.xml')

#ServoBlaster Settings
panDegrees = 1 # Pan degree change
tiltDegrees= 1 # Tilt degree change
initialX = 140 # starting x position
initialY = 140 # starting tilt position

#Pinouts
"""
Servo number    GPIO number   Pin in P1 header
          0               4             P1-7
          1              17             P1-11
          2              18             P1-12
          3             21/27           P1-13
          4              22             P1-15
          5              23             P1-16
          6              24             P1-18
          7              25             P1-22
"""
panGpioPin = 1  # gpio pin 4
tiltGpioPin = 2  # gpio pin 12

GPIO_TRIGGER = 23 # pin 16
GPIO_ECHO = 22	# pin 18
 
#set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
 
def distance():
    new_reading = False
    counter = 0
    # set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER, True)
 
    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
 
    StartTime = time.time()
    StopTime = time.time()
 
    # save StartTime
    while GPIO.input(GPIO_ECHO) == 0:
        pass
        counter +=1
        if counter == 2000:
                new_reading==True
                break
    StartTime = time.time()
    
    if new_reading:
        return False

    # save time of arrival
    while GPIO.input(GPIO_ECHO) == 1:
        pass
    StopTime = time.time()
 
    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2

    print ("Measured Distance = %.1f cm" % distance)
    time.sleep(0.25)
    return distance

def move(servo, angle):
    command = 'echo %s=%s > /dev/servoblaster' % (str(servo), str(angle))
    os.system(command)

def detect(cap, faceCascade):
	ret, img = cap.read()
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	faces = faceCascade.detectMultiScale(
		gray,     
		scaleFactor=2,
		minNeighbors=3,     
		minSize=(30, 30)
	)
	center = None
	for (x,y,w,h) in faces:
		pt1 = (int(x), int(y))
		pt2 = (int(x + w), int(y + h))
		cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)
		roi_gray = gray[y:y+h, x:x+w]
		roi_color = img[y:y+h, x:x+w]
		topLeft = pt1[0]
		topRight = pt2[0]
		bottomLeft = pt1[1]
		bottomRight = pt2[1]
		centerX = topLeft+((topRight-topLeft)/2)
		centerY = bottomLeft+((bottomRight-bottomLeft)/2)
		center = (centerX, centerY)
		
	cv2.imshow('video',img)
	return center



if __name__ == '__main__':
	cap = cv2.VideoCapture(0)
	cap.set(3,640) # set Width
	cap.set(4,480) # set Height
	width = cap.get(3)
	height = cap.get(4)

	print("Moving to initial position...")
	move(panGpioPin, initialX)
	move(tiltGpioPin, initialY)
	dist=0
	while True:
		dist = distance()
		if ((dist < 10) and (dist > 0.5)) :
			move(panGpioPin, initialX)
			move(tiltGpioPin, initialY)
			
			centerScreenX = (width/2)
			centerScreenY = (height/2)
			
			
			center = detect(cap, faceCascade)
			
			if ((center is not None) and (GPIO.input(12) == False) and (GPIO.input(16) == False) and (GPIO.input(20) == False) and (GPIO.input(21) == False)):
				centerX = center[0]
				centerY = center[1]
				# Check if right of center
				if(centerX < (centerScreenX - 30)):
					# Move servo right
					initialX += panDegrees
					print str(centerX) + " > " + str(centerScreenX) + " : Pan Right : " + str(initialX)
				# Check if left of center
				elif(centerX > (centerScreenX + 30)):
					# Move servo left
					initialX -= panDegrees
					print str(centerX) + " > " + str(centerScreenX) + " : Pan Left : " + str(initialX)
				else:
					print str(centerX) + " ~ " + str(centerScreenX) + " : " + str(initialX)
				
				initialX = min(initialX, 249)
				initialX = max(initialX, 1)               
				move(panGpioPin, initialX)

				# Check if above center of screen
				if(centerY < (centerScreenY - 30)):
					if(initialY <= 249):
						# Tilt down
						initialY -= tiltDegrees
						print str(centerY) + " > " + str(centerScreenY) + " : Tilt Up : " + str(initialY)
				# Check if below center of screen
				elif(centerY > (centerScreenY + 30)):
					if(initialY >= 1):
						# Tilt up
						initialY += tiltDegrees
						print str(centerY) + " > " + str(centerScreenY) + " : Tilt Down : " + str(initialY)
				else:
					print str(centerY) + " ~ " + str(centerScreenY) + " : " + str(initialY)
				
				initialY = min(initialY, 249)
				initialY = max(initialY, 1)  
				move(tiltGpioPin, initialY)
		
			elif (GPIO.input(12) == True):
				print("DOWN")
				initialY += tiltDegrees+2
				initialY = min(initialY, 249)
				initialY = max(initialY, 1)  
				move(tiltGpioPin, initialY)			
				time.sleep(0.3)
				
			elif (GPIO.input(16) == True):
				print("UP")
				initialY -= tiltDegrees+2
				initialY = min(initialY, 249)
				initialY = max(initialY, 1)
				move(tiltGpioPin, initialY)			
				time.sleep(0.3)
				
			elif (GPIO.input(20) == True):
				print("RIGHT")
				initialX += panDegrees+2
				initialX = min(initialX, 249)
				initialX = max(initialX, 1)
				move(panGpioPin, initialX)
				time.sleep(0.3)
				
			elif (GPIO.input(21) == True):
				print("LEFT")
				initialX -= panDegrees+2
				initialX = min(initialX, 249)
				initialX = max(initialX, 1)
				move(panGpioPin, initialX)
				time.sleep(0.3)
				
		elif (GPIO.input(12) == True):
			print("DOWN")
			initialY += tiltDegrees+2
			initialY = min(initialY, 249)
			initialY = max(initialY, 1)  
			move(tiltGpioPin, initialY)			
			time.sleep(0.3)
			
		elif (GPIO.input(16) == True):
			print("UP")
			initialY -= tiltDegrees+2
			initialY = min(initialY, 249)
			initialY = max(initialY, 1)
			move(tiltGpioPin, initialY)			
			time.sleep(0.3)
			
		elif (GPIO.input(20) == True):
			print("RIGHT")
			initialX += panDegrees+2
			initialX = min(initialX, 249)
			initialX = max(initialX, 1)
			move(panGpioPin, initialX)
			time.sleep(0.3)
			
		elif (GPIO.input(21) == True):
			print("LEFT")
			initialX -= panDegrees+2
			initialX = min(initialX, 249)
			initialX = max(initialX, 1)
			move(panGpioPin, initialX)
			time.sleep(0.3)
			
		k = cv2.waitKey(30) & 0xff

		if k == 27: # press 'ESC' to quit
			break

	GPIO.cleanup()
	cap.release()
	cv2.destroyAllWindows()