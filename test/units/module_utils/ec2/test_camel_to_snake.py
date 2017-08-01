# -*- coding: utf-8 -*-
# (c) 2017, Will Thames <will.thames@xvt.com.au>
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

from ansible.compat.tests import unittest
from ansible.module_utils.ec2 import _camel_to_snake

EXPECTED_SNAKIFICATION = {
    'alllower': 'alllower',
    'TwoWords': 'two_words',
    'AllUpperAtEND': 'all_upper_at_end',
    'AllUpperButPLURALs': 'all_upper_but_plurals',
    'TargetGroupARNs': 'target_group_arns',
    'HTTPEndpoints': 'http_endpoints',
    'PLURALs': 'plurals'
}


class CamelToSnakeTestCase(unittest.TestCase):

    def test_camel_to_snake(self):
        for (k, v) in EXPECTED_SNAKIFICATION.items():
            self.assertEqual(_camel_to_snake(k), v)
