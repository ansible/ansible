# -*- coding: utf-8 -*-
# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.text.formatters import human_to_bytes


NUM_IN_METRIC = {
    'K': 1024,
    'M': 1048576,
    'G': 1073741824,
    'T': 1099511627776,
    'P': 1125899906842624,
    'E': 1152921504606846976,
    'Z': 1180591620717411303424,
    'Y': 1208925819614629174706176,
}


@pytest.mark.parametrize(
    'input_data,expected',
    [
        ((0, u'0B'), 0),
        ((1024, u'1024B'), NUM_IN_METRIC['K']),
        ((u'1K', u'1KB'), NUM_IN_METRIC['K']),
        ((u'1M', u'1MB'), NUM_IN_METRIC['M']),
        ((u'1G', u'1GB'), NUM_IN_METRIC['G']),
        ((u'1T', u'1TB'), NUM_IN_METRIC['T']),
        ((u'1P', u'1PB'), NUM_IN_METRIC['P']),
        ((u'1E', u'1EB'), NUM_IN_METRIC['E']),
        ((u'1Z', u'1ZB'), NUM_IN_METRIC['Z']),
        ((u'1Y', u'1YB'), NUM_IN_METRIC['Y']),
    ]
)
def test_human_to_bytes_number(input_data, expected):
    """Test of human_to_bytes function, only number arg is passed."""
    for elem in input_data:
        assert human_to_bytes(elem) == expected


@pytest.mark.parametrize(
    'input_data,units',
    [
        (u'1024', (u'B', u'B')),
        (1, (u'K', u'KB')),
        (u'1', (u'M', u'MB')),
        (1, (u'G', u'GB')),
        (1, (u'T', u'TB')),
        (u'1', (u'P', u'PB')),
        (u'1', (u'E', u'EB')),
        (u'1', (u'Z', u'ZB')),
        (u'1', (u'Y', u'YB')),
    ]
)
def test_human_to_bytes_number_unit(input_data, units):
    """Test of human_to_bytes function, number and default_unit args are passed."""
    for unit in units:
        if unit[0] == u'B':
            assert human_to_bytes(input_data, default_unit=unit) == int(input_data)
        else:
            assert human_to_bytes(input_data, default_unit=unit) == NUM_IN_METRIC[unit[0]]


@pytest.mark.parametrize('test_input', [u'1024s', u'1024w', ])
def test_human_to_bytes_wrong_unit(test_input):
    """Test of human_to_bytes function, wrong units."""
    with pytest.raises(ValueError, match="The suffix must be one of"):
        human_to_bytes(test_input)


@pytest.mark.parametrize('test_input', [u'b1bbb', u'm2mmm', u'', u' ', ])
def test_human_to_bytes_wrong_number(test_input):
    """Test of human_to_bytes function, number param is invalid string / number."""
    with pytest.raises(ValueError, match="can't interpret"):
        human_to_bytes(test_input)


@pytest.mark.parametrize(
    'input_data,expected',
    [
        ((0, u'0B'), 0),
        ((u'1024b', u'1024B'), 1024),
        ((u'1K', u'1Kb'), NUM_IN_METRIC['K']),
        ((u'1M', u'1Mb'), NUM_IN_METRIC['M']),
        ((u'1G', u'1Gb'), NUM_IN_METRIC['G']),
        ((u'1T', u'1Tb'), NUM_IN_METRIC['T']),
        ((u'1P', u'1Pb'), NUM_IN_METRIC['P']),
        ((u'1E', u'1Eb'), NUM_IN_METRIC['E']),
        ((u'1Z', u'1Zb'), NUM_IN_METRIC['Z']),
        ((u'1Y', u'1Yb'), NUM_IN_METRIC['Y']),
    ]
)
def test_human_to_bytes_isbits(input_data, expected):
    """Test of human_to_bytes function, isbits = True."""
    for elem in input_data:
        assert human_to_bytes(elem, isbits=True) == expected


@pytest.mark.parametrize(
    'input_data,units',
    [
        (1024, (u'b', u'B')),
        (1, (u'K', u'Kb')),
        (u'1', (u'M', u'Mb')),
        (1, (u'G', u'Gb')),
        (1, (u'T', u'Tb')),
        (u'1', (u'P', u'Pb')),
        (u'1', (u'E', u'Eb')),
        (u'1', (u'Z', u'Zb')),
        (u'1', (u'Y', u'Yb')),
    ]
)
def test_human_to_bytes_isbits_default_unit(input_data, units):
    """Test of human_to_bytes function, isbits = True and default_unit args are passed."""
    for unit in units:
        if unit[0].lower() == u'b':
            assert human_to_bytes(input_data, default_unit=unit, isbits=True) == int(input_data)
        else:
            assert human_to_bytes(input_data, default_unit=unit, isbits=True) == NUM_IN_METRIC[unit[0]]


@pytest.mark.parametrize(
    'test_input,isbits',
    [
        ('1024Kb', False),
        ('10Mb', False),
        ('1Gb', False),
        ('10MB', True),
        ('2KB', True),
        ('4GB', True),
    ]
)
def test_human_to_bytes_isbits_wrong_unit(test_input, isbits):
    """Test of human_to_bytes function, unit identifier is in an invalid format for isbits value."""
    with pytest.raises(ValueError, match="Value is not a valid string"):
        human_to_bytes(test_input, isbits=isbits)


@pytest.mark.parametrize(
    'test_input,unit,isbits',
    [
        (1024, 'Kb', False),
        ('10', 'Mb', False),
        ('10', 'MB', True),
        (2, 'KB', True),
        ('4', 'GB', True),
    ]
)
def test_human_to_bytes_isbits_wrong_default_unit(test_input, unit, isbits):
    """Test of human_to_bytes function, default_unit is in an invalid format for isbits value."""
    with pytest.raises(ValueError, match="Value is not a valid string"):
        human_to_bytes(test_input, default_unit=unit, isbits=isbits)
