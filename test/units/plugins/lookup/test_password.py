# -*- coding: utf-8 -*-
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.compat.six import text_type

from ansible.plugins.lookup import password

DEFAULT_CHARS = sorted([u'ascii_letters', u'digits', u".,:-_"])
DEFAULT_CANDIDATE_CHARS = u'.,:-_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

class TestPasswordLookup(unittest.TestCase):

    # Currently there isn't a new-style
    old_style_params_data = (
        # Simple case
        dict(term=u'/path/to/file',
             filename=u'/path/to/file',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=DEFAULT_CHARS),
             candidate_chars=DEFAULT_CANDIDATE_CHARS,
             ),

        # Special characters in path
        dict(term=u'/path/with/embedded spaces and/file',
             filename=u'/path/with/embedded spaces and/file',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=DEFAULT_CHARS),
             candidate_chars=DEFAULT_CANDIDATE_CHARS,
             ),
        dict(term=u'/path/with/equals/cn=com.ansible',
             filename=u'/path/with/equals/cn=com.ansible',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=DEFAULT_CHARS),
             candidate_chars=DEFAULT_CANDIDATE_CHARS,
             ),
        dict(term=u'/path/with/unicode/くらとみ/file',
             filename=u'/path/with/unicode/くらとみ/file',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=DEFAULT_CHARS),
             candidate_chars=DEFAULT_CANDIDATE_CHARS,
             ),
        # Mix several special chars
        dict(term=u'/path/with/utf 8 and spaces/くらとみ/file',
             filename=u'/path/with/utf 8 and spaces/くらとみ/file',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=DEFAULT_CHARS),
             candidate_chars=DEFAULT_CANDIDATE_CHARS,
             ),
        dict(term=u'/path/with/encoding=unicode/くらとみ/file',
             filename=u'/path/with/encoding=unicode/くらとみ/file',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=DEFAULT_CHARS),
             candidate_chars=DEFAULT_CANDIDATE_CHARS,
             ),
        dict(term=u'/path/with/encoding=unicode/くらとみ/and spaces file',
             filename=u'/path/with/encoding=unicode/くらとみ/and spaces file',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=DEFAULT_CHARS),
             candidate_chars=DEFAULT_CANDIDATE_CHARS,
             ),

        # Simple parameters
        dict(term=u'/path/to/file length=42',
             filename=u'/path/to/file',
             params=dict(length=42, encrypt=None, chars=DEFAULT_CHARS),
             candidate_chars=DEFAULT_CANDIDATE_CHARS,
             ),
        dict(term=u'/path/to/file encrypt=pbkdf2_sha256',
             filename=u'/path/to/file',
             params=dict(length=password.DEFAULT_LENGTH, encrypt='pbkdf2_sha256', chars=DEFAULT_CHARS),
             candidate_chars=DEFAULT_CANDIDATE_CHARS,
             ),
        dict(term=u'/path/to/file chars=abcdefghijklmnop',
             filename=u'/path/to/file',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=[u'abcdefghijklmnop']),
             candidate_chars=u'abcdefghijklmnop',
             ),
        dict(term=u'/path/to/file chars=digits,abc,def',
             filename=u'/path/to/file',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=sorted([u'digits', u'abc', u'def'])),
             candidate_chars=u'abcdef0123456789',
             ),

        # Including comma in chars
        dict(term=u'/path/to/file chars=abcdefghijklmnop,,digits',
             filename=u'/path/to/file',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=sorted([u'abcdefghijklmnop', u',', u'digits'])),
             candidate_chars = u',abcdefghijklmnop0123456789',
             ),
        dict(term=u'/path/to/file chars=,,',
             filename=u'/path/to/file',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=[u',']),
             candidate_chars=u',',
             ),

        # Including = in chars
        dict(term=u'/path/to/file chars=digits,=,,',
             filename=u'/path/to/file',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=sorted([u'digits', u'=', u','])),
             candidate_chars=u',=0123456789',
             ),
        dict(term=u'/path/to/file chars=digits,abc=def',
             filename=u'/path/to/file',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=sorted([u'digits', u'abc=def'])),
             candidate_chars=u'abc=def0123456789',
             ),

        # Including unicode in chars
        dict(term=u'/path/to/file chars=digits,くらとみ,,',
             filename=u'/path/to/file',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=sorted([u'digits', u'くらとみ', u','])),
             candidate_chars=u',0123456789くらとみ',
             ),
        # Including only unicode in chars
        dict(term=u'/path/to/file chars=くらとみ',
             filename=u'/path/to/file',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=sorted([u'くらとみ'])),
             candidate_chars=u'くらとみ',
             ),

        # Include ':' in path
        dict(term=u'/path/to/file_with:colon chars=ascii_letters,digits',
             filename=u'/path/to/file_with:colon',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=sorted([u'ascii_letters', u'digits'])),
             candidate_chars=u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
             ),

        # Including special chars in both path and chars
        # Special characters in path
        dict(term=u'/path/with/embedded spaces and/file chars=abc=def',
             filename=u'/path/with/embedded spaces and/file',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=[u'abc=def']),
             candidate_chars=u'abc=def',
             ),
        dict(term=u'/path/with/equals/cn=com.ansible chars=abc=def',
             filename=u'/path/with/equals/cn=com.ansible',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=[u'abc=def']),
             candidate_chars=u'abc=def',
             ),
        dict(term=u'/path/with/unicode/くらとみ/file chars=くらとみ',
             filename=u'/path/with/unicode/くらとみ/file',
             params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=[u'くらとみ']),
             candidate_chars=u'くらとみ',
             ),
        )

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_parse_parameters(self):
        for testcase in self.old_style_params_data:
            filename, params = password._parse_parameters(testcase['term'])
            params['chars'].sort()
            self.assertEqual(filename, testcase['filename'])
            self.assertEqual(params, testcase['params'])

    def test_gen_password(self):
        for testcase in self.old_style_params_data:
            params = testcase['params']
            candidate_chars = testcase['candidate_chars']
            password_string = password._gen_password(length=params['length'],
                                                     chars=params['chars'])
            self.assertEquals(len(password_string),
                              params['length'],
                              msg='generated password=%s has length (%s) instead of expected length (%s)' %
                              (password_string, len(password_string), params['length']))

            for char in password_string:
                self.assertIn(char, candidate_chars,
                              msg='%s not found in %s from chars spect %s' %
                              (char, candidate_chars, params['chars']))

    def _assert_gen_candidate_chars(self, testcase):
        expected_candidate_chars = testcase['candidate_chars']
        params = testcase['params']
        chars_spec = params['chars']
        res = password._gen_candidate_chars(chars_spec)
        self.assertEquals(res, expected_candidate_chars)

    def test_gen_candidate_chars(self):
        for testcase in self.old_style_params_data:
            self._assert_gen_candidate_chars(testcase)


