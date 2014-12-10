from struct import *

# TODO:
# GSV Sentence
# Time Since First Fix
# Time Since Last Good Fix
# Statistics
# Sentence size bound checking

test_RMC = ['$GPRMC,081836,A,3751.65,S,14507.36,E,000.0,360.0,130998,011.3,E*62',
            '$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A',
            '$GPRMC,225446,A,4916.45,N,12311.12,W,000.5,054.7,191194,020.3,E*68',
            '$GPRMC,180041.896,A,3749.1851,N,08338.7891,W,001.9,154.9,240911,,,A*7A',
            '$GPRMC,180049.896,A,3749.1808,N,08338.7869,W,001.8,156.3,240911,,,A*70',
            '$GPRMC,092751.000,A,5321.6802,N,00630.3371,W,0.06,31.66,280511,,,A*45']

test_VTG = ['$GPVTG,232.9,T,,M,002.3,N,004.3,K,A*01']
test_GGA = ['$GPGGA,180050.896,3749.1802,N,08338.7865,W,1,07,1.1,397.4,M,-32.5,M,,0000*6C']
test_GSA = ['$GPGSA,A,3,07,11,28,24,26,08,17,,,,,,2.0,1.1,1.7*37',
            '$GPGSA,A,3,07,02,26,27,09,04,15,,,,,,1.8,1.0,1.5*33']
test_GSV = ['$GPGSV,3,1,12,28,72,355,39,01,52,063,33,17,51,272,44,08,46,184,38*74',
            '$GPGSV,3,2,12,24,42,058,33,11,34,053,33,07,20,171,40,20,15,116,*71',
            '$GPGSV,3,3,12,04,12,204,34,27,11,324,35,32,11,089,,26,10,264,40*7B']


