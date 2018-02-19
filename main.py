#!/usr/bin/env python

import signal
import sys
import time
import zmq
import numpy as np
import picamera
import picamera.array
from Adafruit_MotorHAT import Adafruit_MotorHAT

SERVER_PORT = 7777
CAMERA_RES = (640, 480)

# Create a default object, no changes to I2C address or frequency
motorhat = Adafruit_MotorHAT(addr=0x60)
leftMotor = motorhat.getMotor(1)
rightMotor = motorhat.getMotor(2)

# Create camera object
camera = picamera.PiCamera()
camera.resolution = CAMERA_RES

# Numpy array of shape (rows, columns, colors)
imgArray = picamera.array.PiRGBArray(camera)

frameItr = camera.capture_continuous(imgArray, format='rgb', use_video_port=True)

def setMotors(lSpeed, rSpeed):
    lSpeed = max(-255, min(255, lSpeed * 255))
    rSpeed = max(-255, min(255, rSpeed * 255))

    if lSpeed > 0:
        leftMotor.run(Adafruit_MotorHAT.FORWARD)
        leftMotor.setSpeed(lSpeed)
    else:
        leftMotor.run(Adafruit_MotorHAT.BACKWARD)
        leftMotor.setSpeed(-lSpeed)

    if rSpeed > 0:
        rightMotor.run(Adafruit_MotorHAT.FORWARD)
        rightMotor.setSpeed(rSpeed)
    else:
        rightMotor.run(Adafruit_MotorHAT.BACKWARD)
        rightMotor.setSpeed(-rSpeed)

def getImage():
    # Clear the image array between captures
    imgArray.truncate(0)
    next(frameItr)

    img = imgArray.array

    # Do this on the client, if necessary
    # BGR to RGB
    #img = img[:, :, ::-1]

    img = np.ascontiguousarray(img, dtype=np.uint8)

    return img

def signal_handler(signal, frame):
    print ("exiting")

    # Stop the motors
    leftMotor.run(Adafruit_MotorHAT.RELEASE)
    rightMotor.run(Adafruit_MotorHAT.RELEASE)

    # Close the camera
    camera.close()

    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

##############################################################################

serverAddr = "tcp://*:%s" % SERVER_PORT
print('Starting server at %s' % serverAddr)
context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.bind(serverAddr)

def poll_socket(socket, timetick = 10):
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    # wait up to 10msec
    try:
        print("poller ready")
        while True:
            obj = dict(poller.poll(timetick))
            if socket in obj and obj[socket] == zmq.POLLIN:
                yield socket.recv_json()
    except KeyboardInterrupt:
        print ("stopping server")
        quit()

def handle_message(msg):
    if msg['command'] == 'action':
        print('received motor velocities')
        print(msg['values'])
        left, right = tuple(msg['values'])
        setMotors(left, right)
    elif msg['command'] == 'reset':
        print('got reset command')
    else:
        assert False, "unknown command"

    img = getFrame()

    print('sending image')
    sendArray(socket, img)
    print('sent image')

for message in poll_socket(socket):
    handle_message(message)
