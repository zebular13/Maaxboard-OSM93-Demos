'''
webui.py is the Main applictaion script. Options for running the script on MaaXBoard OSM93 or Linux are provided below. 
'''

run_on_hardware = False

if run_on_hardware == False:
	HardwareSupport = False
	RotateCameraY = False
	RotateCameraX = False
	EnableUSBPowerMonitor = False
else:
	HardwareSupport = True
	RotateCameraY = False
	RotateCameraX = True
	EnableUSBPowerMonitor = True

import os
import sys
import json
import cv2
from netinfo import NETInfo
from camera import cameraSupport
from localWindow import localWindow
from tendo import singleton
from CanTools.car_status import CarStatus
from CanTools.can_main import CanDemoManager

try:
	import uasyncio as asyncio
except ImportError:
	import asyncio

from microdot import Microdot, redirect, send_file

from random import seed
from random import randint

# will sys.exit(-1) if other instance is running
me = singleton.SingleInstance()


seed(1)

serialPortBusy = False
ledStates = [0, 0, 0]	

globalFrame = None
globalCurrentDemo = 0

# Setup Car simulator & can tools
can_app_manager = CanDemoManager(selectedDemo=globalCurrentDemo)

fileDir = os.path.dirname(os.path.realpath(__file__))

def GetFileFullPath(s):
	filePath = os.path.join(fileDir, s)
	filePath = os.path.abspath(os.path.realpath(filePath))
	return filePath

def frameCallback(frame, demoNumber, ret1, ret2, ret3, ret4, ret5):
	global globalFrame
	global globalCurrentDemo

	globalFrame = frame
	window.updateFrame(frame)

	# print("global currnet demo:",globalCurrentDemo)

	if (globalCurrentDemo == 0) and (demoNumber == 0):
		window.UpdateFitnessUI(ret1, ret2, ret3, ret4)
	elif globalCurrentDemo == 1 and (demoNumber == 1):
		window.UpdateDMSUI(ret1, ret2, ret3, ret4, ret5)
	else:
		# CAN demo selected, ignore frame callback
		pass
		
def screenClickCallback(event):
	global globalCurrentDemo

	if event == "event_reset":
		camera.ResetFitnessApp()
		globalCurrentDemo = 0

	elif event == "page0":
		globalCurrentDemo = 0
		window.UpdateActiveDemo(globalCurrentDemo)

	elif event == "page1":
		globalCurrentDemo = 1
		window.UpdateActiveDemo(globalCurrentDemo)

	elif event == "page2":
		globalCurrentDemo = 2
		window.UpdateActiveDemo(globalCurrentDemo)

	elif event == "toggle_DMS_Acceleration":
		camera.ToggleDMSAcceleration()
		window.ToggleNPUAccelerationLabel()

	elif event == "car_accelerate":
		window.UpdateCANUI()
		can_app_manager.update_car_state(carState=CarStatus.ACCELERATE)
		
	elif event == "car_brake":
		window.UpdateCANUI()
		can_app_manager.update_car_state(carState=CarStatus.BRAKE)

	elif event == "car_idle":
		window.UpdateCANUI()
		can_app_manager.update_car_state(carState=CarStatus.IDLE)

	camera.SwitchDemo(globalCurrentDemo)


'''
----------------------------------------------------
Web Server 
----------------------------------------------------
'''
app = Microdot()

@app.route('/video_feed')
async def video_feed(request):
	global usingClip
	global globalFrame
	if sys.implementation.name != 'micropython':
		# CPython supports yielding async generators
		async def stream():
			yield b'--frame\r\n'
			while True:
				if camera.CameraOpen():
					frame = globalFrame
					if(frame is not None):
						_, frame = cv2.imencode('.JPEG', frame)
						yield (b'--frame\r\n'
							b'Content-Type: image/jpeg\r\n\r\n' + frame.tobytes() + b'\r\n')

				await asyncio.sleep(0.01)

	else:
		# MicroPython can only use class-based async generators
		class stream():
			def __init__(self):
				self.i = 0

			def __aiter__(self):
				return self

			async def __anext__(self):
				await asyncio.sleep(1)

	return stream(), 200, {'Content-Type':
						   'multipart/x-mixed-replace; boundary=frame'}


@app.route('/ethernet.cgi', methods=['GET'])
async def ethernet(request):
	response = None
	if request.method == 'GET':
		cmdType = 'ethernet'
		info = NETInfo.GetNetworkInfo()
		data_set = {"cmdType": cmdType, "ethernetInfo": [info]}

		sys_cookie = json.dumps(data_set)
		response = sys_cookie
	return response

@app.route('/uses/rundemo.cgi', methods=['GET', 'POST'])
def demoCgi(request):
	if request.method == 'POST':
		resp = json.loads(request.body)
		if ("cmdType" in resp):
			data_set = {"cmdType": 'rundemo'}

		demo_cookie = json.dumps(data_set)
		response = demo_cookie
	return response

@app.route('/uses/<name>', methods=['GET', 'POST'])
def index(request,name):
	if request.method == 'POST':
		response = redirect('/')
	else:
		response = send_file(GetFileFullPath('web/uses/'+name))

	return response

@app.route('/<name>', methods=['GET', 'POST'])
def index(request,name):
	if request.method == 'POST':
		response = redirect('/')
	else:
		response = send_file(GetFileFullPath('web/'+name))

	return response

@app.route('/', methods=['GET', 'POST'])
def index(request):
	if request.method == 'POST':
		response = redirect('/')
	else:
		response = send_file(GetFileFullPath('web/index.html'))

	return response

camera = cameraSupport(HardwareSupport, frameCallback)

window = localWindow(screenClickCallback)

app.run(debug=True)

camera.close()