class MicroGPSpy(object):
    """GPS NMEA Sentence Parser"""

    def __init__(self, local_offset=0):
        """Setup GPS Object Status Flags, Internal Data Registers, etc"""

        #####################
        # Object Status Flags
        self.sentence_active = False
        self.active_segment = 0
        self.process_crc = False
        self.gps_segments = []
        self.crc_xor = 0

        #####################
        # Data From Sentences
        # Time
        self.timestamp = (0, 0, 0)
        self.date = (0, 0, 0)
        self.local_offset = local_offset

        # Position/Motion
        self.latitude = (0, 0.0, 'N')
        self.longitude = (0, 0.0, 'W')
        self.speed = (0.0, 0.0, 0.0)
        self.course = 0.0
        self.altitude = 0.0
        self.geoid_height = 0.0

        # GPS Info
        self.satellites_in_view = 0
        self.satellites_in_use = 0
        self.satellites_used = []
        self.hdop = 0.0
        self.pdop = 0.0
        self.vdop = 0.0
        self.valid = False
        self.fix_stat = 0
        self.fix_type = 1

        # Object Constants
        self.__hemispheres = ('N', 'S', 'E', 'W')

    def gprmc(self):
        """Parse Recommended Minimum Specific GPS/Transit data (RMC)Sentence. Updates UTC timestamp, latitude,
        longitude, Course, Speed, and Date"""

        # UTC Timestamp
        try:
            utc_string = self.gps_segments[1]
            # Skip timestamp if receiver doesn't have one yet
            if utc_string:
                hours = int(utc_string[0:2]) + self.local_offset
                minutes = int(utc_string[2:4])
                seconds = float(utc_string[4:])
                self.timestamp = (hours, minutes, seconds)
        except ValueError:
            return False

        # Check Receiver Data Valid Flag
        if self.gps_segments[2] == 'A':  # Data from Receiver is valid

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

            if lat_hemi not in self.__hemispheres:
                return False

            if lon_hemi not in self.__hemispheres:
                return False

            # Speed
            try:
                spd_knt = float(self.gps_segments[7])
            except ValueError:
                return False

            # Date
            try:
                # NOTE!!! Date string is assumed to be year >=2000,
                # Sentences recorded in 90s will display as 209X!!!
                # FIXME if you want to parse old GPS logs or are time traveler
                date_string = self.gps_segments[9]
                day = date_string[0:2]
                month = date_string[2:4]
                year = date_string[4:6]
            except ValueError:
                return False

            # Course
            try:
                course = self.gps_segments[8]
            except ValueError:
                return False

            # TODO - Add Magnetic Variation

            # Update Object Data
            self.latitude = (lat_degs, lat_mins, lat_hemi)
            self.longitude = (lon_degs, lon_mins, lon_hemi)
            # Include mph and hm/h
            self.speed = (spd_knt, spd_knt * 1.151, spd_knt * 1.852)
            self.date = (day, month, year)
            self.course = course
            self.valid = True

        else:
            return False

        return True

    def gpvtg(self):
        """Parse Track Made Good and Ground Speed (VTG) Sentence. Updates speed and course"""
        try:
            course = self.gps_segments[1]
            spd_knt = float(self.gps_segments[5])
        except ValueError:
            return False

        # Include mph and hm/h
        self.speed = (spd_knt, spd_knt * 1.151, spd_knt * 1.852)
        self.course = course
        return True

    def gpgga(self):
        """Parse Global Positioning System Fix Data (GGA) Sentence. Updates UTC timestamp, latitude, longitude,
        fix status, satellites in use, Horizontal Dilution of Precision (HDOP), altitude, and geoid height"""

        # UTC Timestamp
        try:
            utc_string = self.gps_segments[1]
            # Skip timestamp if receiver doesn't have on yet
            if utc_string:
                hours = int(utc_string[0:2]) + self.local_offset
                minutes = int(utc_string[2:4])
                seconds = float(utc_string[4:])
                self.timestamp = (hours, minutes, seconds)
        except ValueError:
            return False

        # Number of Satellites in Use
        try:
            self.satellites_in_use = int(self.gps_segments[7])
        except ValueError:
            return False

        # Horizontal Dilution of Precision
        try:
            self.hdop = float(self.gps_segments[8])
        except ValueError:
            return False

        # Get Fix Status
        try:
            self.fix_stat = int(self.gps_segments[6])
        except ValueError:
            return False

        # Process Location and Speed Data if Fix is GOOD
        if self.fix_stat:

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

            if lat_hemi not in self.__hemispheres:
                return False

            if lon_hemi not in self.__hemispheres:
                return False

            # Altitude / Height Above Geoid
            try:
                altitude = float(self.gps_segments[9])
                geoid_height = float(self.gps_segments[11])
            except ValueError:
                return False

            # Update Object Data
            self.latitude = (lat_degs, lat_mins, lat_hemi)
            self.longitude = (lon_degs, lon_mins, lon_hemi)
            self.altitude = altitude
            self.geoid_height = geoid_height

        return True

    def gpgsa(self):
        """Parse GNSS DOP and Active Satellites (GSA) sentence. Updates GPS fix type, list of satellites used in
        fix calculation, Position Dilution of Precision (PDOP), Horizontal Dilution of Precision (HDOP), and Vertical
        Dilution of Precision"""

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
        self.satellites_used = sats_used
        self.hdop = hdop
        self.vdop = vdop
        self.pdop = pdop

        return True

    def gpgsv(self):
        pass

    def new_sentence(self):
        """Adjust Object Flags in Preparation for a New Sentence"""
        self.gps_segments = ['']
        self.active_segment = 0
        self.crc_xor = 0
        self.sentence_active = True
        self.process_crc = True

    def update(self, new_char):
        """Process a new input char and updates GPS object if necessary based on special characters ('$', ',', '*')
        Function builds a list of received string that are validate by CRC prior to parsing by the  appropriate
        sentence function. Returns sentence type on successful parse, None otherwise"""

        valid_sentence = False

        # Validate new_char is a printable char
        ascii_char = ord(new_char)

        if 33 <= ascii_char <= 126:

            # Check if a new string is starting ($)
            if new_char == '$':
                self.new_sentence()
                return False

            # Check if sentence is ending (*)
            elif new_char == '*':
                self.process_crc = False
                self.active_segment += 1
                self.gps_segments.append('')
                return False

            # Check if a section is ended (,), Create a new substring to feed
            # characters to
            elif new_char == ',':
                self.active_segment += 1
                self.gps_segments.append('')

            # Store All Other printable character and check CRC when ready
            else:
                if self.sentence_active:
                    self.gps_segments[self.active_segment] += new_char

                    # When CRC input is disabled, sentence is nearly complete
                    if not self.process_crc:

                        if len(self.gps_segments[self.active_segment]) == 2:
                            try:
                                final_crc = int(self.gps_segments[self.active_segment], 16)
                                if self.crc_xor == final_crc:
                                    valid_sentence = True
                            except ValueError:
                                pass  # CRC Value was deformed and could not have been correct

            # Update CRC
            if self.process_crc:
                self.crc_xor ^= ascii_char

        # If a Valid Sentence Was received and it's a supported sentence, then
        # parse it!!
        if valid_sentence and self.gps_segments[0] in self.supported_sentences:

            # Clear Active Processing Flag
            self.sentence_active = False

            # parse the Sentence Based on the message type, return True if
            # parse is clean
            if self.supported_sentences[self.gps_segments[0]](self):
                # Let host know that the GPS object was updated by returning
                # parsed sentence type
                return self.gps_segments[0]

        # Tell Host no new sentence was parsed
        return None

    # All the currently supported NMEA sentences    
    supported_sentences = {'GPRMC': gprmc, 'GPGGA': gpgga, 'GPVTG': gpvtg, 'GPGSA': gpgsa, 'GPGSV': gpgsv}


if __name__ == "__main__":

    my_gps = MicroGPSpy()
    sentence = ''
    for RMC_sentence in test_RMC:
        for y in RMC_sentence:
            sentence = my_gps.update(y)
        print('Parsed a', sentence, 'Sentence')
        print('Parsed Strings:', my_gps.gps_segments)
        print('Sentence CRC Value:', hex(my_gps.crc_xor))
        print('Longitude:', my_gps.longitude)
        print('Latitude', my_gps.latitude)
        print('UTC Timestamp:', my_gps.timestamp)
        print('Speed:', my_gps.speed)
        print('Date Stamp:', my_gps.date)
        print('Course', my_gps.course)
        print('Data is Valid', my_gps.valid)
        print('')

    for VTG_sentence in test_VTG:
        for y in VTG_sentence:
            sentence = my_gps.update(y)
        print('Parsed a', sentence, 'Sentence')
        print('Parsed Strings', my_gps.gps_segments)
        print('Sentence CRC Value:', hex(my_gps.crc_xor))
        print('Speed:', my_gps.speed)
        print('Course', my_gps.course)
        print('')

    for GGA_sentence in test_GGA:
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
