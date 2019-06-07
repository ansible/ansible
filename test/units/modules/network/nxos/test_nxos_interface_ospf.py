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

from units.compat.mock import patch
from ansible.modules.network.nxos import nxos_interface_ospf
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosInterfaceOspfModule(TestNxosModule):

    module = nxos_interface_ospf

    def setUp(self):
        super(TestNxosInterfaceOspfModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_interface_ospf.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_interface_ospf.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestNxosInterfaceOspfModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, device=''):
        module_name = self.module.__name__.rsplit('.', 1)[1]
        self.get_config.return_value = load_fixture(module_name, 'config.cfg')
        self.load_config.return_value = None

    def test_nxos_interface_ospf(self):
        set_module_args(dict(interface='ethernet1/32', ospf=1, area=1))
        self.execute_module(changed=True, commands=['interface Ethernet1/32', 'ip router ospf 1 area 0.0.0.1'])

    def test_bfd_1(self):
        # default -> enable
        set_module_args(dict(interface='ethernet1/33', ospf=1, area=1, bfd='enable'))
        self.execute_module(changed=True, commands=['interface Ethernet1/33', 'ip router ospf 1 area 0.0.0.1', 'ip ospf bfd'])

        # default -> disable
        set_module_args(dict(interface='ethernet1/33', ospf=1, area=1, bfd='disable'))
        self.execute_module(changed=True, commands=['interface Ethernet1/33', 'ip router ospf 1 area 0.0.0.1', 'ip ospf bfd disable'])

    def test_bfd_2(self):
        # default -> default
        set_module_args(dict(interface='ethernet1/33.101', ospf=1, area=1, bfd='default'))
        self.execute_module(changed=False)

        # enable -> default
        set_module_args(dict(interface='ethernet1/36', ospf=1, area=1, bfd='default'))
        self.execute_module(changed=True, commands=['interface Ethernet1/36', 'no ip ospf bfd'])

        # disable -> default
        set_module_args(dict(interface='ethernet1/37', ospf=1, area=1, bfd='default'))
        self.execute_module(changed=True, commands=['interface Ethernet1/37', 'no ip ospf bfd'])

    def test_bfd_3(self):
        # enable -> idempotence
        set_module_args(dict(interface='ethernet1/36', ospf=1, area=1, bfd='enable'))
        self.execute_module(changed=False)

        # disable -> idempotence
        set_module_args(dict(interface='ethernet1/37', ospf=1, area=1, bfd='disable'))
        self.execute_module(changed=False)

    def test_bfd_4(self):
        # None -> absent
        set_module_args(dict(interface='ethernet1/33.101', ospf=1, area=1, state='absent'))
        self.execute_module(changed=True, commands=['interface Ethernet1/33.101', 'no ip router ospf 1 area 0.0.0.1'])

        # enable -> absent
        set_module_args(dict(interface='ethernet1/36', ospf=1, area=1, bfd='enable', state='absent'))
        self.execute_module(changed=True, commands=['interface Ethernet1/36', 'no ip router ospf 1 area 0.0.0.1', 'no ip ospf bfd'])

        # disable -> absent
        set_module_args(dict(interface='ethernet1/37', ospf=1, area=1, bfd='disable', state='absent'))
        self.execute_module(changed=True, commands=['interface Ethernet1/37', 'no ip router ospf 1 area 0.0.0.1', 'no ip ospf bfd'])

    def test_absent_1(self):
        # area only -> absent
        set_module_args(dict(interface='ethernet1/33.101', ospf=1, area=1, state='absent'))
        self.execute_module(changed=True, commands=['interface Ethernet1/33.101', 'no ip router ospf 1 area 0.0.0.1'])

        # None -> absent
        set_module_args(dict(interface='ethernet1/33', ospf=1, area=1, state='absent'))
        self.execute_module(changed=False)

    def test_loopback_interface_failed(self):
        set_module_args(dict(interface='loopback0', ospf=1, area=0, passive_interface=True))
        self.execute_module(failed=True, changed=False)
        set_module_args(dict(interface='loopback0', ospf=1, area=0, network='broadcast'))
        self.execute_module(failed=True, changed=False)

    def test_nxos_interface_ospf_passive(self):
        # default -> True
        set_module_args(dict(interface='ethernet1/33', ospf=1, area=1, passive_interface=True))
        self.execute_module(changed=True, commands=['interface Ethernet1/33',
                                                    'ip router ospf 1 area 0.0.0.1',
                                                    'ip ospf passive-interface'])
        # default -> False
        set_module_args(dict(interface='ethernet1/33', ospf=1, area=1, passive_interface=False))
        self.execute_module(changed=True, commands=['interface Ethernet1/33',
                                                    'ip router ospf 1 area 0.0.0.1',
                                                    'no ip ospf passive-interface'])
        # True -> False
        set_module_args(dict(interface='ethernet1/34', ospf=1, area=1, passive_interface=False))
        self.execute_module(changed=True, commands=['interface Ethernet1/34',
                                                    'no ip ospf passive-interface'])
        # True -> default (absent)
        set_module_args(dict(interface='ethernet1/34', ospf=1, area=1, state='absent'))
        self.execute_module(changed=True, commands=['interface Ethernet1/34',
                                                    'no ip router ospf 1 area 0.0.0.1',
                                                    'default ip ospf passive-interface'])
        # False -> True
        set_module_args(dict(interface='ethernet1/35', ospf=1, area=1, passive_interface=True))
        self.execute_module(changed=True, commands=['interface Ethernet1/35',
                                                    'ip ospf passive-interface'])
        # False -> default (absent)
        set_module_args(dict(interface='ethernet1/35', ospf=1, area=1, state='absent'))
        self.execute_module(changed=True, commands=['interface Ethernet1/35',
                                                    'no ip router ospf 1 area 0.0.0.1',
                                                    'default ip ospf passive-interface'])