class TestRandomPassword(unittest.TestCase):
    def _assert_valid_chars(self, res, chars):
        for res_char in res:
            self.assertIn(res_char, chars)

    def test_default(self):
        res = password._random_password()
        self.assertEquals(len(res), password.DEFAULT_LENGTH)
        self.assertTrue(isinstance(res, text_type))
        self._assert_valid_chars(res, DEFAULT_CANDIDATE_CHARS)

    def test_zero_length(self):
        res = password._random_password(length=0)
        self.assertEquals(len(res), 0)
        self.assertTrue(isinstance(res, text_type))
        self._assert_valid_chars(res, u',')

    def test_just_a_common(self):
        res = password._random_password(length=1, chars=u',')
        self.assertEquals(len(res), 1)
        self.assertEquals(res, u',')

    def test_free_will(self):
        # A Rush and Spinal Tap reference twofer
        res = password._random_password(length=11, chars=u'a')
        self.assertEquals(len(res), 11)
        self.assertEquals(res, 'aaaaaaaaaaa')
        self._assert_valid_chars(res, u'a')

    def test_unicode(self):
        res = password._random_password(length=11, chars=u'くらとみ')
        self._assert_valid_chars(res, u'くらとみ')
        self.assertEquals(len(res), 11)


class TestRandomSalt(unittest.TestCase):
    def test(self):
        res = password._random_salt()
        expected_salt_candidate_chars = u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./'
        self.assertEquals(len(res), 8)
        for res_char in res:
            self.assertIn(res_char, expected_salt_candidate_chars)
