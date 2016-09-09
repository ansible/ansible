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

from ansible.plugins.lookup import password

DEFAULT_CHARS = sorted([u'ascii_letters', u'digits', u".,:-_"])

class TestPasswordLookup(unittest.TestCase):

    # Currently there isn't a new-style
    old_style_params_data = (
            # Simple case
            dict(term=u'/path/to/file',
                filename=u'/path/to/file',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=DEFAULT_CHARS)
                ),

            # Special characters in path
            dict(term=u'/path/with/embedded spaces and/file',
                filename=u'/path/with/embedded spaces and/file',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=DEFAULT_CHARS)
                ),
            dict(term=u'/path/with/equals/cn=com.ansible',
                filename=u'/path/with/equals/cn=com.ansible',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=DEFAULT_CHARS)
                ),
            dict(term=u'/path/with/unicode/くらとみ/file',
                filename=u'/path/with/unicode/くらとみ/file',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=DEFAULT_CHARS)
                ),
            # Mix several special chars
            dict(term=u'/path/with/utf 8 and spaces/くらとみ/file',
                filename=u'/path/with/utf 8 and spaces/くらとみ/file',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=DEFAULT_CHARS)
                ),
            dict(term=u'/path/with/encoding=unicode/くらとみ/file',
                filename=u'/path/with/encoding=unicode/くらとみ/file',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=DEFAULT_CHARS)
                ),
            dict(term=u'/path/with/encoding=unicode/くらとみ/and spaces file',
                filename=u'/path/with/encoding=unicode/くらとみ/and spaces file',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=DEFAULT_CHARS)
                ),

            # Simple parameters
            dict(term=u'/path/to/file length=42',
                filename=u'/path/to/file',
                params=dict(length=42, encrypt=None, chars=DEFAULT_CHARS)
                ),
            dict(term=u'/path/to/file encrypt=pbkdf2_sha256',
                filename=u'/path/to/file',
                params=dict(length=password.DEFAULT_LENGTH, encrypt='pbkdf2_sha256', chars=DEFAULT_CHARS)
                ),
            dict(term=u'/path/to/file chars=abcdefghijklmnop',
                filename=u'/path/to/file',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=[u'abcdefghijklmnop'])
                ),
            dict(term=u'/path/to/file chars=digits,abc,def',
                filename=u'/path/to/file',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=sorted([u'digits', u'abc', u'def']))
                ),
            # Including comma in chars
            dict(term=u'/path/to/file chars=abcdefghijklmnop,,digits',
                filename=u'/path/to/file',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=sorted([u'abcdefghijklmnop', u',', u'digits']))
                ),
            dict(term=u'/path/to/file chars=,,',
                filename=u'/path/to/file',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=[u','])
                ),

            # Including = in chars
            dict(term=u'/path/to/file chars=digits,=,,',
                filename=u'/path/to/file',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=sorted([u'digits', u'=', u',']))
                ),
            dict(term=u'/path/to/file chars=digits,abc=def',
                filename=u'/path/to/file',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=sorted([u'digits', u'abc=def']))
                ),

            # Including unicode in chars
            dict(term=u'/path/to/file chars=digits,くらとみ,,',
                filename=u'/path/to/file',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=sorted([u'digits', u'くらとみ', u',']))
                ),
            # Including only unicode in chars
            dict(term=u'/path/to/file chars=くらとみ',
                filename=u'/path/to/file',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=sorted([u'くらとみ']))
                ),

            # Include ':' in path
            dict(term=u'/path/to/file_with:colon chars=ascii_letters,digits',
                 filename=u'/path/to/file_with:colon',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=sorted([u'ascii_letters', u'digits']))
                ),

            # Including special chars in both path and chars
            # Special characters in path
            dict(term=u'/path/with/embedded spaces and/file chars=abc=def',
                filename=u'/path/with/embedded spaces and/file',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=[u'abc=def'])
                ),
            dict(term=u'/path/with/equals/cn=com.ansible chars=abc=def',
                filename=u'/path/with/equals/cn=com.ansible',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=[u'abc=def'])
                ),
            dict(term=u'/path/with/unicode/くらとみ/file chars=くらとみ',
                filename=u'/path/with/unicode/くらとみ/file',
                params=dict(length=password.DEFAULT_LENGTH, encrypt=None, chars=[u'くらとみ'])
                ),

            # zero length
            #dict(term=u'/path/to/zero_length chars=ascii_letters,digits length=0',
            #     filename=u'/path/to/zero_length',
            #    params=dict(length=0, encrypt=None, chars=sorted([u'ascii_letters', u'digits']))
            #    ),

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
            # password_lookup = password.LookupModule()
#            print(params)
#            print()
            candidate_chars = password._new_gen_candidate_chars(params['chars'])
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
