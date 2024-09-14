import os
import time
import threading
import cv2
import numpy as np
# from PostureModel.posture_main import posture_core
from FitnessApp.fitnessApp import init_fitness_app
from FitnessApp.fitnessApp import process_frame_fitness, reset_fitness_app
from dms.dms_manager import DMSManager

init_fitness_app()

'''
Configure dms managers below with correct flags based on system setup
Linux
--------
dms_cpu = DMSManager(run_on_hardware=True, use_npu=False)
dms_npu = DMSManager(run_on_hardware=True, use_npu=True)

MaaXBoard OSM93
--------
dms_cpu = DMSManager(run_on_hardware=True, use_npu=False)
dms_npu = DMSManager(run_on_hardware=True, use_npu=True)
'''

dms_cpu = DMSManager(run_on_hardware=False, use_npu=False)
dms_npu = DMSManager(run_on_hardware=False, use_npu=True)

class cameraSupport():
	''' Class for managing camera functionality and callbacks with frame data.

	Args:
		run_on_hardware (bool): runs on SBC hardware or linux desktop environment.
			Defaults to False.
		
		callback (callable): A function to be called when a new frame is captured.
			Defaults to None.

	Attributes:
		runningDemo (int): Flag to set which demo to run, DMS or fitness application.
		callback (callable): Callback function when new frame captured.
		onHardware (bool): Indicating whether to run on SBC or linux desktop env.
		CameraOpen (bool): Indicates whether camera is open or not.
		running (bool): Indicates whether frames are being capture or not. 
			Set as True when initialized.
		frame (object): Last captured frame from openCV.
		FrameGetterThread (threading.Thread): Thread for capturing frame data from camera.
		EnableNPU (bool): Indicates whether or not to run DMS demo with models 
			dispatched to CPU or NPU. 
	'''

	def __init__(self, run_on_hardware = False, callback = None):
		self.runningDemo = 0
		self.callback = callback
		self.onHardware = run_on_hardware
		self.cameraOpen = False
		self.running = True
		self.frame = None
		self.FrameGetterThread = threading.Thread(target=self.FrameGetter)
		self.FrameGetterThread.start()
		self.enableNPU = False

	def ResetFitnessApp(self):
		reset_fitness_app()

	def SwitchDemo(self, demo):
		self.runningDemo = demo

	def ToggleDMSAcceleration(self):
		if self.enableNPU == False:
			self.enableNPU = True
		else:
			self.enableNPU = False

	def close(self):
		self.running = False
		self.CloseCVDevice(self)

	def OpenCVDevice(self):
		try:
			if(self.cap.isOpened() == True):
				self.CloseCVDevice(self)
		except:
			pass
		
		try:
			if self.onHardware == True:
				os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'hwaccel;qsv|video_codec;h264_qsv|vsync;0'

			self.cap = cv2.VideoCapture(cv2.CAP_V4L2)
			self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
			self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
			self.cap.set(cv2.CAP_PROP_FPS, 30)

			# camera exposure - auto=3, manual=1
			self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)

			self.cameraOpen = True
		except:
			self.cameraOpen = False

	def CloseCVDevice(self):
		try:
			self.cameraOpen = False
			self.cap.release()
		except:
			pass
	def CameraOpen(self):
		return self.cameraOpen

	def GetFrame(self):
		return self.frame

	def FrameGetter(self):
		while self.running:
			if(self.cameraOpen == False):
				self.OpenCVDevice()
				time.sleep(1)
				continue

			else:
				try:
					ret, image = self.cap.read()

					if ret and np.any(image):
						dim = (320, 240)
						image = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)

						if self.runningDemo == 1:
							#DMS demo app
							if self.enableNPU == False:
								newFrame, attention_status, yawning_status, eye_status, inference_speed, penalty_score = dms_cpu.process_frame_dms(image)
								self.frame = newFrame
								self.callback(self.frame, 1, attention_status, yawning_status, eye_status, inference_speed, penalty_score)

							else:	
								newFrame, attention_status, yawning_status, eye_status, inference_speed, penalty_score = dms_npu.process_frame_dms(image)
								self.frame = newFrame
								self.callback(self.frame, 1, attention_status, yawning_status, eye_status, inference_speed, penalty_score)

						elif self.runningDemo == 0:
							#Fitness app demo
							newFrame, rom, _, repCount, name, status = process_frame_fitness(image)
							self.frame = newFrame
							self.callback(self.frame, 0, rom, repCount, name, status, 0)

						else:
							# CAN demo selected, ignore input stream
							pass
				except:
					pass


 


	
	



