# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

from units.compat import unittest
from units.compat.mock import MagicMock

from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.playbook import Playbook
from ansible.template import Templar
from ansible.utils import context_objects as co

from units.mock.loader import DictDataLoader


class TestPlaybookExecutor(unittest.TestCase):

    def setUp(self):
        # Reset command line args for every test
        co.GlobalCLIArgs._Singleton__instance = None

    def tearDown(self):
        # And cleanup after ourselves too
        co.GlobalCLIArgs._Singleton__instance = None

    def mock_host(self, name, vars=None):
        if vars is None:
            vars = {}
        return MagicMock(name=name, vars=vars)

    def test_get_serialized_batches(self):
        fake_loader = DictDataLoader({
            'no_serial.yml': '''
            - hosts: all
              gather_facts: no
              tasks:
              - debug: var=inventory_hostname
            ''',
            'serial_int.yml': '''
            - hosts: all
              gather_facts: no
              serial: 2
              tasks:
              - debug: var=inventory_hostname
            ''',
            'serial_pct.yml': '''
            - hosts: all
              gather_facts: no
              serial: 20%
              tasks:
              - debug: var=inventory_hostname
            ''',
            'serial_list.yml': '''
            - hosts: all
              gather_facts: no
              serial: [1, 2, 3]
              tasks:
              - debug: var=inventory_hostname
            ''',
            'serial_list_mixed.yml': '''
            - hosts: all
              gather_facts: no
              serial: [1, "20%", -1]
              tasks:
              - debug: var=inventory_hostname
            ''',
            'serial_inv_tier.yml': '''
            - hosts: all
              gather_facts: no
              serial: [1, 2, 3]
              serial_inv_tier: test
              tasks:
              - debug: var=inventory_hostname
            ''',
        })

        mock_inventory = MagicMock()
        mock_var_manager = MagicMock()

        templar = Templar(loader=fake_loader)

        pbe = PlaybookExecutor(
            playbooks=['no_serial.yml', 'serial_int.yml', 'serial_pct.yml', 'serial_list.yml', 'serial_list_mixed.yml', 'serial_inv_tier.yml'],
            inventory=mock_inventory,
            variable_manager=mock_var_manager,
            loader=fake_loader,
            passwords=[],
        )

        playbook = Playbook.load(pbe._playbooks[0], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0', 'host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7', 'host8', 'host9']
        self.assertEqual(pbe._get_serialized_batches(play), [['host0', 'host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7', 'host8', 'host9']])

        playbook = Playbook.load(pbe._playbooks[1], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0', 'host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7', 'host8', 'host9']
        self.assertEqual(
            pbe._get_serialized_batches(play),
            [['host0', 'host1'], ['host2', 'host3'], ['host4', 'host5'], ['host6', 'host7'], ['host8', 'host9']]
        )

        playbook = Playbook.load(pbe._playbooks[2], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0', 'host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7', 'host8', 'host9']
        self.assertEqual(
            pbe._get_serialized_batches(play),
            [['host0', 'host1'], ['host2', 'host3'], ['host4', 'host5'], ['host6', 'host7'], ['host8', 'host9']]
        )

        playbook = Playbook.load(pbe._playbooks[3], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0', 'host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7', 'host8', 'host9']
        self.assertEqual(
            pbe._get_serialized_batches(play),
            [['host0'], ['host1', 'host2'], ['host3', 'host4', 'host5'], ['host6', 'host7', 'host8'], ['host9']]
        )

        playbook = Playbook.load(pbe._playbooks[4], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0', 'host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7', 'host8', 'host9']
        self.assertEqual(pbe._get_serialized_batches(play), [['host0'], ['host1', 'host2'], ['host3', 'host4', 'host5', 'host6', 'host7', 'host8', 'host9']])

        # Test when tier attribute does not exist on any host
        playbook = Playbook.load(pbe._playbooks[5], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        hosts = []
        for id in range(0, 10):
            hosts.append(self.mock_host("host%i" % id))
        mock_inventory.get_hosts.return_value = hosts
        self.assertEqual(pbe._get_serialized_batches(play), [hosts])

        # Test when tier attribute exists on some hosts
        playbook = Playbook.load(pbe._playbooks[5], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        hosts = []
        for id in range(0, 3):
            hosts.append(self.mock_host("host%i" % id, {"test": "group1"}))
        for id in range(3, 7):
            hosts.append(self.mock_host("host%i" % id, {"test": "group2"}))
        for id in range(7, 8):
            hosts.append(self.mock_host("host%i" % id, {"test": "group3"}))
        for id in range(8, 10):
            hosts.append(self.mock_host("host%i" % id))
        mock_inventory.get_hosts.return_value = hosts
        # need to ensure the same elements exist. order does not matter
        self.assertEqual(sorted(pbe._get_serialized_batches(play), key=len), sorted([hosts[0:3], hosts[3:7], hosts[7:8], hosts[8:10]], key=len))

        # Test when serial percent is under 1.0
        playbook = Playbook.load(pbe._playbooks[2], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0', 'host1', 'host2']
        self.assertEqual(pbe._get_serialized_batches(play), [['host0'], ['host1'], ['host2']])

        # Test when there is a remainder for serial as a percent
        playbook = Playbook.load(pbe._playbooks[2], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0', 'host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7', 'host8', 'host9', 'host10']
        self.assertEqual(
            pbe._get_serialized_batches(play),
            [['host0', 'host1'], ['host2', 'host3'], ['host4', 'host5'], ['host6', 'host7'], ['host8', 'host9'], ['host10']]
        )
