# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.plugins.inventory import expand_hostname_range


@pytest.mark.parametrize('pattern, expected', [
    ('db[1:3]', ['db1', 'db2', 'db3']),
    ('db[01:03]', ['db01', 'db02', 'db03']),
    ('db[9:11]', ['db9', 'db10', 'db11']),
    ('db[1:5:2]', ['db1', 'db3', 'db5']),
    ('db[a:c]', ['dba', 'dbb', 'dbc']),
    ('db[1:2]-[a:b]', ['db1-a', 'db1-b', 'db2-a', 'db2-b']),
    ('192.0.2.[1:3]', ['192.0.2.1', '192.0.2.2', '192.0.2.3']),
    # decimal-looking ranges keep their decimal meaning, even in IPv6 addresses
    ('2001:db8::[9:11]', ['2001:db8::9', '2001:db8::10', '2001:db8::11']),
    # hexadecimal ranges in IPv6 addresses
    ('2001:db8::[8:b]', ['2001:db8::8', '2001:db8::9', '2001:db8::a', '2001:db8::b']),
    ('2001:db8::[ab:ad]', ['2001:db8::ab', '2001:db8::ac', '2001:db8::ad']),
    ('2001:db8::[AB:AD]', ['2001:db8::AB', '2001:db8::AC', '2001:db8::AD']),
    ('2001:db8::[0e:11]', ['2001:db8::0e', '2001:db8::0f', '2001:db8::10', '2001:db8::11']),
    ('2001:db8::[ff:105:2]', ['2001:db8::ff', '2001:db8::101', '2001:db8::103', '2001:db8::105']),
])
def test_expand_hostname_range(pattern: str, expected: list[str]) -> None:
    assert expand_hostname_range(pattern) == expected


def test_expand_hostname_range_hex_count() -> None:
    assert len(expand_hostname_range('2001:db8::[1:ff]')) == 255
