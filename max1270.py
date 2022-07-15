# Patrick McCorkell
# June 2022
# US Naval Academy
# Robotics and Control TSD

# Driver for 12bit ADC, MAX1270.

class MAX1270():
	def __init__(self,spi_bus,chip_select):
		# Initialize SPI.
		self._bus = spi_bus
		self._cs = chip_select
		self._cs.value = 1

		self._init_max1270()
		self._default_channel = 0



	def _form_control_byte(self,channel=0):
		control_byte = 0x80 + (channel << 4) + (self.range << 3) + (self.bipolar << 2) + self.power_mode
		
		# print(control_byte)
		return control_byte.to_bytes(2,'big')	# Convert to byte of length 1, big-endian.

	def _init_max1270(self):
		# See datasheet page 11
		self.range = 0		# 1bit; Range: 0 5V, 1 10V
		self.bipolar = 0	# 1bit; Bipolar: 0 unipolar, 1 bipolar
		self.power_mode = 0	# 2bit; PowerDown: 00 always on w/internal clock, 01 always on w/external clock, 
		 						# 11 full powerdown, 10 standby powerdown

		self.last_values = {}
		for i in range(8):
			self.last_values[i] = None


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
		# Configure SPI bus to 0ph / 0pol per datasheet page 10.
		self._bus.configure(phase=0,polarity=0)
		buffer_in = bytearray(nlength)

		# RD CNTR -> 0x40 'RD' + 0x20 'CNTR' = 0x60
		# 	instruction byte to the device.
		buffer_out = self._form_control_byte(channel)

		# Gate the SPI bus by bringing chip select low,
		#	and write the command RD CNTR,
		#	and read into the 4 bytes buffer_in, received from the device.
		self._cs.value = 0	# Gate device by setting chip select low.
		self._bus.write(buffer_out)	# Write command 'RD CNTR' to the device across the MOSI line.
		self._bus.readinto(buffer_in)				# Read into buffer_in object, from the MISO line.
		self._cs.value = 1	# End gating to the device by setting chip select high.

		buffer_int = (int.from_bytes(buffer_in,'big')) >> 4

		# print(buffer_in, buffer_int >>4) #, reversed_int)  #, hex(buffer_int_b))

		# Convert the unsigned integer to a signed int using twos compliment.
		return buffer_int

	@property
	def value(self):
		# print(f"value, default ch: {self.default_channel}")
		# return self.read_volts(self.default_channel)
		return self.read(self.default_channel)

	@property
	def volts(self):
		return self.read_volts(self.default_channel)

	@property
	def default_channel(self):
		return self._default_channel

	@default_channel.setter
	def default_channel(self,val):
		# print(f"setter: {val}")
		self._default_channel = val

	# Reads ADC channel, normalized to [-1,1]
	def read(self,channel):
		# print(f"read_volts ch: {channel}")
		read_buffer = self._read(channel)
		signed_reading = (self.bipolar * self.twos_comp(read_buffer)) + ((not self.bipolar) * read_buffer)
		scale = 0x1000/(1+self.bipolar)
		scaled_reading = signed_reading/scale
		self.last_values[channel] = scaled_reading
		# print(read_buffer, signed_reading, scale, scaled_reading)
		return scaled_reading

	# Converts normalized [-1,1] reading to Volts.
	def read_volts(self,channel):
		voltage = self.read(channel) * ((self.range * 10) + ((not self.range) * 5))
		return voltage

	# Function to convert 'unsigned_int' of bit length 'unsigned_l'
	# 	into a signed int using twos compliment.
	def twos_comp(self, unsigned_int, unsigned_l = 12):
		# Initiate first bit of value mask in string format.
		value_mask = '0b1'

		# Iterate and append for additional bit up to 'unsigned_l'.
		#	Subtract 2, because first bit is the sign, and second bit was preloaded above.
		for _ in range(unsigned_l-2):
			value_mask += '1'

		# Form integers of the mask strings.
		value_mask = int(value_mask)
		sign_mask = value_mask + 1

		# Get the absolute value by bitwise comparing to the value_mask.
		# 	Create boolean of negative (True) or positive (False) by bitwise comparing to sign_mask.
		# 	If negative, subtract the sign_mask.
		return (unsigned_int & value_mask) - (sign_mask * bool(unsigned_int & sign_mask))

	def deinit(self):
		return 1



