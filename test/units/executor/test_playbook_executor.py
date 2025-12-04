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

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.playbook import Playbook
from ansible._internal._templating._engine import TemplateEngine
from ansible.utils import context_objects as co

from units.mock.loader import DictDataLoader


class TestPlaybookExecutor(unittest.TestCase):

    def setUp(self):
        # Reset command line args for every test
        co.GlobalCLIArgs._Singleton__instance = None

    def tearDown(self):
        # And cleanup after ourselves too
        co.GlobalCLIArgs._Singleton__instance = None

    def test_get_serialized_batches(self):
        fake_loader = DictDataLoader({
            'no_serial.yml': """
            - hosts: all
              gather_facts: no
              tasks:
              - debug: var=inventory_hostname
            """,
            'serial_int.yml': """
            - hosts: all
              gather_facts: no
              serial: 2
              tasks:
              - debug: var=inventory_hostname
            """,
            'serial_pct.yml': """
            - hosts: all
              gather_facts: no
              serial: 20%
              tasks:
              - debug: var=inventory_hostname
            """,
            'serial_list.yml': """
            - hosts: all
              gather_facts: no
              serial: [1, 2, 3]
              tasks:
              - debug: var=inventory_hostname
            """,
            'serial_list_mixed.yml': """
            - hosts: all
              gather_facts: no
              serial: [1, "20%", -1]
              tasks:
              - debug: var=inventory_hostname
            """,
        })

        mock_inventory = MagicMock()
        mock_var_manager = MagicMock()

        templar = TemplateEngine(loader=fake_loader)

        pbe = PlaybookExecutor(
            playbooks=['no_serial.yml', 'serial_int.yml', 'serial_pct.yml', 'serial_list.yml', 'serial_list_mixed.yml'],
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

    def test_get_serialized_batches_with_batch_groups(self):
        """Test the batch_groups feature for ordering hosts by groups."""
        fake_loader = DictDataLoader({
            'batch_groups.yml': """
            - hosts: all
              gather_facts: no
              batch_groups:
                - webservers
                - dbservers
              serial: 2
              tasks:
              - debug: var=inventory_hostname
            """,
        })

        mock_inventory = MagicMock()
        mock_var_manager = MagicMock()

        templar = TemplateEngine(loader=fake_loader)

        pbe = PlaybookExecutor(
            playbooks=['batch_groups.yml'],
            inventory=mock_inventory,
            variable_manager=mock_var_manager,
            loader=fake_loader,
            passwords=[],
        )

        # Create mock host objects
        web1 = MagicMock()
        web1.name = 'web1'
        web2 = MagicMock()
        web2.name = 'web2'
        web3 = MagicMock()
        web3.name = 'web3'
        db1 = MagicMock()
        db1.name = 'db1'
        db2 = MagicMock()
        db2.name = 'db2'
        app1 = MagicMock()
        app1.name = 'app1'

        all_hosts = [web1, web2, web3, db1, db2, app1]

        def mock_get_hosts(pattern=None, order=None):
            # pattern might be a list
            if pattern == 'all' or (isinstance(pattern, list) and 'all' in pattern):
                return all_hosts
            elif pattern == 'webservers' or (isinstance(pattern, list) and 'webservers' in pattern):
                return [web1, web2, web3]
            elif pattern == 'dbservers' or (isinstance(pattern, list) and 'dbservers' in pattern):
                return [db1, db2]
            else:
                return []

        mock_inventory.get_hosts.side_effect = mock_get_hosts

        playbook = Playbook.load('batch_groups.yml', variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]

        play.post_validate(templar)

        batches = pbe._get_serialized_batches(play)

        # With our current implementation (reorder then batch):
        # 1. Reorder by batch_groups: web1, web2, web3, db1, db2, app1
        # 2. Apply serial=2: [web1, web2], [web3, db1], [db2, app1]

        # Check we have 3 batches
        self.assertEqual(len(batches), 3)

        # Check batch contents
        batch_names = [[h.name for h in batch] for batch in batches]
        self.assertEqual(batch_names[0], ['web1', 'web2'])
        self.assertEqual(batch_names[1], ['web3', 'db1'])
        self.assertEqual(batch_names[2], ['db2', 'app1'])

        # Also test that hosts are reordered (webservers before dbservers)
        # Even though batches mix groups, order within reordered list is correct
        all_reordered = [h for batch in batches for h in batch]
        reordered_names = [h.name for h in all_reordered]

        # Check webservers come before dbservers in the flattened list
        web_indices = [i for i, name in enumerate(reordered_names) if name.startswith('web')]
        db_indices = [i for i, name in enumerate(reordered_names) if name.startswith('db')]

        # All webserver indices should be less than all dbserver indices
        if web_indices and db_indices:
            self.assertTrue(max(web_indices) < min(db_indices))
