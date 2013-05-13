pyLCD – A library for controlling LCDs on various hardware backends
===================================================================
The instructions and tips below are for HD44780 compatible character LCDs. Using KS0108 compatible graphical LCDs is basically the same, only with different pin names and function names.

License
-------
This program is licensed under the AGPLv3. See the `LICENSE` file for more information.

Installation
------------
You can easily install the pyLCD lib using the Python Package Index. Just type:

	sudo pip install pylcd

Hardware support
----------------
This library supports multiple hardware platforms for input and output.

Currently available output backends:
* Velleman K8055 USB Experiment Interface Board
* Raspberry Pi GPIO pins
* Arduino pins using serial communication (Still in development)
* Debug output showing the states of the interface pins
* Dummy output that does nothing

Currently available input backends:
* System standard input (e.g. Keyboard)
* Raspberry Pi GPIO pins
* No input

See the usage examples below for examples on how to use them.

Output pinmaps
--------------
When instantiating a display, you need to pass it a dictionary containing a mapping from pin names on the LCD to output numbers on the device you're connecting the LCD to.
For a K8055, you might want to use this pinmap:

```python
PINMAP = {
	'RS': 1,
	'RW': 2,
	'E': 3,
	'D4': 4,
	'D5': 5,
	'D6': 6,
	'D7': 7,
	'LED': 9,
}
```

Note that the backlight LED pin is numbered 9 here, even though the K8055 only has 8 digital outputs. But since there are two additional analog outputs, I numbered them 9 and 10 to avoid confusion.
Using an analog output for backlight control enables you to dim the backlight by using PWM!

For a Raspberry Pi, you need to use WiringPi's `WPI_MODE_GPIO` pin numbering scheme. I connected my LCD as follows:

```python
PINMAP = {
	'RS': 2,
	'RW': 3,
	'E': 4,
	'D4': 22,
	'D5': 10,
	'D6': 9,
	'D7': 11,
	'LED': 18,
}
```

By using pin 18 for the backlight control, it's once again possible to dim the backlight since this pin is the only available hardware PWM pin of the Pi, so I recommend using this one.
If you are using the `DebugBackend` backend, the pin numbers don't matter.

Input pinmaps
-------------
If you are using an input module that uses I/O pins, you need to specify a pinmap for that module as well.
Currently, only five keys are supported: Up, Left, OK, Right and Down, as well as two LEDs: Ready and Error.
My pinmap looks like this:

```python
INPUT_PINMAP = {
	'UP': 23,
	'LEFT': 7,
	'OK': 8,
	'RIGHT': 24,
	'DOWN': 25,
	'READY': 27,
	'ERROR': 22,
}
```

Character maps
--------------
You can also specify a character map to use for defining custom characters. This is a dictionary in the following format:

```python
CHARMAP = {
	0: (
		0b10101,
		0b01010,
		0b10101,
		0b01010,
		0b10101,
		0b01010,
		0b10101,
		0b01010,
	),
}
```

The keys should be integers from 0 to 7, since the HD44780 can store up to 8 custom characters.
The values should be tuples or lists of 8 integers, where each integer represents a line of the custom character. I recommend writing these integers in binary notation, since it's easy to see which pixels will be active and which won't if you do it this way.

You can also specify a single key, `dir`, to load custom characters from image files:

```python
CHARMAP = {
	'dir': "/path/to/directory",
}
```

The specified directory should contain up to 8 image files (preferably in PNG format) numbered `0.<suffix>` to `7.<suffix>`. Each of these files must be 5 pixels wide and 8 pixels tall and should consist of black and white pixels, where a black pixel will translate into an active pixel on the display.
To use this feature, you need to have the Python Imaging Library (PIL) installed.

User Interface
--------------
This library comes with a `DisplayUI` class which allows you to create simple text-based user interfaces with just a few lines of code!
See the usage examples below. Have a look at the `lcd.py` file to see what is possible.

Usage examples
--------------
To initialize a standard 16x2 character LCD with a blinking cursor on a Raspberry Pi, you would do:

```python
import hd44780
PINMAP = {} # Your pinmap here
display = hd44780.Display(backend = hd44780.GPIOBackend, pinmap = PINMAP, lines = 2, columns = 16)
display.set_display_enable(cursor = True, cursor_blink = True)
display.clear()
display.home()
```

To display a Yes / No dialog and react to the user's choice on said display, using physical keys attached to the Pi, do the following:

```python
INPUT_PINMAP = {} # Your pinmap here
ui = hd44780.DisplayUI(display, hd44780.GPIOInput, input_kwargs = {'pinmap': INPUT_PINMAP})
selected_index, selected_text = ui.dialog("Proceed?", buttons = ("Yes", "No"))
if selected_index == 0:
	ui.message("Doing stuff...")
else:
	ui.message("Aborted.")
```

Note that if you are using the `SystemInput` input backend you need to be able to send keypresses to the terminal running the script, or else it won't be able to react to your input.
For more examples I would suggest looking at the included example scripts.
