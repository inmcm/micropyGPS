# micropyGPS Sentence Test
# When properly connected to working GPS module,
# will print the names of the sentences it receives
# If you are having issues receiving sentences, use UART_test.py to ensure
# your UART is hooked up and configured correctly

from pyb import UART
from micropyGPS import MicropyGPS

# Setup the connection to your GPS here
# This example uses UART 3 with RX on pin Y10
# Baudrate is 9600bps, with the standard 8 bits, 1 stop bit, no parity
uart = UART(3, 9600)

# Instatntiate the micropyGPS object
my_gps = MicropyGPS()

# Continuous Tests for characters available in the UART buffer, any characters are feed into the GPS
# object. When enough char are feed to represent a whole, valid sentence, stat is set as the name of the
# sentence and printed
while True:
    if uart.any():
        stat = my_gps.update(chr(uart.readchar())) # Note the conversion to to chr, UART outputs ints normally
        if stat:
            print(stat)
            stat = None
