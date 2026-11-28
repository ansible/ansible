# coding: utf-8
# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

from ansible.parsing.quoting import is_quoted, unquote

import pytest

UNQUOTE_DATA = (
    (u'1', u'1'),
    (u'\'1\'', u'1'),
    (u'"1"', u'1'),
    (u'"1 \'2\'"', u'1 \'2\''),
    (u'\'1 "2"\'', u'1 "2"'),
    (u'\'1 \'2\'\'', u'1 \'2\''),
    (u'"1\\"', u'"1\\"'),
    (u'\'1\\\'', u'\'1\\\''),
    (u'"1 \\"2\\" 3"', u'1 \\"2\\" 3'),
    (u'\'1 \\\'2\\\' 3\'', u'1 \\\'2\\\' 3'),
    (u'"', u'"'),
    (u'\'', u'\''),
    # Not entirely sure these are good but they match the current
    # behaviour
    (u'"1""2"', u'1""2'),
    (u'\'1\'\'2\'', u'1\'\'2'),
    (u'"1" 2 "3"', u'1" 2 "3'),
    (u'"1"\'2\'"3"', u'1"\'2\'"3'),
)


@pytest.mark.parametrize("quoted, expected", UNQUOTE_DATA)
def test_unquote(quoted, expected):
    assert unquote(quoted) == expected


@pytest.mark.parametrize("value", ('"value\\\\"', "'value\\\\'"))
def test_is_quoted_even_trailing_backslashes(value):
    assert is_quoted(value)
    assert unquote(value) == value[1:-1]


@pytest.mark.parametrize("value", ('"value\\"', "'value\\'"))
def test_is_quoted_odd_trailing_backslashes(value):
    assert not is_quoted(value)
    assert unquote(value) == value
