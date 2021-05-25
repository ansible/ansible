# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.utils.display import Display


@pytest.fixture
def warning_message():
    warning_message = 'bad things will happen'
    expected_warning_message = '[WARNING]: {0}\n'.format(warning_message)
    return warning_message, expected_warning_message


def test_warning(capsys, mocker, warning_message):
    warning_message, expected_warning_message = warning_message

    mocker.patch('ansible.utils.color.ANSIBLE_COLOR', True)
    mocker.patch('ansible.utils.color.parsecolor', return_value=u'1;35')  # value for 'bright purple'

    d = Display()
    d.warning(warning_message)
    out, err = capsys.readouterr()
    assert d._warns == {expected_warning_message: 1}
    assert err == '\x1b[1;35m{0}\x1b[0m\n'.format(expected_warning_message.rstrip('\n'))


def test_warning_no_color(capsys, mocker, warning_message):
    warning_message, expected_warning_message = warning_message

    mocker.patch('ansible.utils.color.ANSIBLE_COLOR', False)

    d = Display()
    d.warning(warning_message)
    out, err = capsys.readouterr()
    assert d._warns == {expected_warning_message: 1}
    assert err == expected_warning_message
