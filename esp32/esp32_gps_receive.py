
#Receives GPS data over the ESP32 UART 
#and prints main GPS information: date, time, latitute, longitude

from machine import UART

from mini_micropyGPS import MicropyGPS

uart = UART(2, tx=17, rx=16)
uart.init(38400, bits=8, parity=None, stop=1)

# Instatntiate the micropyGPS object
my_gps = MicropyGPS()

# Continuous Tests for characters available in the UART buffer, any characters are feed into the GPS
# object. When enough char are feed to represent a whole, valid sentence, stat is set as the name of the
# sentence and printed
while True:
    if uart.any():
        c=int.from_bytes(uart.read(1), "big")
        stat = my_gps.update(chr(c)) # Note the conversion to to chr, UART outputs ints normally
        if stat:
            print(stat)
            stat = None
            print('UTC Timestamp:', my_gps.timestamp)
            print('Date:', my_gps.date_string('long'))
            print('Latitude:', my_gps.latitude_string())
            print('Longitude:', my_gps.longitude_string())
            print('Horizontal Dilution of Precision:', my_gps.hdop)
            print()
            new_data = False  # Clear the flag
