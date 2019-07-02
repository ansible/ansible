# -*- coding: utf-8 -*-
# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.text.formatters import human_to_bytes


@pytest.mark.parametrize(
    'input_data,expected',
    [
        (0, 0),
        (1024, 1024),
        (u'1024B', 1024),
        (u'0B', 0),
        (u'1K', 1024),
        (u'1KB', 1024),
        (u'1MB', 1048576),
        (u'1M', 1048576),
        (u'1G', 1073741824),
        (u'1GB', 1073741824),
        (u'1T', 1099511627776),
        (u'1TB', 1099511627776),
        (u'1P', 1125899906842624),
        (u'1PB', 1125899906842624),
        (u'1E', 1152921504606846976),
        (u'1EB', 1152921504606846976),
        (u'1Z', 1180591620717411303424),
        (u'1ZB', 1180591620717411303424),
        (u'1Y', 1208925819614629174706176),
        (u'1YB', 1208925819614629174706176),
    ]
)
def test_human_to_bytes_number(input_data, expected):
    """Test of human_to_bytes function, only number arg is passed."""
    assert human_to_bytes(input_data) == expected


@pytest.mark.parametrize(
    'input_data,unit,expected',
    [
        (u'1024', u'B', 1024),
        (1, u'K', 1024),
        (1, u'KB', 1024),
        (u'1', u'M', 1048576),
        (u'1', u'MB', 1048576),
        (1, u'G', 1073741824),
        (1, u'GB', 1073741824),
        (1, u'T', 1099511627776),
        (1, u'TB', 1099511627776),
        (u'1', u'P', 1125899906842624),
        (u'1', u'PB', 1125899906842624),
        (u'1', u'E', 1152921504606846976),
        (u'1', u'EB', 1152921504606846976),
        (u'1', u'Z', 1180591620717411303424),
        (u'1', u'ZB', 1180591620717411303424),
        (u'1', u'Y', 1208925819614629174706176),
        (u'1', u'YB', 1208925819614629174706176),
    ]
)
def test_human_to_bytes_number_unit(input_data, unit, expected):
    """Test of human_to_bytes function, number and default_unit args are passed."""
    assert human_to_bytes(input_data, default_unit=unit) == expected


@pytest.mark.parametrize('test_input', [u'1024s', u'1024w', ])
def test_human_to_bytes_wrong_unit(test_input):
    """Test of human_to_bytes function, wrong units."""
    with pytest.raises(ValueError, match="The suffix must be one of"):
        human_to_bytes(test_input)


@pytest.mark.parametrize('test_input', [u'b1bbb', u'm2mmm', u'', u' ', ])
def test_human_to_bytes_wrong_number(test_input):
    """Test of human_to_bytes function, nubmer param is invalid string / number."""
    with pytest.raises(ValueError, match="can't interpret"):
        human_to_bytes(test_input)


@pytest.mark.parametrize(
    'input_data,expected',
    [
        (0, 0),
        (1024, 1024),
        (u'1024b', 1024),
        (u'1024B', 1024),
        (u'0B', 0),
        (u'1K', 1024),
        (u'1Kb', 1024),
        (u'1M', 1048576),
        (u'1Mb', 1048576),
        (u'1G', 1073741824),
        (u'1Gb', 1073741824),
        (u'1T', 1099511627776),
        (u'1Tb', 1099511627776),
        (u'1P', 1125899906842624),
        (u'1Pb', 1125899906842624),
        (u'1E', 1152921504606846976),
        (u'1Eb', 1152921504606846976),
        (u'1Z', 1180591620717411303424),
        (u'1Zb', 1180591620717411303424),
        (u'1Y', 1208925819614629174706176),
        (u'1Yb', 1208925819614629174706176),
    ]
)
def test_human_to_bytes_isbits(input_data, expected):
    """Test of human_to_bytes function, isbits = True."""
    assert human_to_bytes(input_data, isbits=True) == expected


@pytest.mark.parametrize(
    'input_data,unit,expected',
    [
        (1024, u'b', 1024),
        (u'1024', u'B', 1024),
        (1, u'K', 1024),
        (1, u'Kb', 1024),
        (u'1', u'M', 1048576),
        (u'1', u'Mb', 1048576),
        (1, u'G', 1073741824),
        (1, u'Gb', 1073741824),
        (1, u'T', 1099511627776),
        (1, u'Tb', 1099511627776),
        (u'1', u'P', 1125899906842624),
        (u'1', u'Pb', 1125899906842624),
        (u'1', u'E', 1152921504606846976),
        (u'1', u'Eb', 1152921504606846976),
        (u'1', u'Z', 1180591620717411303424),
        (u'1', u'Zb', 1180591620717411303424),
        (u'1', u'Y', 1208925819614629174706176),
        (u'1', u'Yb', 1208925819614629174706176),
    ]
)
def test_human_to_bytes_isbits_default_unit(input_data, unit, expected):
    """Test of human_to_bytes function, isbits = True and default_unit args are passed."""
    assert human_to_bytes(input_data, default_unit=unit, isbits=True) == expected


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
