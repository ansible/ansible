#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_lldp_interface
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxLldpInterfaceModule(TestOnyxModule):

    module = onyx_lldp_interface

    def setUp(self):
        super(TestOnyxLldpInterfaceModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_lldp_interface.OnyxLldpInterfaceModule,
            "_get_lldp_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxLldpInterfaceModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_lldp_interface_show.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_lldp_no_change(self):
        set_module_args(dict(name='Eth1/1', state='present'))
        self.execute_module(changed=False)

    def test_no_lldp_no_change(self):
        set_module_args(dict(name='Eth1/2', state='absent'))
        self.execute_module(changed=False)

    def test_no_lldp_change(self):
        set_module_args(dict(name='Eth1/2', state='present'))
        commands = ['interface ethernet 1/2 lldp receive',
                    'interface ethernet 1/2 lldp transmit']
        self.execute_module(changed=True, commands=commands)

    def test_lldp_change(self):
        set_module_args(dict(name='Eth1/1', state='absent'))
        commands = ['interface ethernet 1/1 no lldp receive',
                    'interface ethernet 1/1 no lldp transmit']
        self.execute_module(changed=True, commands=commands)

    def test_lldp_aggregate(self):
        aggregate = [dict(name='Eth1/1'), dict(name='Eth1/2')]
        set_module_args(dict(aggregate=aggregate, state='present'))
        commands = ['interface ethernet 1/2 lldp receive',
                    'interface ethernet 1/2 lldp transmit']
        self.execute_module(changed=True, commands=commands)

    def test_lldp_aggregate_purge(self):
        aggregate = [dict(name='Eth1/3'), dict(name='Eth1/2')]
        set_module_args(dict(aggregate=aggregate, state='present', purge=True))
        commands = ['interface ethernet 1/2 lldp receive',
                    'interface ethernet 1/2 lldp transmit',
                    'interface ethernet 1/3 lldp receive',
                    'interface ethernet 1/3 lldp transmit',
                    'interface ethernet 1/1 no lldp receive',
                    'interface ethernet 1/1 no lldp transmit']
        self.execute_module(changed=True, commands=commands)
