#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
tests.py
Tests for micropyGPS module
# Copyright (c) 2018 Michael Calvin McCoy (calvin.mccoy@protonmail.com)
# MIT License (MIT) - see LICENSE file
"""
import hashlib
from micropyGPS import MicropyGPS
from micropyGPS import LONG, L_YMD, S_DMY, S_MDY
from micropyGPS import S_HMS
from micropyGPS import MPH, KPH, KNOT
from micropyGPS import DD, DMS


test_RMC = [
    "$GPRMC,081836,A,3751.65,S,14507.36,E,000.0,360.0,130998,011.3,E*62\n",
    "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A\n",
    "$GPRMC,225446,A,4916.45,N,12311.12,W,000.5,054.7,191194,020.3,E*68\n",
    "$GPRMC,180041.896,A,3749.1851,N,08338.7891,W,001.9,154.9,240911,,,A*7A\n",
    "$GPRMC,180049.896,A,3749.1808,N,08338.7869,W,001.8,156.3,240911,,,A*70\n",
    "$GPRMC,092751.000,A,5321.6802,N,00630.3371,W,0.06,31.66,280511,,,A*45\n",
    "$GPRMC,193448.00,A,3746.2622056,N,12224.1897266,W,0.01,,041218,,,D*58\n",
    "$GPRMC,193449.00,A,3746.2622284,N,12224.1897308,W,0.01,,041218,,,D*5D\n",
    "$GPRMC,193449.00,A,3746.2622284,N,12224.1897308,W,1.00,,041218,,,D*5D\n",
]
rmc_parsed_strings = [
    [
        "GPRMC",
        "081836",
        "A",
        "3751.65",
        "S",
        "14507.36",
        "E",
        "000.0",
        "360.0",
        "130998",
        "011.3",
        "E",
        "62",
    ],
    [
        "GPRMC",
        "123519",
        "A",
        "4807.038",
        "N",
        "01131.000",
        "E",
        "022.4",
        "084.4",
        "230394",
        "003.1",
        "W",
        "6A",
    ],
    [
        "GPRMC",
        "225446",
        "A",
        "4916.45",
        "N",
        "12311.12",
        "W",
        "000.5",
        "054.7",
        "191194",
        "020.3",
        "E",
        "68",
    ],
    [
        "GPRMC",
        "180041.896",
        "A",
        "3749.1851",
        "N",
        "08338.7891",
        "W",
        "001.9",
        "154.9",
        "240911",
        "",
        "",
        "A",
        "7A",
    ],
    [
        "GPRMC",
        "180049.896",
        "A",
        "3749.1808",
        "N",
        "08338.7869",
        "W",
        "001.8",
        "156.3",
        "240911",
        "",
        "",
        "A",
        "70",
    ],
    [
        "GPRMC",
        "092751.000",
        "A",
        "5321.6802",
        "N",
        "00630.3371",
        "W",
        "0.06",
        "31.66",
        "280511",
        "",
        "",
        "A",
        "45",
    ],
    [
        "GPRMC",
        "193448.00",
        "A",
        "3746.2622056",
        "N",
        "12224.1897266",
        "W",
        "0.01",
        "",
        "041218",
        "",
        "",
        "D",
        "58",
    ],
    [
        "GPRMC",
        "193449.00",
        "A",
        "3746.2622284",
        "N",
        "12224.1897308",
        "W",
        "0.01",
        "",
        "041218",
        "",
        "",
        "D",
        "5D",
    ],
    [
        "GPRMC",
        "193449.00",
        "A",
        "3746.2622284",
        "N",
        "12224.1897308",
        "W",
        "1.00",
        "",
        "041218",
        "",
        "",
        "D",
        "5D",
    ],
]
rmc_crc_values = [0x62, 0x6A, 0x68, 0x7A, 0x70, 0x45, 0x58, 0x5D, 0x5D]
rmc_longitude = [
    [145, 7.36, "E"],
    [11, 31.0, "E"],
    [123, 11.12, "W"],
    [83, 38.7891, "W"],
    [83, 38.7869, "W"],
    [6, 30.3371, "W"],
    [122, 24.1897266, "W"],
    [122, 24.1897308, "W"],
    [122, 24.1897308, "W"],
]
rmc_latitude = [
    [37, 51.65, "S"],
    [48, 7.038, "N"],
    [49, 16.45, "N"],
    [37, 49.1851, "N"],
    [37, 49.1808, "N"],
    [53, 21.6802, "N"],
    [37, 46.2622056, "N"],
    [37, 46.2622284, "N"],
    [37, 46.2622284, "N"],
]

rmc_utc = [
    [8, 18, 36.0],
    [12, 35, 19.0],
    [22, 54, 46.0],
    [18, 0, 41.896],
    [18, 0, 49.896],
    [9, 27, 51.0],
    [19, 34, 48.0],
    [19, 34, 49.0],
    [19, 34, 49.0],
]
rmc_speed = [
    [0.0, 0.0, 0.0],
    [22.4, 25.7824, 41.4848],
    [0.5, 0.5755, 0.926],
    [1.9, 2.1869, 3.5188],
    [1.8, 2.0718, 3.3336],
    [0.06, 0.06906, 0.11112],
    [0.01, 0.011510000000000001, 0.018520000000000002],
    [0.01, 0.011510000000000001, 0.018520000000000002],
    [1.00, 1.1510000000000001, 1.8520000000000002],
]
rmc_date = [
    [13, 9, 98],
    [23, 3, 94],
    [19, 11, 94],
    [24, 9, 11],
    [24, 9, 11],
    [28, 5, 11],
    [4, 12, 18],
    [4, 12, 18],
    [4, 12, 18],
]
rmc_course = [360.0, 84.4, 54.7, 154.9, 156.3, 31.66, 0.0, 0.0, 0.0]
rmc_compass = ["N", "E", "NE", "SSE", "SSE", "NNE", "N", "N", "N"]

test_VTG = ["$GPVTG,232.9,T,,M,002.3,N,004.3,K,A*01\n"]

test_GGA = [
    "$GPGGA,180126.905,4254.931,N,07702.496,W,0,00,,,M,,M,,*54\n",
    "$GPGGA,181433.343,4054.931,N,07502.498,W,0,00,,,M,,M,,*52\n",
    "$GPGGA,180050.896,3749.1802,N,08338.7865,W,1,07,1.1,397.4,M,-32.5,M,,0000*6C\n",
    "$GPGGA,172814.0,3723.46587704,N,12202.26957864,W,2,6,1.2,18.893,M,-25.669,M,2.0,0031*4F\n",
]
gga_parsed_strings = [
    [
        "GPGGA",
        "180126.905",
        "4254.931",
        "N",
        "07702.496",
        "W",
        "0",
        "00",
        "",
        "",
        "M",
        "",
        "M",
        "",
        "",
        "54",
    ],
    [
        "GPGGA",
        "181433.343",
        "4054.931",
        "N",
        "07502.498",
        "W",
        "0",
        "00",
        "",
        "",
        "M",
        "",
        "M",
        "",
        "",
        "52",
    ],
    [
        "GPGGA",
        "180050.896",
        "3749.1802",
        "N",
        "08338.7865",
        "W",
        "1",
        "07",
        "1.1",
        "397.4",
        "M",
        "-32.5",
        "M",
        "",
        "0000",
        "6C",
    ],
    [
        "GPGGA",
        "172814.0",
        "3723.46587704",
        "N",
        "12202.26957864",
        "W",
        "2",
        "6",
        "1.2",
        "18.893",
        "M",
        "-25.669",
        "M",
        "2.0",
        "0031",
        "4F",
    ],
]
gga_latitudes = [
    [0, 0.0, "N"],
    [0, 0.0, "N"],
    [37, 49.1802, "N"],
    [37, 23.46587704, "N"],
]
gga_longitudes = [
    [0, 0.0, "W"],
    [0, 0.0, "W"],
    [83, 38.7865, "W"],
    [122, 2.26957864, "W"],
]
gga_fixes = [0, 0, 1, 2]
gga_timestamps = [[18, 1, 26.905], [18, 14, 33.343], [18, 0, 50.896], [17, 28, 14.0]]
gga_hdops = [0.0, 0.0, 1.1, 1.2]
gga_altitudes = [0.0, 0.0, 397.4, 18.893]
gga_satellites_in_uses = [0, 0, 7, 6]
gga_geoid_heights = [0.0, 0.0, -32.5, -25.669]
gga_crc_xors = [84, 82, 108, 79]

test_GSA = [
    "$GPGSA,A,3,07,11,28,24,26,08,17,,,,,,2.0,1.1,1.7*37\n",
    "$GPGSA,A,3,07,02,26,27,09,04,15,,,,,,1.8,1.0,1.5*33\n",
]
gsa_parsed_strings = [
    [
        "GPGSA",
        "A",
        "3",
        "07",
        "11",
        "28",
        "24",
        "26",
        "08",
        "17",
        "",
        "",
        "",
        "",
        "",
        "2.0",
        "1.1",
        "1.7",
        "37",
    ],
    [
        "GPGSA",
        "A",
        "3",
        "07",
        "02",
        "26",
        "27",
        "09",
        "04",
        "15",
        "",
        "",
        "",
        "",
        "",
        "1.8",
        "1.0",
        "1.5",
        "33",
    ],
]
gsa_crc_values = [0x37, 0x33]
gsa_sats_used = [[7, 11, 28, 24, 26, 8, 17], [7, 2, 26, 27, 9, 4, 15]]
gsa_hdop = [1.1, 1.0]
gsa_vdop = [1.7, 1.5]
gsa_pdop = [2.0, 1.8]
test_GSV = [
    "$GPGSV,3,1,12,28,72,355,39,01,52,063,33,17,51,272,44,08,46,184,38*74\n",
    "$GPGSV,3,2,12,24,42,058,33,11,34,053,33,07,20,171,40,20,15,116,*71\n",
    "$GPGSV,3,3,12,04,12,204,34,27,11,324,35,32,11,089,,26,10,264,40*7B\n",
    "$GPGSV,3,1,11,03,03,111,00,04,15,270,00,06,01,010,00,13,06,292,00*74\n",
    "$GPGSV,3,2,11,14,25,170,00,16,57,208,39,18,67,296,40,19,40,246,00*74\n",
    "$GPGSV,3,3,11,22,42,067,42,24,14,311,43,27,05,244,00,,,,*4D\n",
    "$GPGSV,4,1,14,22,81,349,25,14,64,296,22,18,54,114,21,51,40,212,*7D\n",
    "$GPGSV,4,2,14,24,30,047,22,04,22,312,26,31,22,204,,12,19,088,23*72\n",
    "$GPGSV,4,3,14,25,17,127,18,21,16,175,,11,09,315,16,19,05,273,*72\n",
    "$GPGSV,4,4,14,32,05,303,,15,02,073,*7A\n",
    "$GPGSV,3,1,12,13,65,002,50,02,61,098,47,39,60,352,,05,56,183,49*70\n",
    "$GPGSV,3,2,12,15,35,325,50,29,32,229,49,06,25,070,44,30,16,096,38*70\n",
    "$GPGSV,3,3,12,19,08,022,35,07,07,122,,12,06,316,49,25,03,278,36*7D\n",
]
gsv_parsed_string = [
    [
        "GPGSV",
        "3",
        "1",
        "12",
        "28",
        "72",
        "355",
        "39",
        "01",
        "52",
        "063",
        "33",
        "17",
        "51",
        "272",
        "44",
        "08",
        "46",
        "184",
        "38",
        "74",
    ],
    [
        "GPGSV",
        "3",
        "2",
        "12",
        "24",
        "42",
        "058",
        "33",
        "11",
        "34",
        "053",
        "33",
        "07",
        "20",
        "171",
        "40",
        "20",
        "15",
        "116",
        "",
        "71",
    ],
    [
        "GPGSV",
        "3",
        "3",
        "12",
        "04",
        "12",
        "204",
        "34",
        "27",
        "11",
        "324",
        "35",
        "32",
        "11",
        "089",
        "",
        "26",
        "10",
        "264",
        "40",
        "7B",
    ],
    [
        "GPGSV",
        "3",
        "1",
        "11",
        "03",
        "03",
        "111",
        "00",
        "04",
        "15",
        "270",
        "00",
        "06",
        "01",
        "010",
        "00",
        "13",
        "06",
        "292",
        "00",
        "74",
    ],
    [
        "GPGSV",
        "3",
        "2",
        "11",
        "14",
        "25",
        "170",
        "00",
        "16",
        "57",
        "208",
        "39",
        "18",
        "67",
        "296",
        "40",
        "19",
        "40",
        "246",
        "00",
        "74",
    ],
    [
        "GPGSV",
        "3",
        "3",
        "11",
        "22",
        "42",
        "067",
        "42",
        "24",
        "14",
        "311",
        "43",
        "27",
        "05",
        "244",
        "00",
        "",
        "",
        "",
        "",
        "4D",
    ],
    [
        "GPGSV",
        "4",
        "1",
        "14",
        "22",
        "81",
        "349",
        "25",
        "14",
        "64",
        "296",
        "22",
        "18",
        "54",
        "114",
        "21",
        "51",
        "40",
        "212",
        "",
        "7D",
    ],
    [
        "GPGSV",
        "4",
        "2",
        "14",
        "24",
        "30",
        "047",
        "22",
        "04",
        "22",
        "312",
        "26",
        "31",
        "22",
        "204",
        "",
        "12",
        "19",
        "088",
        "23",
        "72",
    ],
    [
        "GPGSV",
        "4",
        "3",
        "14",
        "25",
        "17",
        "127",
        "18",
        "21",
        "16",
        "175",
        "",
        "11",
        "09",
        "315",
        "16",
        "19",
        "05",
        "273",
        "",
        "72",
    ],
    ["GPGSV", "4", "4", "14", "32", "05", "303", "", "15", "02", "073", "", "7A"],
    [
        "GPGSV",
        "3",
        "1",
        "12",
        "13",
        "65",
        "002",
        "50",
        "02",
        "61",
        "098",
        "47",
        "39",
        "60",
        "352",
        "",
        "05",
        "56",
        "183",
        "49",
        "70",
    ],
    [
        "GPGSV",
        "3",
        "2",
        "12",
        "15",
        "35",
        "325",
        "50",
        "29",
        "32",
        "229",
        "49",
        "06",
        "25",
        "070",
        "44",
        "30",
        "16",
        "096",
        "38",
        "70",
    ],
    [
        "GPGSV",
        "3",
        "3",
        "12",
        "19",
        "08",
        "022",
        "35",
        "07",
        "07",
        "122",
        "",
        "12",
        "06",
        "316",
        "49",
        "25",
        "03",
        "278",
        "36",
        "7D",
    ],
]
gsv_crc_values = [
    0x74,
    0x71,
    0x7B,
    0x74,
    0x74,
    0x4D,
    0x7D,
    0x72,
    0x72,
    0x7A,
    0x70,
    0x70,
    0x7D,
]
gsv_sv_setence = [1, 2, 3, 1, 2, 3, 1, 2, 3, 4, 1, 2, 3]
gsv_total_sentence = [3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 3, 3, 3]
gsv_num_sats_in_view = [12, 12, 12, 11, 11, 11, 14, 14, 14, 14, 12, 12, 12]
gsv_data_valid = [
    False,
    False,
    True,
    False,
    False,
    True,
    False,
    False,
    False,
    True,
    False,
    False,
    True,
]
gsv_sat_data = [
    {28: (72, 355, 39), 1: (52, 63, 33), 17: (51, 272, 44), 8: (46, 184, 38)},
    {
        28: (72, 355, 39),
        1: (52, 63, 33),
        17: (51, 272, 44),
        8: (46, 184, 38),
        24: (42, 58, 33),
        11: (34, 53, 33),
        7: (20, 171, 40),
        20: (15, 116, None),
    },
    {
        28: (72, 355, 39),
        1: (52, 63, 33),
        17: (51, 272, 44),
        8: (46, 184, 38),
        24: (42, 58, 33),
        11: (34, 53, 33),
        7: (20, 171, 40),
        20: (15, 116, None),
        4: (12, 204, 34),
        27: (11, 324, 35),
        32: (11, 89, None),
        26: (10, 264, 40),
    },
    {3: (3, 111, 0), 4: (15, 270, 0), 6: (1, 10, 0), 13: (6, 292, 0)},
    {
        3: (3, 111, 0),
        4: (15, 270, 0),
        6: (1, 10, 0),
        13: (6, 292, 0),
        14: (25, 170, 0),
        16: (57, 208, 39),
        18: (67, 296, 40),
        19: (40, 246, 0),
    },
    {
        3: (3, 111, 0),
        4: (15, 270, 0),
        6: (1, 10, 0),
        13: (6, 292, 0),
        14: (25, 170, 0),
        16: (57, 208, 39),
        18: (67, 296, 40),
        19: (40, 246, 0),
        22: (42, 67, 42),
        24: (14, 311, 43),
        27: (5, 244, 0),
    },
    {22: (81, 349, 25), 14: (64, 296, 22), 18: (54, 114, 21), 51: (40, 212, None)},
    {
        22: (81, 349, 25),
        14: (64, 296, 22),
        18: (54, 114, 21),
        51: (40, 212, None),
        24: (30, 47, 22),
        4: (22, 312, 26),
        31: (22, 204, None),
        12: (19, 88, 23),
    },
    {
        22: (81, 349, 25),
        14: (64, 296, 22),
        18: (54, 114, 21),
        51: (40, 212, None),
        24: (30, 47, 22),
        4: (22, 312, 26),
        31: (22, 204, None),
        12: (19, 88, 23),
        25: (17, 127, 18),
        21: (16, 175, None),
        11: (9, 315, 16),
        19: (5, 273, None),
    },
    {
        22: (81, 349, 25),
        14: (64, 296, 22),
        18: (54, 114, 21),
        51: (40, 212, None),
        24: (30, 47, 22),
        4: (22, 312, 26),
        31: (22, 204, None),
        12: (19, 88, 23),
        25: (17, 127, 18),
        21: (16, 175, None),
        11: (9, 315, 16),
        19: (5, 273, None),
        32: (5, 303, None),
        15: (2, 73, None),
    },
    {13: (65, 2, 50), 2: (61, 98, 47), 39: (60, 352, None), 5: (56, 183, 49)},
    {
        13: (65, 2, 50),
        2: (61, 98, 47),
        39: (60, 352, None),
        5: (56, 183, 49),
        15: (35, 325, 50),
        29: (32, 229, 49),
        6: (25, 70, 44),
        30: (16, 96, 38),
    },
    {
        13: (65, 2, 50),
        2: (61, 98, 47),
        39: (60, 352, None),
        5: (56, 183, 49),
        15: (35, 325, 50),
        29: (32, 229, 49),
        6: (25, 70, 44),
        30: (16, 96, 38),
        19: (8, 22, 35),
        7: (7, 122, None),
        12: (6, 316, 49),
        25: (3, 278, 36),
    },
]
gsv_sats_in_view = [
    [28, 1, 17, 8],
    [28, 1, 17, 8, 24, 11, 7, 20],
    [28, 1, 17, 8, 24, 11, 7, 20, 4, 27, 32, 26],
    [3, 4, 6, 13],
    [3, 4, 6, 13, 14, 16, 18, 19],
    [3, 4, 6, 13, 14, 16, 18, 19, 22, 24, 27],
    [22, 14, 18, 51],
    [22, 14, 18, 51, 24, 4, 31, 12],
    [22, 14, 18, 51, 24, 4, 31, 12, 25, 21, 11, 19],
    [22, 14, 18, 51, 24, 4, 31, 12, 25, 21, 11, 19, 32, 15],
    [13, 2, 39, 5],
    [13, 2, 39, 5, 15, 29, 6, 30],
    [13, 2, 39, 5, 15, 29, 6, 30, 19, 7, 12, 25],
]
test_GLL = [
    "$GPGLL,3711.0942,N,08671.4472,W,000812.000,A,A*46\n",
    "$GPGLL,4916.45,N,12311.12,W,225444,A,*1D\n",
    "$GPGLL,4250.5589,S,14718.5084,E,092204.999,A*2D\n",
    "$GPGLL,0000.0000,N,00000.0000,E,235947.000,V*2D\n",
]
gll_parsed_string = [
    ["GPGLL", "3711.0942", "N", "08671.4472", "W", "000812.000", "A", "A", "46"],
    ["GPGLL", "4916.45", "N", "12311.12", "W", "225444", "A", "", "1D"],
    ["GPGLL", "4250.5589", "S", "14718.5084", "E", "092204.999", "A", "2D"],
    ["GPGLL", "0000.0000", "N", "00000.0000", "E", "235947.000", "V", "2D"],
]
gll_crc_values = [0x46, 0x1D, 0x2D, 0x2D]
gll_longitude = [
    [86, 71.4472, "W"],
    [123, 11.12, "W"],
    [147, 18.5084, "E"],
    [0, 0.0, "W"],
]
gll_latitude = [[37, 11.0942, "N"], [49, 16.45, "N"], [42, 50.5589, "S"], [0, 0.0, "N"]]
gll_timestamp = [[0, 8, 12.0], [22, 54, 44.0], [9, 22, 4.999], [23, 59, 47.0]]
gll_valid = [True, True, True, False]

test_PGTOP = [  # PGTOP,11,3 *6F\r\n
    "$PGTOP,11,1*6D\n",
    "$PGTOP,11,2*6E\n",
    "$PGTOP,11,3*6F\n",
]
pgtop_parsed_string = [
    ["PGTOP", "11", "1", "6D"],
    ["PGTOP", "11", "2", "6E"],
    ["PGTOP", "11", "3", "6F"],
]
pgtop_crc_values = [0x6D, 0x6E, 0x6F]
pgtop_valid = [True, True, True]


def test_rmc_sentences():
    my_gps = MicropyGPS()
    sentence = ""
    print("")
    for sentence_count, RMC_sentence in enumerate(test_RMC):
        for y in RMC_sentence:
            sentence = my_gps.update(y)
            if sentence:
                assert sentence == "GPRMC"
                print("Parsed a", sentence, "Sentence")
                assert my_gps.gps_segments == rmc_parsed_strings[sentence_count]
                print("Parsed Strings:", my_gps.gps_segments)
                assert my_gps.crc_xor == rmc_crc_values[sentence_count]
                print("Sentence CRC Value:", hex(my_gps.crc_xor))
                assert my_gps.longitude == rmc_longitude[sentence_count]
                print("Longitude:", my_gps.longitude)
                assert my_gps.latitude == rmc_latitude[sentence_count]
                print("Latitude", my_gps.latitude)
                assert my_gps.timestamp == rmc_utc[sentence_count]
                print("UTC Timestamp:", my_gps.timestamp)
                assert my_gps.speed == rmc_speed[sentence_count]
                print("Speed:", my_gps.speed)
                assert my_gps.date == rmc_date[sentence_count]
                print("Date Stamp:", my_gps.date)
                assert my_gps.course == rmc_course[sentence_count]
                print("Course", my_gps.course)
                assert my_gps.valid
                print("Data is Valid:", my_gps.valid)
                assert my_gps.compass_direction() == rmc_compass[sentence_count]
                print("Compass Direction:", my_gps.compass_direction())
    assert my_gps.clean_sentences == len(test_RMC)
    assert my_gps.parsed_sentences == len(test_RMC)
    assert my_gps.crc_fails == 0


def test_vtg_sentences():
    my_gps = MicropyGPS()
    sentence = ""
    print("")
    for VTG_sentence in test_VTG:
        for y in VTG_sentence:
            sentence = my_gps.update(y)
            if sentence:
                assert sentence == "GPVTG"
                print("Parsed a", sentence, "Sentence")
                assert my_gps.gps_segments == [
                    "GPVTG",
                    "232.9",
                    "T",
                    "",
                    "M",
                    "002.3",
                    "N",
                    "004.3",
                    "K",
                    "A",
                    "01",
                ]
                print("Parsed Strings", my_gps.gps_segments)
                assert my_gps.crc_xor == 0x1
                print("Sentence CRC Value:", hex(my_gps.crc_xor))
                assert my_gps.speed == [2.3, 2.6473, 4.2596]
                print("Speed:", my_gps.speed)
                assert my_gps.course == 232.9
                print("Course", my_gps.course)
                assert my_gps.compass_direction() == "SW"
                print("Compass Direction:", my_gps.compass_direction())
    assert my_gps.clean_sentences == len(test_VTG)
    assert my_gps.parsed_sentences == len(test_VTG)
    assert my_gps.crc_fails == 0


def test_gga_sentences():
    my_gps = MicropyGPS()
    sentence = ""
    print("")
    for sentence_count, GGA_sentence in enumerate(test_GGA):
        for y in GGA_sentence:
            sentence = my_gps.update(y)
            if sentence:
                assert sentence == "GPGGA"
                print("Parsed a", sentence, "Sentence")
                assert my_gps.gps_segments == gga_parsed_strings[sentence_count]
                print("Parsed Strings", my_gps.gps_segments)
                assert my_gps.crc_xor == gga_crc_xors[sentence_count]
                print("Sentence CRC Value:", hex(my_gps.crc_xor))
                assert my_gps.longitude == gga_longitudes[sentence_count]
                print("Longitude", my_gps.longitude)
                assert my_gps.latitude == gga_latitudes[sentence_count]
                print("Latitude", my_gps.latitude)
                assert my_gps.timestamp == gga_timestamps[sentence_count]
                print("UTC Timestamp:", my_gps.timestamp)
                assert my_gps.fix_stat == gga_fixes[sentence_count]
                print("Fix Status:", my_gps.fix_stat)
                assert my_gps.altitude == gga_altitudes[sentence_count]
                print("Altitude:", my_gps.altitude)
                assert my_gps.geoid_height == gga_geoid_heights[sentence_count]
                print("Height Above Geoid:", my_gps.geoid_height)
                assert my_gps.hdop == gga_hdops[sentence_count]
                print("Horizontal Dilution of Precision:", my_gps.hdop)
                assert (
                    my_gps.satellites_in_use == gga_satellites_in_uses[sentence_count]
                )
                print("Satellites in Use by Receiver:", my_gps.satellites_in_use)
    assert my_gps.clean_sentences == len(test_GGA)
    assert my_gps.parsed_sentences == len(test_GGA)
    assert my_gps.crc_fails == 0


def test_gsa_sentences():
    my_gps = MicropyGPS()
    sentence = ""
    print("")
    for sentence_count, GSA_sentence in enumerate(test_GSA):
        for y in GSA_sentence:
            sentence = my_gps.update(y)
            if sentence:
                assert sentence == "GPGSA"
                print("Parsed a", sentence, "Sentence")
                assert my_gps.gps_segments == gsa_parsed_strings[sentence_count]
                print("Parsed Strings", my_gps.gps_segments)
                assert my_gps.crc_xor == gsa_crc_values[sentence_count]
                print("Sentence CRC Value:", hex(my_gps.crc_xor))
                assert my_gps.satellites_used == gsa_sats_used[sentence_count]
                print("Satellites Used", my_gps.satellites_used)
                assert my_gps.fix_type == 3
                print("Fix Type Code:", my_gps.fix_type)
                assert my_gps.hdop == gsa_hdop[sentence_count]
                print("Horizontal Dilution of Precision:", my_gps.hdop)
                assert my_gps.vdop == gsa_vdop[sentence_count]
                print("Vertical Dilution of Precision:", my_gps.vdop)
                assert my_gps.pdop == gsa_pdop[sentence_count]
                print("Position Dilution of Precision:", my_gps.pdop)
    assert my_gps.clean_sentences == len(test_GSA)
    assert my_gps.parsed_sentences == len(test_GSA)
    assert my_gps.crc_fails == 0


def test_gsv_sentences():
    my_gps = MicropyGPS()
    sentence = ""
    print("")
    for sentence_count, GSV_sentence in enumerate(test_GSV):
        for y in GSV_sentence:
            sentence = my_gps.update(y)
            if sentence:
                assert sentence == "GPGSV"
                print("Parsed a", sentence, "Sentence")
                assert my_gps.gps_segments == gsv_parsed_string[sentence_count]
                print("Parsed Strings", my_gps.gps_segments)
                assert my_gps.crc_xor == gsv_crc_values[sentence_count]
                print("Sentence CRC Value:", hex(my_gps.crc_xor))
                assert my_gps.last_sv_sentence == gsv_sv_setence[sentence_count]
                print("SV Sentences Parsed", my_gps.last_sv_sentence)
                assert my_gps.total_sv_sentences == gsv_total_sentence[sentence_count]
                print("SV Sentences in Total", my_gps.total_sv_sentences)
                assert my_gps.satellites_in_view == gsv_num_sats_in_view[sentence_count]
                print("# of Satellites in View:", my_gps.satellites_in_view)
                assert my_gps.satellite_data_updated() == gsv_data_valid[sentence_count]
                data_valid = my_gps.satellite_data_updated()
                print("Is Satellite Data Valid?:", data_valid)
                if data_valid:
                    print("Complete Satellite Data:", my_gps.satellite_data)
                    print("Complete Satellites Visible:", my_gps.satellites_visible())
                else:
                    print("Current Satellite Data:", my_gps.satellite_data)
                    print("Current Satellites Visible:", my_gps.satellites_visible())
                assert my_gps.satellite_data == gsv_sat_data[sentence_count]
                assert my_gps.satellites_visible() == gsv_sats_in_view[sentence_count]
    assert my_gps.clean_sentences == len(test_GSV)
    assert my_gps.parsed_sentences == len(test_GSV)
    assert my_gps.crc_fails == 0


def test_gll_sentences():
    my_gps = MicropyGPS()
    sentence = ""
    print("")
    for sentence_count, GLL_sentence in enumerate(test_GLL):
        for y in GLL_sentence:
            sentence = my_gps.update(y)
            if sentence:
                assert sentence == "GPGLL"
                print("Parsed a", sentence, "Sentence")
                assert my_gps.gps_segments == gll_parsed_string[sentence_count]
                print("Parsed Strings", my_gps.gps_segments)
                assert my_gps.crc_xor == gll_crc_values[sentence_count]
                print("Sentence CRC Value:", hex(my_gps.crc_xor))
                assert my_gps.longitude == gll_longitude[sentence_count]
                print("Longitude:", my_gps.longitude)
                assert my_gps.latitude == gll_latitude[sentence_count]
                print("Latitude", my_gps.latitude)
                assert my_gps.timestamp == gll_timestamp[sentence_count]
                print("UTC Timestamp:", my_gps.timestamp)
                assert my_gps.valid == gll_valid[sentence_count]
                print("Data is Valid:", my_gps.valid)
    assert my_gps.clean_sentences == len(test_GLL)
    assert my_gps.parsed_sentences == len(test_GLL)
    assert my_gps.crc_fails == 0


def test_pgtop_sentences():
    my_gps = MicropyGPS()
    sentence = ""
    print("")
    for sentence_count, PGTOP_sentence in enumerate(test_PGTOP):
        for y in PGTOP_sentence:
            sentence = my_gps.update(y)
            if sentence:
                assert sentence == "PGTOP"
                print("Parsed a", sentence, "Sentence")
                assert my_gps.gps_segments == pgtop_parsed_string[sentence_count]
                print("Parsed Strings", my_gps.gps_segments)
                assert my_gps.crc_xor == pgtop_crc_values[sentence_count]
                print("Sentence CRC Value:", hex(my_gps.crc_xor))
    assert my_gps.clean_sentences == len(test_PGTOP)
    assert my_gps.parsed_sentences == len(test_PGTOP)
    assert my_gps.crc_fails == 0


def test_logging():
    my_gps = MicropyGPS()
    assert my_gps.start_logging("test.txt", mode="new")
    assert my_gps.write_log("micropyGPS test log\n")
    for RMC_sentence in test_RMC:
        for y in RMC_sentence:
            my_gps.update(y)
    assert my_gps.stop_logging()
    with open("test.txt", "rb") as log_file:
        log_hash = hashlib.md5()
        log_hash.update(log_file.read())
        assert log_hash.digest() == b"'\xd8\xaeN\xa0\nS\x04e\x1cgb'\x95\xb7\xe3"
    assert my_gps.start_logging("test.txt", mode="append")
    for GSV_sentence in test_GSV:
        for y in GSV_sentence:
            my_gps.update(y)
    assert my_gps.stop_logging()
    with open("test.txt", "rb") as log_file:
        log_hash = hashlib.md5()
        log_hash.update(log_file.read())
        assert log_hash.digest() == b"\xceY\xdeMlwH\x85N\xf2\x1b=\xf9\x8e\x81\x16"


def test_pretty_print():
    my_gps = MicropyGPS()
    for RMC_sentence in test_RMC[5]:
        for y in RMC_sentence:
            my_gps.update(y)
    for GGA_sentence in test_GGA[2]:
        for y in GGA_sentence:
            my_gps.update(y)
    for VTG_sentence in test_VTG:
        for y in VTG_sentence:
            my_gps.update(y)
    print("")
    assert my_gps.latitude_string() == "37° 49.1802' N"
    print("Latitude:", my_gps.latitude_string())
    assert my_gps.longitude_string() == "83° 38.7865' W"
    print("Longitude:", my_gps.longitude_string())
    # Legacy speed format
    assert my_gps.speed_string(KPH) == "4.2596 km/h"
    print(
        "Speed:",
        my_gps.speed_string(KPH),
        "or",
        my_gps.speed_string(MPH),
        "or",
        my_gps.speed_string(KNOT),
    )
    assert my_gps.speed_string(MPH) == "2.6473 mph"
    assert my_gps.speed_string(KNOT) == "2.3 knots"

    # xx.yy speed format
    my_gps.set_speed_formatter(my_gps.f2_2_format)
    assert my_gps.speed_string(KPH) == "04.26 km/h"
    print(
        "Speed:",
        my_gps.speed_string(KPH),
        "or",
        my_gps.speed_string(MPH),
        "or",
        my_gps.speed_string(KNOT),
    )
    assert my_gps.speed_string(MPH) == "02.65 mph"
    assert my_gps.speed_string(KNOT) == "02.30 knots"

    assert my_gps.date_string(LONG) == "May 28th, 2011"
    print("Date (Long Format):", my_gps.date_string(LONG))
    assert my_gps.date_string(S_DMY) == "28/05/11"
    print("Date (Short D/M/Y Format):", my_gps.date_string(S_DMY))
    assert my_gps.date_string(S_MDY) == "05/28/11"
    print("Date (Short M/D/Y Format):", my_gps.date_string(S_MDY))
    assert my_gps.date_string(L_YMD) == "2011-05-28"
    print("Date (Long Y/M/D Format):", my_gps.date_string(L_YMD))

    assert my_gps.timestamp_string(S_HMS) == "18:00:50.896"
    print("Timestamp (hh:mm:ss.us format):", my_gps.timestamp_string(S_HMS))


def test_coordinate_representations():
    my_gps = MicropyGPS(location_formatting=DD)
    for RMC_sentence in test_RMC[5]:
        for y in RMC_sentence:
            my_gps.update(y)
    print("")
    assert my_gps.latitude_string() == "53.361336666666666° N"
    print("Decimal Degrees Latitude:", my_gps.latitude_string())
    assert my_gps.longitude_string() == "6.5056183333333335° W"
    print("Decimal Degrees Longitude:", my_gps.longitude_string())
    my_gps.coord_format = DMS
    print("Degrees Minutes Seconds Latitude:", my_gps.latitude_string())
    assert my_gps.latitude_string() == """53° 21' 41" N"""
    assert my_gps.longitude_string() == """6° 30' 20" W"""
    print("Degrees Minutes Seconds Longitude:", my_gps.longitude_string())
