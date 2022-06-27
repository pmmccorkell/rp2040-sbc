# Patrick McCorkell
# June 2022
# US Naval Academy
# Robotics and Control TSD

# Driver for 12bit ADC, MAX1270.

from collections import OrderedDict

# def tictoc(func):
# 	def wrapper(*args):
# 		start = monotonic_ns()
# 		func(*args)
# 		end = monotonic_ns()
# 		# print(func)
# 		print(str(func)+': '+str((end-start) / (10**9)))
# 	return wrapper


class MAX1270():
	# Length of each function, for shifting purposes.
		# Permanent and Private class variable. Static.
	# __control_bits_l = OrderedDict([
	# 	('START' , 1),		# 1bit;
	# 	('SEL' , 3),		# 3bit;
	# 	('RNG' , 1),		# 1bit;
	# 	('BIP' , 1),		# 1bit;
	# 	('PD' , 2),			# 2bit;
	# ])

	def __init__(self,spi_bus,chip_select):
		# Initialize SPI.
		self._bus = spi_bus
		self._cs = chip_select
		self._cs.value = 1

		self.outputs = {}
		for i in range(8):
			self.outputs[i]=0
		
		# See datasheet page 11
		# self.control_bits = OrderedDict([
			# ('START', 1),	# 1bit; Must be 1 after cs' goes low. A high triggers the rest of this.
			# ('SEL', 0),		# 3bit; Channel Select: 000 to 111 for ch0 to ch7.
		# 	('RNG', 0),		# 1bit; Range: 0 5V, 1 10V
		# 	('BIP', 0),		# 1bit; Bipolar: 0 unipolar, 1 bipolar
		# 	('PD', 0),		# 2bit; PowerDown: 00 always on w/internal clock, 01 always on w/external clock, 
		# 						# 11 full powerdown, 10 standby powerdown
		# ])
		self.range = 0		# 1bit; Range: 0 5V, 1 10V
		self.bipolar = 0	# 1bit; Bipolar: 0 unipolar, 1 bipolar
		self.power_mode = 0	# 2bit; PowerDown: 00 always on w/internal clock, 01 always on w/external clock, 
		 						# 11 full powerdown, 10 standby powerdown

		self.last_values = {}
		# for i in range(8):
		# 	self.last_values[i] = 0
		self._init_max1270()


	def _form_control_byte(self,channel=0):
		control_byte = 0x80 + (channel << 4) + (self.range << 3) + (self.bipolar << 2) + self.power_mode
		return control_byte.to_bytes(1,'big')	# Convert to byte of length 1, big-endian.

	def _init_max1270(self):
		for i in range(8):
			self.last_values[i] = 0


	def _write(self,data_set):
		# Configure SPI bus to 0ph / 0pol per datasheet page 10.
		self._bus.configure(phase=0,polarity=0)

		# Gate the SPI bus by bringing chip select low,
		#	and write the buffer.
		self._cs.value = 0
		for data in data_set:
			# print(data)
			self._bus.write(data)

		# End gating to the device by bringing chip select high
		self._cs.value = 1


	def _read(self,channel,nlength=2):
		# Configure SPI bus to 0ph / 0pol

		self._bus.configure(phase=0,polarity=0)
		buffer_in = bytearray(nlength)

		# RD CNTR -> 0x40 'RD' + 0x20 'CNTR' = 0x60
		# 	instruction byte to the device.
		buffer = self._form_control_byte(channel)

		# Gate the SPI bus by bringing chip select low,
		#	and write the command RD CNTR,
		#	and read into the 4 bytes buffer_in, received from the device.
		self._cs.value = 0	# Gate device by setting chip select low.
		self._bus.write(buffer)	# Write command 'RD CNTR' to the device across the MOSI line.
		self._bus.readinto(buffer_in)				# Read into buffer_in object, from the MISO line.
		self._cs.value = 1	# End gating to the device by setting chip select high.
		# buffer_in >>= 4
		# print(buffer_in)

		buffer_int = (int.from_bytes(buffer_in,'big')) >> 4
		# print('reversed')
		reversed_hex = '0x'
		for i in list(reversed(hex(buffer_int))):
			if i == 'x':
				break
			reversed_hex+=i
		reversed_int = int(reversed_hex)

		# print(buffer_in, buffer_int, reversed_int)  #, hex(buffer_int_b))

		# Convert the unsigned integer to a signed int using twos compliment.
		return reversed_int

	# Function to convert unsigned bytes of length 'unsigned_l'
	# 	into a signed int using twos compliment.
	def twos_comp(self,unsigned_int,unsigned_l = 4):
		# Initiate first byte of each mask in string format.
		value_mask = '0x7f'		# Every bit following the sign.
		sign_mask = '0x80'		# Only the signed bit.

		# Iterate and append for additional bytes up to 'unsigned_l'.
		for _ in range(unsigned_l-1):
			value_mask += 'ff'
			sign_mask += '00'

		# Form base16 integers of the mask strings.
		value_mask = int(value_mask,16)
		sign_mask = int(sign_mask,16)

		# Get the absolute value by bitwise comparing to the value_mask.
		# Create boolean of negative (True) or positive (False) by bitwise comparing to sign_mask.
		# If negative, subtract the sign_mask.
		return (unsigned_int & value_mask) - (sign_mask * bool(unsigned_int & sign_mask))

	def read_volts(self,channel):
		read_buffer = self._read(channel)
		signed_reading = (self.bipolar * self.twos_comp(read_buffer)) + ((not self.bipolar) * read_buffer)
		scale = 0xfff/(1+self.bipolar)
		scaled_reading = signed_reading/scale * ((self.range * 10) + ((not self.range) * 5))
		self.last_values[channel] = scaled_reading
		# print(read_buffer, signed_reading, scale, scaled_reading)
		return scaled_reading

	def deinit(self):
		return 1



