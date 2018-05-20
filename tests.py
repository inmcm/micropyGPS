#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
tests.py
Tests for micropyGPS module
# Copyright (c) 2017 Michael Calvin McCoy (calvin.mccoy@gmail.com)
# MIT License (MIT) - see LICENSE file
"""

from micropyGPS import MicropyGPS

def run_tests():
    sentence_count = 0

    test_RMC = ['$GPRMC,081836,A,3751.65,S,14507.36,E,000.0,360.0,130998,011.3,E*62\n',
                '$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A\n',
                '$GPRMC,225446,A,4916.45,N,12311.12,W,000.5,054.7,191194,020.3,E*68\n',
                '$GPRMC,180041.896,A,3749.1851,N,08338.7891,W,001.9,154.9,240911,,,A*7A\n',
                '$GPRMC,180049.896,A,3749.1808,N,08338.7869,W,001.8,156.3,240911,,,A*70\n',
                '$GPRMC,092751.000,A,5321.6802,N,00630.3371,W,0.06,31.66,280511,,,A*45\n']

    test_VTG = ['$GPVTG,232.9,T,,M,002.3,N,004.3,K,A*01\n']
    test_GGA = ['$GPGGA,180050.896,3749.1802,N,08338.7865,W,1,07,1.1,397.4,M,-32.5,M,,0000*6C\n']
    test_GSA = ['$GPGSA,A,3,07,11,28,24,26,08,17,,,,,,2.0,1.1,1.7*37\n',
                '$GPGSA,A,3,07,02,26,27,09,04,15,,,,,,1.8,1.0,1.5*33\n']
    test_GSV = ['$GPGSV,3,1,12,28,72,355,39,01,52,063,33,17,51,272,44,08,46,184,38*74\n',
                '$GPGSV,3,2,12,24,42,058,33,11,34,053,33,07,20,171,40,20,15,116,*71\n',
                '$GPGSV,3,3,12,04,12,204,34,27,11,324,35,32,11,089,,26,10,264,40*7B\n',
                '$GPGSV,3,1,11,03,03,111,00,04,15,270,00,06,01,010,00,13,06,292,00*74\n',
                '$GPGSV,3,2,11,14,25,170,00,16,57,208,39,18,67,296,40,19,40,246,00*74\n',
                '$GPGSV,3,3,11,22,42,067,42,24,14,311,43,27,05,244,00,,,,*4D\n',
                '$GPGSV,4,1,14,22,81,349,25,14,64,296,22,18,54,114,21,51,40,212,*7D\n',
                '$GPGSV,4,2,14,24,30,047,22,04,22,312,26,31,22,204,,12,19,088,23*72\n',
                '$GPGSV,4,3,14,25,17,127,18,21,16,175,,11,09,315,16,19,05,273,*72\n',
                '$GPGSV,4,4,14,32,05,303,,15,02,073,*7A\n']
    test_GLL = ['$GPGLL,3711.0942,N,08671.4472,W,000812.000,A,A*46\n',
                '$GPGLL,4916.45,N,12311.12,W,225444,A,*1D\n',
                '$GPGLL,4250.5589,S,14718.5084,E,092204.999,A*2D\n',
                '$GPGLL,0000.0000,N,00000.0000,E,235947.000,V*2D\n']

    my_gps = MicropyGPS()
    my_gps.start_logging('test.txt', mode="new")
    my_gps.write_log('micropyGPS test log\n')
    sentence = ''
    for RMC_sentence in test_RMC:
        sentence_count += 1
        for y in RMC_sentence:
            sentence = my_gps.update(y)
            if sentence:
                break
        print('Parsed a', sentence, 'Sentence')
        print('Parsed Strings:', my_gps.gps_segments)
        print('Sentence CRC Value:', hex(my_gps.crc_xor))
        print('Longitude:', my_gps.longitude)
        print('Latitude', my_gps.latitude)
        print('UTC Timestamp:', my_gps.timestamp)
        print('Speed:', my_gps.speed)
        print('Date Stamp:', my_gps.date)
        print('Course', my_gps.course)
        print('Data is Valid:', my_gps.valid)
        print('Compass Direction:', my_gps.compass_direction())
        print('')

    for GLL_sentence in test_GLL:
        sentence_count += 1
        for y in GLL_sentence:
            sentence = my_gps.update(y)
            if sentence:
                break
        print('Parsed a', sentence, 'Sentence')
        print('Parsed Strings', my_gps.gps_segments)
        print('Sentence CRC Value:', hex(my_gps.crc_xor))
        print('Longitude:', my_gps.longitude)
        print('Latitude', my_gps.latitude)
        print('UTC Timestamp:', my_gps.timestamp)
        print('Data is Valid:', my_gps.valid)
        print('')

    for VTG_sentence in test_VTG:
        sentence_count += 1
        for y in VTG_sentence:
            sentence = my_gps.update(y)
            if sentence:
                break
        print('Parsed a', sentence, 'Sentence')
        print('Parsed Strings', my_gps.gps_segments)
        print('Sentence CRC Value:', hex(my_gps.crc_xor))
        print('Speed:', my_gps.speed)
        print('Course', my_gps.course)
        print('Compass Direction:', my_gps.compass_direction())
        print('')

    for GGA_sentence in test_GGA:
        sentence_count += 1
        for y in GGA_sentence:
            sentence = my_gps.update(y)
            if sentence:
                break
        print('Parsed a', sentence, 'Sentence')
        print('Parsed Strings', my_gps.gps_segments)
        print('Sentence CRC Value:', hex(my_gps.crc_xor))
        print('Longitude', my_gps.longitude)
        print('Latitude', my_gps.latitude)
        print('UTC Timestamp:', my_gps.timestamp)
        print('Fix Status:', my_gps.fix_stat)
        print('Altitude:', my_gps.altitude)
        print('Height Above Geoid:', my_gps.geoid_height)
        print('Horizontal Dilution of Precision:', my_gps.hdop)
        print('Satellites in Use by Receiver:', my_gps.satellites_in_use)
        print('')

    for GSA_sentence in test_GSA:
        sentence_count += 1
        for y in GSA_sentence:
            sentence = my_gps.update(y)
            if sentence:
                break
        print('Parsed a', sentence, 'Sentence')
        print('Parsed Strings', my_gps.gps_segments)
        print('Sentence CRC Value:', hex(my_gps.crc_xor))
        print('Satellites Used', my_gps.satellites_used)
        print('Fix Type Code:', my_gps.fix_type)
        print('Horizontal Dilution of Precision:', my_gps.hdop)
        print('Vertical Dilution of Precision:', my_gps.vdop)
        print('Position Dilution of Precision:', my_gps.pdop)
        print('')

    for GSV_sentence in test_GSV:
        sentence_count += 1
        for y in GSV_sentence:
            sentence = my_gps.update(y)
            if sentence:
                break
        print('Parsed a', sentence, 'Sentence')
        print('Parsed Strings', my_gps.gps_segments)
        print('Sentence CRC Value:', hex(my_gps.crc_xor))
        print('SV Sentences Parsed', my_gps.last_sv_sentence)
        print('SV Sentences in Total', my_gps.total_sv_sentences)
        print('# of Satellites in View:', my_gps.satellites_in_view)
        data_valid = my_gps.satellite_data_updated()
        print('Is Satellite Data Valid?:', data_valid)
        if data_valid:
            print('Satellite Data:', my_gps.satellite_data)
            print('Satellites Visible:', my_gps.satellites_visible())
        print('')

    print("Pretty Print Examples:")
    print('Latitude:', my_gps.latitude_string())
    print('Longitude:', my_gps.longitude_string())
    print('Speed:', my_gps.speed_string('kph'), 'or', my_gps.speed_string('mph'), 'or', my_gps.speed_string('knot'))
    print('Date (Long Format):', my_gps.date_string('long'))
    print('Date (Short D/M/Y Format):', my_gps.date_string('s_dmy'))
    print('Date (Short M/D/Y Format):', my_gps.date_string('s_mdy'))
    print()

    print('### Final Results ###')
    print('Sentences Attempted:', sentence_count)
    print('Sentences Found:', my_gps.clean_sentences)
    print('Sentences Parsed:', my_gps.parsed_sentences)
    print('CRC_Fails:', my_gps.crc_fails)

import unittest

class TestMicroPyGPS(unittest.TestCase):

    def test_smoke(self):
        try:
            run_tests()
        except:
            self.fail("smoke test raised exception")

if __name__ == "__main__":
    run_tests()
