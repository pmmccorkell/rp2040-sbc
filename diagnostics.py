from sbc import SBC
import adafruit_bno055
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import (
    BNO_REPORT_ROTATION_VECTOR,
	BNO_REPORT_GAME_ROTATION_VECTOR,
	BNO_REPORT_ACTIVITY_CLASSIFIER,
)
from time import sleep
import board
import busio
import atexit
import sys
from math import atan2,asin,copysign,pi
from random import randint
tau = 2*pi


# I2C bus
i2c_SDA = board.GP16
i2c_SCL = board.GP17
i2c_bus = busio.I2C(scl=i2c_SCL,sda=i2c_SDA)
print("Setting up I2C bus.")


# BNO055 IMU setup
print("\r\nLooking for BNO-055.")
for i in range(3):
	try:
		imu = adafruit_bno055.BNO055_I2C(i2c_bus)
		print(f"BNO-055 found.")
		break
	except:
		print(f"BNO-055 imu not found, attempt: {i+1}.")

# BNO085 IMU setup
print("\r\nLooking for BNO-085.")
for i in range(3):
	try:
		imu = BNO08X_I2C(i2c_bus)
		imu.enable_feature(BNO_REPORT_ROTATION_VECTOR)
		imu.enable_feature(BNO_REPORT_GAME_ROTATION_VECTOR)
		imu.enable_feature(BNO_REPORT_ACTIVITY_CLASSIFIER)
		print("BNO-085 found.")
		break
	except:
		print(f"BNO-085 imu not found, attempt: {i+1}.")


project = SBC(i2c=i2c_bus)

# For a clean program shutdown
deinit_repository = [
	project,
	# enc_device1, enc_device2, digipot_device, adc_device, dac_device,		# deinit device drivers
	i2c_bus, # spi,																# deinit comm buses
	# cs1,cs2,cs3,cs4,cs5,													# deinit other pins
	i2c_SDA, i2c_SCL
]
def exit_program():
	# del sys.modules['ls7366']
	for obj in deinit_repository:
		try:
			obj_type = type(obj)
			obj.deinit()
			print('deinitialized %s of type %s.' %(obj,obj_type))
		except:
			pass
atexit.register(exit_program)


# Test pause and restart functionality of LS7366 encoder1
pause_enc1 = True
def startstop_enc1():
	global pause_enc1

	print()
	if pause_enc1:
		print('pause:')
		project._enc_device1.pause()
	else:
		print('resume:')
		project._enc_device1.resume()

	for i in range(5):
		project._enc_device1.read_counter()
		print(i,project._enc_device1.last_count)
		sleep(0.2)

	pause_enc1 = not pause_enc1

# Test MAX522 DAC chA
def max522_iterate():
	for i in range(256):
		print(i, i/255 * 4.6)
		project._dac_device.set_dac_A(i/255)
		sleep(0.01)

# Test MAX1270 forming of SPI hex for ch3
#	datasheet page 11
def test_form_control_byte():
	project._adc_device.range = 0
	project._adc_device.bipolar = 1
	project._adc_device.power_mode = 0
	return project._adc_device._form_control_byte(3)


# Test MAX522 DAC chA and chB to MAX1270 ADC ch5
def test_adc_from_dac():
	project._adc_device.bipolar=0		# unipolar
	project._adc_device.range=0			# 5V range
	project._adc_device.power_mode = 0	# normal, internal clock

	n = 100
	for i in range(n):
		print(project._dac_device.set_dac_all(i/n))
		sleep(1)
		print(project._adc_device.read_volts(5))
		print(i/n*5)
		print()
		sleep(1)

# Test AD5293 digipot output
def test_digipot():
	rangen = 1024
	for i in range(rangen):
		print(project._digipot_device.set_pot(i/rangen))
		sleep(0.05)
	for i in range(rangen):
		print(project._digipot_device.set_pot(-1 * i/rangen))
		sleep(0.1)

# Display raw output of digipot to voltage set
	# shift and scale [0,1024] to [10,-10] respectively.
	# sign is flipped due to OpAmp
def convert_digipot_to_V(raw_val):
	# print(raw_val)
	return -1 * ((raw_val/51.2) - 10)

