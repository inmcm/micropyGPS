from pyb import UART
from micropyGPS import MicropyGPS

uart = UART(3, 9600)

# Basic UART --> terminal printer, use to test your GPS module
# while True:
#     if uart.any():
#         print(chr(uart.readchar()), end='')


my_gps = MicropyGPS()

sentence_count = 0
while True:
    if uart.any():
        stat = my_gps.update(chr(uart.readchar()))
        if stat:
            print(stat)
            stat = None
            sentence_count += 1
    if sentence_count == 300:
        break;    


print('Sentences Found:', my_gps.clean_sentences)
print('Sentences Parsed:', my_gps.parsed_sentences)
print('CRC_Fails:', my_gps.crc_fails)

