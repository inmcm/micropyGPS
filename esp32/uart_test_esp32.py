#This program shows raw GPS messages received over the serial port, just to check if the data reception is ok.
#You may have to adjust the speed, according with your GPS: for example: 4800, 9600, 19200...

from machine import UART

uart = UART(2, tx=17, rx=16)
uart.init(38400, bits=8, parity=None, stop=1)

while True:
    data = uart.read(1)

    if data is not None:
        # Show the byte as 2 hex digits then in the default way
        #print("%02x " % (data[0]), end='')
        # Or, show the string as received
        print("%c" % (data[0]), end='')
