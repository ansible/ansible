# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from jinja2 import Environment

import ansible.plugins.filter.mathstuff as ms
from ansible.errors import AnsibleError

UNIQUE_DATA: list[tuple[list, list]] = [
    ([], []),
    ([1, 3, 4, 2], [1, 3, 4, 2]),
    ([1, 3, 2, 4, 2, 3], [1, 3, 2, 4]),
    ([1, 2, 3, 4], [1, 2, 3, 4]),
    ([1, 1, 4, 2, 1, 4, 3, 2], [1, 4, 2, 3]),
]

TWO_SETS_DATA: list[tuple[list, list, tuple]] = [
    ([], [], ([], [], [])),
    ([1, 2], [1, 2], ([1, 2], [], [])),
    ([1, 2], [3, 4], ([], [1, 2], [1, 2, 3, 4])),
    ([1, 2, 3], [5, 3, 4], ([3], [1, 2], [1, 2, 5, 4])),
    ([1, 2, 3], [4, 3, 5], ([3], [1, 2], [1, 2, 4, 5])),
]


def dict_values(values: list[int]) -> list[dict[str, int]]:
    """Return a list of non-hashable values derived from the given list."""
    return [dict(x=value) for value in values]


for _data, _expected in list(UNIQUE_DATA):
    UNIQUE_DATA.append((dict_values(_data), dict_values(_expected)))

for _dataset1, _dataset2, _expected in list(TWO_SETS_DATA):
    TWO_SETS_DATA.append((dict_values(_dataset1), dict_values(_dataset2), tuple(dict_values(answer) for answer in _expected)))


env = Environment()


def assert_lists_contain_same_elements(a, b) -> None:
    """Assert that the two values given are lists that contain the same elements, even when the elements cannot be sorted or hashed."""
    assert isinstance(a, list)
    assert isinstance(b, list)

    missing_from_a = [item for item in b if item not in a]
    missing_from_b = [item for item in a if item not in b]

    assert not missing_from_a, f'elements from `b` {missing_from_a} missing from `a` {a}'
    assert not missing_from_b, f'elements from `a` {missing_from_b} missing from `b` {b}'


@pytest.mark.parametrize('data, expected', UNIQUE_DATA, ids=str)
def test_unique(data, expected):
    assert_lists_contain_same_elements(ms.unique(env, data), expected)


@pytest.mark.parametrize('dataset1, dataset2, expected', TWO_SETS_DATA, ids=str)
def test_intersect(dataset1, dataset2, expected):
    assert_lists_contain_same_elements(ms.intersect(env, dataset1, dataset2), expected[0])


@pytest.mark.parametrize('dataset1, dataset2, expected', TWO_SETS_DATA, ids=str)
def test_difference(dataset1, dataset2, expected):
    assert_lists_contain_same_elements(ms.difference(env, dataset1, dataset2), expected[1])


@pytest.mark.parametrize('dataset1, dataset2, expected', TWO_SETS_DATA, ids=str)
def test_symmetric_difference(dataset1, dataset2, expected):
    assert_lists_contain_same_elements(ms.symmetric_difference(env, dataset1, dataset2), expected[2])


class TestLogarithm:
    def test_log_non_number(self):
        with pytest.raises(AnsibleError, match='log\\(\\) can only be used on numbers: must be real number, not str'):
            ms.logarithm('a')
        with pytest.raises(AnsibleError, match='log\\(\\) can only be used on numbers: must be real number, not str'):
            ms.logarithm(10, base='a')

    def test_log_ten(self):
        assert ms.logarithm(10, 10) == 1.0
        assert ms.logarithm(69, 10) * 1000 // 1 == 1838

    def test_log_natural(self):
        assert ms.logarithm(69) * 1000 // 1 == 4234

    def test_log_two(self):
        assert ms.logarithm(69, 2) * 1000 // 1 == 6108


