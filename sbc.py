from ls7366 import LS7366
from ad5293 import AD5293
from max522 import MAX522
from max1270 import MAX1270
import board
import busio
from digitalio import DigitalInOut, Direction


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

		# Deinit order matters. Drivers, then Buses, then Pins.
		self.deinit_repository_drivers.extend(self.deinit_repository_buses)
		self.deinit_repository_drivers.extend(self.deinit_repository_pins)


	def _init_i2c(self,i2c_in):
		if (str(type(i2c_in)) == "<class 'I2C'>"):
			self._i2c = i2c_in
		else:
			print()
			print('I2C not detected.')
			self._start_internal_i2c()


	def _start_internal_i2c(self):
		print('SBC Class initializing internal I2C', end=".")
		self._sda = board.GP16
		self._scl = board.GP17
		self._i2c = busio.I2C(scl=self._scl,sda=self._sda)

		self.deinit_repository_pins.extend([self._sda,self._scl])
		self.deinit_repository_buses.append(self._i2c)
		print("\r\n I2C bus setup complete.")


	def _init_spi(self,spi_in):
		if (str(type(spi_in)) == "<class 'SPI'>"):
			self._spi = spi_in
		else:
			print()
			print('SPI not detected.')
			self._start_internal_spi()

		print()
		print('SBC Class obtaining lock of SPI',end='.')
		while not self._spi.try_lock():
			print('',end='.')
		self._spi.configure(phase=0,polarity=0,baudrate=1000000)
		print('\r\nSPI configured.')

	def _start_internal_spi(self):
		print('SBC Class initializing internal SPI')
		self._sclk = board.GP2
		self._mosi = board.GP3
		self._miso = board.GP4
		self._spi = busio.SPI(self._sclk,MOSI=self._mosi,MISO=self._miso)

		self.deinit_repository_pins.extend([self._sclk,self._mosi,self._miso])
		self.deinit_repository_buses.append(self._spi)
		print("\r\n SPI bus setup complete.")

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


	def deinit(self):
		for obj in self.deinit_repository_drivers:
			try:
				obj_type = type(obj)
				obj.deinit()
				print('deinitialized %s of type %s.' %(obj,obj_type))
			except:
				pass





