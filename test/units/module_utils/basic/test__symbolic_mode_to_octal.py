# -*- coding: utf-8 -*-
# Copyright:
#   (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
#   (c) 2016-2017 Ansible Project
# License: GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

import pytest

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import MagicMock

from ansible.module_utils.basic import AnsibleModule


#
# Info helpful for making new test cases:
#
# base_mode = {'dir no perms': 0o040000,
# 'file no perms': 0o100000,
# 'dir all perms': 0o400000 | 0o777,
# 'file all perms': 0o100000, | 0o777}
#
# perm_bits = {'x': 0b001,
# 'w': 0b010,
# 'r': 0b100}
#
# role_shift = {'u': 6,
# 'g': 3,
# 'o': 0}

DATA = (  # Going from no permissions to setting all for user, group, and/or other
    (0o040000, u'a+rwx', 0o0777),
    (0o040000, u'u+rwx,g+rwx,o+rwx', 0o0777),
    (0o040000, u'o+rwx', 0o0007),
    (0o040000, u'g+rwx', 0o0070),
    (0o040000, u'u+rwx', 0o0700),

    # Going from all permissions to none for user, group, and/or other
    (0o040777, u'a-rwx', 0o0000),
    (0o040777, u'u-rwx,g-rwx,o-rwx', 0o0000),
    (0o040777, u'o-rwx', 0o0770),
    (0o040777, u'g-rwx', 0o0707),
    (0o040777, u'u-rwx', 0o0077),

    # now using absolute assignment from None to a set of perms
    (0o040000, u'a=rwx', 0o0777),
    (0o040000, u'u=rwx,g=rwx,o=rwx', 0o0777),
    (0o040000, u'o=rwx', 0o0007),
    (0o040000, u'g=rwx', 0o0070),
    (0o040000, u'u=rwx', 0o0700),

    # X effect on files and dirs
    (0o040000, u'a+X', 0o0111),
    (0o100000, u'a+X', 0),
    (0o040000, u'a=X', 0o0111),
    (0o100000, u'a=X', 0),
    (0o040777, u'a-X', 0o0666),
    # Same as chmod but is it a bug?
    # chmod a-X statfile <== removes execute from statfile
    (0o100777, u'a-X', 0o0666),

    # Multiple permissions
    (0o040000, u'u=rw-x+X,g=r-x+X,o=r-x+X', 0o0755),
    (0o100000, u'u=rw-x+X,g=r-x+X,o=r-x+X', 0o0644),
)


INVALID_DATA = (
    (0o040000, u'a=foo', "bad symbolic permission for mode: a=foo"),
    (0o040000, u'f=rwx', "bad symbolic permission for mode: f=rwx"),
)


@pytest.mark.parametrize('stat_info, mode_string, expected', DATA)
def test_good_symbolic_modes(stat_info, mode_string, expected):
    mock_stat = MagicMock()
    mock_stat.st_mode = stat_info
    assert AnsibleModule._symbolic_mode_to_octal(mock_stat, mode_string) == expected


def test_umask_with_symbolic_modes(mocker):
    mock_stat = MagicMock()
    mock_stat.st_mode = 0o100000

    mock_umask = mocker.patch('os.umask')
    mock_umask.return_value = 0o7

    assert AnsibleModule._symbolic_mode_to_octal(mock_stat, '+rwx') == 0o770

    mock_stat = MagicMock()
    mock_stat.st_mode = 0o100777

    assert AnsibleModule._symbolic_mode_to_octal(mock_stat, '-rwx') == 0o007


@pytest.mark.parametrize('stat_info, mode_string, expected', INVALID_DATA)
def test_invalid_symbolic_modes(stat_info, mode_string, expected):
    mock_stat = MagicMock()
    mock_stat.st_mode = stat_info
    with pytest.raises(ValueError) as exc:
        assert AnsibleModule._symbolic_mode_to_octal(mock_stat, mode_string) == 'blah'
    assert exc.match(expected)
