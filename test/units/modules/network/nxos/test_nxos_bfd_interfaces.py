# (c) 2019 Red Hat Inc.
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

from textwrap import dedent
from units.compat.mock import patch
from units.modules.utils import AnsibleFailJson
from ansible.modules.network.nxos import nxos_bfd_interfaces
from ansible.module_utils.network.nxos.config.bfd_interfaces.bfd_interfaces import Bfd_interfaces
from .nxos_module import TestNxosModule, load_fixture, set_module_args

ignore_provider_arg = True


class TestNxosBfdInterfacesModule(TestNxosModule):

    module = nxos_bfd_interfaces

    def setUp(self):
        super(TestNxosBfdInterfacesModule, self).setUp()

        self.mock_FACT_LEGACY_SUBSETS = patch('ansible.module_utils.network.nxos.facts.facts.FACT_LEGACY_SUBSETS')
        self.FACT_LEGACY_SUBSETS = self.mock_FACT_LEGACY_SUBSETS.start()

        self.mock_get_resource_connection_config = patch('ansible.module_utils.network.common.cfg.base.get_resource_connection')
        self.get_resource_connection_config = self.mock_get_resource_connection_config.start()

        self.mock_get_resource_connection_facts = patch('ansible.module_utils.network.common.facts.facts.get_resource_connection')
        self.get_resource_connection_facts = self.mock_get_resource_connection_facts.start()

        self.mock_edit_config = patch('ansible.module_utils.network.nxos.config.bfd_interfaces.bfd_interfaces.Bfd_interfaces.edit_config')
        self.edit_config = self.mock_edit_config.start()

    def tearDown(self):
        super(TestNxosBfdInterfacesModule, self).tearDown()
        self.mock_FACT_LEGACY_SUBSETS.stop()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.mock_FACT_LEGACY_SUBSETS.return_value = dict()
        self.get_resource_connection_config.return_value = None
        self.edit_config.return_value = None

    # ---------------------------
    # Bfd_interfaces Test Cases
    # ---------------------------

    SHOW_CMD = 'show running-config | section ^interface'
    def test_1(self):
        # Setup: No BFD configs shown on device interface
        # NOTE: The enable configs do not nvgen.
        existing = 'interface Ethernet1/1'
        self.get_resource_connection_facts.return_value = { self.SHOW_CMD: existing }
        playbook = dict(config=[dict(
            name='Ethernet1/1',
            bfd='enable',
            bfd_echo='enable',
        )])
        # Expected result commands for each 'state'
        merged = [ 'interface Ethernet1/1', 'bfd', 'bfd echo' ]
        deleted = []
        overridden = merged
        replaced = merged

        playbook['state'] = 'merged'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=merged)

        playbook['state'] = 'deleted'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=False, commands=deleted)

        playbook['state'] = 'overridden'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=overridden)

        playbook['state'] = 'replaced'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=replaced)

    def test_2(self):
        # enable -> disable
        # Setup: No BFD configs shown on device interface
        # NOTE: The enable configs do not nvgen.
        existing = 'interface Ethernet1/1'
        self.get_resource_connection_facts.return_value = { self.SHOW_CMD: existing }
        playbook = dict(config=[dict(
            name='Ethernet1/1',
            bfd='disable',
            # bfd_echo='enable',
        )])
        # Expected result commands for each 'state'
        merged = [ 'interface Ethernet1/1', 'no bfd', 'no bfd echo' ]
        deleted = []
        overridden = merged
        replaced = merged

        playbook['state'] = 'merged'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=merged)

        playbook['state'] = 'deleted'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=False, commands=deleted)

        playbook['state'] = 'overridden'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=overridden)

        playbook['state'] = 'replaced'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=replaced)

    def test_3(self):
        # disable -> enable
        existing = dedent('''\
          interface Ethernet1/1
            no bfd
            no bfd echo
        ''')
        self.get_resource_connection_facts.return_value = { self.SHOW_CMD: existing }
        playbook = dict(config=[dict(
            name='Ethernet1/1',
            bfd='enable',
            bfd_echo='enable',
        )])
        # Expected result commands for each 'state'
        merged = [ 'interface Ethernet1/1', 'bfd', 'bfd echo' ]
        deleted = merged
        overridden = merged
        replaced = merged

        playbook['state'] = 'merged'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=merged)

        playbook['state'] = 'deleted'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=deleted)

        playbook['state'] = 'overridden'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=overridden)

        playbook['state'] = 'replaced'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=replaced)

def build_args(data, type, state=None, check_mode=None):
    if state is None:
        state = 'merged'
    if check_mode is None:
        check_mode = False
    args = {
        'state': state,
        '_ansible_check_mode': check_mode,
        'config': {
            type: data
        }
    }
    return args
