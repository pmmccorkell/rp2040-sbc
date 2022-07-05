# Patrick McCorkell
# January 2022
# US Naval Academy
# Robotics and Control TSD
#
# Built on AD5293 Datasheet Revision E
#



# 0x1b 0xff		initialization
# 0x04 0x00		min
# 0x07 0xff		max

from time import monotonic_ns
def tictoc(func):
	def wrapper(*args):
		start = monotonic_ns()
		func(*args)
		end = monotonic_ns()
		# print(func)
		print(str(func)+': '+str((end-start) / (10**9)))
	return wrapper


class AD5293():
	def __init__(self,spi_bus,chip_select):
		self._bus = spi_bus
		self._cs = chip_select
		self._cs.value = 1

		# Set range of pot [0,1023]
		self._minn = 0x000
		self._maxn = 0x3ff

		self.set_val = 0xffff

		self._init_ad5293()

	def _init_ad5293(self):
		self._write([0x1b,0xff])
		self._write([0x06,0x02])

	# write data to the SPI bus
	# data shall be a list of 2 integers, both in range [0,255]
	def _write(self,data):
		# print(hex(data[0]),hex(data[1]))
		self._bus.configure(phase=1,polarity=0)
		if (len(data) == 2):
			self._cs.value = 0
			self._bus.write(bytes(data))
			self._cs.value = 1
			return 1
		else:
			print("LOG: Data sent to AD5293._write() of incorrect length.")
			print("LOG: Shall be list[] of length 2. All values in range[0x00,0xFF].")
			return 0

	# Clamp n to [minn,maxn]
	# @tictoc
	def _clamp(self,n):
		return min(max(n,self._minn),self._maxn)

	# Transform [-1,1] to [0,1023]
	# @tictoc
	def _transform(self,n):
		return self._clamp(int((511.5 * n)+0.5) + 511)	# 1.0166 s / 2048 cycles
		# return self._clamp(round((511.5 * n)+0.5) + 511)	# 1.1025 s / 2048 cycles

	# val shall be [0,1023]
	def set_raw(self,val):
		update_command = 0x04
		data_LSB = val & 0xff
		data_MSB = ((val & 0xff00) >> 8) | update_command
		self._write([data_MSB,data_LSB])
		self.set_val = val
		return self.set_val

	# val shall be [-1,1]
	def set_pot(self,val):
		return self.set_raw(self._transform(val))

	# Zero out the potentiometer during object deinitialization.
	def deinit(self):
		for _ in range(3):
			self.set_pot(0)
		return 1






