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
   
   
### Usage

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
[Micropython]:https://micropython.org/
[NMEA-0183]:http://aprs.gids.nl/nmea/
[TinyGPS]:http://arduiniana.org/libraries/tinygps/ 