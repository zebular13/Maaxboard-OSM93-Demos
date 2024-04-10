import os
import gi
import cairo
import threading
import cv2
from math import pi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

scriptFolder = os.path.dirname(__file__)
layoutPath = "resources/mainApp.glade"
globalFrame = None
cameraOpen = False

GladeBuilder = Gtk.Builder()

class localWindow():
	def __init__(self, callback = None):
		self.eventHandler = self.Handler(self)
		self.running = True
		self.frame = None

		self.rom = None
		self.repCount = None
		self.name = None
		self.status = None

		self.attention_status = None
		self.yawning_status = None
		self.eye_status = None
		self.inference_speed = None

		self.enableNPU = False

		self.clickCallback = callback
		self.loaclAppThread = threading.Thread(target=self.localApp)
		self.loaclAppThread.start()

	def updateFrame(self,frame):
		global globalFrame
		global cameraOpen

		globalFrame = frame
		cameraOpen = True


	def ToggleNPUAccelerationLabel(self):
		if self.enableNPU == False:
			self.enableNPU = True
		else:
			self.enableNPU = False


	def UpdateFitnessUI(self, rom, repCount, name, status):
		GLib.idle_add(self.update_FitnessUI_elements, rom, repCount, name, status)

	def UpdateDMSUI(self, attention_status, yawning_status, eye_status, inference_speed):
		GLib.idle_add(self.update_DMSUI_elements, attention_status, yawning_status, eye_status, inference_speed)


	def ReportClick(self, event):
		self.clickCallback(event)

	def update_FitnessUI_elements(self, rom, repCount, name, status):
		label1 = GladeBuilder.get_object("Demo1_label1")
		label2 = GladeBuilder.get_object("Demo1_label2")
		label3 = GladeBuilder.get_object("Demo1_label3")
		progress = GladeBuilder.get_object("progress_bar")

		if (self.name != name):
			
			label1.set_label("Exercise: " + str(name))
			self.name = name

		if (self.repCount != repCount):
			
			label2.set_label("Repititions: " +str(repCount))
			self.repCount = repCount

		if (self.status != status):
			
			if str(status) == "Good Landmark Detection":
				label3_text = '<span foreground="#00ff00" size="xx-large">Status: {}</span>'.format(str(status))
				label3.set_markup(label3_text)
			else:
				label3_text = '<span foreground="#ff0000" size="xx-large">Status: {}</span>'.format(str(status))
				label3.set_markup(label3_text)
			self.status = status

		if (self.rom != rom):
			progress.set_fraction(rom / 100)
			self.rom = rom

	def update_DMSUI_elements(self, attention_status, yawning_status, eye_status, inference_speed):
		label1 = GladeBuilder.get_object("Demo2_label1")
		label2 = GladeBuilder.get_object("Demo2_label2")
		label3 = GladeBuilder.get_object("Demo2_label3")
		label4 = GladeBuilder.get_object("inference_speed_label")
		label5 = GladeBuilder.get_object("npu_enable_label")

		if (self.attention_status != attention_status):
			if attention_status != "Forward":
				#label1_text = '<span foreground="#ff0000" size="xx-large">Attention: {}</span>'.format(str(attention_status))
				label1_text = '<span weight="bold" foreground="#ff0000" size="xx-large">{}</span>'.format(str(attention_status))
				label1.set_markup(label1_text)
			else:
				#label1_text = '<span foreground="#00ff00" size="xx-large">Attention: {}</span>'.format(str("Forward"))
				label1_text = '<span weight="bold" foreground="#00ff00" size="xx-large">{}</span>'.format(str("Forward"))
				label1.set_markup(label1_text)
			self.attention_status = attention_status

		if (self.yawning_status != yawning_status):
			
			if yawning_status == True:
				#label2_text = '<span foreground="#ff0000" size="xx-large">Yawning: {}</span>'.format(str("YES"))
				label2_text = '<span weight="bold" foreground="#ff0000" size="xx-large">{}</span>'.format(str("Yes"))
				label2.set_markup(label2_text)
			else:
				#label2_text = '<span foreground="#00ff00" size="xx-large">Yawning: {}</span>'.format(str("No"))
				label2_text = '<span weight="bold" foreground="#00ff00" size="xx-large">{}</span>'.format(str("No"))
				label2.set_markup(label2_text)
			self.yawning_status = yawning_status

		if (self.eye_status != eye_status):
			if eye_status == True:
				#label3_text = '<span foreground="#ff0000" size="xx-large">Eyes: {}</span>'.format(str("CLOSED"))
				label3_text = '<span weight="bold" foreground="#ff0000" size="xx-large">{}</span>'.format(str("Closed"))
				label3.set_markup(label3_text)
			else:
				#label3_text = '<span foreground="#00ff00" size="xx-large">Eyes: {}</span>'.format(str("Open"))
				label3_text = '<span weight="bold" foreground="#00ff00" size="xx-large">{}</span>'.format(str("Open"))
				label3.set_markup(label3_text)
			self.eye_status = eye_status

		if (self.inference_speed != inference_speed):
			#label4_text = '<span size="large">Inference Speed: </span><span weight="bold" size="xx-large">{}</span>'.format(str(inference_speed + " ms"))
			label4_text = '<span weight="bold" size="xx-large">{}</span>'.format(str(inference_speed + " ms"))
			label4.set_markup(label4_text)
			self.inference_speed = inference_speed

		if self.enableNPU == False:
			#label5_text = '<span size="large">Inference: </span><span weight="bold" size="xx-large">{}</span>'.format(str("CPU"))
			label5_text = '<span weight="bold" size="xx-large">{}</span>'.format(str("CPU"))
			label5.set_markup(label5_text)
		else:
			#label5_text = '<span size="large">Inference: </span><span weight="bold" size="xx-large">{}</span>'.format(str("NPU"))
			label5_text = '<span weight="bold" size="xx-large">{}</span>'.format(str("NPU"))
			label5.set_markup(label5_text)


	def localApp(self):
		global GladeBuilder

		GladeBuilder.add_from_file(os.path.join(scriptFolder, layoutPath))
		GladeBuilder.connect_signals(self.eventHandler)

		screen = Gdk.Screen.get_default()
		provider = Gtk.CssProvider()
		provider.load_from_path(os.path.join(scriptFolder, "resources/app.css"))
		Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

		MainWindow = GladeBuilder.get_object("mainWindow")

		MainWindow.fullscreen()
		MainWindow.show_all()

		Gtk.main()

	class Handler:
		def __init__(self, outer_instance):
			self.outer_instance = outer_instance
					
		def on_mainWindow_destroy(self, *args):
			Gtk.main_quit(*args)

		def CapImage_event(self, widget, context):
			global globalFrame
			global cameraOpen

			if cameraOpen:
				frame = globalFrame[:, ::-1, :]
				frame = cv2.cvtColor(frame[:,:,::-1], cv2.COLOR_BGR2RGBA).astype('uint8')
				H, W, C = frame.shape
				surface = cairo.ImageSurface.create_for_data(frame, cairo.FORMAT_ARGB32, W, H)
				CWidth = widget.get_allocation().width
				CHeight = widget.get_allocation().height

				frameScale = CHeight/H
				context.scale(frameScale, frameScale)
				
				if frameScale > 1:
					context.set_source_surface(surface, 0, 0)
				else:
					context.set_source_surface(surface, (W-CWidth)/2, 0)
				context.rotate (pi/2)
				context.paint()
			widget.queue_draw()

		def reset_button_clicked_cb(self, widget):
			self.outer_instance.clickCallback("event_reset")

		def on_demo_select_switch_page(self, notebook, page, page_number):
			self.outer_instance.clickCallback("page"+str(page_number))

		def toggle_DMS_acceleration(self, widget):
			self.outer_instance.clickCallback("toggle_DMS_Acceleration")