# (c) 2017, David Moreau Simard <dmsimard@redhat.com>
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
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.plugins.lookup.batch import LookupModule


LONG_LIST = [i for i in range(1, 61)]
CUSTOM_SIZE = dict(
    variables={
        'batch_lookup_size': 3
    }
)
BAD_SIZE = dict(
    variables={
        'batch_lookup_size': 'three'
    }
)


class TestBatchLookup(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_batch_with_defaults(self):
        lookup_plugin = LookupModule()
        result = lookup_plugin.run(LONG_LIST, **{})
        self.assertEqual(len(LONG_LIST), 60)
        # 60 / 5 = 12
        self.assertEqual(len(result), 12)

    def test_batch_with_custom_size(self):
        lookup_plugin = LookupModule()
        result = lookup_plugin.run(LONG_LIST, **CUSTOM_SIZE)
        self.assertEqual(len(LONG_LIST), 60)
        # 60 / 3 = 20
        self.assertEqual(len(result), 20)

    def test_batch_with_bad_size(self):
        lookup_plugin = LookupModule()

        with self.assertRaises(ValueError):
            lookup_plugin.run(LONG_LIST, **BAD_SIZE)
