# RP2040 Single Board Computer

Examples and various testing functions in diagnostics.py

## Instantiate SBC:<br/>
	from sbc import SBC
	lab = SBC()
	or
	lab = SBC(i2c = i2c_bus)

	* either pass a i2c bus, or SBC class will start its own i2c bus on GP16 and GP17

## Teardown SBC:<br/>
	lab.deinit()
	
	VERY STRONGLY SUGGESTED TO IMPLEMENT:
	import atexit
	def exit_program():
		lab.deinit()
	atexit.register(exit_program)

	If you don't do this, you may have an interesting time.

## Motors:<br/>
	Must be instantiated by user.
	Returns lab.mot1 or lab.mot2

	use motors with in1 / in2 as pwm, and en digital
		lab._init_mot1_pwm()
		lab._init_mot2_pwm()

	use motors with in1 / in2 as digital, and en pwm
		lab._init_mot1_dig()
		lab._init_mot2_dig()

		* Can also be used in 2pin mode with in1 (pwm) and in2 (digital) by
		instantiating directly through L298N_dig class in mot.py.
		PWMOut and DigitalOut must be established externally and passed in.


	Examples using mot1:
		lab.mot1.min_bias = x	# DC bias, where x is [-1,1]; default to 0
		lab.mot1.off()		# disable en
		lab.mot1.free_spin()	# free spin
		lab.mot1.brake()	# brake
		lab.mot1.set_w(speed)	# where 'speed' is [-1,1]; default to 0
		lab.mot1.last_w		# returns last speed set.

## AD5293 Digital Pot:<br/>
	Insantiated automatically by SBC class:
		lab._digipot_device
	
	Examples:
		lab._digipot_device.set_pot(val)	# Set digital pot, val [-1,1]


## MAX522 Digital to Analog:
	Insantiated automatically by SBC class:
		lab._dac_device

	Examples:
		'val' in the following examples shall be [0,1]

		lab._dac_device.set_dac_all(val)	# Set both channels
		lab._dac_device.set_dac_A(val)		# Set chA
		lab._dac_device.set_dac_B(val)		# Set chB
		lab._dac_device.shutdown_all()		# Shutdown both channels
		lab._dac_device.shutdown_A()		# Shutdown chA
		lab._dac_device.shutdown_B()		# Shutdown chB
		lab._dac_device.activate()		# Turn it all back on after shutdown

## MAX1270 Analog to Digital:
	Insantiated automatically by SBC class:
		lab._adc_device
	
	Examples:
		'channel' in the following examples shall be [0,7]; default channel 0

		lab._adc_device.default_channel = channel	# Set a default channel; default 0
		lab._adc_device.bipolar	= 0		# 0 unipolar, 1 bipolar; default 0
		lab._adc_device.range = 0		# 0 5V range, 1 10V range; default 0
		lab._adc_device.read(channel)		# Returns reading as normalized [-1,1]
		lab._adc_device.read_volts(channel)	# Returns reading in Volts
		lab._adc_device.last_values		# Returns dictionary of the last reading on
								each channel; normalized [-1,1]
								ie last_values[0] for ch0


## LS7366 encoder counters 1 and 2:
	Insantiated automatically by SBC class:
		lab._enc_device1
		lab._enc_device2

	Examples using encoder 1:
		lab._enc_device1.read_counter()		# Pull latest count from the device
		lab._enc_device1.last_count		# Returns the last count
		lab._enc_device1.pause()		# Pause encoder counting
		lab._enc_device1.resume()		# Resume encoder counting

		* There is significantly more functionality available on this device.
		Count range. How to handle rollover. Half / Full Quadrature.
		And more!
		These are all implemented in the LS7366 class, but their explanation is beyond
		the scope of this quick setup guide. Check comments in the LS7366 class and datasheet.




![picture](https://github.com/pmmccorkell-usna/rp2040-sbc/blob/main/media/oscope.jpg)
