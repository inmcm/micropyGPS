"""Character-stream regressions for fractional timezone offsets (#38)."""
import pytest
from micropyGPS import MicropyGPS
from test_micropyGPS import test_RMC, test_GGA, test_GLL


def timed_sentence(template, utc):
    fields = template[1:template.index('*')].split(',')
    fields[5 if fields[0].endswith('GLL') else 1] = utc
    body = ','.join(fields)
    checksum = 0
    for char in body:
        checksum ^= ord(char)
    return '$%s*%02X\r\n' % (body, checksum)


def feed(gps, sentence):
    parsed = []
    for char in sentence:
        result = gps.update(char)
        if result:
            parsed.append(result)
    return parsed


@pytest.mark.parametrize('template', [test_RMC[0], test_GGA[0], test_GLL[0]])
@pytest.mark.parametrize('utc,offset,expected', [
    ('234512.5', 5.5, [5, 15, 12.5]),
    ('001512.5', -3.5, [20, 45, 12.5]),
    ('234512.5', 12.75, [12, 30, 12.5]),
    ('001512.5', -9.5, [14, 45, 12.5]),
    ('234512.5', 0, [23, 45, 12.5]),
    ('234512.5', -5, [18, 45, 12.5]),
])
def test_fractional_offset(template, utc, offset, expected):
    gps = MicropyGPS(offset)
    assert feed(gps, timed_sentence(template, utc)) == [template[1:6]]
    assert gps.timestamp == expected
    assert isinstance(gps.timestamp[0], int)
    assert isinstance(gps.timestamp[1], int)
    # The documented date remains UTC, even if the local time crosses midnight.
    if template[1:6] == 'GPRMC':
        assert gps.date == (13, 9, 98)


@pytest.mark.parametrize('template', [test_RMC[0], test_GGA[0], test_GLL[0]])
def test_offset_can_change_between_messages(template):
    gps = MicropyGPS()
    message = timed_sentence(template, '001512.5')
    feed(gps, message)
    assert gps.timestamp == [0, 15, 12.5]
    gps.local_offset = -3.5
    feed(gps, message)
    assert gps.timestamp == [20, 45, 12.5]
