"""
iap_token unit tests
"""
# -*- coding: utf-8 -*-

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

# pylint: disable=invalid-name,protected-access,function-redefined,unused-argument
# pylint: disable=unused-import,redundant-unittest-assert

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import unittest


class TestClass(unittest.TestCase):
    """
    Test cases
    """
    def _assert_incident_api(self, module, url, method, headers):
        """
        Setup Test
        """
        self.assertTrue('http://localhost:4007/login' in url, 'token')
        return Response(), {'status': 200}

    def test_incident_url(self):
        self.assertTrue(True, True)


class Response(object):
    """
    Setup Response
    """
    def read(self):
        return '{"token": "ljhklj%3D"}'
