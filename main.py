#!/usr/bin/env python

import time
import zmq

import numpy as np

import picamera
import picamera.array
#from picamera.array import PiRGBArray

from Adafruit_MotorHAT import Adafruit_MotorHAT

# Create a default object, no changes to I2C address or frequency
motorhat = Adafruit_MotorHAT(addr=0x60)
leftMotor = motorhat.getMotor(1)
rightMotor = motorhat.getMotor(2)

# Create camera object
camera = picamera.PiCamera()
camera.resolution = (640, 480)

# Numpy array of shape (rows, columns, colors)
imgArray = picamera.array.PiRGBArray(camera)



startTime = time.time()
frameItr = camera.capture_continuous(imgArray, format='rgb', use_video_port=True)

for i in range(0, 100):

    # Clear the image array between captures
    imgArray.truncate(0)
    next(frameItr)



    print(imgArray.array.shape)

    print(mean)


endTime = time.time()

fps = 100 / (endTime - startTime)
print('fps: %s' % fps)



























#leftMotor.run(Adafruit_MotorHAT.FORWARD)
#rightMotor.run(Adafruit_MotorHAT.FORWARD)
#leftMotor.setSpeed(120)
#rightMotor.setSpeed(60)









# Stop the motors
leftMotor.run(Adafruit_MotorHAT.RELEASE)
rightMotor.run(Adafruit_MotorHAT.RELEASE)
