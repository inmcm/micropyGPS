"""
# MicropyGPS - a GPS NMEA sentence parser for Micropython/Python 3.X
# Copyright (c) 2017 Michael Calvin McCoy (calvin.mccoy@protonmail.com)
# The MIT License (MIT) - see LICENSE file
"""

# TODO:
# Time Since First Fix
# Distance/Time to Target
# More Helper Functions
# Dynamically limit sentences types to parse

from math import floor, modf
from typing import Final, Callable

#
# Proposal of improvements 2023-02
#  - formatted by black
#  - add new format in date_string ('2023-01-01'): 'l_ymd'
#  - add new format in speed_string ('3.2f')
#  - add new 'timestamp_string' helper function
#  - adjust code for being compliant with typing (pylance & mypy)
#  - add parser for the antenna status: PGTOP: $PGTOP,11,x
#  - implement suggestions from https://github.com/inmcm/micropyGPS/issues/14
#     - use of fstring instead of % formating
#     - use of lists instead of tuples
#  - adjust code in 'speed_string' when knot speed is within +-1 range (English grammar to be confirmed)
#  - add pytest tests for checking the above
#  - adjust minor clerical errors
# Works with python 3.11.2
# Works with MicroPython 1.19.1 after stripping annotations (refer to https://github.com/orgs/micropython/discussions/10529#discussioncomment-4764412)

# Import utime or time for fix time handling
try:
    # Assume running on MicroPython
    import utime
except ImportError:
    # Otherwise default to time module for non-embedded implementations
    # Should still support millisecond resolution.
    import time

L_YMD: Final[str] = "l_ymd"
S_MDY: Final[str] = "s_mdy"
S_DMY: Final[str] = "s_dmy"
LONG: Final[str] = "long"
_DATE_FORMAT: tuple = (
    L_YMD,
    S_MDY,
    S_DMY,
    LONG,
)  # Not in use; could be checked against, as guard

S_HMS: Final[str] = "s_hms"
_TIME_FORMAT: tuple = (S_HMS,)  # Not in use; could be checked against, as guard

_NORTH: Final[str] = "N"
_SOUTH: Final[str] = "S"
_EAST: Final[str] = "E"
_WEST: Final[str] = "W"

MPH: Final[str] = "mph"
KPH: Final[str] = "km/h"
KNOT: Final[str] = "knot"
_SPEED_UNIT: tuple = (MPH, KPH, KNOT)

FULL_FLOAT: Final[str] = "full_float"
F2_2: Final[str] = "f2_2"
_SPEED_FORMAT: tuple = (
    FULL_FLOAT,
    F2_2,
)  # Not in use; could be checked against, as guard

DD: Final[str] = "dd"
DMS: Final[str] = "dms"
DDM: Final[str] = "ddm"
_LONG_LAT_FORMAT: tuple = (
    DD,
    DMS,
    DDM,
)  # Not in use; could be checked against, as guard

# Month ending formats
_FIRST: tuple = (1, 21, 31)
_SECOND: tuple = (2, 22)
_THIRD: tuple = (3, 23)

# Specific types
t_code_message = dict[str, str]
t_antenna = tuple[dict[str, str], ...]
t_satellite = tuple[int | None, int | None, int | None]
t_satellite_dict = dict[int, t_satellite]


ANTENNA_PA1616S: Final[t_antenna] = (
    {"code": "1", "message": "Internal"},
    {"code": "2", "message": "Active"},
    {"code": "3", "message": "Error. Antenna shorted"},
)
ANTENNA_PA6H: Final[t_antenna] = (
    {"code": "2", "message": "Internal"},
    {"code": "3", "message": "Active"},
    {"code": "1", "message": "Error. Antenna shorted"},
)


