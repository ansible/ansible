# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.utils.display import Display
from ansible.module_utils import basic
from units.test_utils.controller.display import emits_warnings


def test_module_utils_warn() -> None:
    """Verify that `module_utils.basic.warn` on the controller is routed to `Display.warning`."""
    with emits_warnings(warning_pattern="hello"):
        basic.warn("hello")


def test_module_utils_error_as_warning() -> None:
    """Verify that `module_utils.basic.error_as_warning` on the controller is routed to `Display.error_as_warning`."""
    with emits_warnings(warning_pattern="hello.*world"):
        try:
            raise Exception("world")
        except Exception as ex:
            basic.error_as_warning("hello", ex)


def test_module_utils_deprecate() -> None:
    """Verify that `module_utils.basic.deprecate` on the controller is routed to `Display.deprecated`."""
    with emits_warnings(deprecation_pattern="hello"):
        basic.deprecate("hello", version='9999.9')


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
    d._warns.clear()
    d.warning(warning_message)
    out, err = capsys.readouterr()
    assert d._warns == {expected_warning_message}
    assert err == '\x1b[1;35m{0}\x1b[0m\n'.format(expected_warning_message.rstrip('\n'))


def test_warning_no_color(capsys, mocker, warning_message):
    warning_message, expected_warning_message = warning_message

    mocker.patch('ansible.utils.color.ANSIBLE_COLOR', False)

    d = Display()
    d._warns.clear()
    d.warning(warning_message)
    out, err = capsys.readouterr()
    assert d._warns == {expected_warning_message}
    assert err == expected_warning_message
