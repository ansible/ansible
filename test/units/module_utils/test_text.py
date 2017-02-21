# -*- coding: utf-8 -*-
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.six import PY3
from ansible.compat.tests import unittest
from units.mock.generator import add_method


# Internal API while this is still being developed.  Eventually move to
# module_utils.text
from ansible.module_utils._text import to_text, to_bytes, to_native

# Format: byte representation, text representation, encoding of byte representation
VALID_STRINGS = (
    (b'abcde', u'abcde', 'ascii'),
    (b'caf\xc3\xa9', u'caf\xe9', 'utf-8'),
    (b'caf\xe9', u'caf\xe9', 'latin-1'),
    # u'くらとみ'
    (b'\xe3\x81\x8f\xe3\x82\x89\xe3\x81\xa8\xe3\x81\xbf', u'\u304f\u3089\u3068\u307f', 'utf-8'),
    (b'\x82\xad\x82\xe7\x82\xc6\x82\xdd', u'\u304f\u3089\u3068\u307f', 'shift-jis'),
    )

def _check_to_text(self, in_string, encoding, expected):
    """test happy path of decoding to text"""
    self.assertEqual(to_text(in_string, encoding), expected)

def _check_to_bytes(self, in_string, encoding, expected):
    """test happy path of encoding to bytes"""
    self.assertEqual(to_bytes(in_string, encoding), expected)

def _check_to_native(self, in_string, encoding, py2_expected, py3_expected):
    """test happy path of encoding to native strings"""
    if PY3:
        self.assertEqual(to_native(in_string, encoding), py3_expected)
    else:
        self.assertEqual(to_native(in_string, encoding), py2_expected)


@add_method(_check_to_text, [(i[0], i[2], i[1]) for i in VALID_STRINGS])
@add_method(_check_to_text, [(i[1], i[2], i[1]) for i in VALID_STRINGS])
@add_method(_check_to_bytes, [(i[0], i[2], i[0]) for i in VALID_STRINGS])
@add_method(_check_to_bytes, [(i[1], i[2], i[0]) for i in VALID_STRINGS])
@add_method(_check_to_native, [(i[0], i[2], i[0], i[1]) for i in VALID_STRINGS])
@add_method(_check_to_native, [(i[1], i[2], i[0], i[1]) for i in VALID_STRINGS])
class TestModuleUtilsText(unittest.TestCase):
    pass
