#!/usr/bin/env python

import threading
import signal
import sys
import time
import zmq
import numpy as np
import picamera
import picamera.array
from duckiebot_driver.serial_interface import DuckietownSerial
from duckiebot_driver.message import DuckietownCommand

SERVER_PORT = 7777
CAMERA_RES = (640, 480)

PORT = '/dev/ttyS0'
BAUDRATE = 57600

# Create a default object, no changes to I2C address or frequency
motordriver=DuckietownSerial(PORT, BAUDRATE)
cmd = DuckietownCommand()

# Create camera object
camera = picamera.PiCamera()
camera.resolution = CAMERA_RES
camera.framerate = 10

# Numpy array of shape (rows, columns, colors)
imgArray = picamera.array.PiRGBArray(camera)

frameItr = camera.capture_continuous(imgArray, format='bgr', use_video_port=True)

def setMotors(lSpeed, rSpeed):
    lSpeed = min(max(lSpeed,-1.0),1.0)
    rSpeed = min(max(rSpeed,-1.0),1.0)

    if lSpeed > 0:
        cmd.pwm_ch1 = 255 - int(254*lSpeed)
    else:
        cmd.pwm_ch1 = int(255*lSpeed)
    if rSpeed > 0:
        cmd.pwm_ch2 = 255 - int(254*rSpeed)
    else:
        cmd.pwm_ch2 = int(255*rSpeed)
    driver.send_command(self.cmd)

exiting = False
lastImg = None

def camWorker():
    global exiting
    global lastImg
    while not exiting:
        lastImg = getImage()
    print('camera thread exiting')

def getImage():
    # Clear the image array between captures
    imgArray.truncate(0)
    next(frameItr)

    img = imgArray.array

    # Drop some rows and columns to downsize the image
    # Full image size is 1.2MB, which can be slow to stream over wifi
    img = img[0:480:4, 0:640:4]
    
    img = np.ascontiguousarray(img, dtype=np.uint8)

    return img

def signal_handler(signal, frame):
    global exiting

    print("exiting")

    exiting = True
    thread.join()

    # Stop the motors
    cmd.pwm_ch1 = 0
    cmd.pwm_ch2 = 0
    driver.send_command(cmd)
    
    # Close the camera
    camera.close()

    time.sleep(0.25)

    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

##############################################################################

serverAddr = "tcp://*:%s" % SERVER_PORT
print('Starting server at %s' % serverAddr)
context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.bind(serverAddr)

# Start a new thread for the camera
thread = threading.Thread(target=camWorker)
thread.start()

def sendArray(socket, array):
    """Send a numpy array with metadata over zmq"""
    md = dict(
        dtype=str(array.dtype),
        shape=array.shape,
    )
    # SNDMORE flag specifies this is a multi-part message
    socket.send_json(md, flags=zmq.SNDMORE)
    return socket.send(array, flags=0, copy=True, track=False)

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

    print('sending image')
    sendArray(socket, lastImg)
    print('sent image')

for message in poll_socket(socket):
    handle_message(message)
