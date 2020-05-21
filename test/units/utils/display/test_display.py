# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.errors import AnsibleError
from ansible.utils.display import Display

nonascii_text = u'\u00c5\u00d1\u015a\u00cc\u03b2\u0141\u00c8'
nonascii_utf8_bytes = nonascii_text.encode('utf-8')


def test_display_basic_message(capsys, mocker):
    # Disable logging
    mocker.patch('ansible.utils.display.logger', return_value=None)

    d = Display()
    d.display(u'Some displayed message')
    out, err = capsys.readouterr()
    assert out == 'Some displayed message\n'
    assert err == ''


# ensure that display methods won't barf on bad string inputs (note we're not validating output yet)
def test_display_defensive_strings():
    d = Display()
    d.display(nonascii_text)
    d.display(nonascii_utf8_bytes)


def test_warning_defensive_strings():
    d = Display()
    for formatted in [False, True]:
        d.warning(nonascii_text, formatted=formatted)
        d.warning(nonascii_utf8_bytes, formatted=formatted)


def test_deprecated_defensive_strings():
    d = Display()
    with pytest.raises(AnsibleError):
        d.deprecated(nonascii_text, nonascii_utf8_bytes, removed=True)
    with pytest.raises(AnsibleError):
        d.deprecated(nonascii_utf8_bytes, nonascii_text, removed=True)


def test_banner_defensive_strings():
    d = Display()
    for cows in [False, True]:
        d.banner(nonascii_text, cows=cows)
        d.banner(nonascii_utf8_bytes, cows=cows)


def test_debug_defensive_strings():
    d = Display()
    d.debug(nonascii_text, nonascii_utf8_bytes)
    d.debug(nonascii_utf8_bytes, nonascii_text)
