# Patrick McCorkell
# June 2022
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



class MAX522():
	def __init__(self,spi_bus,chip_select):
		# Initialize SPI.
		self._bus = spi_bus
		self._cs = chip_select
		self._cs.value = 1

		# From MAX522 datasheet page 9.
		self.control_byte = {
			'load_A' : 0x21,
			'load_B' : 0x22,
			'load_all' : 0x23,
			'shutdown_A' : 0x28,
			'shutdown_B' : 0x30,
			'shutdown_all' : 0x38,
			'activate' : 0x20
		}
		self._default_control_byte = 0x0
		self._init_max522()

	def _init_max522(self):
		# Activate, and set both DACs to 0.
		self.set_dac_all(0)

	# Data must be in the form of a byte.
	def _write(self, data_set):
		# Configure SPI bus to 0ph / 0pol per MAX522 datasheet page 10.
		self._bus.configure(phase=0,polarity=0 )

		# Gate the SPI bus by bringing chip select low,
		#	and write the buffer.
		self._cs.value = 0
		for data in data_set:
			# print(data)
			self._bus.write(data.to_bytes(1,'big'))

		# End gating to the device by bringing chip select high
		self._cs.value = 1

	def _parse_command(self,type,cmd):
		if isinstance(cmd,str):
			control_key = type + '_' + cmd
		else:
			print('Error, 1st argument "id" not correct format.')
			print('Must be "A", "B", or "all".')
		return self.control_byte.get(control_key, self._default_control_byte)

	# Clamp n to range [minn,maxn]
	def _clamp(self,n,minn=0,maxn=255):
		return min(max(n,minn),maxn)

	# Transform [0,1] to [0,255]
	def _transform(self,val_float):
		return val_float*255


	# Functions to set channels A and B DACs using ints in range [0,255]
	def set_raw(self,id,val_int):
		update_command = self._parse_command('load',id)
		data_byte = self._clamp(int(val_int + 0.5))
		self._write([update_command,data_byte])
		return data_byte
	def set_raw_A(self,val):
		return self.set_raw('A',val)	
	def set_raw_B(self,val):
		return self.set_raw('B',val)
	def set_raw_all(self,val):
		return self.set_raw('all',val)

	# Functions to set channels A and B DACs using floats in range [0,1]
	def set_dac(self,id,val_float):
		return self.set_raw(id,self._transform(val_float))
	def set_dac_A(self,val):
		return self.set_dac('A',val)
	def set_dac_B(self,val):
		return self.set_dac('B',val)
	def set_dac_all(self,val):
		return self.set_dac('all',val)

	# Functions to shut down channels A and B DACs.
	def shutdown(self,id):
		update_command = self._parse_command('shutdown',id)
		self._write([update_command,0x0])
	def shutdown_A(self):
		self.shutdown('A')
	def shutdown_B(self):
		self.shutdown('B')
	def shutdown_all(self):
		self.shutdown('all')

	# Activate both DAC channels.
	def activate(self):
		update_command = self.control_byte.get('activate', self._default_control_byte)
		self._write([update_command,0x0])

	def deinit(self):
		self.set_dac_all(0)
		self.shutdown_all()
		return 1