class MicropyGPS(object):
    """GPS NMEA Sentence Parser. Creates object that stores all relevant GPS data and statistics.
    Parses sentences one character at a time using update()."""

    # Max Number of Characters a valid sentence can be (based on GGA sentence)
    SENTENCE_LIMIT: Final[int] = 90

    __HEMISPHERES: Final[tuple[str, str, str, str]] = (_NORTH, _SOUTH, _EAST, _WEST)
    __NO_FIX = 1
    # __FIX_2D = 2 # Not used
    # __FIX_3D = 3 # Not used
    __DIRECTIONS: Final[tuple[str, ...]] = (
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    )
    __MONTHS: Final[tuple[str, ...]] = (
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    )

    def __init__(self, local_offset: int = 0, location_formatting: str = DDM):
        """
        Setup GPS Object Status Flags, Internal Data Registers, etc
            local_offset (int): Timezone Difference to UTC
            location_formatting (str): Style For Presenting Longitude/Latitude:
                                       Decimal Degree Minute (ddm) - 40° 26.767′ N
                                       Degrees Minutes Seconds (dms) - 40° 26′ 46″ N
                                       Decimal Degrees (dd) - 40.446° N
        """

        #####################
        # Object Status Flags
        self.sentence_active: bool = False
        self.active_segment: int = 0
        self.process_crc: bool = False
        self.gps_segments: list[str] = []
        self.crc_xor: int = 0
        self.char_count: int = 0
        self.fix_time = 0

        #####################
        # Sentence Statistics
        self.crc_fails = 0
        self.clean_sentences = 0
        self.parsed_sentences = 0

        #####################
        # Logging Related
        self.log_handle = None
        self.log_en: bool = False

        #####################
        # Data From Sentences
        # Time
        self.timestamp: list[int | float] = [0, 0, 0.0]
        self.date: list[int | float] = [0, 0, 0]
        self.local_offset = local_offset

        # Position/Motion
        self._latitude = [0, 0.0, _NORTH]
        self._longitude = [0, 0.0, _WEST]
        self.coord_format = location_formatting
        self.speed: list[float] = [0.0, 0.0, 0.0]
        self.course = 0.0
        self.altitude = 0.0
        self.geoid_height = 0.0

        # GPS Info
        self.satellites_in_view = 0
        self.satellites_in_use = 0
        self.satellites_used: list[int] = []
        self.last_sv_sentence = 0
        self.total_sv_sentences = 0
        self.satellite_data: t_satellite_dict = dict()
        self.hdop = 0.0
        self.pdop = 0.0
        self.vdop = 0.0
        self.valid: bool = False
        self.fix_stat = 0
        self.fix_type = 1

        # Antenna status
        self.antenna_status = "Unknown antenna status"

        # Speed format representation
        self._speed_formatter: Callable = self.full_format

    ########################################
    # Coordinates Translation Functions
    ########################################
    @property
    def latitude(self):
        """Format Latitude Data Correctly"""
        if self.coord_format == DD:
            decimal_degrees: float = self._latitude[0] + (self._latitude[1] / 60)
            return [decimal_degrees, self._latitude[2]]
        elif self.coord_format == DMS:
            minute_parts = modf(self._latitude[1])
            seconds = round(minute_parts[0] * 60)
            return [self._latitude[0], int(minute_parts[1]), seconds, self._latitude[2]]
        else:
            return self._latitude

    @property
    def longitude(self):
        """Format Longitude Data Correctly"""
        if self.coord_format == DD:
            decimal_degrees = self._longitude[0] + (float(self._longitude[1]) / 60)
            return [decimal_degrees, self._longitude[2]]
        elif self.coord_format == DMS:
            minute_parts: tuple[float, float] = modf(float(self._longitude[1]))
            seconds = round(minute_parts[0] * 60)
            return [
                self._longitude[0],
                int(minute_parts[1]),
                seconds,
                self._longitude[2],
            ]
        else:
            return self._longitude

    ########################################
    # Logging Related Functions
    ########################################
    def start_logging(self, target_file, mode="append") -> bool:
        """
        Create GPS data log object
        """
        # Set Write Mode Overwrite or Append
        mode_code = "w" if mode == "new" else "a"

        try:
            self.log_handle = open(target_file, mode_code)
        except AttributeError:
            print("Invalid FileName")
            return False

        self.log_en = True
        return True

    def stop_logging(self) -> bool:
        """
        Closes the log file handler and disables further logging
        """
        # try:
        #    self.log_handle.close()
        # except AttributeError:
        #    print("Invalid Handle")
        #    return False
        if self.log_handle is None:
            print("Invalid Handle")
            return False

        self.log_handle.close()
        self.log_en = False
        return True

    def write_log(self, log_string) -> bool:
        """Attempts to write the last valid NMEA sentence character to the active file handler"""
        # try:
        #    self.log_handle.write(log_string)
        # except TypeError:
        #    return False
        # return True
        if self.log_handle is None:
            print("Invalid Handle")
            return False
        self.log_handle.write(log_string)
        return True

    ########################################
    # Sentence Parsers
    ########################################
    def gprmc(self) -> bool:
        """Parse Recommended Minimum Specific GPS/Transit data (RMC)Sentence.
        Updates UTC timestamp, latitude, longitude, Course, Speed, Date, and fix status
        """

        # UTC Timestamp
        try:
            utc_string = self.gps_segments[1]

            if utc_string:  # Possible timestamp found
                hours = (int(utc_string[0:2]) + self.local_offset) % 24
                minutes = int(utc_string[2:4])
                seconds = float(utc_string[4:])
                self.timestamp = [hours, minutes, seconds]
            else:  # No Time stamp yet
                self.timestamp = [0, 0, 0.0]

        except ValueError:  # Bad Timestamp value present
            return False

        # Date stamp
        try:
            date_string = self.gps_segments[9]

            # Date string printer function assumes to be year >=2000,
            # date_string() must be supplied with the correct century argument to display correctly
            if date_string:  # Possible date stamp found
                day = int(date_string[0:2])
                month = int(date_string[2:4])
                year = int(date_string[4:6])
                self.date = [day, month, year]
            else:  # No Date stamp yet
                self.date = [0, 0, 0]

        except ValueError:  # Bad Date stamp value present
            return False

        # Check Receiver Data Valid Flag
        if self.gps_segments[2] == "A":  # Data from Receiver is Valid/Has Fix
            # Longitude / Latitude
            try:
                # Latitude
                l_string = self.gps_segments[3]
                lat_degs = int(l_string[0:2])
                lat_mins = float(l_string[2:])
                lat_hemi = self.gps_segments[4]

                # Longitude
                l_string = self.gps_segments[5]
                lon_degs = int(l_string[0:3])
                lon_mins = float(l_string[3:])
                lon_hemi = self.gps_segments[6]
            except ValueError:
                return False

            if lat_hemi not in self.__HEMISPHERES:
                return False

            if lon_hemi not in self.__HEMISPHERES:
                return False

            # Speed
            try:
                spd_knt = float(self.gps_segments[7])
            except ValueError:
                return False

            # Course
            try:
                if self.gps_segments[8]:
                    course = float(self.gps_segments[8])
                else:
                    course = 0.0
            except ValueError:
                return False

            # TODO - Add Magnetic Variation

            # Update Object Data
            self._latitude = [lat_degs, lat_mins, lat_hemi]
            self._longitude = [lon_degs, lon_mins, lon_hemi]
            # Include mph and hm/h
            self.speed = [spd_knt, spd_knt * 1.151, spd_knt * 1.852]
            self.course = course
            self.valid = True

            # Update Last Fix Time
            self.new_fix_time()

        else:  # Clear Position Data if Sentence is 'Invalid'
            self._latitude = [0, 0.0, _NORTH]
            self._longitude = [0, 0.0, _WEST]
            self.speed = [0.0, 0.0, 0.0]
            self.course = 0.0
            self.valid = False

        return True

    def gpgll(self) -> bool:
        """Parse Geographic Latitude and Longitude (GLL)Sentence. Updates UTC timestamp, latitude,
        longitude, and fix status"""

        # UTC Timestamp
        try:
            utc_string = self.gps_segments[5]

            if utc_string:  # Possible timestamp found
                hours = (int(utc_string[0:2]) + self.local_offset) % 24
                minutes = int(utc_string[2:4])
                seconds = float(utc_string[4:])
                self.timestamp = [hours, minutes, seconds]
            else:  # No Time stamp yet
                self.timestamp = [0, 0, 0.0]

        except ValueError:  # Bad Timestamp value present
            return False

        # Check Receiver Data Valid Flag
        if self.gps_segments[6] == "A":  # Data from Receiver is Valid/Has Fix
            # Longitude / Latitude
            try:
                # Latitude
                l_string = self.gps_segments[1]
                lat_degs = int(l_string[0:2])
                lat_mins = float(l_string[2:])
                lat_hemi = self.gps_segments[2]

                # Longitude
                l_string = self.gps_segments[3]
                lon_degs = int(l_string[0:3])
                lon_mins = float(l_string[3:])
                lon_hemi = self.gps_segments[4]
            except ValueError:
                return False

            if lat_hemi not in self.__HEMISPHERES:
                return False

            if lon_hemi not in self.__HEMISPHERES:
                return False

            # Update Object Data
            self._latitude = [lat_degs, lat_mins, lat_hemi]
            self._longitude = [lon_degs, lon_mins, lon_hemi]
            self.valid = True

            # Update Last Fix Time
            self.new_fix_time()

        else:  # Clear Position Data if Sentence is 'Invalid'
            self._latitude = [0, 0.0, _NORTH]
            self._longitude = [0, 0.0, _WEST]
            self.valid = False

        return True

    def gpvtg(self) -> bool:
        """Parse Track Made Good and Ground Speed (VTG) Sentence. Updates speed and course"""
        try:
            course = float(self.gps_segments[1]) if self.gps_segments[1] else 0.0
            spd_knt = float(self.gps_segments[5]) if self.gps_segments[5] else 0.0
        except ValueError:
            return False

        # Include mph and km/h
        # self.speed = (spd_knt, spd_knt * 1.151, spd_knt * 1.852)
        self.speed = [spd_knt, spd_knt * 1.151, spd_knt * 1.852]
        self.course = course
        return True

    def gpgga(self) -> bool:
        """Parse Global Positioning System Fix Data (GGA) Sentence. Updates UTC timestamp, latitude, longitude,
        fix status, satellites in use, Horizontal Dilution of Precision (HDOP), altitude, geoid height and fix status
        """

        try:
            # UTC Timestamp
            utc_string = self.gps_segments[1]

            # Skip timestamp if receiver doesn't have on yet
            if utc_string:
                hours = (int(utc_string[0:2]) + self.local_offset) % 24
                minutes = int(utc_string[2:4])
                seconds = float(utc_string[4:])
            else:
                hours = 0
                minutes = 0
                seconds = 0.0

            # Number of Satellites in Use
            satellites_in_use = int(self.gps_segments[7])

            # Get Fix Status
            fix_stat = int(self.gps_segments[6])

        except (ValueError, IndexError):
            return False

        try:
            # Horizontal Dilution of Precision
            hdop = float(self.gps_segments[8])
        except (ValueError, IndexError):
            hdop = 0.0

        # Process Location and Speed Data if Fix is GOOD
        if fix_stat:
            # Longitude / Latitude
            try:
                # Latitude
                l_string = self.gps_segments[2]
                lat_degs = int(l_string[0:2])
                lat_mins = float(l_string[2:])
                lat_hemi = self.gps_segments[3]

                # Longitude
                l_string = self.gps_segments[4]
                lon_degs = int(l_string[0:3])
                lon_mins = float(l_string[3:])
                lon_hemi = self.gps_segments[5]
            except ValueError:
                return False

            if lat_hemi not in self.__HEMISPHERES:
                return False

            if lon_hemi not in self.__HEMISPHERES:
                return False

            # Altitude / Height Above Geoid
            try:
                altitude = float(self.gps_segments[9])
                geoid_height = float(self.gps_segments[11])
            except ValueError:
                altitude = 0
                geoid_height = 0

            # Update Object Data
            self._latitude = [lat_degs, lat_mins, lat_hemi]
            self._longitude = [lon_degs, lon_mins, lon_hemi]
            self.altitude = altitude
            self.geoid_height = geoid_height

        # Update Object Data
        self.timestamp = [hours, minutes, seconds]
        self.satellites_in_use = satellites_in_use
        self.hdop = hdop
        self.fix_stat = fix_stat

        # If Fix is GOOD, update fix timestamp
        if fix_stat:
            self.new_fix_time()

        return True

    def gpgsa(self) -> bool:
        """Parse GNSS DOP and Active Satellites (GSA) sentence. Updates GPS fix type, list of satellites used in
        fix calculation, Position Dilution of Precision (PDOP), Horizontal Dilution of Precision (HDOP), Vertical
        Dilution of Precision, and fix status"""

        # Fix Type (None,2D or 3D)
        try:
            fix_type = int(self.gps_segments[2])
        except ValueError:
            return False

        # Read All (up to 12) Available PRN Satellite Numbers
        sats_used: list[int] = []
        for sats in range(12):
            sat_number_str = self.gps_segments[3 + sats]
            if sat_number_str:
                try:
                    sat_number = int(sat_number_str)
                    sats_used.append(sat_number)
                except ValueError:
                    return False
            else:
                break

        # PDOP,HDOP,VDOP
        try:
            pdop = float(self.gps_segments[15])
            hdop = float(self.gps_segments[16])
            vdop = float(self.gps_segments[17])
        except ValueError:
            return False

        # Update Object Data
        self.fix_type = fix_type

        # If Fix is GOOD, update fix timestamp
        if fix_type > self.__NO_FIX:
            self.new_fix_time()

        self.satellites_used = sats_used
        self.hdop = hdop
        self.vdop = vdop
        self.pdop = pdop

        return True

    def gpgsv(self) -> bool:
        """Parse Satellites in View (GSV) sentence. Updates number of SV Sentences,the number of the last SV sentence
        parsed, and data on each satellite present in the sentence"""
        try:
            num_sv_sentences = int(self.gps_segments[1])
            current_sv_sentence = int(self.gps_segments[2])
            sats_in_view = int(self.gps_segments[3])
        except ValueError:
            return False

        # Create a blank dict to store all the satellite data from this sentence in:
        # satellite PRN is key, tuple containing telemetry is value
        satellite_dict: t_satellite_dict = dict()
        # Calculate  Number of Satelites to pull data for and thus how many segment positions to read
        if num_sv_sentences == current_sv_sentence:
            # Last sentence may have 1-4 satellites; 5 - 20 positions
            sat_segment_limit = (sats_in_view - ((num_sv_sentences - 1) * 4)) * 5
        else:
            sat_segment_limit = 20  # Non-last sentences have 4 satellites and thus read up to position 20

        # Try to recover data for up to 4 satellites in sentence
        for sats in range(4, sat_segment_limit, 4):
            # If a PRN is present, grab satellite data
            if self.gps_segments[sats]:
                try:
                    sat_id = int(self.gps_segments[sats])
                except (ValueError, IndexError):
                    return False

                try:  # elevation can be null (no value) when not tracking
                    elevation = int(self.gps_segments[sats + 1])
                except (ValueError, IndexError):
                    elevation = None

                try:  # azimuth can be null (no value) when not tracking
                    azimuth = int(self.gps_segments[sats + 2])
                except (ValueError, IndexError):
                    azimuth = None

                try:  # SNR can be null (no value) when not tracking
                    snr = int(self.gps_segments[sats + 3])
                except (ValueError, IndexError):
                    snr = None
            # If no PRN is found, then the sentence has no more satellites to read
            else:
                break

            # Add Satellite Data to Sentence Dict
            satellite_dict[sat_id] = (elevation, azimuth, snr)

        # Update Object Data
        self.total_sv_sentences = num_sv_sentences
        self.last_sv_sentence = current_sv_sentence
        self.satellites_in_view = sats_in_view

        # For a new set of sentences, we either clear out the existing sat data or
        # update it as additional SV sentences are parsed
        if current_sv_sentence == 1:
            self.satellite_data = satellite_dict
        else:
            self.satellite_data.update(satellite_dict)

        return True

    def pgtop(self) -> bool:
        """
        Receive antenna status

        # $PGTOP,11,x
        When issuing one of the following commands:
         - PGCMD_PERIODIC_ANTENNA_STATUS or PGCMD_NO_PERIODIC_ANTENNA_STATUS to disable
           periodic output
         - INQUIRE_ANTENNA_STATUS: Inquiry antenna status - one shot

        The MTK responses with: $PGTOP,11,value*checksum
        """
        try:
            segment1: str = self.gps_segments[1]
        except ValueError:
            return False
        if segment1 == "11":
            self.antenna_status = self.gps_segments[2]
        else:
            self.antenna_status = "-1"  # unknown status
        return True

    def get_antenna_status(self, GPS_module_type: t_antenna) -> str:
        """
        Get Antenna status, after MTK has responded with: $PGTOP,11,value*checksum.

        :param GPS_module_type holds the data for the relevant GPS module

        :return: status of the antenna connected to the GPS module.
        """
        for antenna in GPS_module_type:
            if self.antenna_status == antenna["code"]:
                return antenna["message"]
        else:
            return "Error in antenna status"

    ##########################################
    # Data Stream Handler Functions
    ##########################################

    def new_sentence(self) -> None:
        """Adjust Object Flags in Preparation for a New Sentence"""
        self.gps_segments = [""]
        self.active_segment = 0
        self.crc_xor = 0
        self.sentence_active = True
        self.process_crc = True
        self.char_count = 0

    def update(self, new_char: str) -> None | str:
        """
        Process a new input char and updates GPS object if necessary based on special characters ('$', ',', '*')

        Function builds a list of received string that are validate by CRC prior to parsing by the  appropriate
        sentence function.
        :return: sentence type on successful parse, None otherwise
        """

        valid_sentence = False

        # Validate new_char is a printable char
        ascii_char = ord(new_char)

        if 10 <= ascii_char <= 126:
            self.char_count += 1

            # Write Character to log file if enabled
            if self.log_en:
                self.write_log(new_char)

            # Check if a new string is starting ($)
            if new_char == "$":
                self.new_sentence()
                return None

            elif self.sentence_active:
                # Check if sentence is ending (*)
                if new_char == "*":
                    self.process_crc = False
                    self.active_segment += 1
                    self.gps_segments.append("")
                    return None

                # Check if a section is ended (,), Create a new substring to feed
                # characters to
                elif new_char == ",":
                    self.active_segment += 1
                    self.gps_segments.append("")

                # Store All Other printable character and check CRC when ready
                else:
                    self.gps_segments[self.active_segment] += new_char

                    # When CRC input is disabled, sentence is nearly complete
                    if not self.process_crc:
                        if len(self.gps_segments[self.active_segment]) == 2:
                            try:
                                final_crc = int(
                                    self.gps_segments[self.active_segment], 16
                                )
                                if self.crc_xor == final_crc:
                                    valid_sentence = True
                                else:
                                    self.crc_fails += 1
                            except ValueError:
                                pass  # CRC Value was deformed and could not have been correct

                # Update CRC
                if self.process_crc:
                    self.crc_xor ^= ascii_char

                # If a Valid Sentence Was received and it's a supported sentence, then parse it!!
                if valid_sentence:
                    self.clean_sentences += 1  # Increment clean sentences received
                    self.sentence_active = False  # Clear Active Processing Flag

                    if self.gps_segments[0] in self.supported_sentences:
                        # parse the Sentence Based on the message type, return True if parse is clean
                        if self.supported_sentences[self.gps_segments[0]](self):
                            # Let host know that the GPS object was updated by returning parsed sentence type
                            self.parsed_sentences += 1
                            return self.gps_segments[0]

                # Check that the sentence buffer isn't filling up with Garage waiting for the sentence to complete
                if self.char_count > self.SENTENCE_LIMIT:
                    self.sentence_active = False

        # Tell Host no new sentence was parsed
        return None

    def new_fix_time(self) -> None:
        """
        Updates a high resolution (soft) counter with current time when fix is updated.

        Currently only triggered from GGA, GSA and RMC sentences
        """
        try:
            self.fix_time = utime.ticks_ms()
        except NameError:
            self.fix_time = time.time()

    #########################################
    # User Helper Functions
    # These functions make working with the GPS object data easier
    #########################################

    def satellite_data_updated(self) -> bool:
        """
        Checks if the all the GSV sentences in a group have been read, making satellite data complete
        :return: boolean
        """
        if (
            self.total_sv_sentences > 0
            and self.total_sv_sentences == self.last_sv_sentence
        ):
            return True
        else:
            return False

    def unset_satellite_data_updated(self) -> None:
        """
        Mark GSV sentences as read indicating the data has been used and future updates are fresh
        """
        self.last_sv_sentence = 0

    def satellites_visible(self) -> list[int]:
        """
        Returns a list of of the satellite PRNs currently visible to the receiver

        :return: list of satellite ids
        """
        return list(self.satellite_data.keys())

    def time_since_fix(self) -> float:
        """Returns number of millisecond since the last sentence with a valid fix was parsed. Returns -1.0 if
        no fix has been found"""

        # Test if a Fix has been found
        if self.fix_time == 0:
            return -1.0

        # Try calculating fix time using utime; if not running MicroPython
        # time.time() returns a floating point value in secs
        try:
            current = utime.ticks_diff(utime.ticks_ms(), self.fix_time)
        except NameError:
            current = (time.time() - self.fix_time) * 1000  # ms

        return current

    def compass_direction(self):
        """
        Determine a cardinal or inter-cardinal direction based on current course.
        :return: string
        """
        # Calculate the offset for a rotated compass
        if self.course >= 348.75:
            offset_course = 360 - self.course
        else:
            offset_course = self.course + 11.25

        # Each compass point is separated by 22.5 degrees, divide to find lookup value
        dir_index = floor(offset_course / 22.5)

        final_dir = self.__DIRECTIONS[dir_index]

        return final_dir

    def latitude_string(self) -> str:
        """
        Create a readable string of the current latitude data

        :return: formatted string according to 'self.coord_format'
        """
        if self.coord_format == DD:
            formatted_latitude = self.latitude
            lat_string = f"{formatted_latitude[0]}° {self._latitude[2]}"
        elif self.coord_format == DMS:
            formatted_latitude = self.latitude
            lat_string = (
                f"{formatted_latitude[0]}° {formatted_latitude[1]}'"
                f' {formatted_latitude[2]}" {formatted_latitude[3]}'
            )
        else:
            lat_string = (
                f"{self._latitude[0]}° {self._latitude[1]}' {self._latitude[2]}"
            )
        return lat_string

    def longitude_string(self) -> str:
        """
        Create a readable string of the current longitude data

        :return: formatted string according to
        """
        if self.coord_format == DD:
            formatted_longitude = self.longitude
            lon_string = f"{formatted_longitude[0]}° {self._longitude[2]}"
        elif self.coord_format == DMS:
            formatted_longitude = self.longitude
            lon_string = (
                f"{formatted_longitude[0]}° {formatted_longitude[1]}'"
                f' {formatted_longitude[2]}" {formatted_longitude[3]}'
            )
        else:
            lon_string = (
                f"{self._longitude[0]}° {self._longitude[1]}' {self._longitude[2]}"
            )
        return lon_string

    def set_speed_formatter(self, formatter: Callable) -> None:
        """Initialise the format function for speed representation"""
        self._speed_formatter = formatter

    def full_format(self, speed: float) -> str:
        """
        Function to format the speed.

        Here: full float format (any length)

        :return: string formatted speed value
        """
        return f"{speed}"

    def f2_2_format(self, speed: float) -> str:
        """
        Function to format the speed.

        Here: '06.78'

        :return: string formatted speed value
        """
        return f"{speed:0>5.2f}"

    def speed_string(self, unit=KPH) -> str:
        """
        Creates a readable string of the current speed data in one of three units

        The 'self._speed_formatter()' object contains the format function representation to apply to the speed

        :param unit: string of SPEED_UNIT
        :return: speed formatted string according to the SPEED_UNIT
        """
        if unit not in _SPEED_UNIT:
            print(f"Unknown unit for speed: {unit}")

        if unit == MPH:
            speed_string = f"{self._speed_formatter(self.speed[1])} {MPH}"
        elif unit == KNOT:
            if 1 >= self.speed[0] >= -1:
                speed_string = f"{self._speed_formatter(self.speed[0])} {KNOT}"
            else:
                speed_string = f"{self._speed_formatter(self.speed[0])} {KNOT}s"
        else:
            speed_string = f"{self._speed_formatter(self.speed[2])} {KPH}"

        return speed_string

    def date_string(self, formatting=S_MDY, century="20") -> str:
        """
        Creates a readable string of the current date.

        Select between:
         - long format: Januray 1st, 2014
         - or two short numeric formats:
           - 11/01/2014 (MM/DD/YYYY)
           - 01/11/2014 (DD/MM/YYYY)
         - or this long numeric one:
           - 2023-01-01 (YYY-MM-DD)

        :param formatting: string of DATE_FORMAT
        :param century: int delineating the century the GPS data is from (19 for 19XX, 20 for 20XX)
        :return: date_string  string with long or short format date
        """

        # Long Format January 1st, 2014
        if formatting == LONG:
            # Retrieve Month string from private set
            month = self.__MONTHS[int(self.date[1]) - 1]

            # Determine Date Suffix
            if self.date[0] in _FIRST:
                day = f"{self.date[0]}st"
            elif self.date[0] in _SECOND:
                day = f"{self.date[0]}nd"
            elif self.date[0] in _THIRD:
                day = f"{self.date[0]}rd"
            else:
                day = f"{self.date[0]}th"

            year = f"{century}{self.date[2]}"  # Create Year String
            date_string = f"{month} {day}, {year}"  # Put it all together

        else:
            # Add leading zeros to day string if necessary
            if self.date[0] < 10:
                day = f"0{self.date[0]}"
            else:
                day = f"{self.date[0]}"

            # Add leading zeros to month string if necessary
            if self.date[1] < 10:
                month = f"0{self.date[1]}"
            else:
                month = f"{self.date[1]}"

            # Add leading zeros to year string if necessary
            if self.date[2] < 10:
                year = f"0{self.date[2]}"
            else:
                year = f"{self.date[2]}"

            # Build final string based on desired formatting
            if formatting == S_DMY:
                date_string = f"{day}/{month}/{year}"

            elif formatting == L_YMD:
                date_string = f"{century}{year}-{month}-{day}"

            else:  # Default date format (S_MDY)
                date_string = f"{month}/{day}/{year}"

        return date_string

    def timestamp_string(self, formatting=S_HMS) -> str:
        """
        Creates a readable string of the current timestamp.

        One format hh:mm:ss.us   12:00:23.789

        :param formatting: string 's_hms'
        :return: timestamp_string  string format timestamp
        """

        if formatting == S_HMS:
            # Add leading zeros to hour string if necessary
            if self.timestamp[0] < 10:
                hour = f"0{self.timestamp[0]}"
            else:
                hour = f"{self.timestamp[0]}"

            # Add leading zeros to minute string if necessary
            if self.timestamp[1] < 10:
                minute = f"0{self.timestamp[1]}"
            else:
                minute = f"{self.timestamp[1]}"

            # Add leading zeros to second string if necessary
            if self.timestamp[2] < 10:
                second = f"0{self.timestamp[2]}"
            else:
                second = f"{self.timestamp[2]}"

            # Build final string
            timestamp_string = f"{hour}:{minute}:{second}"

        else:
            raise ValueError("Unkown timestamp format")

        return timestamp_string

    # All the currently supported NMEA sentences
    supported_sentences = {
        "GPRMC": gprmc,
        "GLRMC": gprmc,
        "GPGGA": gpgga,
        "GLGGA": gpgga,
        "GPVTG": gpvtg,
        "GLVTG": gpvtg,
        "GPGSA": gpgsa,
        "GLGSA": gpgsa,
        "GPGSV": gpgsv,
        "GLGSV": gpgsv,
        "GPGLL": gpgll,
        "GLGLL": gpgll,
        "GNGGA": gpgga,
        "GNRMC": gprmc,
        "GNVTG": gpvtg,
        "GNGLL": gpgll,
        "GNGSA": gpgsa,
        "PGTOP": pgtop,
    }


if __name__ == "__main__":
    pass
