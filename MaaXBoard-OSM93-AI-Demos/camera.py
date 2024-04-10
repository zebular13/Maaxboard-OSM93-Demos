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

# configure dms managers below with correct flags based on system setup
# Linux
# 	both dms clients -run_on_hardware = False, use_npu = False
# MaaXBoard OSM93
# 	dms cpu client -run_on_hardware = True, use_npu = False
# 	dms npu client -run_on_hardware = True, use_npu = False

dms_cpu = DMSManager(run_on_hardware=False, use_npu=False)
dms_npu = DMSManager(run_on_hardware=False, use_npu=False)

class cameraSupport():
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
		# self.PostureDemo = posture_core(None, False)

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
		# self.PostureDemo.Close(self)
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
						#dim = (192, 144)
						image = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)

						if self.runningDemo == 1:
							#DMS demo app
							if self.enableNPU == False:
								newFrame, attention_status, yawning_status, eye_status, inference_speed = dms_cpu.process_frame_dms(image)
								self.frame = newFrame
								self.callback(self.frame, 1, attention_status, yawning_status, eye_status, inference_speed)

							else:
								newFrame, attention_status, yawning_status, eye_status, inference_speed = dms_npu.process_frame_dms(image)
								self.frame = newFrame
								self.callback(self.frame, 1, attention_status, yawning_status, eye_status, inference_speed)

						else:
							#Fitness app demo
							newFrame, rom, _, repCount, name, status = process_frame_fitness(image)
							self.frame = newFrame
							self.callback(self.frame, 0, rom, repCount, name, status)
				except:
					pass

			#time.sleep(0.1)

 


	
	



