#
# (c) 2016 Red Hat Inc.
# (c) 2017 Paul Neumann
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

import json

from units.compat.mock import patch
from ansible.modules.network.ios import ios_logging
from units.modules.utils import set_module_args
from .ios_module import TestIosModule, load_fixture


class TestIosLoggingModule(TestIosModule):

    module = ios_logging

    def setUp(self):
        super(TestIosLoggingModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.ios.ios_logging.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.ios.ios_logging.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_capabilities = patch('ansible.modules.network.ios.ios_logging.get_capabilities')
        self.get_capabilities = self.mock_get_capabilities.start()
        self.get_capabilities.return_value = {'device_info': {'network_os_version': '15.6(2)T'}}

    def tearDown(self):
        super(TestIosLoggingModule, self).tearDown()

        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_get_capabilities.stop()

    def load_fixtures(self, commands=None):
        self.get_config.return_value = load_fixture('ios_logging_config.cfg')
        self.load_config.return_value = None

    def test_ios_logging_buffer_size_changed_implicit(self):
        set_module_args(dict(dest='buffered'))
        commands = ['logging buffered 4096']
        self.execute_module(changed=True, commands=commands)

    def test_ios_logging_buffer_size_changed_explicit(self):
        set_module_args(dict(dest='buffered', size=6000))
        commands = ['logging buffered 6000']
        self.execute_module(changed=True, commands=commands)

    def test_ios_logging_add_host(self):
        set_module_args(dict(dest='host', name='192.168.1.1'))
        commands = ['logging host 192.168.1.1']
        self.execute_module(changed=True, commands=commands)

    def test_ios_logging_host_idempotent(self):
        set_module_args(dict(dest='host', name='2.3.4.5'))
        commands = []
        self.execute_module(changed=False, commands=commands)

    def test_ios_logging_delete_non_exist_host(self):
        set_module_args(dict(dest='host', name='192.168.1.1', state='absent'))
        commands = []
        self.execute_module(changed=False, commands=commands)

    def test_ios_logging_delete_host(self):
        set_module_args(dict(dest='host', name='2.3.4.5', state='absent'))
        commands = ['no logging host 2.3.4.5']
        self.execute_module(changed=True, commands=commands)

    def test_ios_logging_configure_disabled_monitor_destination(self):
        set_module_args(dict(dest='monitor', level='debugging'))
        commands = ['logging monitor debugging']
        self.execute_module(changed=True, commands=commands)


class TestIosLoggingModuleIOS12(TestIosModule):

    module = ios_logging

    def setUp(self):
        super(TestIosLoggingModuleIOS12, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.ios.ios_logging.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.ios.ios_logging.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_capabilities = patch('ansible.modules.network.ios.ios_logging.get_capabilities')
        self.get_capabilities = self.mock_get_capabilities.start()
        self.get_capabilities.return_value = {'device_info': {'network_os_version': '12.1(2)T'}}

    def tearDown(self):
        super(TestIosLoggingModuleIOS12, self).tearDown()

        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_get_capabilities.stop()

    def load_fixtures(self, commands=None):
        self.get_config.return_value = load_fixture('ios_logging_config_ios12.cfg')
        self.load_config.return_value = None

    def test_ios_logging_add_host(self):
        set_module_args(dict(dest='host', name='192.168.1.1'))
        commands = ['logging 192.168.1.1']
        self.execute_module(changed=True, commands=commands)

    def test_ios_logging_host_idempotent(self):
        set_module_args(dict(dest='host', name='2.3.4.5'))
        commands = []
        self.execute_module(changed=False, commands=commands)

    def test_ios_logging_delete_non_exist_host(self):
        set_module_args(dict(dest='host', name='192.168.1.1', state='absent'))
        commands = []
        self.execute_module(changed=False, commands=commands)

    def test_ios_logging_delete_host(self):
        set_module_args(dict(dest='host', name='2.3.4.5', state='absent'))
        commands = ['no logging 2.3.4.5']
        self.execute_module(changed=True, commands=commands)
