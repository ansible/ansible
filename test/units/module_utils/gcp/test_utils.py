# -*- coding: utf-8 -*-
# (c) 2016, Tom Melendez <tom@supertom.com>
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
import os
import sys

from ansible.compat.tests import mock, unittest
from ansible.module_utils.gcp import (check_min_pkg_version)

def build_distribution(version):
    obj = mock.MagicMock()
    obj.version = '0.5.0'
    return obj


class GCPUtilsTestCase(unittest.TestCase):

    @mock.patch("pkg_resources.get_distribution", side_effect=build_distribution)
    def test_check_minimum_pkg_version(self, mockobj):
        self.assertTrue(check_min_pkg_version('foobar', '0.4.0'))
        self.assertTrue(check_min_pkg_version('foobar', '0.5.0'))
        self.assertFalse(check_min_pkg_version('foobar', '0.6.0'))
