import can
import queue
from random import randrange
from CanTools.car_attributes_handler import CarAttributesHandler


class CanBusManager():
    """
    Class to manage CAN bus communication. Create a bus, send, and receive messages. 
    """
    def __init__(self, can_channel, can_interface, can_baud):
        self.serial_manager = None
        self.can_channel = can_channel
        self.can_interface = can_interface
        self.can_baud = can_baud
        self.message_queue = queue.Queue()
        self.tx_arb_id = 0x7E8 # ECU arbitration ID
        self.rx_arb_id = 0x7DF # OBDII scanner arbitration ID
        self.bus = can.interface.Bus(channel=self.can_channel, bustype=self.can_interface, bitrate=self.can_baud)
        self.notifier = self.notifier = can.Notifier(self.bus, [self.enqueue_message]) # start the notifier immediately after creating the bus
        self.car_speed = 0
        self.car_rpm = 1400
        self.car_throttle_pos = 0

    def set_serial_manager(self, serial_manager):
        self.serial_manager = serial_manager

    def enqueue_message(self, msg):
        if msg.arbitration_id == self.rx_arb_id:
            # Initial Pairing Message 0201
            if msg.data == bytearray(b'\x02\x01\x00\x00\x00\x00\x00\x00'):
                # print("Received 0100 PID support request.")
                PID_0100_response_1 = bytearray(b'\x06\x41\x00\x98\x3A\x80\x13')
                PID_0100_response_2 = bytearray(b'\x06\x41\x00\xBE\x3F\xA8\x13')
                message1 = can.Message(arbitration_id=self.tx_arb_id, data=PID_0100_response_1, is_extended_id=False)
                message2 = can.Message(arbitration_id=self.tx_arb_id, data=PID_0100_response_2, is_extended_id=False)
                self.bus.send(message1, 1)
                self.bus.send(message2, 1)

            # RPM (02 01 0C)
            elif msg.data == bytearray(b'\x02\x01\x0C\x00\x00\x00\x00\x00'):
                rpm_data = self.update_rpm_in_bytearray(self.car_rpm)
                try:
                    self.bus.send(can.Message(arbitration_id=self.tx_arb_id, data=rpm_data, is_extended_id=False), 1)
                except:
                    print("Error sending RPM")
                pass

            # SPEED (02 01 0D)
            elif msg.data == bytearray(b'\x02\x01\x0D\x00\x00\x00\x00\x00'):
                speed_data = self.update_speed_in_bytearray(self.car_speed)
                try:
                    self.bus.send(can.Message(arbitration_id=self.tx_arb_id, data=speed_data, is_extended_id=False), 1)
                
                except:
                    print("Error sending SPEED")
                pass

            # THROTTLE POS (02 01 11)
            elif msg.data == bytearray(b'\x02\x01\x11\x00\x00\x00\x00\x00'):
                throttle_pos = self.update_throttle_position_bytearray(self.car_throttle_pos)
                try:
                    self.bus.send(can.Message(arbitration_id=self.tx_arb_id, data=throttle_pos, is_extended_id=False), 1)
                
                except:
                    print("Error sending SPEED")
                pass
            # INTAKE AIR TEMP (02 01 0F)
            elif msg.data == bytearray(b'\x02\x01\x0F\x00\x00\x00\x00\x00'):

                intake_air_temp_data = self.generate_air_intake_temp_value_bytearray()
                try:
                    self.bus.send(can.Message(arbitration_id=self.tx_arb_id, data=intake_air_temp_data, is_extended_id=False), 1)
                
                except:
                    print("Error sending INTAKE AIR TEMP")
                pass

            # COOLANT (02 01 05)
            elif msg.data == bytearray(b'\x02\x01\x05\x00\x00\x00\x00\x00'):

                coolant_data = self.generate_coolant_temp_value_bytearray()
                try:
                    self.bus.send(can.Message(arbitration_id=self.tx_arb_id, data=coolant_data, is_extended_id=False), 1)
                
                except:
                    print("Error sending COOLANT")
                pass

            # ENGINE LOAD % (02 01 04)
            elif msg.data == bytearray(b'\x02\x01\x04\x00\x00\x00\x00\x00'):

                engine_load_data = self.generate_engine_load_percent_value_bytearray()
                try:
                    self.bus.send(can.Message(arbitration_id=self.tx_arb_id, data=engine_load_data, is_extended_id=False), 1)
                
                except:
                    print("Error sending ENGINE LOAD")
                pass

            # # TIMING ADVANCE (02 01 0E) - This sensor not shown on CarScanner app?
            # elif msg.data == bytearray(b'\x02\x01\x0E\x00\x00\x00\x00\x00'):

            #     timing_advance_data = self.generate_timing_advance_value_bytearray()
            #     try:
            #         self.bus.send(can.Message(arbitration_id=self.tx_arb_id, data=timing_advance_data, is_extended_id=False), 1)
                
            #     except:
            #         print("Error sending TIMING")
            #     pass

            # INTAKE AIR PRESSURE (02 01 0B) 
            elif msg.data == bytearray(b'\x02\x01\x0B\x00\x00\x00\x00\x00'):

                intake_air_pressure = self.generate_intake_manifold_pressure_bytearray()
                try:
                    self.bus.send(can.Message(arbitration_id=self.tx_arb_id, data=intake_air_pressure, is_extended_id=False), 1)
                
                except:
                    print("Error sending INTAKE AIR PRESSURE")
                pass

            # # ENGINE OIL TEMP (02 01 5C) 
            # elif msg.data == bytearray(b'\x02\x01\x5C\x00\x00\x00\x00\x00'):

            #     engine_oil_temp = self.generate_engine_oil_temp_bytearray()
            #     try:
            #         self.bus.send(can.Message(arbitration_id=self.tx_arb_id, data=engine_oil_temp, is_extended_id=False), 1)
                
            #     except:
            #         print("Error sending ENGINE OIL TEMP")
            #     pass

            else:
                # handle all other requests here
                pass

    def stop_can_notifier(self):
        print("stopping notifier")
        if self.notifier:
            self.notifier.stop(timeout=2)

    def start_can_notifier(self):
        print("starting notifier")
        self.notifier = can.Notifier(self.bus, [self.enqueue_message], timeout=1)

    def update_car_speed_rpm(self, speed, rpm, throttle):
        self.car_speed = speed
        self.car_rpm = rpm
        self.car_throttle_pos = throttle

    def update_speed_in_bytearray(self, speed):
        # print("speed response update: ", speed)
        speed = int(speed * 1.61) # not completely accurate for mph, but close enough
        speed_response = bytearray(b'\x04\x41\x0D\x00\x00\x00\x00\x00')
        speed_response[3] = speed
        return speed_response
    
    def update_rpm_in_bytearray(self, rpm):
        # print("speed response update: ", rpm)
        rpm_bytes = self.format_rpm_for_bytearray(rpm)
        rpm_response = bytearray(b'\x04\x41\x0C\x00\x00\x00\x00\x00')
        rpm_response[3] = rpm_bytes[0]
        rpm_response[4] = rpm_bytes[1]
        return rpm_response

    def update_throttle_position_bytearray(self, throttle):
        A = int((throttle / 100) * 255) 
        throttle_position_response = bytearray(b'\x04\x41\x11\x00\x00\x00\x00\x00')
        throttle_position_response[3] = A  
        return throttle_position_response

    def format_rpm_for_bytearray(self, rpm):
        """
        Calculation for RPM from OBD standard:
        https://en.wikipedia.org/wiki/OBD-II_PIDs - Reference Command "010C" for RPM formula

        RPM: returns 2 bytes of data A[7...0], B[7...0]
        Min Value: 0
        Max Value: 16,383.75 

        Formula: RPM = (256 * A + B) / (4)

        Function inputs:
        rpm: The RPM value returned by the system (non byte formatted)

        Returns:
        bytearray([A,B])
        """
        rpm_value = rpm * 4 
        A = rpm_value // 256
        B = rpm_value % 256
        A = int(A)
        B = int(B)
        return bytearray([A, B])
    
    def generate_air_intake_temp_value_bytearray(self):
        intake_air_temp_value = randrange(-40, 121) 
        A = intake_air_temp_value + 40
        intake_air_temp_response = bytearray(b'\x04\x41\x0F\x00\x00\x00\x00\x00')
        intake_air_temp_response[3] = A     
        return intake_air_temp_response

    def generate_coolant_temp_value_bytearray(self):
        coolant_temp_value = randrange(-40, 126)
        A = coolant_temp_value + 40
        coolant_response = bytearray(b'\x04\x41\x05\x00\x00\x00\x00\x00')
        coolant_response[3] = A
        return coolant_response
    
    def generate_engine_load_percent_value_bytearray(self):
        engine_load_percent = randrange(0, 101)
        A = int((engine_load_percent/100) * 255 )
        engine_load_response = bytearray(b'\x04\x41\x04\x00\x00\x00\x00\x00')
        engine_load_response[3] = A
        return engine_load_response
    
    # def generate_timing_advance_value_bytearray(self):
    #     timing_advance_degrees = randrange(-25, 26) 
    #     A = (timing_advance_degrees * 2) 
    #     timing_advance_response = bytearray(b'\x04\x41\x0E\x00\x00\x00\x00\x00')
    #     timing_advance_response[3] = A  
    #     return timing_advance_response

    def generate_intake_manifold_pressure_bytearray(self):
        pressure_value = randrange(20, 100) 
        pressure_response = bytearray(b'\x04\x41\x0B\x00\x00\x00\x00\x00')
        pressure_response[3] = pressure_value  
        return pressure_response
    
    # def generate_engine_oil_temp_bytearray(self):
    #     temp_celsius = randrange(-40, 150)
    #     A = temp_celsius + 40  
    #     oil_temp_response = bytearray(b'\x04\x41\x5C\x00\x00\x00\x00\x00')
    #     oil_temp_response[3] = A 
    #     return oil_temp_response