def test_adc_from_digipot():
	project._adc_device.bipolar=1		# bipolar
	project._adc_device.range=1			# 10V range
	project._adc_device.power_mode = 0	# normal, internal clock

	n = 1024
	for i in range(n):
		print("Digipot (AD5293) set: %0.2f (V)" %convert_digipot_to_V(project._digipot_device.set_raw(1023-i)))
		# sleep(1)
		print("ADC (MAX1270) read ch0: %0.2f (V)" %project._adc_device.read_volts(0))
		print()
		sleep(0.1)


# BNO 085 quaternion to euler conversion for Tait–Bryan angles.
def q_to_e(x,y,z,w):
	conversion_factor = 360/tau	# radians to degrees.

	# https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles#Intuition
	# 	w = q0, x = q1, y = q2, z = q3
	# 	BNO 085 quaternion outputs are in a different order, placing 'w'/'q0' as the last entry.
	# 	BNO 085 quaternion outputs are already normalized.
	heading = - atan2(2* ((w*z) + (x*y)), 1 - 2 * ((y*y) + (z*z)) ) * conversion_factor
	pitch = asin(-2 * (y*w) - (x*z) ) * conversion_factor
	roll = atan2(2 * ((y * z) + (w * x)) , 1 - (2 * ( (x*x) + (y*y) ))) * conversion_factor

	return heading,pitch,roll


def run():
	project.initiate_motor(1,'dig')
	project._adc_device.bipolar = 1
	project._adc_device.range = 1
	project._mot1.set_w(randint(0,100)/100)

	project._mot1.min_bias = 0.08
	print(project._mot1._min_bias)
	# while(1):
	n = 1024
	while(1):
		for i in range(2*n):
		# for _ in range(3):
			print()
			last_last_count = project._enc_device1.last_count
			print(f"encoder ch1: {project._enc_device1.read_counter():0.2f}")
			print(f"Digipot (AD5293) set: {convert_digipot_to_V(project._digipot_device.set_raw((abs(project._enc_device1.last_count) % 1024))):0.2f} (V)" )
			print(f"ADC (MAX1270) read ch0: {project._adc_device.read_volts(0):0.2f} (V)" )
			print(f"DAC (MAX522) set all ch: {(project._dac_device.set_dac_all((abs(project._enc_device1.last_count) % 256) / 256)/256 * 5):0.2f} (V)")
			print(f"ADC (MAX1270) read ch5: {project._adc_device.read_volts(5):0.2f} (V)" )
			# print(f"BNO 55 Euler angles: {imu.euler}")
			print(f"BNO 85 Quaternion: {q_to_e(*imu.quaternion)}")
			print(f"BNO 85 Game Quatr: {q_to_e(*imu.game_quaternion)}")
			imu_classification = imu.activity_classification
			print(f"IMU activity: {imu_classification['most_likely']}, confidence {imu_classification[imu_classification['most_likely']]:0.2f}%%")

			# dcount = project._enc_device1.last_count-last_last_count
			# last_mot = project._mot1.set_w( project._enc_device1.last_count / 32768 )
			# print(f"Mot1 set: {last_mot}")
			# if (abs(last_mot) < min_bias):
			# 	project._mot1.set_w(copysign(min_bias,last_mot))
			# 	# sleep(1)
			# 	print(f"encoder ch1: {project._enc_device1.read_counter():0.2f}",i)

			# looking for min bias necessary to drive motor
			# project._mot1.set_w(i/(n*2))

			# Sweep full range
			# print(f"motor: {project._mot1.set_w((i-n)/(3*n))}")
			print(f"motor: {project._mot1.set_w(randint(-256,256)/256)}")
			# print(f"motor: {project._mot1.set_w(i/(2*n))}, i: {i/(2*n)}")

			sleep(0.1)
			# test_adc_from_digipot()

			# max522_iterate()
			# print(test_form_control_byte())
			# project._adc_device.power_mode = 0
			# test_adc_from_dac()
			# test_reform_bytes()
		print()
		print(f"encoder ch1: {project._enc_device1.read_counter():0.2f}")
		print(f"motor brake: {project._mot1.brake()}")
		sleep(5)
		print(f"encoder ch1: {project._enc_device1.read_counter():0.2f}")
		print(f"motor freespin: {project._mot1.free_spin()}")
		sleep(5)
		print(f"encoder ch1: {project._enc_device1.read_counter():0.2f}")
		print()


