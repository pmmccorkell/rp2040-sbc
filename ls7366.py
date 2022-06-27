# Patrick McCorkell
# May 2022
# US Naval Academy
# Robotics and Control TSD

# def tictoc(func):
# 	def wrapper(*args):
# 		start = monotonic_ns()
# 		func(*args)
# 		end = monotonic_ns()
# 		# print(func)
# 		print(str(func)+': '+str((end-start) / (10**9)))
# 	return wrapper


class LS7366():
	def __init__(self,spi_bus,chip_select,quadrature=4):
		self._bus = spi_bus
		self._cs = chip_select
		self._cs.value = 1

		# MDR0 settings. See page 4 of datasheet.
		self.quad_setting = quadrature
		self.running_mode = 0x0		# What happens when range reached
									# 0x0 free, 0x4 single-cycle, 0x8 range-limit to DTR, 0xC use DTR as modulo
		self.index_mode = 0x0		# What happens when Index input, pin 10, triggers.
									# 0x0 disabled, 0x10 'LOAD CNTR', 0x20 'CLR CNTR', 0x30 'LOAD OTR'
		self.index_sign = 0x0		# Triggers index_mode on high or low
									# 0x0 low, 0x40 high
		self.clock_division = 0x0	# Filter clock division.
									# 0x0 factor of 1, 0x80 factor of 2


		# MDR1 settings. See page 4 of datasheet.
		self.counter_bytes = 0x0	# How many bytes the counter stores.
									# 0x0 4byte, 0x1 3byte, 0x2 2byte, 0x3 1byte
		self.start_stop = 0x0		# Enable/Disable counting
									# 0x0 enable, 0x4 disable

		# STR register information.
		self.STR_carry = 0x0
		self.STR_borrow = 0x0
		self.STR_compare = 0x0
		self.STR_index_latch = 0x0

		# Last count read from the encoder.
		self.last_count = 0x0


		# Bits 7 and 6, per datasheet page 3
		self._instruction_function = {
			'CLR':0,		# 0x00 CLR
			'RD': 64,		# 0x40 RD
			'WR': 128,		# 0x80 WR
			'LOAD': 192		# 0xC0 LOAD
		}
		# Bits 5, 4, and 3 per datasheet page 3
		self._instruction_register = {
			'MDR0':8,	# 8bit mode register 0		0x08 MDR0
			'MDR1':16,	# 8bit mode register 1		0x10 MDR1
			'DTR':24,	# 32bit data register		0x18 DTR
			'CNTR':32,	# 32bit count register		0x20 CNTR
			'OTR':40,	# 32bit output register		0x28 OTR
			'STR':48,	# 8bit status register		0x30 STR
		}

		self._init_ls7366()

	# Initialize the LS7366 quadrature counter.
	def _init_ls7366(self,):
		# Set quadrature to desired setting.
		self.set_quadrature(self.quad_setting)
		# Reset the counter.
		self.reset_counter()
		# Initial reading of counter.
		self.read_counter()

	def _read(self,nlength=4):
		# Configure SPI bus to 0ph / 0pol
		self._bus.configure(phase=0,polarity=0)
		buffer_in = bytearray(nlength)

		# RD CNTR -> 0x40 'RD' + 0x20 'CNTR' = 0x60
		# 	instruction byte to the device.
		buffer = 0x60

		# Gate the SPI bus by bringing chip select low,
		#	and write the command RD CNTR,
		#	and read into the 4 bytes buffer_in, received from the device.
		self._cs.value = 0	# Gate device by setting chip select low.
		self._bus.write(buffer.to_bytes(1,'big'))	# Write command 'RD CNTR' to the device across the MOSI line.
		self._bus.readinto(buffer_in)				# Read into buffer_in object, from the MISO line.
		self._cs.value = 1	# End gating to the device by setting chip select high.


		# Convert buffer_in from the device into an integer.
		buffer_int = int.from_bytes(buffer_in,'big')

		# Convert the unsigned integer to a signed int using twos compliment.
		self.last_count = self.twos_comp(buffer_int)

	# Data must be in the form of a byte.
	def _write(self, data_set):
		# Configure SPI bus to 0ph / 0pol
		self._bus.configure(phase=0,polarity=0)

		# Gate the SPI bus by bringing chip select low,
		#	and write the buffer.
		self._cs.value = 0
		for data in data_set:
			# print(data)
			self._bus.write(data)

		# End gating to the device by bringing chip select high
		self._cs.value = 1


	def _send_instructions(self,action,register,added_data=None,added_l=4):
		# Get the instruction value.
		act = self._instruction_function.get(action)
		# Get the instruction register.
		target = self._instruction_register.get(register)

		# Form the instruction byte from the dictionaries
		# 	for the desired action and target register.
		buffer_command = (act+target).to_bytes(1,'big')
		buffer = [buffer_command]
		if (added_data != None):
			buffer.append(added_data.to_bytes(added_l,'big'))
		# print(action,register,buffer,act,target)
		# Write the instruction byte.
		self._write(buffer)


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

	# 
	def load_counter(self):
		self._send_instructions('LOAD','CNTR')

	# Function to reset the counter.
	def reset_counter(self):
		# self.write_DTR(0)
		self._send_instructions('CLR','CNTR')
		# self._send_instructions('LOAD','CNTR')

	# Function to load a value into the counter register.
	def set_counter(self,data):
		self._send_instructions('WR','DTR',data)
		self.load_counter()



	# Datasheet page 4.
	# 	MDR0 register is 1byte (8bit) long.
	def _set_MDR0(self):
		buffer = (self.quad_setting - 1) + self.running_mode + self.index_mode + self.index_sign + self.clock_division
		self._send_instructions('WR','MDR0',buffer,1)

	def set_quadrature(self,quadrature_pulses=4):
		# self._send_instructions('WR','MDR0',quadrature_pulses - 1, 1)
		self.quad_setting = quadrature_pulses
		self._set_MDR0()

	def set_free_running(self):
		# Datasheet page 4.
		# 	MDR0 register is 1byte (8bit) long.
		# self._send_instructions('WR','MDR0',0x0,1)
		self.running_mode = 0x0
		self._set_MDR0()

	def set_single_cycle(self):
		# Datasheet page 4.
		# 	MDR0 register is 1byte (8bit) long.
		# self._send_instructions('WR','MDR0',0x4,1)
		self.running_mode = 0x4
		self._set_MDR0()

	def set_encoder_range(self,data):
		self._send_instructions('WR','DTR',data)
		self.running_mode = 0x8
		self._set_MDR0()

	def set_encoder_range_rollover(self,data):
		self._send_instructions('WR','DTR',data)
		self.running_mode = 0xC
		self._set_MDR0()
	

	# Datasheet page 4.
	# 	MDR1 register is 1byte (8bit) long.
	def _set_MDR1(self):
		buffer = self.counter_bytes + self.start_stop
		# print(buffer)
		self._send_instructions('WR','MDR1',buffer,1)

	# Part of MDR1 register. Datasheet page 4.
	def set_counter_bytes(self,n):
		if n == 1:
			self.counter_bytes = 0x3	# 1 byte
		elif n==2:
			self.counter_bytes = 0x2	# 2 bytes
		elif n==3:
			self.counter_bytes = 0x1	# 3 bytes
		else:
			self.counter_bytes = 0x0	# 4 bytes

	# Part of MDR1 register. Datasheet page 4.
	def resume(self):
		self.start_stop = 0x0	# enable counting
		self._set_MDR1()
	def pause(self):
		self.start_stop = 0x4	# disable counting
		self._set_MDR1()

	# Loads the present counter (CNTR) register into the output (OTR) register.
	# 	Because the CNTR is continually doing operations, the OTR acts as a buffer.
	def read_counter(self):
		self._send_instructions('LOAD','OTR')
		self._read()
		return self.last_count

	def deinit(self):
		return 1
