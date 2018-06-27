# -*- coding: utf-8 -*-
#
# (c) 2017 Red Hat, Inc.
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.module_utils.network.common.parsing import Conditional

test_results = ['result_1', 'result_2', 'result_3']
c1 = Conditional('result[1] == result_2')
c2 = Conditional('result[2] not == result_2')
c3 = Conditional('result[0] neq not result_1')


class TestNotKeyword(unittest.TestCase):
    def test_negate_instance_variable_assignment(self):
        assert c1.negate is False and c2.negate is True

    def test_key_value_instance_variable_assignment(self):
        c1_assignments = c1.key == 'result[1]' and c1.value == 'result_2'
        c2_assignments = c2.key == 'result[2]' and c2.value == 'result_2'
        assert c1_assignments and c2_assignments

    def test_conditionals_w_not_keyword(self):
        assert c1(test_results) and c2(test_results) and c3(test_results)

if __name__ == '__main__':
    unittest.main()
