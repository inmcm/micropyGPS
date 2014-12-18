from pyb import UART

# Setup the connection to your GPS here
# This example uses UART 3 with RX on pin Y10
# Baudrate is 9600bps, with the standard 8 bits, 1 stop bit, no parity
uart = UART(3, 9600)

# Basic UART --> terminal printer, use to test your GPS module
while True:
    if uart.any():
        print(chr(uart.readchar()), end='')


