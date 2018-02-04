# micropyGPS

## Overview

micropyGPS is a full featured GPS NMEA sentence parser for use with [MicroPython] and the PyBoard embedded
platform. It's also fully compatible with Python 3.x

Features:

 - Parses and verifies most of the important [NMEA-0183] output messages into easily handled data structures
 - Provides helper methods to interpret, present, log, and manipulate the GPS data
 - Written in pure Python 3.x using only the standard libraries available in Micropython
 - Implemented as a single class within a single file for easy integration into an embedded project
 - Parser written with a serial UART data source in mind; works on a single character at a time with
   robust error handling for noisy embedded environments
 - Modeled after the great [TinyGPS] Arduino library
   
   
## Basic Usage

micropyGPS is easy to use: copy micropyGPS.py into your project directory and import the MicropyGPS class into your script. From
there, just create a new GPS object and start feeding it data using the ```update()``` method. After you've feed it an entire valid sentence, it will return the sentence type and the internal values will be updated. The example below shows the parsing of an RMC sentence and the object return a tuple with the current latitude data

```sh
>>> from micropyGPS import MicropyGPS
>>> my_gps = MicropyGPS()
>>> my_sentence = '$GPRMC,081836,A,3751.65,S,14507.36,E,000.0,360.0,130998,011.3,E*62'
>>> for x in my_sentence:
...     my_gps.update(x)
...
'GPRMC'
>>> my_gps.latitude
(37, 51.65, 'S')
```
The object will continue to accept new characters and parse sentences for as long as it exists. Running the ```tests.py``` script will parse a number of example sentences and print the results demonstrating the variety of data tracked by the object

```sh
$ python tests.py
```

### Currently Supported Sentences 

* GPRMC
* GLRMC
* GNRMC
* GPGLL
* GLGLL
* GPGGA
* GLGGA
* GNGGA
* GPVTG
* GLVTG
* GNVTG
* GPGSA
* GLGSA
* GPGSV
* GLGSV


### Position Data
Data successfully parsed from valid sentences is stored in easily accessible object variables. Data with multiple components (like latitude and longitude) is stored in tuples.
```sh
## Latitude is 37° 51.65' S
>>> my_gps.latitude
(37, 51.65, 'S')
# Longitude is 145° 7.36' E
>>> my_gps.longitude
(145, 7.36, 'E')
# Course is 54.7°
>>> my_gps.course
54.7
# Altitude is 280.2 meters
>>> my_gps.altitude
280.2
# Distance from ideal geoid is -34 meters
>>> my_gps.geoid_height
-34.0
```
Current speed is stored in a tuple of values representing knots, miles per hours and kilometers per hour
```sh
>>> my_gps.speed
(5.5, 6.3305, 10.186)
```

### Time and Date
The current UTC time is stored (hours,minutes,seconds)
```sh
>>> my_gps.timestamp
(8, 18, 36.0)
>>> my_gps.date
(22, 9, 05)
```
The timezone can be automatically adjusted for using the by setting the ```local_offset``` when you create the object or anytime after. Setting it to ```-5``` means you are on Eastern Standard time in the United States.
```sh
>>> my_gps = MicropyGPS(-5)
>>> my_gps.local_offset
-5
# Update With Timestamp Sentence Data...
>>> my_gps.timestamp
(3, 18, 36.0)
```

The current UTC date is stored (day,month,year). **NOTE:** The date is not currently adjusted to match the timezone set in ```local_offset```. 
```sh
>>> my_gps.date
(22, 9, 05)
```

### Satellite Data
Signal quality and individual satellite information is collected from GSV, GSA, and GGA sentences and made available in the following variables.
```sh
>>> my_gps.satellites_in_use
7
>>> my_gps.satellites_used
[7, 2, 26, 27, 9, 4, 15]
# Fix types can be: 1 = no fix, 2 = 2D fix, 3 = 3D fix
>>> my_gps.fix_type
3
# Dilution of Precision (DOP) values close to 1.0 indicate excellent quality position data
>>> my_gps.hdop  
1.0
>>> my_gps.vdop
1.5
>>> my_gps.pdop
1.8
```
 The ```satellite_data_updated()``` method should be check to be ```True``` before trying to read out individual satellite data. This ensures all related GSV sentences are parsed and satellite info is complete
```sh
>>> my_gps.satellite_data_updated()
True
# Satellite data is a dict where the key is the satellite number and the value pair is a tuple containing (Elevation, Azimuth, SNR (if available))
>>> my_gps.satellite_data 
{19: (5, 273, None), 32: (5, 303, None), 4: (22, 312, 26), 11: (9, 315, 16), 12: (19, 88, 23), 14: (64, 296, 22), 15: (2, 73, None), 18: (54, 114, 21), 51: (40, 212, None), 21: (16, 175, None), 22: (81, 349, 25), 24: (30, 47, 22), 25: (17, 127, 18), 31: (22, 204, None)}
# Returns just the satellite PRNs visible
>>> my_gps.satellites_visible()
[19, 32, 4, 11, 12, 14, 15, 18, 51, 21, 22, 24, 25, 31]
```

