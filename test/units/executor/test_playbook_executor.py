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

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.playbook import Playbook

from units.mock.loader import DictDataLoader

class TestPlayIterator(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_playbook_executor__get_serialized_batches(self):
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
        })

        mock_inventory = MagicMock()
        mock_var_manager = MagicMock()

        # fake out options to use the syntax CLI switch, which will ensure
        # the PlaybookExecutor doesn't create a TaskQueueManager
        mock_options = MagicMock()
        mock_options.syntax.value = True

        pbe = PlaybookExecutor(
            playbooks=['no_serial.yml', 'serial_int.yml', 'serial_pct.yml'],
            inventory=mock_inventory,
            variable_manager=mock_var_manager,
            loader=fake_loader,
            options=mock_options,
            passwords=[],
        )

        playbook = Playbook.load(pbe._playbooks[0], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        mock_inventory.get_hosts.return_value = ['host0','host1','host2','host3','host4','host5','host6','host7','host8','host9']
        self.assertEqual(pbe._get_serialized_batches(play), [['host0','host1','host2','host3','host4','host5','host6','host7','host8','host9']])

        playbook = Playbook.load(pbe._playbooks[1], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        mock_inventory.get_hosts.return_value = ['host0','host1','host2','host3','host4','host5','host6','host7','host8','host9']
        self.assertEqual(pbe._get_serialized_batches(play), [['host0','host1'],['host2','host3'],['host4','host5'],['host6','host7'],['host8','host9']])

        playbook = Playbook.load(pbe._playbooks[2], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        mock_inventory.get_hosts.return_value = ['host0','host1','host2','host3','host4','host5','host6','host7','host8','host9']
        self.assertEqual(pbe._get_serialized_batches(play), [['host0','host1'],['host2','host3'],['host4','host5'],['host6','host7'],['host8','host9']])

