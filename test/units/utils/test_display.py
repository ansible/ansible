# -*- coding: utf-8 -*-
# (c) 2020 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import locale

import pytest

from ansible.utils.display import get_text_width

# Set the locale to the users default setting
locale.setlocale(locale.LC_ALL, '')


def test_get_text_width():
    assert get_text_width(u'コンニチハ') == 10
    assert get_text_width(u'abコcd') == 6
    assert get_text_width(u'café') == 4
    assert get_text_width(u'four') == 4
    assert get_text_width(1) == 1
    assert get_text_width(b'four') == 4
    assert get_text_width(u'\u001B') == 0
    assert get_text_width(u'a\u0000b') == 2
    assert get_text_width(u'a\u0000bコ') == 4
