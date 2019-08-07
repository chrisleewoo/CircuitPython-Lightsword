"""
Prop-Maker based Light Up Prop.
Adafruit invests time and resources providing this open source code.
Please support Adafruit and open source hardware by purchasing
products from Adafruit!
Written by Kattni Rembor for Adafruit Industries
Copyright (c) 2019 Adafruit Industries
Licensed under the MIT license.
All text above must be included in any redistribution.
"""
import time
import random
import digitalio
import audioio
import busio
import board
import adafruit_rgbled
import adafruit_lis3dh
import neopixel
from analogio import AnalogIn

# CUSTOMISE COLORS HERE:
MAIN_COLOR = (90, 90, 0)  # Default is red
HIT_COLOR = (255, 255, 255)  # Default is white
RED_COLOR = (255, 0, 0)
ORANGE_COLOR = (255, 165, 0)
YELLOW_COLOR =  (255, 255, 0)
GREEN_COLOR = (0, 255, 0)
BLUE_COLOR = (0, 0, 255)
INDIGO_COLOR = (127, 0, 255)
VIOLET_COLOR = (255, 0, 255)

# CUSTOMISE SENSITIVITY HERE: smaller numbers = more sensitive to motion
HIT_THRESHOLD = 300
SWING_THRESHOLD = 125

OnOffBUTTON = digitalio.DigitalInOut(board.D4)
OnOffBUTTON.direction = digitalio.Direction.INPUT
OnOffBUTTON.pull = digitalio.Pull.UP

# Set to the length in seconds of the "on.wav" file
POWER_ON_SOUND_DURATION = 1.5

POWER_PIN = board.D10

enable = digitalio.DigitalInOut(POWER_PIN)
enable.direction = digitalio.Direction.OUTPUT
enable.value = False

# Pin the Red LED is connected to
RED_LED = board.D11

# Pin the Green LED is connected to
GREEN_LED = board.D12

# Pin the Blue LED is connected to
BLUE_LED = board.D13

# Create the RGB LED object
led = adafruit_rgbled.RGBLED(RED_LED, GREEN_LED, BLUE_LED)

audio = audioio.AudioOut(board.A0)  # Speaker

# Set up accelerometer on I2C bus, 4G range:
i2c = busio.I2C(board.SCL, board.SDA)
accel = adafruit_lis3dh.LIS3DH_I2C(i2c)
accel.range = adafruit_lis3dh.RANGE_4_G

COLOR_HIT = HIT_COLOR  # "hit" color is HIT_COLOR set above
COLOR_SWING = MAIN_COLOR  # "swing" color is MAIN_COLOR set above

pixel_pin = board.NEOPIXEL
num_pixels = 1
ORDER = neopixel.GRB
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER)

WheelPot = AnalogIn(board.A1)
print(WheelPot.value)

def get_wheel():
	wheelint = int( (WheelPot.value * 7) / 65536 )  # from 0 to 65535 because 16 bits
	return wheelint

def wheel_color():
	if get_wheel() == 0:
		return RED_COLOR
	if get_wheel() == 1:
		return ORANGE_COLOR
	if get_wheel() == 2:
		return YELLOW_COLOR
	if get_wheel() == 3:
		return GREEN_COLOR
	if get_wheel() == 4:
		return BLUE_COLOR
	if get_wheel() == 5:
		return INDIGO_COLOR
	if get_wheel() >= 6:
		return VIOLET_COLOR	

#print (get_wheel())

def play_wav(name, loop=False):
    """
    Play a WAV file in the 'sounds' directory.
    :param name: partial file name string, complete name will be built around
                 this, e.g. passing 'foo' will play file 'sounds/foo.wav'.
    :param loop: if True, sound will repeat indefinitely (until interrupted
                 by another sound).
    """
    print("playing", name)
    try:
        wave_file = open('sounds/' + name + '.wav', 'rb')
        wave = audioio.WaveFile(wave_file)
        audio.play(wave, loop=loop)
    except:  # pylint: disable=bare-except
        return


# List of swing wav files without the .wav in the name for use with play_wav()
swing_sounds = [
    'swing1',
    'swing2',
    'swing3',
    'swing4',
    'swing5',
    'swing6',
    'swing7',
]

# List of hit wav files without the .wav in the name for use with play_wav()
hit_sounds = [
    'hit1',
    'hit2',
    'hit3',
    'hit4',
    'hit5',
    'hit6',
    'hit7',
]

mode = 0  # Initial mode = OFF

pixels.fill(wheel_color())
pixels.show()

enable.value = True
play_wav('power')

# Main loop
while True:
    pixels.fill(wheel_color())
    pixels.show()
    time.sleep(.2)
    if mode == 0:  # If currently off...
        if OnOffBUTTON.value == False:
            enable.value = True
            play_wav('on')  # Power up!
            led.color = wheel_color()
            time.sleep(POWER_ON_SOUND_DURATION)
            play_wav('idle', loop=True)  # Play idle sound now
            mode = 1  # Idle mode

    elif mode >= 1:  # If not OFF mode...
        starthold = time.monotonic()
        while OnOffBUTTON.value == False:
            endhold = time.monotonic()
            if endhold - starthold >= 2:
                play_wav('poweroff')
                led.color = (0, 0, 0)
                mode = 0
        x, y, z = accel.acceleration  # Read accelerometer
        accel_total = x * x + z * z
        # (Y axis isn't needed, due to the orientation that the Prop-Maker
        # Wing is mounted.  Also, square root isn't needed, since we're
        # comparing thresholds...use squared values instead.)
        if accel_total > HIT_THRESHOLD:  # Large acceleration = HIT
            play_wav(random.choice(hit_sounds))  # Start playing 'hit' sound
            COLOR_ACTIVE = COLOR_HIT  # Set color to fade from
            mode = 3  # HIT mode
        elif mode == 1 and accel_total > SWING_THRESHOLD:  # Mild = SWING
            play_wav(random.choice(swing_sounds))  # Randomly choose from available swing sounds
            led.color = wheel_color()  # Set color to main color
            mode = 2  # SWING mode
        elif mode == 1:
            # Idle color
            led.color = wheel_color()
        elif mode > 1:  # If in SWING or HIT mode...
            if audio.playing:  # And sound currently playing...
                if mode == 2:  # If SWING,
                    led.color = wheel_color()
                else:
                    for v in range (10):
                            led.color = HIT_COLOR  # Set color to hit color
                            led.color = (0, 0, 0)
                            time.sleep(.05)
                    mode = 2
            else:  # No sound now, but still SWING or HIT modes
                play_wav('idle', loop=True)  # Resume idle sound
                mode = 1  # Return to idle mode
