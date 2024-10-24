# -*- coding: utf-8 -*-
# Copyright: (c) 2018 Ansible Project
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.modules.copy import AnsibleModuleError, split_pre_existing_dir

from ansible.module_utils.basic import AnsibleModule

success_testdata = [
    # Level 1
    ('/dir1/dir2', [True], ('/dir1', ['dir2'])),
    ('/dir1/dir2/', [True], ('/dir1/dir2', [''])),
    ('dir1/dir2', [True], ('dir1', ['dir2'])),
    ('dir1/dir2/', [True], ('dir1/dir2', [''])),
    ('/dir1', [True], ('/', ['dir1'])),
    ('/dir1/', [True], ('/dir1', [''])),
    ('dir1', [True], ('.', ['dir1'])),
    ('dir1/', [True], ('dir1', [''])),
    # Level 2
    ('/dir1/dir2', [False, True], ('/', ['dir1', 'dir2'])),
    ('/dir1/dir2/', [False, True], ('/dir1', ['dir2', ''])),
    ('dir1/dir2', [False, True], ('.', ['dir1', 'dir2'])),
    ('dir1/dir2/', [False, True], ('dir1', ['dir2', ''])),
    ('/dir1/', [False, True], ('/', ['dir1', ''])),
    ('dir1', [False, True], ('.', ['dir1'])),
    ('dir1/', [False, True], ('.', ['dir1', ''])),
    # Level 3
    ('/dir1/dir2/', [False, False, True], ('/', ['dir1', 'dir2', ''])),
    ('dir1/dir2', [False, False, True], ('.', ['dir1', 'dir2'])),
    ('dir1/dir2/', [False, False, True], ('.', ['dir1', 'dir2', ''])),
    ('dir1', [False, False, True], ('.', ['dir1'])),
    ('dir1/', [False, False, True], ('.', ['dir1', ''])),
]


failure_testdata = [
    # Level 2
    ('/dir1', [False, True]),
    # Level 3
    ('/dir1/dir2', [False, False, True]),
    ('/dir1', [False, False, True]),
    ('/dir1/', [False, False, True]),
]


@pytest.mark.parametrize("actual, mock_os_exists, expected", success_testdata)
def test_split_pre_existing_dir_root_does_exist(actual, mock_os_exists, expected, mocker):
    mocker.patch('os.path.exists', side_effect=mock_os_exists)
    assert split_pre_existing_dir(actual) == expected


@pytest.mark.parametrize("actual, mock_os_exists", failure_testdata)
def test_split_pre_existing_dir_root_does_not_exist(actual, mock_os_exists, mocker):
    mocker.patch('os.path.exists', side_effect=mock_os_exists)
    with pytest.raises(AnsibleModuleError) as excinfo:
        split_pre_existing_dir(actual)
    assert excinfo.value.results['msg'].startswith("The '/' directory doesn't exist on this machine.")

#
# Info helpful for making new test cases:
#
# base_mode = {
# 'dir no perms':   0o040000,
# 'file no perms':  0o100000,
# 'dir all perms':  0o040000 | 0o777,
# 'file all perms': 0o100000 | 0o777}
#
# perm_bits = {
# 'x': 0b001,
# 'w': 0b010,
# 'r': 0b100}
#
# role_shift = {
# 'u': 6,
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

    # Verify X uses computed not original mode
    (0o100777, u'a=,u=rX', 0o0400),
    (0o040777, u'a=,u=rX', 0o0500),

    # Multiple permissions
    (0o040000, u'u=rw-x+X,g=r-x+X,o=r-x+X', 0o0755),
    (0o100000, u'u=rw-x+X,g=r-x+X,o=r-x+X', 0o0644),
)

UMASK_DATA = (
    (0o100000, '+rwx', 0o770),
    (0o100777, '-rwx', 0o007),
)

INVALID_DATA = (
    (0o040000, u'a=foo', "bad symbolic permission for mode: a=foo"),
    (0o040000, u'f=rwx', "bad symbolic permission for mode: f=rwx"),
    (0o100777, u'of=r', "bad symbolic permission for mode: of=r"),

    (0o100777, u'ao=r', "bad symbolic permission for mode: ao=r"),
    (0o100777, u'oa=r', "bad symbolic permission for mode: oa=r"),
)


@pytest.mark.parametrize('stat_info, mode_string, expected', DATA)
def test_good_symbolic_modes(mocker, stat_info, mode_string, expected):
    mock_stat = mocker.MagicMock()
    mock_stat.st_mode = stat_info
    assert AnsibleModule._symbolic_mode_to_octal(mock_stat, mode_string) == expected


@pytest.mark.parametrize('stat_info, mode_string, expected', UMASK_DATA)
def test_umask_with_symbolic_modes(mocker, stat_info, mode_string, expected):
    mock_umask = mocker.patch('os.umask')
    mock_umask.return_value = 0o7

    mock_stat = mocker.MagicMock()
    mock_stat.st_mode = stat_info

    assert AnsibleModule._symbolic_mode_to_octal(mock_stat, mode_string) == expected


@pytest.mark.parametrize('stat_info, mode_string, expected', INVALID_DATA)
def test_invalid_symbolic_modes(mocker, stat_info, mode_string, expected):
    mock_stat = mocker.MagicMock()
    mock_stat.st_mode = stat_info
    with pytest.raises(ValueError) as exc:
        AnsibleModule._symbolic_mode_to_octal(mock_stat, mode_string)
    assert exc.match(expected)
