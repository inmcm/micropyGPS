# micropyGPS

### Overview

micropyGPS is a full featured GPS NMEA sentence parser for use with [MicroPython] and the PyBoard embedded
platform. It's also fully compatible with Python 3.x

Features:

 - Parses and verifies most of the important [NMEA-0183] output messages into easily handled data structures
 - Provides helper methods to interperate, present, and manipulate the GPS data
 - Written in pure Python 3.x using only the standard libraries available in Micropython
 - Implemented as a single class within a single file for easy integration into an embedded project
 - Parser written with a serial UART data source in mind; works on a single character at a time with
   robust error handling for noisy embedded environments
 - Modeled after the great [TinyGPS] Arduino library
   
   
### Basic Usage

micropyGPS is easy to use; copy micropyGPS.py into your project directory and import the MicropyGPS class. From
there, just create a new GPS object and start feeding it data. After you've feed it an entire valid sentence, it will return the sentence type and the internal values will be update. The example below shows the parsing of an RMC sentence and the object return a tuple with the current latitude data

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
The object will continue to accept new characters and parse sentences for as long as it exists. Running the script standalone will parse a number of example sentences and print the results demonstrating the variety of data tracked by the object

```sh
$ python micropyGPS.py
```
### Pyboard Usage

Test scripts are included to help get started with using micropyGPS on the [pyboard] platform. These scripts can be copied over to the pyboards internal memory or placed on the SD Card. Make sure to rename whichever script you're using to **main.py** when running them on the pyboard.

 - **uart_test.py** is a simple UART echo program to test if both your GPS is hooked up and UART is configured correctly. Some of the standard NMEA setences should print out once a second (or faster depending on your GPS update rate) if everything is OK
 - **sentence_test.py** will try and parse all incoming characters from the UART. This script requires micropyGPS.py be present in the same area of storage (SD Card or internal). Whenever a set of characters comprising a valid sentence is received and parsed, the script will print the type of sentence.

An example of how to hookup the pyboard to the Adafruit [Ultimate GPS Breakout] is shown below:

![hookup](http://i.imgur.com/yd4Mjka.jpg?1) 


[Micropython]:https://micropython.org/
[NMEA-0183]:http://aprs.gids.nl/nmea/
[TinyGPS]:http://arduiniana.org/libraries/tinygps/ 
[pyboard]:http://docs.micropython.org/en/latest/quickref.html
[Ultimate GPS Breakout]:http://www.adafruit.com/product/746