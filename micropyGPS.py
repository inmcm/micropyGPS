# MicropyGPS - a GPS NMEA sentence parser for Micropython/Python 3.X

#
# The MIT License (MIT)

# Copyright (c) 2017 Michael Calvin McCoy (calvin.mccoy@gmail.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


# TODO:
# Time Since First Fix
# Distance/Time to Target
# More Helper Functions
# Dynamically limit sentences types to parse

from math import floor, modf

# Import pyb or time for fix time handling
try:
    # Assume running on pyboard
    import pyb
except ImportError:
    # Otherwise default to time module for non-embedded implementations
    # Note that this forces the resolution of the fix time 1 second instead
    # of milliseconds as on the pyboard
    import time


class MicropyGPS(object):
    """GPS NMEA Sentence Parser. Creates object that stores all relevant GPS data and statistics.
    Parses sentences one character at a time using update(). """

    # Max Number of Characters a valid sentence can be (based on GGA sentence)
    SENTENCE_LIMIT = 76
    __HEMISPHERES = ('N', 'S', 'E', 'W')
    __NO_FIX = 1
    __FIX_2D = 2
    __FIX_3D = 3
    __DIRECTIONS = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W',
                    'WNW', 'NW', 'NNW']
    __MONTHS = ('January', 'February', 'March', 'April', 'May',
                'June', 'July', 'August', 'September', 'October',
                'November', 'December')

    def __init__(self, local_offset=0, location_formatting='ddm'):
        """
        Setup GPS Object Status Flags, Internal Data Registers, etc
            local_offset (int): Timzone Difference to UTC
            location_formatting (str): Style For Presenting Longitude/Latitude:
                                       Decimal Degree Minute (ddm) - 40° 26.767′ N
                                       Degrees Minutes Seconds (dms) - 40° 26′ 46″ N
                                       Decimal Degrees (dd) - 40.446° N
        """

        #####################
        # Object Status Flags
        self.sentence_active = False
        self.active_segment = 0
        self.process_crc = False
        self.gps_segments = []
        self.crc_xor = 0
        self.char_count = 0
        self.fix_time = 0

        #####################
        # Sentence Statistics
        self.crc_fails = 0
        self.clean_sentences = 0
        self.parsed_sentences = 0

        #####################
        # Logging Related
        self.log_handle = None
        self.log_en = False

        #####################
        # Data From Sentences
        # Time
        self.timestamp = (0, 0, 0)
        self.date = (0, 0, 0)
        self.local_offset = local_offset

        # Position/Motion
        self._latitude = (0, 0.0, 'N')
        self._longitude = (0, 0.0, 'W')
        self.coord_format = location_formatting
        self.speed = (0.0, 0.0, 0.0)
        self.course = 0.0
        self.altitude = 0.0
        self.geoid_height = 0.0

        # GPS Info
        self.satellites_in_view = 0
        self.satellites_in_use = 0
        self.satellites_used = []
        self.last_sv_sentence = 0
        self.total_sv_sentences = 0
        self.satellite_data = dict()
        self.hdop = 0.0
        self.pdop = 0.0
        self.vdop = 0.0
        self.valid = False
        self.fix_stat = 0
        self.fix_type = 1

    ########################################
    # Coordinates Translation Functions
    ########################################
    @property
    def latitude(self):
        """Format Latitude Data Correctly"""
        if self.coord_format == 'dd':
            decimal_degrees = self._latitude[0] + (self._latitude[1] / 60)
            return [decimal_degrees, self._latitude[2]]
        elif self.coord_format == 'dms':
            minute_parts = modf(self._latitude[1])
            seconds = round(minute_parts[0] * 60)
            return [self._latitude[0], int(minute_parts[1]), seconds, self._latitude[2]]
        else:
            return self._latitude

    @property
    def longitude(self):
        """Format Longitude Data Correctly"""
        if self.coord_format == 'dd':
            decimal_degrees = self._longitude[0] + (self._longitude[1] / 60)
            return [decimal_degrees, self._longitude[2]]
        elif self.coord_format == 'dms':
            minute_parts = modf(self._longitude[1])
            seconds = round(minute_parts[0] * 60)
            return [self._longitude[0], int(minute_parts[1]), seconds, self._longitude[2]]
        else:
            return self._longitude

    ########################################
    # Logging Related Functions
    ########################################
    def start_logging(self, target_file, mode="append"):
        """
        Create GPS data log object
        """
        # Set Write Mode Overwrite or Append
        mode_code = 'w' if mode == 'new' else 'a'

        try:
            self.log_handle = open(target_file, mode_code)
        except AttributeError:
            print("Invalid FileName")
            return False

        self.log_en = True
        return True

    def stop_logging(self):
        """
        Closes the log file handler and disables further logging
        """
        try:
            self.log_handle.close()
        except AttributeError:
            print("Invalid Handle")
            return False

        self.log_en = False
        return True

    def write_log(self, log_string):
        """Attempts to write the last valid NMEA sentence character to the active file handler
        """
        try:
            self.log_handle.write(log_string)
        except TypeError:
            return False
        return True

    ########################################
    # Sentence Parsers
    ########################################
    def gprmc(self):
        """Parse Recommended Minimum Specific GPS/Transit data (RMC)Sentence.
        Updates UTC timestamp, latitude, longitude, Course, Speed, Date, and fix status
        """

        # UTC Timestamp
        try:
            utc_string = self.gps_segments[1]

            if utc_string:  # Possible timestamp found
                hours = int(utc_string[0:2]) + self.local_offset
                minutes = int(utc_string[2:4])
                seconds = float(utc_string[4:])
                self.timestamp = (hours, minutes, seconds)
            else:  # No Time stamp yet
                self.timestamp = (0, 0, 0)

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
                self.date = (day, month, year)
            else:  # No Date stamp yet
                self.date = (0, 0, 0)

        except ValueError:  # Bad Date stamp value present
            return False

        # Check Receiver Data Valid Flag
        if self.gps_segments[2] == 'A':  # Data from Receiver is Valid/Has Fix

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
                course = float(self.gps_segments[8])
            except ValueError:
                return False

            # TODO - Add Magnetic Variation

            # Update Object Data
            self._latitude = (lat_degs, lat_mins, lat_hemi)
            self._longitude = (lon_degs, lon_mins, lon_hemi)
            # Include mph and hm/h
            self.speed = (spd_knt, spd_knt * 1.151, spd_knt * 1.852)
            self.course = course
            self.valid = True

            # Update Last Fix Time
            self.new_fix_time()

        else:  # Clear Position Data if Sentence is 'Invalid'
            self._latitude = (0, 0.0, 'N')
            self._longitude = (0, 0.0, 'W')
            self.speed = (0.0, 0.0, 0.0)
            self.course = 0.0
            self.date = (0, 0, 0)
            self.valid = False

        return True

    def gpgll(self):
        """Parse Geographic Latitude and Longitude (GLL)Sentence. Updates UTC timestamp, latitude,
        longitude, and fix status"""

        # UTC Timestamp
        try:
            utc_string = self.gps_segments[5]

            if utc_string:  # Possible timestamp found
                hours = int(utc_string[0:2]) + self.local_offset
                minutes = int(utc_string[2:4])
                seconds = float(utc_string[4:])
                self.timestamp = (hours, minutes, seconds)
            else:  # No Time stamp yet
                self.timestamp = (0, 0, 0)

        except ValueError:  # Bad Timestamp value present
            return False

        # Check Receiver Data Valid Flag
        if self.gps_segments[6] == 'A':  # Data from Receiver is Valid/Has Fix

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
            self._latitude = (lat_degs, lat_mins, lat_hemi)
            self._longitude = (lon_degs, lon_mins, lon_hemi)
            self.valid = True

            # Update Last Fix Time
            self.new_fix_time()

        else:  # Clear Position Data if Sentence is 'Invalid'
            self._latitude = (0, 0.0, 'N')
            self._longitude = (0, 0.0, 'W')
            self.valid = False

        return True

    def gpvtg(self):
        """Parse Track Made Good and Ground Speed (VTG) Sentence. Updates speed and course"""
        try:
            course = float(self.gps_segments[1])
            spd_knt = float(self.gps_segments[5])
        except ValueError:
            return False

        # Include mph and km/h
        self.speed = (spd_knt, spd_knt * 1.151, spd_knt * 1.852)
        self.course = course
        return True

    def gpgga(self):
        """Parse Global Positioning System Fix Data (GGA) Sentence. Updates UTC timestamp, latitude, longitude,
        fix status, satellites in use, Horizontal Dilution of Precision (HDOP), altitude, geoid height and fix status"""

        try:
            # UTC Timestamp
            utc_string = self.gps_segments[1]

            # Skip timestamp if receiver doesn't have on yet
            if utc_string:
                hours = int(utc_string[0:2]) + self.local_offset
                minutes = int(utc_string[2:4])
                seconds = float(utc_string[4:])
            else:
                hours = 0
                minutes = 0
                seconds = 0.0

            # Number of Satellites in Use
            satellites_in_use = int(self.gps_segments[7])

            # Horizontal Dilution of Precision
            hdop = float(self.gps_segments[8])

            # Get Fix Status
            fix_stat = int(self.gps_segments[6])

        except ValueError:
            return False

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
                return False

            # Update Object Data
            self._latitude = (lat_degs, lat_mins, lat_hemi)
            self._longitude = (lon_degs, lon_mins, lon_hemi)
            self.altitude = altitude
            self.geoid_height = geoid_height

        # Update Object Data
        self.timestamp = (hours, minutes, seconds)
        self.satellites_in_use = satellites_in_use
        self.hdop = hdop
        self.fix_stat = fix_stat

        # If Fix is GOOD, update fix timestamp
        if fix_stat:
            self.new_fix_time()

        return True

    def gpgsa(self):
        """Parse GNSS DOP and Active Satellites (GSA) sentence. Updates GPS fix type, list of satellites used in
        fix calculation, Position Dilution of Precision (PDOP), Horizontal Dilution of Precision (HDOP), Vertical
        Dilution of Precision, and fix status"""

        # Fix Type (None,2D or 3D)
        try:
            fix_type = int(self.gps_segments[2])
        except ValueError:
            return False

        # Read All (up to 12) Available PRN Satellite Numbers
        sats_used = []
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

    def gpgsv(self):
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
        satellite_dict = dict()

        # Calculate  Number of Satelites to pull data for and thus how many segment positions to read
        if num_sv_sentences == current_sv_sentence:
            sat_segment_limit = ((sats_in_view % 4) * 4) + 4  # Last sentence may have 1-4 satellites
        else:
            sat_segment_limit = 20  # Non-last sentences have 4 satellites and thus read up to position 20

        # Try to recover data for up to 4 satellites in sentence
        for sats in range(4, sat_segment_limit, 4):

            # If a PRN is present, grab satellite data
            if self.gps_segments[sats]:
                try:
                    sat_id = int(self.gps_segments[sats])
                except ValueError:
                    return False

                try:  # elevation can be null (no value) when not tracking
                    elevation = int(self.gps_segments[sats+1])
                except ValueError:
                    elevation = None

                try:  # azimuth can be null (no value) when not tracking
                    azimuth = int(self.gps_segments[sats+2])
                except ValueError:
                    azimuth = None

                try:  # SNR can be null (no value) when not tracking
                    snr = int(self.gps_segments[sats+3])
                except ValueError:
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

    ##########################################
    # Data Stream Handler Functions
    ##########################################

    def new_sentence(self):
        """Adjust Object Flags in Preparation for a New Sentence"""
        self.gps_segments = ['']
        self.active_segment = 0
        self.crc_xor = 0
        self.sentence_active = True
        self.process_crc = True
        self.char_count = 0

    def update(self, new_char):
        """Process a new input char and updates GPS object if necessary based on special characters ('$', ',', '*')
        Function builds a list of received string that are validate by CRC prior to parsing by the  appropriate
        sentence function. Returns sentence type on successful parse, None otherwise"""

        valid_sentence = False

        # Validate new_char is a printable char
        ascii_char = ord(new_char)

        if 10 <= ascii_char <= 126:
            self.char_count += 1

            # Write Character to log file if enabled
            if self.log_en:
                self.write_log(new_char)

            # Check if a new string is starting ($)
            if new_char == '$':
                self.new_sentence()
                return None

            elif self.sentence_active:

                # Check if sentence is ending (*)
                if new_char == '*':
                    self.process_crc = False
                    self.active_segment += 1
                    self.gps_segments.append('')
                    return None

                # Check if a section is ended (,), Create a new substring to feed
                # characters to
                elif new_char == ',':
                    self.active_segment += 1
                    self.gps_segments.append('')

                # Store All Other printable character and check CRC when ready
                else:
                    self.gps_segments[self.active_segment] += new_char

                    # When CRC input is disabled, sentence is nearly complete
                    if not self.process_crc:

                        if len(self.gps_segments[self.active_segment]) == 2:
                            try:
                                final_crc = int(self.gps_segments[self.active_segment], 16)
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

    def new_fix_time(self):
        """Updates a high resolution counter with current time when fix is updated. Currently only triggered from
        GGA, GSA and RMC sentences"""
        try:
            self.fix_time = pyb.millis()
        except NameError:
            self.fix_time = time.time()

    #########################################
    # User Helper Functions
    # These functions make working with the GPS object data easier
    #########################################

    def satellite_data_updated(self):
        """
        Checks if the all the GSV sentences in a group have been read, making satellite data complete
        :return: boolean
        """
        if self.total_sv_sentences > 0 and self.total_sv_sentences == self.last_sv_sentence:
            return True
        else:
            return False

    def satellites_visible(self):
        """
        Returns a list of of the satellite PRNs currently visible to the receiver
        :return: list
        """
        return list(self.satellite_data.keys())

    def time_since_fix(self):
        """Returns number of millisecond since the last sentence with a valid fix was parsed. Returns 0 if
        no fix has been found"""

        # Test if a Fix has been found
        if self.fix_time == 0:
            return -1

        # Try calculating fix time assuming using millis on a pyboard; default to seconds if not
        try:
            current = pyb.elapsed_millis(self.fix_time)
        except NameError:
            current = time.time() - self.fix_time

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

    def latitude_string(self):
        """
        Create a readable string of the current latitude data
        :return: string
        """
        if self.coord_format == 'dd':
            formatted_latitude = self.latitude
            lat_string = str(formatted_latitude[0]) + '° ' + str(self._latitude[2])
        elif self.coord_format == 'dms':
            formatted_latitude = self.latitude
            lat_string = str(formatted_latitude[0]) + '° ' + str(formatted_latitude[1]) + "' " + str(formatted_latitude[2]) + '" ' + str(formatted_latitude[3])
        else:
            lat_string = str(self._latitude[0]) + '° ' + str(self._latitude[1]) + "' " + str(self._latitude[2])
        return lat_string

    def longitude_string(self):
        """
        Create a readable string of the current longitude data
        :return: string
        """
        if self.coord_format == 'dd':
            formatted_longitude = self.longitude
            lon_string = str(formatted_longitude[0]) + '° ' + str(self._longitude[2])
        elif self.coord_format == 'dms':
            formatted_longitude = self.longitude
            lon_string = str(formatted_longitude[0]) + '° ' + str(formatted_longitude[1]) + "' " + str(formatted_longitude[2]) + '" ' + str(formatted_longitude[3])
        else:
            lon_string = str(self._longitude[0]) + '° ' + str(self._longitude[1]) + "' " + str(self._longitude[2])
        return lon_string

    def speed_string(self, unit='kph'):
        """
        Creates a readable string of the current speed data in one of three units
        :param unit: string of 'kph','mph, or 'knot'
        :return:
        """
        if unit == 'mph':
            speed_string = str(self.speed[1]) + ' mph'

        elif unit == 'knot':
            if self.speed[0] == 1:
                unit_str = ' knot'
            else:
                unit_str = ' knots'
            speed_string = str(self.speed[0]) + unit_str

        else:
            speed_string = str(self.speed[2]) + ' km/h'

        return speed_string

    def date_string(self, formatting='s_mdy', century='20'):
        """
        Creates a readable string of the current date.
        Can select between long format: Januray 1st, 2014
        or two short formats:
        11/01/2014 (MM/DD/YYYY)
        01/11/2014 (DD/MM/YYYY)
        :param formatting: string 's_mdy', 's_dmy', or 'long'
        :param century: int delineating the century the GPS data is from (19 for 19XX, 20 for 20XX)
        :return: date_string  string with long or short format date
        """

        # Long Format Januray 1st, 2014
        if formatting == 'long':
            # Retrieve Month string from private set
            month = self.__MONTHS[self.date[1] - 1]

            # Determine Date Suffix
            if self.date[0] in (1, 21, 31):
                suffix = 'st'
            elif self.date[0] in (2, 22):
                suffix = 'nd'
            elif self.date[0] == 3:
                suffix = 'rd'
            else:
                suffix = 'th'

            day = str(self.date[0]) + suffix  # Create Day String

            year = century + str(self.date[2])  # Create Year String

            date_string = month + ' ' + day + ', ' + year  # Put it all together

        else:
            # Add leading zeros to day string if necessary
            if self.date[0] < 10:
                day = '0' + str(self.date[0])
            else:
                day = str(self.date[0])

            # Add leading zeros to month string if necessary
            if self.date[1] < 10:
                month = '0' + str(self.date[1])
            else:
                month = str(self.date[1])

            # Add leading zeros to year string if necessary
            if self.date[2] < 10:
                year = '0' + str(self.date[2])
            else:
                year = str(self.date[2])

            # Build final string based on desired formatting
            if formatting == 's_dmy':
                date_string = day + '/' + month + '/' + year

            else:  # Default date format
                date_string = month + '/' + day + '/' + year

        return date_string

    # All the currently supported NMEA sentences
    supported_sentences = {'GPRMC': gprmc, 'GPGGA': gpgga, 'GPVTG': gpvtg, 'GPGSA': gpgsa, 'GPGSV': gpgsv,
                           'GPGLL': gpgll}

if __name__ == "__main__":

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
