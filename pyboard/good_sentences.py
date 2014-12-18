from pyb import UART
from micropyGPS import MicropyGPS

uart = UART(3, 9600)

my_gps = MicropyGPS()


# Reads 300 sentences and reports how many were parsed and if any failed the CRC check
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

