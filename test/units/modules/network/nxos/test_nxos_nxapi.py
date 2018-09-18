# (c) 2016 Red Hat Inc.
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

from ansible.compat.tests.mock import patch
from ansible.modules.network.nxos import nxos_nxapi
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosNxapiModule(TestNxosModule):

    module = nxos_nxapi

    def setUp(self):
        super(TestNxosNxapiModule, self).setUp()

        self.mock_run_commands = patch('ansible.modules.network.nxos.nxos_nxapi.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_nxapi.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_capabilities = patch('ansible.modules.network.nxos.nxos_nxapi.get_capabilities')
        self.get_capabilities = self.mock_get_capabilities.start()
        self.get_capabilities.return_value = {'device_info': {'network_os_platform': 'N7K-C7018', 'network_os_version': '8.3(1)'}, 'network_api': 'cliconf'}

    def tearDown(self):
        super(TestNxosNxapiModule, self).tearDown()
        self.mock_run_commands.stop()
        self.mock_load_config.stop()
        self.mock_get_capabilities.stop()

    def load_fixtures(self, commands=None, device=''):
        def load_from_file(*args, **kwargs):
            module, commands = args
            module_name = self.module.__name__.rsplit('.', 1)[1]

            output = list()
            for command in commands:
                filename = str(command).split(' | ')[0].replace(' ', '_')
                output.append(load_fixture(module_name, filename, device))
            return output

        self.run_commands.side_effect = load_from_file
        self.load_config.return_value = None

    def test_nxos_nxapi_no_change(self):
        set_module_args(dict(http=True, https=False, http_port=80, https_port=443, sandbox=False))
        self.execute_module_devices(changed=False, commands=[])

    def test_nxos_nxapi_disable(self):
        set_module_args(dict(state='absent'))
        self.execute_module_devices(changed=True, commands=['no feature nxapi'])

    def test_nxos_nxapi_no_http(self):
        set_module_args(dict(https=True, http=False, https_port=8443))
        self.execute_module_devices(changed=True, commands=['no nxapi http', 'nxapi https port 8443'])
