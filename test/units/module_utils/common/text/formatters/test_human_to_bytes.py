# -*- coding: utf-8 -*-
# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# Copyright 2019, Sviatoslav Sydorenko <webknjaz@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.common.text.formatters import human_to_bytes


NUM_IN_METRIC = {
    'K': 2 ** 10,
    'M': 2 ** 20,
    'G': 2 ** 30,
    'T': 2 ** 40,
    'P': 2 ** 50,
    'E': 2 ** 60,
    'Z': 2 ** 70,
    'Y': 2 ** 80,
}


@pytest.mark.parametrize(
    'input_data,expected',
    [
        (0, 0),
        (u'0B', 0),
        (1024, NUM_IN_METRIC['K']),
        (u'1024B', NUM_IN_METRIC['K']),
        (u'1K', NUM_IN_METRIC['K']),
        (u'1KB', NUM_IN_METRIC['K']),
        (u'1M', NUM_IN_METRIC['M']),
        (u'1MB', NUM_IN_METRIC['M']),
        (u'1G', NUM_IN_METRIC['G']),
        (u'1GB', NUM_IN_METRIC['G']),
        (u'1T', NUM_IN_METRIC['T']),
        (u'1TB', NUM_IN_METRIC['T']),
        (u'1P', NUM_IN_METRIC['P']),
        (u'1PB', NUM_IN_METRIC['P']),
        (u'1E', NUM_IN_METRIC['E']),
        (u'1EB', NUM_IN_METRIC['E']),
        (u'1Z', NUM_IN_METRIC['Z']),
        (u'1ZB', NUM_IN_METRIC['Z']),
        (u'1Y', NUM_IN_METRIC['Y']),
        (u'1YB', NUM_IN_METRIC['Y']),
    ]
)
def test_human_to_bytes_number(input_data, expected):
    """Test of human_to_bytes function, only number arg is passed."""
    assert human_to_bytes(input_data) == expected


@pytest.mark.parametrize(
    'input_data,unit',
    [
        (u'1024', 'B'),
        (1, u'K'),
        (1, u'KB'),
        (u'1', u'M'),
        (u'1', u'MB'),
        (1, u'G'),
        (1, u'GB'),
        (1, u'T'),
        (1, u'TB'),
        (u'1', u'P'),
        (u'1', u'PB'),
        (u'1', u'E'),
        (u'1', u'EB'),
        (u'1', u'Z'),
        (u'1', u'ZB'),
        (u'1', u'Y'),
        (u'1', u'YB'),
    ]
)
def test_human_to_bytes_number_unit(input_data, unit):
    """Test of human_to_bytes function, number and default_unit args are passed."""
    assert human_to_bytes(input_data, default_unit=unit) == NUM_IN_METRIC.get(unit[0], 1024)


@pytest.mark.parametrize('test_input', [u'1024s', u'1024w', ])
def test_human_to_bytes_wrong_unit(test_input):
    """Test of human_to_bytes function, wrong units."""
    with pytest.raises(ValueError, match="The suffix must be one of"):
        human_to_bytes(test_input)


@pytest.mark.parametrize('test_input', [u'b1bbb', u'm2mmm', u'', u' ', -1])
def test_human_to_bytes_wrong_number(test_input):
    """Test of human_to_bytes function, number param is invalid string / number."""
    with pytest.raises(ValueError, match="can't interpret"):
        human_to_bytes(test_input)


