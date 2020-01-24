# -*- coding: utf-8 -*-
# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.removed import removed_module


@pytest.mark.parametrize('input_data', [u'2.8', 2.8, 2, '', ])
def test_removed_module_sys_exit(input_data):
    """Test for removed_module function, sys.exit()."""

    with pytest.raises(SystemExit) as wrapped_e:
        removed_module(input_data)

    assert wrapped_e.type == SystemExit
    assert wrapped_e.value.code == 1


@pytest.mark.parametrize(
    'input_data, expected_msg, expected_warn',
    [
        (
            u'2.8',
            u'This module has been removed. '
            'The module documentation for Ansible-2.7 may contain hints for porting',
            u'',
        ),
        (
            2.8,
            u'This module has been removed. '
            'The module documentation for Ansible-2.7 may contain hints for porting',
            u'',
        ),
        (
            2,
            u'This module has been removed. '
            'The module documentation for Ansible-1 may contain hints for porting',
            u'',
        ),
        (
            u'café',
            u'This module has been removed',
            u'"warnings": ["removed modules should specify the version they were removed in"]',
        ),
        (
            0.1,
            u'This module has been removed. '
            'The module documentation for Ansible-0.0 may contain hints for porting',
            u'',
        ),
    ]
)
def test_removed_module_msgs(input_data, expected_msg, expected_warn, capsys):
    """Test for removed_module function, content of output messages."""

    captured = capsys.readouterr()
    assert expected_msg, expected_warn in captured.out
