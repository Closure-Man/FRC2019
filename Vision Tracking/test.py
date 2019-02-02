#!/usr/bin/env python3
#----------------------------------------------------------------------------
# Copyright (c) 2018 FIRST. All Rights Reserved.
# Open Source Software - may be modified and shared by FRC teams. The code
# must be accompanied by the FIRST BSD license file in the root directory of
# the project.
#----------------------------------------------------------------------------



import json
import time
import sys
import numpy as np
import cv2
from networktables import NetworkTables
from cscore import CameraServer, VideoSource, UsbCamera, MjpegServer

ip = '10.30.6.2'

NetworkTables.initialize(server=ip)

lower_green = np.array([0, 90, 90]) # 0, 90, 90
upper_green = np.array([86, 255, 255]) #

camWidth = 320
camHeight = 240
center_x = camWidth * .5
margin = 20

cs = CameraServer.getInstance()
cs.enableLogging()

cam1 = UsbCamera("cam1", 0)
cam2 = UsbCamera("cam2", 1)

cam1.setResolution(camWidth, camHeight)
cam2.setResolution(camWidth, camHeight)

cam1.setExposureManual(10)
cam2.setExposureManual(10)

cvSink = cs.getVideo(camera = cam1)

outputStream = cs.putVideo("Cam1", camWidth, camHeight)

frame = np.zeros(shape=(camHeight, camWidth, 3), dtype=np.uint8)

def listener(table, key, value, isNew):
	print("value changed: key: '%s'; value: %s; isNew: %s" % (key, value, isNew))
	return value
def connectionListener(connected, info):
	print(info, "; Connected=%s" % connected)

sd = NetworkTables.getTable("SmartDashboard")
NetworkTables.addConnectionListener(connectionListener, immediateNotify = True)
sd.addEntryListener(listener, key="cam")
sd.putString('dir', 'working')
print(sd.getString(key="cam", defaultValue = ""))

while(True):
	camMode = sd.getString(key="cam", defaultValue = "y")

	if(camMode == "y"):
		cvSink.setSource(cam2)
	else:
		cvSink.setSource(cam1)

	time, frame = cvSink.grabFrame(frame)
	
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
	mask = cv2.inRange(hsv, lower_green, upper_green)
	contours = cv2.findContours(mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)[-2] 
	
	largest_area = 0
	largest_contour = np.array([0, 0])
	sec_largest_area = 0
	sec_largest_contour = np.array([0, 0])
	
	for c in contours:
		area = cv2.contourArea(c)
		if area > largest_area:
			sec_largest_contour = largest_contour
			sec_largest_area = largest_area
			largest_contour = c
			largest_area = area
		elif area > sec_largest_area:
			sec_largest_contour = c
			sec_largest_area = area
		
	#print(largest_area)
	#print(sec_largest_area)

	if(largest_area > 0 and sec_largest_area > 0):
		M1 = cv2.moments(largest_contour)
		center_contour_x = int(M1['m10']/M1['m00'])
		
		M2 = cv2.moments(sec_largest_contour)
		center_contour_x_2 = int(M2['m10']/M2['m00'])
		
		center_average_x = .5 * (center_contour_x + center_contour_x_2)
		
		if abs(center_average_x - center_x) > margin:
			if center_average_x < center_x:
				sd.putString('dir', 'r')
				print('r')
			elif center_average_x > center_x:
				sd.putString('dir', 'l')
				print('l')
		else:
			sd.putString('dir', 'f')
			print('f')
		
		cv2.drawContours(frame, [largest_contour], 0, (0, 255, 0), 3)
		cv2.drawContours(frame, [sec_largest_contour], 0, (0, 255, 0), 3)

	outputStream.putFrame(frame)
	
NetworkTables.shutdown()
cap.release()
cv2.destroyAllWindows()