### GPS Statistics
While parsing sentences, the MicropyGPS object tracks the number of number of parsed sentences as well as the number of CRC failures. ```parsed_sentences``` are those sentences that passed the base sentence catcher with clean CRCs. ```clean_sentences``` refers to the number of sentences parsed by their specific function successfully.
```sh
>>> my_gps.parsed_sentences
14
>>> my_gps.clean_sentences
14
>>> my_gps.crc_fails
0
```
The amount of real time passed since the last sentence with valid fix data was parse is also made available. **NOTE:** On the pyBoard, this value is returned in milliseconds while on Unix/Windows it is returned in seconds.
```sh
# Assume running on pyBoard
>>> my_gps.time_since_fix()
3456
```

### Logging
micropyGPS currently can do very basic automatic logging of raw NMEA sentence data to a file. Any valid ASCII character passed into the parser, while the logging is enabled, is logged to a target file.  This is useful if processing GPS sentences, but want to save the collected data for archive or further analysis. Due to the relative size of the log files, it's highly recommended to use an SD card as your storage medium as opposed to the emulated memory on the STM32 micro. All logging methods return a boolean if the operation succeeded or not.
```sh
# Logging can be started at any time with the start_logging()
>>> my_gps.start_logging('log.txt')
True
# Arbitrary strings can be written into the log file with write_log() method
>>> my_gps.write_log('Some note for the log file')
True
# Stop logging and close the log file with stop_logging()
>>> my_gps.stop_logging()
True
```

### Prettier Printing
Several functions are included that allow for GPS data to be expressed in nicer formats than tuples and ints.
```sh
>>> my_gps.latitude_string()
"41° 24.8963' N"
>>> my_gps.longitude_string()
"81° 51.6838' W"
>>> my_gps.speed_string('kph')
'10.186 km/h'
>>> my_gps.speed_string('mph')
'6.3305 mph'
my_gps.speed_string('knot')
'5.5 knots'
# Nearest compass point based on current course
my_gps.compass_direction()
'NE'
>>> my_gps.date_string('long')
'September 13th, 2098'
# Note the correct century should be provided for GPS data taken in the 1900s
>>> my_gps.date_string('long','19')
'September 13th, 1998'
>>> my_gps.date_string('s_mdy')
'09/13/98'
>>> my_gps.date_string('s_dmy')
'13/09/98'
```
## Pyboard Usage

Test scripts are included to help get started with using micropyGPS on the [pyboard] platform. These scripts can be copied over to the pyboards internal memory or placed on the SD Card. Make sure, when running them on the pyboard, to rename script you're using to **main.py** or update **boot.py** with the name of script you wish to run.

 - **uart_test.py** is a simple UART echo program to test if both your GPS is hooked up and UART is configured correctly. Some of the standard NMEA sentences should print out once a second (or faster depending on your GPS update rate) if everything is OK
 - **sentence_test.py** will try and parse all incoming characters from the UART. This script requires micropyGPS.py be present in the same area of storage (SD Card or internal). Whenever a set of characters comprising a valid sentence is received and parsed, the script will print the type of sentence.
 - **GPIO_interrupt_updater.py** is an example of how to use external interrupt to trigger an update of GPS data. In this case, a periodic signal (1Hz GPS output) is attached to pin X8 causing a mass parsing event every second.

Adjusting the baud rate and update rate of the receiver can be easily accomplished with my companion [MTK_command] script

An example of how to hookup the pyboard to the Adafruit [Ultimate GPS Breakout] (minus the PPS signal needed in the external interrupt example) is shown below.

![hookup](http://i.imgur.com/yd4Mjka.jpg?1)

## ESP32
You can follow the setup instructions for the pyboard. The only difference is, that you shoud use micropyGPS as a [frozen module]. Otherwise there will be exceptions, because there is not enough heap space available.

## Other Platforms
As mentioned above, micropyGPS also runs on Python3.x (that's where most of the development was done!). This is useful for testing code or just parsing existing log files. 

Beyond the pyBoard and ESP32, micropyGPS should run on other embedded platforms that have an Python3 interpreter such as the Raspberry Pi and BeagleBone boards. These other devices are currently untested.

[Micropython]:https://micropython.org/
[frozen module]:https://learn.adafruit.com/micropython-basics-loading-modules/frozen-modules
[NMEA-0183]:http://aprs.gids.nl/nmea/
[TinyGPS]:http://arduiniana.org/libraries/tinygps/ 
[pyboard]:http://docs.micropython.org/en/latest/pyboard/pyboard/quickref.html
[MTK_command]:https://github.com/inmcm/MTK_commands
[Ultimate GPS Breakout]:http://www.adafruit.com/product/746
