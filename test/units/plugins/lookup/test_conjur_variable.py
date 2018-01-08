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


from ansible.module_utils.basic import AnsibleModule
from ansible.compat.tests import unittest
# from ansible.module_utils.urls import open_url
# from ansible.compat.tests.mock import mock_open, patch
from ansible.errors import AnsibleError
from ansible.plugins.loader import PluginLoader
from ansible.plugins.lookup import conjur_variable
import tempfile


class TestLookupModule(unittest.TestCase):
    def test_valid_netrc_file(self):
        with tempfile.NamedTemporaryFile() as temp_netrc:
            temp_netrc.write(b"machine http://localhost/authn\n")
            temp_netrc.write(b"  login admin\n")
            temp_netrc.write(b"  password my-pass\n")
            temp_netrc.seek(0)

            results = conjur_variable._load_identity_from_file(temp_netrc.name, 'http://localhost')

            self.assertEquals(results['id'], 'admin')
            self.assertEquals(results['api_key'], 'my-pass')

    def test_netrc_without_host_file(self):
        with tempfile.NamedTemporaryFile() as temp_netrc:
            temp_netrc.write(b"machine http://localhost/authn\n")
            temp_netrc.write(b"  login admin\n")
            temp_netrc.write(b"  password my-pass\n")
            temp_netrc.seek(0)

            with self.assertRaises(AnsibleError):
                conjur_variable._load_identity_from_file(temp_netrc.name, 'http://foo')


    def test_valid_configuration(self):
        with tempfile.NamedTemporaryFile() as configuration_file:
            configuration_file.write(b"---\n")
            configuration_file.write(b"account: demo-policy\n")
            configuration_file.write(b"plugins: []\n")
            configuration_file.write(b"appliance_url: http://localhost:8080\n")
            configuration_file.seek(0)

            results = conjur_variable._load_conf_from_file(configuration_file.name)
            self.assertEquals(results['account'], 'demo-policy')
            self.assertEquals(results['appliance_url'], 'http://localhost:8080')

    # This test fails do to missing patch :(
    # @patch('ansible.plugins.lookup.conjur_variable.open_url')
    # def test_token_retrieval():
    #     stream = open_url.return_value
    #     stream.read.return_value = "foo-bar-token"
    #     stream.getcode.return_value = 200
    #     open_url.return_value = stream
    #
    #     response = conjur_variable._fetch_conjur_token('http://conjur', 'account', 'username', 'api_key')
    #
    #     self.assertEqual(stream.read.return_value, response)
