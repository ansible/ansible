# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

import ansible.plugins.filter.mathstuff as ms
from ansible.errors import AnsibleFilterError


UNIQUE_DATA = (([1, 3, 4, 2], sorted([1, 2, 3, 4])),
               ([1, 3, 2, 4, 2, 3], sorted([1, 2, 3, 4])),
               (['a', 'b', 'c', 'd'], sorted(['a', 'b', 'c', 'd'])),
               (['a', 'a', 'd', 'b', 'a', 'd', 'c', 'b'], sorted(['a', 'b', 'c', 'd'])),
               )

TWO_SETS_DATA = (([1, 2], [3, 4], ([], sorted([1, 2]), sorted([1, 2, 3, 4]), sorted([1, 2, 3, 4]))),
                 ([1, 2, 3], [5, 3, 4], ([3], sorted([1, 2]), sorted([1, 2, 5, 4]), sorted([1, 2, 3, 4, 5]))),
                 (['a', 'b', 'c'], ['d', 'c', 'e'], (['c'], sorted(['a', 'b']), sorted(['a', 'b', 'd', 'e']), sorted(['a', 'b', 'c', 'e', 'd']))),
                 )


@pytest.mark.parametrize('data, expected', UNIQUE_DATA)
class TestUnique:
    def test_unhashable(self, data, expected):
        assert sorted(ms.unique(list(data))) == expected

    def test_hashable(self, data, expected):
        assert sorted(ms.unique(tuple(data))) == expected


@pytest.mark.parametrize('dataset1, dataset2, expected', TWO_SETS_DATA)
class TestIntersect:
    def test_unhashable(self, dataset1, dataset2, expected):
        assert sorted(ms.intersect(list(dataset1), list(dataset2))) == expected[0]

    def test_hashable(self, dataset1, dataset2, expected):
        assert sorted(ms.intersect(tuple(dataset1), tuple(dataset2))) == expected[0]


@pytest.mark.parametrize('dataset1, dataset2, expected', TWO_SETS_DATA)
class TestDifference:
    def test_unhashable(self, dataset1, dataset2, expected):
        assert sorted(ms.difference(list(dataset1), list(dataset2))) == expected[1]

    def test_hashable(self, dataset1, dataset2, expected):
        assert sorted(ms.difference(tuple(dataset1), tuple(dataset2))) == expected[1]


@pytest.mark.parametrize('dataset1, dataset2, expected', TWO_SETS_DATA)
class TestSymmetricDifference:
    def test_unhashable(self, dataset1, dataset2, expected):
        assert sorted(ms.symmetric_difference(list(dataset1), list(dataset2))) == expected[2]

    def test_hashable(self, dataset1, dataset2, expected):
        assert sorted(ms.symmetric_difference(tuple(dataset1), tuple(dataset2))) == expected[2]


class TestMin:
    def test_min(self):
        assert ms.min((1, 2)) == 1
        assert ms.min((2, 1)) == 1
        assert ms.min(('p', 'a', 'w', 'b', 'p')) == 'a'


class TestMax:
    def test_max(self):
        assert ms.max((1, 2)) == 2
        assert ms.max((2, 1)) == 2
        assert ms.max(('p', 'a', 'w', 'b', 'p')) == 'w'


class TestLogarithm:
    def test_log_non_number(self):
        with pytest.raises(AnsibleFilterError, message='log() can only be used on numbers: a float is required'):
            ms.logarithm('a')
        with pytest.raises(AnsibleFilterError, message='log() can only be used on numbers: a float is required'):
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
        with pytest.raises(AnsibleFilterError, message='pow() can only be used on numbers: a float is required'):
            ms.power('a', 10)

        with pytest.raises(AnsibleFilterError, message='pow() can only be used on numbers: a float is required'):
            ms.power(10, 'a')

    def test_power_squared(self):
        assert ms.power(10, 2) == 100

    def test_power_cubed(self):
        assert ms.power(10, 3) == 1000


