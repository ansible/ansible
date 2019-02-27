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

from units.compat.mock import patch
from ansible.modules.network.asa import asa_og
from units.modules.utils import set_module_args
from .asa_module import TestAsaModule, load_fixture


class TestAsaOgModule(TestAsaModule):

    module = asa_og

    def setUp(self):
        super(TestAsaOgModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.asa.asa_og.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.asa.asa_og.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestAsaOgModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        self.get_config.return_value = load_fixture('asa_og_config.cfg').strip()
        self.load_config.return_value = dict(diff=None, session='session')

    def test_asa_og_idempotent(self):
        set_module_args(dict(
            name='service_object_test',
            group_type='port-object',
            protocol='udp',
            lines=['range 56832 56959', 'range 61363 65185']
        ))
        commands = []
        self.execute_module(changed=False, commands=commands)

    def test_asa_og_update(self):
        set_module_args(dict(
            name='service_object_test',
            group_type='port-object',
            protocol='udp',
            lines=['range 56832 56959', 'range 61363 65185', 'range 1024 4201']
        ))
        commands = [
            'object-group service service_object_test udp',
            'port-object range 1024 4201'
        ]
        self.execute_module(changed=True, commands=commands)

    def test_asa_og_replace(self):
        set_module_args(dict(
            name='service_object_test',
            group_type='port-object',
            protocol='udp',
            lines=['range 1024 4201']
        ))
        commands = [
            'object-group service service_object_test udp',
            'no port-object range 56832 56959'
            'no port-object range 61363 65185'
        ]
        self.execute_module(changed=True, commands=commands)
