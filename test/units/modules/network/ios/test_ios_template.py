#
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

import json

from ansible.compat.tests.mock import patch
from ansible.modules.network.ios import _ios_template
from .ios_module import TestIosModule, load_fixture, set_module_args

class TestIosTemplateModule(TestIosModule):

    module = _ios_template

    def setUp(self):
        self.mock_get_config = patch('ansible.modules.network.ios._ios_template.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.ios._ios_template.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        config_file = 'ios_template_config.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_ios_template_unchanged(self):
        src = load_fixture('ios_template_config.cfg')
        set_module_args(dict(src=src))
        self.execute_module()

    def test_ios_template_simple(self):
        src = load_fixture('ios_template_src.cfg')
        set_module_args(dict(src=src))
        commands = ['hostname foo',
                    'interface GigabitEthernet0/0',
                    'no ip address']
        self.execute_module(changed=True, commands=commands)

    def test_ios_template_force(self):
        src = load_fixture('ios_template_config.cfg')
        set_module_args(dict(src=src, force=True))
        commands = [str(s).strip() for s in src.split('\n') if s and s != '!']
        self.execute_module(changed=True, commands=commands)
        self.assertFalse(self.get_config.called)

    def test_ios_template_backup(self):
        set_module_args(dict(backup=True))
        result = self.execute_module()
        self.assertIn('__backup__', result)

    def test_ios_template_config(self):
        src = load_fixture('ios_template_config.cfg')
        config = 'hostname router'
        set_module_args(dict(src=src, config=config))
        commands = ['interface GigabitEthernet0/0',
                    'ip address 1.2.3.4 255.255.255.0',
                    'description test string',
                    'interface GigabitEthernet0/1',
                    'ip address 6.7.8.9 255.255.255.0',
                    'description test string',
                    'shutdown']
        self.execute_module(changed=True, commands=commands)
        self.assertFalse(self.get_config.called)