class TestHaversine:
    def test_haversine_non_number(self):
        with pytest.raises(AnsibleFilterError, message='haversine() only accepts floats'):
            ms.haversine(['a', 'b', 'c', 'd'])

        with pytest.raises(AnsibleFilterError, message='haversine() only accepts floats'):
            ms.haversine({'lon1': 'a', 'lat1': 'b', 'lon2': 'c', 'lat2': 'd'})

        with pytest.raises(AnsibleFilterError, message='haversine() supplied list should contain 4 elements for lat1, lon1, lat2 and lon2.'):
            ms.haversine(['35.9914928', '-78.907046', '-33.8523063'])

        with pytest.raises(AnsibleFilterError, message='haversine() supplied list should contain 4 elements for lat1, lon1, lat2 and lon2.'):
            ms.haversine(['11.44', '43.44', '35.9914928', '-78.907046', '-33.8523063'])

        with pytest.raises(AnsibleFilterError, message='haversine() supplied dicts should contain 4 keys: lat1, lon1, lat2 and lon2'):
            ms.haversine({'lon1': '-78.907046', 'lat1': '35.9914928'})

        with pytest.raises(AnsibleFilterError, message='haversine() unit must be m or km if defined'):
            ms.haversine(['35.9914928', '-78.907046', '-33.8523063', '151.2085984', 'z'])

        with pytest.raises(AnsibleFilterError, message='haversine() unit must be m or km if defined'):
            ms.haversine({'lon2': '151.2085984', 'lat1': '35.9914928', 'lon1': '-78.907046', 'lat2': '-33.8523063', 'unit': 'z'})

    def test_km(self):
        assert ms.haversine(['35.9914928', '-78.907046', '-33.8523063', '151.2085984']).get('km') == 15490.46

    def test_only_km(self):
        assert ms.haversine(['35.9914928', '-78.907046', '-33.8523063', '151.2085984', 'km']) == 15490.46

    def test_m(self):
        assert ms.haversine({'lat1': '35.9914928', 'lon1': '-78.907046', 'lat2': '-33.8523063', 'lon2': '151.2085984'}).get('m') == 9625.31

    def test_order(self):
        assert ms.haversine({'lon2': '151.2085984', 'lat1': '35.9914928', 'lon1': '-78.907046', 'lat2': '-33.8523063'}).get('m') == 9625.31

    def test_compare_both(self):
        assert (ms.haversine({'lat1': '-78.907046', 'lon1': '35.9914928', 'lon2': '-33.8523063', 'lat2': '151.2085984'}).get('m') ==
                ms.haversine(['-78.907046', '35.9914928', '151.2085984', '-33.8523063']).get('m'))


class TestInversePower:
    def test_root_non_number(self):
        with pytest.raises(AnsibleFilterError, message='root() can only be used on numbers: a float is required'):
            ms.inversepower(10, 'a')

        with pytest.raises(AnsibleFilterError, message='root() can only be used on numbers: a float is required'):
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
        ([{"proto": "eigrp", "state": "enabled"}], 'invalid_key', "Key invalid_key was not found"),
        ({"eigrp": {"proto": "eigrp", "state": "enabled"}}, 'invalid_key', "Key invalid_key was not found"),
        # Fail when key is duplicated
        ([{"proto": "eigrp"}, {"proto": "ospf"}, {"proto": "ospf"}],
         'proto', 'Key ospf is not unique, cannot correctly turn into dict'),
        # Fail when value is not a dict
        (["string"], 'proto', "List item is not a valid dict"),
        ([123], 'proto', "List item is not a valid dict"),
        ([[{'proto': 1}]], 'proto', "List item is not a valid dict"),
        # Fail when we do not send a dict or list
        ("string", 'proto', "Type is not a valid list, set, or dict"),
        (123, 'proto', "Type is not a valid list, set, or dict"),
    )

    @pytest.mark.parametrize("list_original, key, expected", VALID_ENTRIES)
    def test_rekey_on_member_success(self, list_original, key, expected):
        assert ms.rekey_on_member(list_original, key) == expected

    @pytest.mark.parametrize("list_original, key, expected", INVALID_ENTRIES)
    def test_fail_rekey_on_member(self, list_original, key, expected):
        with pytest.raises(AnsibleFilterError) as err:
            ms.rekey_on_member(list_original, key)

        assert err.value.message == expected

    def test_duplicate_strategy_overwrite(self):
        list_original = ({'proto': 'eigrp', 'id': 1}, {'proto': 'ospf', 'id': 2}, {'proto': 'eigrp', 'id': 3})
        expected = {'eigrp': {'proto': 'eigrp', 'id': 3}, 'ospf': {'proto': 'ospf', 'id': 2}}
        assert ms.rekey_on_member(list_original, 'proto', duplicates='overwrite') == expected