class TestPower:
    def test_power_non_number(self):
        with pytest.raises(AnsibleError, match='pow\\(\\) can only be used on numbers: must be real number, not str'):
            ms.power('a', 10)

        with pytest.raises(AnsibleError, match='pow\\(\\) can only be used on numbers: must be real number, not str'):
            ms.power(10, 'a')

    def test_power_squared(self):
        assert ms.power(10, 2) == 100

    def test_power_cubed(self):
        assert ms.power(10, 3) == 1000


class TestInversePower:
    def test_root_non_number(self):
        with pytest.raises(AnsibleError, match="root\\(\\) can only be used on numbers: could not convert string to float: 'a'"):
            ms.inversepower(10, 'a')

        with pytest.raises(AnsibleError, match="root\\(\\) can only be used on numbers: must be real number, not str"):
            ms.inversepower('a', 10)

    def test_square_root(self):
        assert ms.inversepower(100) == 10
        assert ms.inversepower(100, 2) == 10

    def test_cube_root(self):
        assert ms.inversepower(27, 3) == 3


class TestRekeyOnMember():
    # (Input data structure, member to rekey on, expected return)
    VALID_ENTRIES = (
        ([{"proto": "eigrp", "state": "enabled"}, {"proto": "ospf", "state": "enabled"}],
         'proto',
         {'eigrp': {'state': 'enabled', 'proto': 'eigrp'}, 'ospf': {'state': 'enabled', 'proto': 'ospf'}}),
        ({'eigrp': {"proto": "eigrp", "state": "enabled"}, 'ospf': {"proto": "ospf", "state": "enabled"}},
         'proto',
         {'eigrp': {'state': 'enabled', 'proto': 'eigrp'}, 'ospf': {'state': 'enabled', 'proto': 'ospf'}}),
    )

    # (Input data structure, member to rekey on, expected error message)
    INVALID_ENTRIES = (
        # Fail when key is not found
        (AnsibleError, [{"proto": "eigrp", "state": "enabled"}], 'invalid_key', "Key 'invalid_key' was not found."),
        (AnsibleError, {"eigrp": {"proto": "eigrp", "state": "enabled"}}, 'invalid_key', "Key 'invalid_key' was not found."),
        # Fail when key is duplicated
        (AnsibleError, [{"proto": "eigrp"}, {"proto": "ospf"}, {"proto": "ospf"}],
         'proto', "Key 'ospf' is not unique, cannot convert to dict."),
        # Fail when value is not a dict
        (AnsibleError, ["string"], 'proto', "List item is not a valid dict"),
        (AnsibleError, [123], 'proto', "List item is not a valid dict"),
        (AnsibleError, [[{'proto': 1}]], 'proto', "List item is not a valid dict"),
        # Fail when we do not send a dict or list
        (AnsibleError, "string", 'proto', "Type is not a valid list, set, or dict"),
        (AnsibleError, 123, 'proto', "Type is not a valid list, set, or dict"),
    )

    @pytest.mark.parametrize("list_original, key, expected", VALID_ENTRIES)
    def test_rekey_on_member_success(self, list_original, key, expected):
        assert ms.rekey_on_member(list_original, key) == expected

    @pytest.mark.parametrize("expected_exception_type, list_original, key, expected", INVALID_ENTRIES)
    def test_fail_rekey_on_member(self, expected_exception_type, list_original, key, expected):
        with pytest.raises(expected_exception_type) as err:
            ms.rekey_on_member(list_original, key)

        assert err.value.message == expected

    def test_duplicate_strategy_overwrite(self):
        list_original = ({'proto': 'eigrp', 'id': 1}, {'proto': 'ospf', 'id': 2}, {'proto': 'eigrp', 'id': 3})
        expected = {'eigrp': {'proto': 'eigrp', 'id': 3}, 'ospf': {'proto': 'ospf', 'id': 2}}
        assert ms.rekey_on_member(list_original, 'proto', duplicates='overwrite') == expected
