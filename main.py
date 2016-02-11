#!/usr/bin/env python

import time
import zmq

import picamera
from picamera import PiCamera
from picamera.array import PiRGBArray

from Adafruit_MotorHAT import Adafruit_MotorHAT

# create a default object, no changes to I2C address or frequency
motorhat = Adafruit_MotorHAT(addr=0x60)
leftMotor = motorhat.getMotor(1)
rightMotor = motorhat.getMotor(2)


#leftMotor.run(Adafruit_MotorHAT.FORWARD)
#rightMotor.run(Adafruit_MotorHAT.FORWARD)
#leftMotor.setSpeed(120)
#rightMotor.setSpeed(60)









# Stop the motors
leftMotor.run(Adafruit_MotorHAT.RELEASE)
rightMotor.run(Adafruit_MotorHAT.RELEASE)
