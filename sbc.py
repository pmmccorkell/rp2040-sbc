from math import pi
from time import monotonic_ns, sleep
import board
import busio
import rotaryio
from digitalio import DigitalInOut, Direction
from ad5293 import AD5293_309
import ticker
import atexit
from json import dumps


class SBC():
	def __init__(self,counts_per_revolution,sample_size):
		self.array_size = sample_size
		self.encoder_pos = self.__form_array()
		self.encoder_time = self.__form_array()

		self.tickers = self.__setup_interrupt()

		self.enc = self.__setup_encoder()
		if (not self.enc):
			# print("LOG: Encoder setup failed on 1st attempt.")
			# print("LOG: Attempting to reset encoder.")
			try:
				self.__disable_encoder()
				self.enc = self.__setup_encoder()
				# print("LOG: Encoder reset.")
			except:
				pass
				# print("LOG: Encoder setup failed on 2nd attempt.")
		self.__sample_offset = -2

		self.encoder_counts_per_rev = counts_per_revolution

		self.digipot = self.__setup_digipot()
		if (not self.digipot):
			# print("LOG: Digipot setup failed on 1st attempt.")
			# print("LOG: Attempting to reset digipot.")
			self.reset_digipot()
			# if (self.digipot):
				# print("LOG: Digipot reset.")
			# else:
				# print("LOG: Digipot failed to reset.")

		self.tau = 2 * pi
		self.controller_update = 0.002
		self.quit = 0

		###########################
		###########################
		###########################
		########### Correct during intake by multiplying by "tau/counts_per_rev"
		self.pid = {
			'Kp' : 0.0001,
			'Ki' : 0.00000000001,
			'Kd' : 0.00000000001
		}
		self.target_speed = self.rad_to_counts(10)
		self.time_limit = 1
		self.motor_bias = 0

	def __form_array(self):
		buffer = []
		try:
			for _ in range(self.array_size):
				buffer.append(0)
		except:
			pass
			# print("LOG: Memory Alloc failed. Device needs to be restarted.")
		return buffer

	def __setup_interrupt(self):
		return ticker.Interrupt_Controller()

	def __setup_encoder(self):
		try:
			encoder = rotaryio.IncrementalEncoder(board.GP15,board.GP14,4)
			return encoder
		except:
			# print('LOG: Error setting up encoder.')
			return 0
	def __disable_encoder(self):
		if (self.enc):
			# print("LOG: Disabling encoder.")
			self.enc.deinit()
	def reset_encoder(self):
		# print("LOG: Resetting encoder.")
		self.__disable_encoder()
		self.digipot.set_pot(0)
		sleep(0.5)
		self.enc = self.__setup_encoder()

	def __setup_digipot(self):
		# try:
		self.cs = DigitalInOut(board.GP5)
		self.cs.direction = Direction.OUTPUT
		self.cs.value = 1
		sclk = board.GP10
		mosi = board.GP11
		miso = board.GP12
		self.spi = busio.SPI(sclk,MOSI=mosi,MISO=miso)
		return AD5293_309(self.spi,self.cs)
	def __disable_digipot(self):
		self.digipot = 0
		self.spi.unlock()
		self.cs.deinit()
		self.spi = 0
		self.cs = 0
	def reset_digipot(self):
		try:
			self.digipot.set_pot(0)
			sleep(0.5)
			self.__disable_digipot()
		except:
			print("LOG: Failed to reset digipot.")
		sleep(0.5)
		self.digipot = self.__setup_digipot()


	def __control_loop_sawtooth(self):
		max_speed = 512
		min_speed = -512
		self.speed += self.step
		# print(self.speed)
		self.digipot.set_pot(self.speed/512)
		if (self.speed == max_speed):
			self.step = -1
		elif (self.speed == min_speed):
			self.step = 1


	def __control_loop_find_bias(self):
		# self.motor_bias = 0
		self.step = 1
		if (abs(self.enc.position)<10):
			self.__control_loop_sawtooth()
		else:
			self.digipot.set_pot(0)
			self.motor_bias = self.speed
			self.tickers.pause()

	def __control_loop_PID(self):
		self.encoder_loop()
		actual_speed, dt = self.get_controller_data()
		error = self.target_speed - actual_speed
		p_term = self.pid['Kp'] * error
		i_term = self.pid['Ki'] * error * dt
		d_term = self.pid['Kd'] * (error - self.last_error) / dt
		# new_rate = self.motor_bias + p_term + i_term + d_term
		# print(new_rate)
		self.digipot.set_pot(self.motor_bias + p_term + i_term + d_term)
		self.last_error = error


	def find_bias(self):
		# print('LOG: auto finding bias')
		self.motor_bias = 0
		self.speed = 0
		self.tickers.interrupt(name='bias',delay=0.1,function=self.__control_loop_find_bias)
		self.tickers.loop()
		self.tickers.remove_interrupt('bias')
		# print('LOG: found bias: ' + str(self.motor_bias))
		# print(self.tickers.tickers)
		self.motor_bias = self.speed/512
		sleep(0.5)

	def auto_control(self):
		self.target_speed = self.rad_to_counts(10)
		self.last_error = 0
		self.find_bias()
		self.reset_encoder()
		self.tickers.interrupt(name='check_quit', delay=self.time_limit,function=self.check_quit_loop)
		self.tickers.interrupt(name='pid_internal',delay=0.00005,function = self.__control_loop_PID)
		print('starting internal PID contorl')
		# print(self.tickers.tickers)
		self.tickers.loop()
		self.print_results_json()
		self.print_results_terminal()

	def attach_controller(self,func_name,update_interval,timeout):
		self.time_limit = timeout
		self.tickers.remove_interrupt_all()
		self.tickers.interrupt(name='check_quit', delay=self.time_limit,function=self.check_quit_loop)
		self.tickers.interrupt(name='pid_internal',delay=update_interval,function = func_name)

	def __prefill_arrays(self):
		for _ in range(3):
			self.encoder_loop()

	def change_sample_offset(self,offset):
		self.__sample_offset = -1 * (offset + 1)

	def run_controller(self):
		quit_function_exists = self.tickers.tickers.get('check_quit')
		if (quit_function_exists[0] <= 10):
			self.reset_encoder()
			# print('LOG: Starting external controller')
			self.__prefill_arrays()
			self.tickers.loop()
			self.print_results_json()
		else:
			print('LOG: Error. Cannot run external controller without all interrupts attached, or for longer than 10s.')
			print('LOG: ' + str(self.tickers.tickers))

	def print_results_json(self):
		json_data = {}
		first_entry = 0
		for i in range(len(self.encoder_pos)):
			if (self.encoder_pos[i] or self.encoder_time[i]):
				if (not first_entry):
					first_entry = i
				json_data['position'] = self.encoder_pos[i] * self.tau / self.encoder_counts_per_rev
				json_data['time'] = (self.encoder_time[i] - self.encoder_time[first_entry]) / 10**9
				print(dumps(json_data))
		# print("LOG: len " + str(len(self.encoder_pos) - first_entry))

	def encoder_loop(self):
		self.encoder_pos.pop(0)
		self.encoder_time.pop(0)
		self.encoder_pos.append(self.enc.position)
		self.encoder_time.append(monotonic_ns())

	def get_dx(self):
		return self.encoder_pos[-1] - self.encoder_pos[self.__sample_offset]

	def get_dt(self):
		return self.encoder_time[-1] - self.encoder_time[self.__sample_offset]

	def rad_to_counts(self,radians):
		return radians * (self.encoder_counts_per_rev / self.tau)

	def check_quit_loop(self):
		if self.quit:
			self.digipot.set_pot(0)
			self.tickers.pause()
		else:
			self.quit = 1





