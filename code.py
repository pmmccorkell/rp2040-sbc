print("Hello " + __name__)
from ls7366 import LS7366
from ad5293 import AD5293
from max522 import MAX522
from max1270 import MAX1270
from time import sleep
import board
import busio
from digitalio import DigitalInOut, Direction
import atexit
import sys



sclk = board.GP2
mosi = board.GP3
miso = board.GP4

# SPI bus
spi = busio.SPI(sclk,MOSI=mosi,MISO=miso)
print('Setting up SPI bus...', end="")
while not spi.try_lock():
	print('',end=".")
print("\r\n SPI bus setup complete.")
spi.configure(baudrate=2000000)
# spi.configure(phase=0,polarity=0)
spi.configure(phase=1,polarity=0)


# encoder 1 chip select
cs1 = DigitalInOut(board.GP19)
cs1.direction = Direction.OUTPUT
cs1.value = 1
enc_device1 = LS7366(spi,cs1)

# encoder 2 chip select
cs2 = DigitalInOut(board.GP18)
cs2.direction = Direction.OUTPUT
cs2.value = 1
enc_device2 = LS7366(spi,cs2)

# AD5293 digipot chip select
cs3 = DigitalInOut(board.GP20)
cs3.direction = Direction.OUTPUT
cs3.value = 1
digipot_device = AD5293(spi,cs3)

# MAX522 DAC chip select
cs4 = DigitalInOut(board.GP21)
cs4.direction = Direction.OUTPUT
cs4.value = 1
dac_device = MAX522(spi,cs4)

# MAX1270 ADC chip select
cs5 = DigitalInOut(board.GP22)
cs5.direction = Direction.OUTPUT
cs5.value = 1
adc_device = MAX1270(spi,cs5)



deinit_repository = [
	digipot_device, adc_device, dac_device,		# deinit device drivers
	spi,										# deinit comm buses
	cs1,cs2,cs3,cs4,cs5,						# deinit other pins
]
def exit_program():
	del sys.modules['ls7366']
	for obj in deinit_repository:
		try:
			obj.deinit()
			print('deinitialized'+str(obj))
		except:
			pass
atexit.register(exit_program)





pause_enc1 = True
def startstop_enc1():
	global pause_enc1

	print()
	if pause_enc1:
		print('pause:')
		enc_device1.pause()
	else:
		print('resume:')
		enc_device1.resume()

	for i in range(5):
		enc_device1.read_counter()
		print(i,enc_device1.last_count)
		sleep(0.2)

	pause_enc1 = not pause_enc1

def max522_iterate():
	for i in range(256):
		print(i, i/255 * 4.6)
		dac_device.set_dac_A(i/255)
		sleep(0.01)

def test_form_control_byte():
	adc_device.control_bits['START'] = 1
	adc_device.control_bits['RNG'] = 1
	print(adc_device._form_control_byte())


from collections import OrderedDict
control_bits = OrderedDict([
		('START' , 0),
		('SEL2' , 0),
		('SEL1' , 0),
		('SEL0' , 0),
		('RNG' , 0),
		('BIP' , 0),
		('PD1' , 0),
		('PD0' , 0)
	])

def form_control_byte():
	global control_bits
	control_byte = 0x0
	for v in control_bits.values():
		control_byte <<= 1
		control_byte += v
		print(v, control_byte)
	return control_byte.to_bytes(1,'big')

while(1):
# for _ in range(3):
	print()
	print(enc_device1.read_counter())
	digipot_device.set_pot((abs(enc_device1.last_count) % 1024) / 1024)
	print(enc_device1.last_count)
	print(digipot_device.set_val)
	# max522_iterate()
	print(test_form_control_byte())
	sleep(1)
	






