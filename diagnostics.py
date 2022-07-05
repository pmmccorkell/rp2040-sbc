from sbc import SBC
import adafruit_bno055
from time import sleep
import board
import busio
import atexit
import sys


# SPI bus
# sclk = board.GP2
# mosi = board.GP3
# miso = board.GP4
# spi = busio.SPI(sclk,MOSI=mosi,MISO=miso)
# print('Setting up SPI bus...', end="")
# while not spi.try_lock():
# 	print('',end=".")
# print("\r\n SPI bus setup complete.")
# spi.configure(phase=0,polarity=0,baudrate=1000000)


# I2C bus
i2c_SDA = board.GP16
i2c_SCL = board.GP17
i2c_bus = busio.I2C(scl=i2c_SCL,sda=i2c_SDA)
print('Setting up I2C bus.')


# BNO055 IMU setup
try:
	imu = adafruit_bno055.BNO055_I2C(i2c_bus)
except:
	print('BNO-055 imu not found.')

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


while(1):
# for _ in range(3):
	project._adc_device.bipolar = 1
	project._adc_device.range = 1
	print()
	print("encoder ch1: %0.2f" %project._enc_device1.read_counter())
	print("Digipot (AD5293) set: %0.2f (V)" %convert_digipot_to_V(project._digipot_device.set_raw((abs(project._enc_device1.last_count) % 1024))))
	print("ADC (MAX1270) read ch0: %0.2f (V)" %project._adc_device.read_volts(0))
	print("DAC (MAX522) set all ch: %0.2f (V)" %(project._dac_device.set_dac_all((abs(project._enc_device1.last_count) % 256) / 256)/256 * 5))
	print("ADC (MAX1270) read ch5: %0.2f (V)" %project._adc_device.read_volts(5))
	print("IMU Euler angles: %s" %(imu.euler,))
	sleep(0.4)
	# test_adc_from_digipot()

	# max522_iterate()
	# print(test_form_control_byte())
	# project._adc_device.power_mode = 0
	# test_adc_from_dac()
	# test_reform_bytes()
