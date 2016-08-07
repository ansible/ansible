# -*- coding: utf-8 -*-
# (c) 2015, Benjamin Morris <ben@rooted.systems>
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

from __future__ import (absolute_import, division, print_function)
from __future__ import unicode_literals
__metaclass__ = type

import math
from nose.tools import assert_raises

from ansible.compat.tests import unittest
from ansible.plugins.filter.mathstuff import to_bytes
from ansible import errors

class TestToBytes(unittest.TestCase):

    def get_multipliers(self, multi_factor):
        return {
            'b': 1,
            'kb': multi_factor,
            'mb': math.pow(multi_factor, 2),
            'gb': math.pow(multi_factor, 3),
            'tb': math.pow(multi_factor, 4),
            'pb': math.pow(multi_factor, 5),
        }

    def test_to_bytes_good_input(self):
        units = (
            'b',
            'kb',
            'mb',
            'gb',
            'tb',
            'pb',
        )

        # test non-si
        multi_factor = 1024
        for unit in units:
            byte_val = 0
            rc = to_bytes('%s%s' % (byte_val, unit))
            self.assertTrue(rc == byte_val * self.get_multipliers(multi_factor).get(unit),
                    'should have returned %s bytes for prefix %s' % (byte_val, unit))

            byte_val = 10
            rc = to_bytes('%s%s' % (byte_val, unit))
            self.assertTrue(rc == byte_val * self.get_multipliers(multi_factor).get(unit),
                    'should have returned %s bytes for prefix %s' % (byte_val, unit))

            byte_val = 10431987413
            rc = to_bytes('%s%s' % (byte_val, unit))
            self.assertTrue(rc == byte_val * self.get_multipliers(multi_factor).get(unit),
                    'should have returned %s bytes for prefix %s' % (byte_val, unit))

        # test si
        multi_factor = 1000
        for unit in units:
            byte_val = 0
            rc = to_bytes('%s%s' % (byte_val, unit), True)
            self.assertTrue(rc == byte_val * self.get_multipliers(multi_factor).get(unit),
                    'should have returned %s bytes for prefix %s' % (byte_val, unit))

            byte_val = 10
            rc = to_bytes('%s%s' % (byte_val, unit), True)
            self.assertTrue(rc == byte_val * self.get_multipliers(multi_factor).get(unit),
                    'should have returned %s bytes for prefix %s' % (byte_val, unit))

            byte_val = 10431987413
            rc = to_bytes('%s%s' % (byte_val, unit), True)
            self.assertTrue(rc == byte_val * self.get_multipliers(multi_factor).get(unit),
                    'should have returned %s bytes for prefix %s' % (byte_val, unit))

    def test_to_bytes_negative_input(self):
        assert_raises(errors.AnsibleFilterError, to_bytes, '-10kb')

    def test_to_bytes_non_str_input(self):
        assert_raises(errors.AnsibleFilterError, to_bytes, 0.0)
        assert_raises(errors.AnsibleFilterError, to_bytes, None)

    def test_to_bytes_invalid_format_input(self):
        assert_raises(errors.AnsibleFilterError, to_bytes, "kb10")
        assert_raises(errors.AnsibleFilterError, to_bytes, "10")
        assert_raises(errors.AnsibleFilterError, to_bytes, "kb")
        assert_raises(errors.AnsibleFilterError, to_bytes, "q")
        assert_raises(errors.AnsibleFilterError, to_bytes, "")
        assert_raises(errors.AnsibleFilterError, to_bytes, "1010b10")

    def test_to_bytes_unicode_input(self):
        assert_raises(errors.AnsibleFilterError, to_bytes, '\x00\x00\x00\x00\x00')
        assert_raises(errors.AnsibleFilterError, to_bytes, 'ﾟ･✿ヾ╲(｡◕‿◕｡)╱✿･ﾟ')
