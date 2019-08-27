# -*- coding: utf-8 -*-
# (c) 2019, Daryl Banttari <dbanttari@gmail.com>
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
from __future__ import (absolute_import, print_function)
__metaclass__ = type

from units.compat import unittest
from ansible.plugins.lookup.hmac import LookupModule


class TestHMACLookup(unittest.TestCase):

    testcases = (
        # simple
        dict(
            term='string_to_be_signed',
            secret='asdf',
            expected=['qoR/uNWjQQa8sS77mRjUDPqV2ZXa44Y1Xnb/3AUvmlg='],
        ),
        # multiple terms
        # (assert that the hasher hasn't been polluted via multiple update()s)
        dict(
            term=['string_to_be_signed2', 'string_to_be_signed'],
            secret='asdf',
            expected=['fGW4FjaIgVzGlWLQ/SITPzp2cs5q9I9wOOVO7YsZPu4=', 'qoR/uNWjQQa8sS77mRjUDPqV2ZXa44Y1Xnb/3AUvmlg='],
        ),
        # alternative algorithm
        dict(
            term='string_to_be_signed',
            secret='asdf',
            encoding='utf-8',
            algorithm='sha512',
            expected=['vy7cBvrvVxQIQWvJGB6iE7nHmMovpFBWGRwTDr54DLpxRBpDC77+iOu1GskUEj1jhBRofEjtTNZeaBqqqfr+uA=='],
        ),
        # base64-encoded secret + alternative algorithm
        dict(
            term='string_to_be_signed',
            secret='YXNkZg==',  # 'asdf' | b64encode
            encoding='base64',
            algorithm='sha512',
            expected=['vy7cBvrvVxQIQWvJGB6iE7nHmMovpFBWGRwTDr54DLpxRBpDC77+iOu1GskUEj1jhBRofEjtTNZeaBqqqfr+uA=='],
        ),
    )

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_parse_parameters(self):
        test = LookupModule()
        for testcase in self.testcases:
            self.assertEqual(test.run(testcase['term'], **testcase), testcase['expected'])
