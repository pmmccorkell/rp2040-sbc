# Patrick McCorkell
# July 2022
# US Naval Academy
# Robotics and Control TSD

from math import copysign



# PWM on both in1 and in2, digital en
class L298N_pwm():
	def __init__(self,in1,in2,en):
		self._in1 = in1
		self._in2 = in2
		self._en = en
		self._min_bias = 0
		self.last_w = None
		self.free_spin()

	@property
	def min_bias(self):
		return self._min_bias

	@min_bias.setter
	def min_bias(self, bias):
		self._min_bias = bias

	def _clip(self,n):
		return copysign(max(abs(n),self.min_bias),n)

	def _clamp(self,n):
		return (min(max(n,0),65535))

	def _transform(self,sp):
		return (65535 * sp)

	def set_raw(self,in1_val=0,in2_val=0):
		in1_val = int(self._clamp((in1_val)))
		in2_val = int(self._clamp((in2_val)))
		# print(f"set_raw: {in1_val,in2_val}")
		self._in1.duty_cycle = in1_val
		self._in2.duty_cycle = in2_val
		self._en.value = 1
		return in1_val,in2_val

	def brake(self,val=1):
		scaled_val = self._transform(abs(val))
		return self.set_raw(scaled_val,scaled_val)

	def free_spin(self):
		return self.set_raw()

	def off(self):
		for _ in range(3):
			self._en.value = 0
			self._in1.duty_cycle = 0
			self._in2.duty_cycle = 0

	def set_w(self,speed=0):
		scaled_speed = self._transform(self._clip(speed))
		self.last_w = speed
		return self.set_raw(-1*scaled_speed,scaled_speed)

	def deinit(self):
		for _ in range(3):
			self.off()
		return 1

# Digital on both in1 and in2, PWM en
class L298N_dig():
	def __init__(self,in1,in2,en=0):
		self._dir0 = in2
		print(type(en))
		if (str(type(en)) == "<class 'PWMOut'>"):
			self._dir1 = in1
			self._pwm = en
			self.brake_enable = True
		else:
			self._dir1 = DummyPin()
			self._pwm = in1
			self.brake_enable = False

		self._min_bias = 0
		self.last_w = None
		self.free_spin()

	@property
	def min_bias(self):
		return self._min_bias

	@min_bias.setter
	def min_bias(self, bias):
		self._min_bias = bias

	def _clip(self,n):
		return copysign(max(abs(n),self.min_bias),n)

	def _clamp(self,n):
		return (min(max(n,0),65535))

	def _transform(self,sp):
		return (65535 * sp)

	def set_raw(self,effort=0):
		pwm_val = int(self._clamp(abs(effort)))
		self._pwm.duty_cycle = pwm_val
		dir_val = int(copysign(0.5,effort)+0.5)
		self._dir0.value = dir_val
		self._dir1.value = not dir_val
		# print(f"raw: {self._pwm.duty_cycle},{self._dir0.value},{self._dir1.value}")
		return pwm_val*(dir_val-0.5)*2

	def brake(self,val=1):
		if (self.brake_enable):
			self._dir0.value = 1
			self._dir1.value = 1
			self._pwm.duty_cycle = self._clamp(self._transform(val))
		else:
			self.off()
		return self._dir1.value

	def free_spin(self):
		self._dir0.value = 0
		self._dir1.value = 0
		self._pwm.duty_cycle = 65535
		return 1

	def off(self):
		for _ in range(3):
			self._dir0.value = 0
			self._dir1.value = 0
			self._pwm.duty_cycle = 0

	def set_w(self,speed=0):
		scaled_speed = self._transform(self._clip(speed))
		self.last_w = speed
		return self.set_raw(scaled_speed)

	def deinit(self):
		for _ in range(3):
			self.off()
		return 1


class DummyPin():
	def __init__(self):
		self.value = 0

	def deinit(self):
		self.value = 0
		return 1


# Motor 1
# gp15	p24		in1
# gp14	p25		in2
# gp13	p26		en

# Motor 2
# gp12	p21		in1
# gp11	p22		in2
# gp10	p23		en


