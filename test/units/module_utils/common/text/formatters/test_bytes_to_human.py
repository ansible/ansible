# -*- coding: utf-8 -*-
# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.common.text.formatters import bytes_to_human


@pytest.mark.parametrize(
    "input_data,expected",
    [
        (0, "0.00 Bytes"),
        (0.5, "0.50 Bytes"),
        (0.54, "0.54 Bytes"),
        (1024, "1.00 KB"),
        (1025, "1.00 KB"),
        (1536, "1.50 KB"),
        (1790, "1.75 KB"),
        (1048576, "1.00 MB"),
        (1073741824, "1.00 GB"),
        (1099511627776, "1.00 TB"),
        (1125899906842624, "1.00 PB"),
        (1152921504606846976, "1.00 EB"),
        (1180591620717411303424, "1.00 ZB"),
        (1208925819614629174706176, "1.00 YB"),
    ],
)
def test_bytes_to_human(input_data, expected):
    """Test of bytes_to_human function, only proper numbers are passed."""
    assert bytes_to_human(input_data) == expected


@pytest.mark.parametrize(
    "input_data,expected",
    [
        (0, "0.00 bits"),
        (0.5, "0.50 bits"),
        (0.54, "0.54 bits"),
        (1024, "1.00 Kb"),
        (1025, "1.00 Kb"),
        (1536, "1.50 Kb"),
        (1790, "1.75 Kb"),
        (1048576, "1.00 Mb"),
        (1073741824, "1.00 Gb"),
        (1099511627776, "1.00 Tb"),
        (1125899906842624, "1.00 Pb"),
        (1152921504606846976, "1.00 Eb"),
        (1180591620717411303424, "1.00 Zb"),
        (1208925819614629174706176, "1.00 Yb"),
    ],
)
def test_bytes_to_human_isbits(input_data, expected):
    """Test of bytes_to_human function with isbits=True proper results."""
    assert bytes_to_human(input_data, isbits=True) == expected


@pytest.mark.parametrize(
    "input_data,unit,expected",
    [
        (0, "B", "0.00 Bytes"),
        (0.5, "B", "0.50 Bytes"),
        (0.54, "B", "0.54 Bytes"),
        (1024, "K", "1.00 KB"),
        (1536, "K", "1.50 KB"),
        (1790, "K", "1.75 KB"),
        (1048576, "M", "1.00 MB"),
        (1099511627776, "T", "1.00 TB"),
        (1152921504606846976, "E", "1.00 EB"),
        (1180591620717411303424, "Z", "1.00 ZB"),
        (1208925819614629174706176, "Y", "1.00 YB"),
        (1025, "KB", "1025.00 Bytes"),
        (1073741824, "Gb", "1073741824.00 Bytes"),
        (1125899906842624, "Pb", "1125899906842624.00 Bytes"),
    ],
)
def test_bytes_to_human_unit(input_data, unit, expected):
    """Test unit argument of bytes_to_human function proper results."""
    assert bytes_to_human(input_data, unit=unit) == expected


@pytest.mark.parametrize(
    "input_data,unit,expected",
    [
        (0, "B", "0.00 bits"),
        (0.5, "B", "0.50 bits"),
        (0.54, "B", "0.54 bits"),
        (1024, "K", "1.00 Kb"),
        (1536, "K", "1.50 Kb"),
        (1790, "K", "1.75 Kb"),
        (1048576, "M", "1.00 Mb"),
        (1099511627776, "T", "1.00 Tb"),
        (1152921504606846976, "E", "1.00 Eb"),
        (1180591620717411303424, "Z", "1.00 Zb"),
        (1208925819614629174706176, "Y", "1.00 Yb"),
        (1025, "KB", "1025.00 bits"),
        (1073741824, "Gb", "1073741824.00 bits"),
        (1125899906842624, "Pb", "1125899906842624.00 bits"),
    ],
)
def test_bytes_to_human_unit_isbits(input_data, unit, expected):
    """Test unit argument of bytes_to_human function with isbits=True proper results."""
    assert bytes_to_human(input_data, isbits=True, unit=unit) == expected


@pytest.mark.parametrize("input_data", [0j, "1B", [1], {1: 1}, None, b"1B"])
def test_bytes_to_human_illegal_size(input_data):
    """Test of bytes_to_human function, illegal objects are passed as a size."""
    e_regexp = (
        r"(no ordering relation is defined for complex numbers)|"
        r"(unsupported operand type\(s\) for /)|(unorderable types)|"
        r"(not supported between instances of)"
    )
    with pytest.raises(TypeError, match=e_regexp):
        bytes_to_human(input_data)
