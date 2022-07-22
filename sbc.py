from ls7366 import LS7366
from ad5293 import AD5293
from max522 import MAX522
from max1270 import MAX1270
from mot import L298N_pwm, L298N_dig
import board
import busio
from digitalio import DigitalInOut, Direction
import pwmio


import board
import displayio
import terminalio
from adafruit_display_text import bitmap_label, label
from adafruit_displayio_sh1107 import SH1107
from adafruit_displayio_sh1107 import DISPLAY_OFFSET_ADAFRUIT_128x128_OLED_5297 as SH1107_OFFSET




class SBC():
	def __init__(self,i2c=0,spi=0):

		self.deinit_repository_drivers = []
		self.deinit_repository_buses = []
		self.deinit_repository_pins = []

		self._init_i2c(i2c)
		self._init_spi(spi)

		self._init_encoder1()	# LS7366 #1
		self._init_encoder2()	# LS7366 #2
		self._init_digipot()	# AD5293
		self._init_dac()		# MAX522
		self._init_adc()		# MAX1270
		# self._init_display()	# SH1107 OLED, 128x128, Monochrome


	def _init_i2c(self,i2c_in):
		displayio.release_displays()
		if (str(type(i2c_in)) == "<class 'I2C'>"):
			self._i2c = i2c_in
			print("External I2C detected.")
		else:
			print()
			print("External I2C not detected.")
			self._start_internal_i2c()


	def _start_internal_i2c(self):
		print("SBC Class initializing I2C.")
		self._sda = board.GP16
		self._scl = board.GP17
		self._i2c = busio.I2C(scl=self._scl,sda=self._sda)

		self.deinit_repository_pins.extend([self._sda,self._scl])
		self.deinit_repository_buses.append(self._i2c)
		print("I2C bus setup complete.")


	def _init_spi(self,spi_in):
		if (str(type(spi_in)) == "<class 'SPI'>"):
			self._spi = spi_in
			print("External SPI detected.")
		else:
			print()
			print("External SPI not detected.")
			self._start_internal_spi()

		print("SBC Class obtaining lock of SPI", end=".")
		while not self._spi.try_lock():
			print("",end=".")
		self._spi.configure(phase=0,polarity=0,baudrate=1000000)
		print("\r\nSPI configured.")

	def _start_internal_spi(self):
		print("SBC Class initializing SPI.")
		self._sclk = board.GP2
		self._mosi = board.GP3
		self._miso = board.GP4
		self._spi = busio.SPI(self._sclk,MOSI=self._mosi,MISO=self._miso)

		self.deinit_repository_pins.extend([self._sclk,self._mosi,self._miso])
		self.deinit_repository_buses.append(self._spi)
		print("SPI bus setup complete.")

	def	_init_encoder1(self):	# LS7366 #1
		self._cs1 = DigitalInOut(board.GP19)
		self._cs1.direction = Direction.OUTPUT
		self._cs1.value = 1
		self._enc_device1 = LS7366(self._spi,self._cs1)
		self.deinit_repository_drivers.append(self._enc_device1)
		self.deinit_repository_pins.append(self._cs1)

	def _init_encoder2(self):	# LS7366 #2
		self._cs2 = DigitalInOut(board.GP18)
		self._cs2.direction = Direction.OUTPUT
		self._cs2.value = 1
		self._enc_device2 = LS7366(self._spi,self._cs2)
		self.deinit_repository_drivers.append(self._enc_device2)
		self.deinit_repository_pins.append(self._cs2)

	def	_init_digipot(self):	# AD5293
		self._cs3 = DigitalInOut(board.GP20)
		self._cs3.direction = Direction.OUTPUT
		self._cs3.value = 1
		self._digipot_device = AD5293(self._spi,self._cs3)
		self.deinit_repository_drivers.append(self._digipot_device)
		self.deinit_repository_pins.append(self._cs3)

	def _init_dac(self):		# MAX522
		self._cs4 = DigitalInOut(board.GP21)
		self._cs4.direction = Direction.OUTPUT
		self._cs4.value = 1
		self._dac_device = MAX522(self._spi,self._cs4)
		self.deinit_repository_drivers.append(self._dac_device)
		self.deinit_repository_pins.append(self._cs4)

	def	_init_adc(self):		# MAX1270
		self._cs5 = DigitalInOut(board.GP22)
		self._cs5.direction = Direction.OUTPUT
		self._cs5.value = 1
		self._adc_device = MAX1270(self._spi,self._cs5)
		self.deinit_repository_drivers.append(self._adc_device)
		self.deinit_repository_pins.append(self._cs5)

	def _init_mot1_pwm(self):
		print('Initiating motor 1 pwm.')
		self._mot1_in1 = pwmio.PWMOut(pin=board.GP15,frequency=440)
		self._mot1_in1.duty_cycle = 0
		self._mot1_in2 = pwmio.PWMOut(pin=board.GP14,frequency=440)
		self._mot1_in2.duty_cycle = 0
		self._mot1_en = DigitalInOut(board.GP13)
		self._mot1_en.direction = Direction.OUTPUT
		self._mot1_en.value = 0

		self._mot1 = L298N_pwm(self._mot1_in1, self._mot1_in2, self._mot1_en)

		self.deinit_repository_drivers.append(self._mot1)
		self.deinit_repository_pins.extend([self._mot1_in1, self._mot1_in2, self._mot1_en])

	def _init_mot2_pwm(self):
		print('Initiating motor 2 pwm.')
		self._mot2_in1 = pwmio.PWMOut(pin=board.GP12,frequency=440)
		self._mot2_in1.duty_cycle = 0
		self._mot2_in2 = pwmio.PWMOut(pin=board.GP11,frequency=440)
		self._mot2_in2.duty_cycle = 0
		self._mot2_en = DigitalInOut(board.GP10)
		self._mot2_en.direction = Direction.OUTPUT
		self._mot2_en.value = 0

		self._mot2 = L298N_pwm(self._mot2_in1, self._mot2_in2, self._mot2_en)

		self.deinit_repository_drivers.append(self._mot2)
		self.deinit_repository_pins.extend([self._mot2_in1, self._mot2_in2, self._mot2_en])

	def _init_mot1_dig(self):
		print('Initiating motor 1 digital.')
		self._mot1_in1 = DigitalInOut(board.GP15)
		self._mot1_in1.direction = Direction.OUTPUT
		self._mot1_in1.value = 0
		self._mot1_in2 = DigitalInOut(board.GP14)
		self._mot1_in2.direction = Direction.OUTPUT
		self._mot1_in2.value = 0
		self._mot1_en = pwmio.PWMOut(pin=board.GP13,frequency=440)
		self._mot1_en.duty_cycle = 0

		self._mot1 = L298N_dig(self._mot1_in1, self._mot1_in2, self._mot1_en)

		self.deinit_repository_drivers.append(self._mot1)
		self.deinit_repository_pins.extend([self._mot1_in1, self._mot1_in2, self._mot1_en])

	def _init_mot2_dig(self):
		print('Initiating motor 2 digital.')
		self._mot2_in1 = DigitalInOut(board.GP12)
		self._mot2_in1.direction = Direction.OUTPUT
		self._mot2_in1.value = 0
		self._mot2_in2 = DigitalInOut(board.GP11)
		self._mot2_in2.direction = Direction.OUTPUT
		self._mot2_in2.value = 0
		self._mot2_en = pwmio.PWMOut(pin=board.GP10,frequency=440)
		self._mot2_en.duty_cycle = 0

		self._mot2 = L298N_dig(self._mot2_in1, self._mot2_in2, self._mot2_en)

		self.deinit_repository_drivers.append(self._mot2)
		self.deinit_repository_pins.extend([self._mot2_in1, self._mot2_in2, self._mot2_en])

	def _init_display(self):
		displayio.release_displays()
		display_bus = displayio.I2CDisplay(self._i2c, device_address=0x3D)
		WIDTH = 128
		HEIGHT = 128
		ROTATION = 90
		# BORDER = 2
		self._display = SH1107(
			display_bus,
			width=WIDTH,
			height=HEIGHT,
			display_offset=SH1107_OFFSET,
			rotation=ROTATION,
		)

		# splash = displayio.Group()
		# self._display.show(splash)
		# self.oled_text('startup')

	# def oled_text(self,text_in=("Hellow"+__name__)):
	# 	text_area = label.Label(terminalio.FONT,text=text_in)
	# 	text_area.x = 10
	# 	text_area.y = 10
	# 	self._display.show(text_area)

	def clear_display(self):
		displayio.release_displays()

	def initiate_motor(self,n,type='dig'):
		func_name = '_init_mot'+str(n)+'_'+str(type)
		func = getattr(self,func_name)
		func()

	def read_adc(self,ch=0):
		return self._adc_device.read_volts(ch)

	def deinit(self):
		# Deinit order matters. Drivers, then Buses, then Pins.
		self.deinit_repository_drivers.extend(self.deinit_repository_buses)
		self.deinit_repository_drivers.extend(self.deinit_repository_pins)
		displayio.release_displays()
		for obj in self.deinit_repository_drivers:
			try:
				obj_type = type(obj)
				obj.deinit()
				print('deinitialized %s of type %s.' %(obj,obj_type))
			except:
				pass