@pytest.mark.parametrize(
    'input_data,expected',
    [
        (0, 0),
        (u'0B', 0),
        (u'1024b', 1024),
        (u'1024B', 1024),
        (u'1K', NUM_IN_METRIC['K']),
        (u'1Kb', NUM_IN_METRIC['K']),
        (u'1M', NUM_IN_METRIC['M']),
        (u'1Mb', NUM_IN_METRIC['M']),
        (u'1G', NUM_IN_METRIC['G']),
        (u'1Gb', NUM_IN_METRIC['G']),
        (u'1T', NUM_IN_METRIC['T']),
        (u'1Tb', NUM_IN_METRIC['T']),
        (u'1P', NUM_IN_METRIC['P']),
        (u'1Pb', NUM_IN_METRIC['P']),
        (u'1E', NUM_IN_METRIC['E']),
        (u'1Eb', NUM_IN_METRIC['E']),
        (u'1Z', NUM_IN_METRIC['Z']),
        (u'1Zb', NUM_IN_METRIC['Z']),
        (u'1Y', NUM_IN_METRIC['Y']),
        (u'1Yb', NUM_IN_METRIC['Y']),
    ]
)
def test_human_to_bytes_isbits(input_data, expected):
    """Test of human_to_bytes function, isbits = True."""
    assert human_to_bytes(input_data, isbits=True) == expected


@pytest.mark.parametrize(
    'input_data,unit',
    [
        (1024, 'b'),
        (1024, 'B'),
        (1, u'K'),
        (1, u'Kb'),
        (u'1', u'M'),
        (u'1', u'Mb'),
        (1, u'G'),
        (1, u'Gb'),
        (1, u'T'),
        (1, u'Tb'),
        (u'1', u'P'),
        (u'1', u'Pb'),
        (u'1', u'E'),
        (u'1', u'Eb'),
        (u'1', u'Z'),
        (u'1', u'Zb'),
        (u'1', u'Y'),
        (u'1', u'Yb'),
    ]
)
def test_human_to_bytes_isbits_default_unit(input_data, unit):
    """Test of human_to_bytes function, isbits = True and default_unit args are passed."""
    assert human_to_bytes(input_data, default_unit=unit, isbits=True) == NUM_IN_METRIC.get(unit[0], 1024)


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


@pytest.mark.parametrize(
    'test_input',
    [
        '10 BBQ sticks please',
        '3000 GB guns of justice',
        '1 EBOOK please',
        '3 eBulletins please',
        '1 bBig family',
    ]
)
def test_human_to_bytes_nonsensical_inputs_first_two_letter_unit(test_input):
    """Test of human_to_bytes function to ensure it raises ValueError for nonsensical inputs that has the first two
    letters as a unit."""
    expected = "can't interpret following string"
    with pytest.raises(ValueError, match=expected):
        human_to_bytes(test_input)


@pytest.mark.parametrize(
    'test_input',
    [
        '12,000 MB',
        '12 000 MB',
        '- |\n   1\n   kB',
        '          12',
        ' 12 MB',  # OGHAM SPACE MARK
        '1\u200B000 MB',  # U+200B zero-width space after 1
    ]
)
def test_human_to_bytes_non_number_truncate_result(test_input):
    """Test of human_to_bytes function to ensure it raises ValueError for handling non-number character and
    truncating result"""
    expected = "can't interpret following string"
    with pytest.raises(ValueError, match=expected):
        human_to_bytes(test_input)


@pytest.mark.parametrize(
    'test_input',
    [
        '3 eBulletins',
        '.1 Geggabytes',
        '3 prettybytes',
        '13youcanhaveabyteofmysandwich',
        '.1 Geggabytes',
        '10 texasburgerbytes',
        '12 muppetbytes',
    ]
)
def test_human_to_bytes_nonsensical(test_input):
    """Test of human_to_bytes function to ensure it raises ValueError for nonsensical input with first letter matches
    [BEGKMPTYZ] and word contains byte"""
    expected = "Value is not a valid string"
    with pytest.raises(ValueError, match=expected):
        human_to_bytes(test_input)


@pytest.mark.parametrize(
    'test_input',
    [
        '8𖭙B',
        '၀k',
        '1.၀k?',
        '᭔ MB'
    ]
)
def test_human_to_bytes_non_ascii_number(test_input):
    """Test of human_to_bytes function,correctly filtering out non ASCII characters"""
    expected = "can't interpret following string"
    with pytest.raises(ValueError, match=expected):
        human_to_bytes(test_input)
