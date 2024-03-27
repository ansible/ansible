# -*- coding: utf-8 -*-
# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# Copyright 2019, Sviatoslav Sydorenko <webknjaz@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.common.text.formatters import human_to_bytes


NUM_IN_METRIC = {
    "K": 2**10,
    "M": 2**20,
    "G": 2**30,
    "T": 2**40,
    "P": 2**50,
    "E": 2**60,
    "Z": 2**70,
    "Y": 2**80,
}


@pytest.mark.parametrize(
    "input_data,expected",
    [
        (0, 0),
        ("0B", 0),
        (1024, NUM_IN_METRIC["K"]),
        ("1024B", NUM_IN_METRIC["K"]),
        ("1K", NUM_IN_METRIC["K"]),
        ("1KB", NUM_IN_METRIC["K"]),
        ("1M", NUM_IN_METRIC["M"]),
        ("1MB", NUM_IN_METRIC["M"]),
        ("1G", NUM_IN_METRIC["G"]),
        ("1GB", NUM_IN_METRIC["G"]),
        ("1T", NUM_IN_METRIC["T"]),
        ("1TB", NUM_IN_METRIC["T"]),
        ("1P", NUM_IN_METRIC["P"]),
        ("1PB", NUM_IN_METRIC["P"]),
        ("1E", NUM_IN_METRIC["E"]),
        ("1EB", NUM_IN_METRIC["E"]),
        ("1Z", NUM_IN_METRIC["Z"]),
        ("1ZB", NUM_IN_METRIC["Z"]),
        ("1Y", NUM_IN_METRIC["Y"]),
        ("1YB", NUM_IN_METRIC["Y"]),
    ],
)
def test_human_to_bytes_number(input_data, expected):
    """Test of human_to_bytes function, only number arg is passed."""
    assert human_to_bytes(input_data) == expected


@pytest.mark.parametrize(
    "input_data,unit",
    [
        ("1024", "B"),
        (1, "K"),
        (1, "KB"),
        ("1", "M"),
        ("1", "MB"),
        (1, "G"),
        (1, "GB"),
        (1, "T"),
        (1, "TB"),
        ("1", "P"),
        ("1", "PB"),
        ("1", "E"),
        ("1", "EB"),
        ("1", "Z"),
        ("1", "ZB"),
        ("1", "Y"),
        ("1", "YB"),
    ],
)
def test_human_to_bytes_number_unit(input_data, unit):
    """Test of human_to_bytes function, number and default_unit args are passed."""
    assert human_to_bytes(input_data, default_unit=unit) == NUM_IN_METRIC.get(
        unit[0], 1024
    )


@pytest.mark.parametrize(
    "test_input",
    [
        "1024s",
        "1024w",
    ],
)
def test_human_to_bytes_wrong_unit(test_input):
    """Test of human_to_bytes function, wrong units."""
    with pytest.raises(ValueError, match="The suffix must be one of"):
        human_to_bytes(test_input)


@pytest.mark.parametrize("test_input", ["b1bbb", "m2mmm", "", " ", -1])
def test_human_to_bytes_wrong_number(test_input):
    """Test of human_to_bytes function, number param is invalid string / number."""
    with pytest.raises(ValueError, match="can't interpret"):
        human_to_bytes(test_input)


@pytest.mark.parametrize(
    "input_data,expected",
    [
        (0, 0),
        ("0B", 0),
        ("1024b", 1024),
        ("1024B", 1024),
        ("1K", NUM_IN_METRIC["K"]),
        ("1Kb", NUM_IN_METRIC["K"]),
        ("1M", NUM_IN_METRIC["M"]),
        ("1Mb", NUM_IN_METRIC["M"]),
        ("1G", NUM_IN_METRIC["G"]),
        ("1Gb", NUM_IN_METRIC["G"]),
        ("1T", NUM_IN_METRIC["T"]),
        ("1Tb", NUM_IN_METRIC["T"]),
        ("1P", NUM_IN_METRIC["P"]),
        ("1Pb", NUM_IN_METRIC["P"]),
        ("1E", NUM_IN_METRIC["E"]),
        ("1Eb", NUM_IN_METRIC["E"]),
        ("1Z", NUM_IN_METRIC["Z"]),
        ("1Zb", NUM_IN_METRIC["Z"]),
        ("1Y", NUM_IN_METRIC["Y"]),
        ("1Yb", NUM_IN_METRIC["Y"]),
    ],
)
def test_human_to_bytes_isbits(input_data, expected):
    """Test of human_to_bytes function, isbits = True."""
    assert human_to_bytes(input_data, isbits=True) == expected


@pytest.mark.parametrize(
    "input_data,unit",
    [
        (1024, "b"),
        (1024, "B"),
        (1, "K"),
        (1, "Kb"),
        ("1", "M"),
        ("1", "Mb"),
        (1, "G"),
        (1, "Gb"),
        (1, "T"),
        (1, "Tb"),
        ("1", "P"),
        ("1", "Pb"),
        ("1", "E"),
        ("1", "Eb"),
        ("1", "Z"),
        ("1", "Zb"),
        ("1", "Y"),
        ("1", "Yb"),
    ],
)
def test_human_to_bytes_isbits_default_unit(input_data, unit):
    """Test of human_to_bytes function, isbits = True and default_unit args are passed."""
    assert human_to_bytes(
        input_data, default_unit=unit, isbits=True
    ) == NUM_IN_METRIC.get(unit[0], 1024)


@pytest.mark.parametrize(
    "test_input,isbits",
    [
        ("1024Kb", False),
        ("10Mb", False),
        ("1Gb", False),
        ("10MB", True),
        ("2KB", True),
        ("4GB", True),
    ],
)
def test_human_to_bytes_isbits_wrong_unit(test_input, isbits):
    """Test of human_to_bytes function, unit identifier is in an invalid format for isbits value."""
    with pytest.raises(ValueError, match="Value is not a valid string"):
        human_to_bytes(test_input, isbits=isbits)


@pytest.mark.parametrize(
    "test_input,unit,isbits",
    [
        (1024, "Kb", False),
        ("10", "Mb", False),
        ("10", "MB", True),
        (2, "KB", True),
        ("4", "GB", True),
    ],
)
def test_human_to_bytes_isbits_wrong_default_unit(test_input, unit, isbits):
    """Test of human_to_bytes function, default_unit is in an invalid format for isbits value."""
    with pytest.raises(ValueError, match="Value is not a valid string"):
        human_to_bytes(test_input, default_unit=unit, isbits=isbits)
