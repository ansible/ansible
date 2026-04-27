# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.common.process import get_bin_path


def test_get_bin_path(mocker):
    path = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
    mocker.patch.dict('os.environ', {'PATH': path})
    mocker.patch('os.pathsep', ':')

    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('ansible.module_utils.common.process.is_executable', return_value=True)

    # pytest-mock 2.0.0 will throw when os.path.exists is messed with
    # and then another method is patched afterwards. Likely
    # something in the pytest-mock chain uses os.path.exists internally, and
    # since pytest-mock prohibits context-specific patching, there's not a
    # good solution. For now, just patch os.path.exists last.
    mocker.patch('os.path.exists', side_effect=[False, True])

    assert '/usr/local/bin/notacommand' == get_bin_path('notacommand')


def test_get_path_path_raise_valueerror(mocker):
    mocker.patch.dict('os.environ', {'PATH': ''})

    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('ansible.module_utils.common.process.is_executable', return_value=True)

    with pytest.raises(ValueError, match='Failed to find required executable "notacommand"'):
        get_bin_path('notacommand')
