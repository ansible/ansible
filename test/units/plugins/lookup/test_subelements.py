# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.plugins.lookup.subelements import LookupModule


def test_subelements_does_not_mutate_input():
    users = [{'name': 'alice', 'ssh': {'authorized': ['key1', 'key2']}}]
    expected = [{'name': 'alice', 'ssh': {'authorized': ['key1', 'key2']}}]

    result = LookupModule().run([users, 'ssh.authorized'])

    assert result == [(users[0], 'key1'), (users[0], 'key2')]
    assert users == expected
