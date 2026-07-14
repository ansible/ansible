# (c) 2015, Marius Gedminas <marius@gedmin.as>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from datetime import datetime

from ansible.utils.helpers import pct_to_int, object_to_dict, deduplicate_list


pct_to_int_testdata = [
    pytest.param(
        1, 100, 1, 1, id="positive_percentage"
    ),
    pytest.param(
        -1, 100, 1, -1, id="negative_percentage"
    ),
    pytest.param(
        "1%", 10, 1, 1, id="string_percentage"
    ),
    pytest.param(
        "1%", 10, 0, 0, id="string_percentage_with_zero_min_value"
    ),
    pytest.param(
        "1", 100, 1, 1, id="string_percentage_without_sign"
    ),
    pytest.param(
        "10%", 100, 1, 10, id="string_percentage_two_digit"
    )
]


@pytest.mark.parametrize("value,num_items,min_value,expected", pct_to_int_testdata)
def test_pct_to_int(value, num_items, min_value, expected):
    assert pct_to_int(value, num_items, min_value) == expected


def test_object_to_dict():
    test_dict = object_to_dict(datetime(2024, 7, 30))
    assert test_dict['day'] == 30
    assert test_dict['year'] == 2024
    assert test_dict['month'] == 7

    test_dict_without_day = object_to_dict(datetime(2024, 7, 30), exclude=['day'])
    assert 'day' not in list(test_dict_without_day.keys())


def test_deduplicate_list():
    assert deduplicate_list([1, 2, 2, 3]) == [1, 2, 3]
    assert deduplicate_list([1, 2, 3]) == [1, 2, 3]
