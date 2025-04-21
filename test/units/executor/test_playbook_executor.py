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

from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.playbook import Playbook
from ansible._internal._templating._engine import TemplateEngine
from ansible.utils import context_objects as co

from units.mock.loader import DictDataLoader


class TestPlaybookExecutor():

    def setup_method(self):
        # Reset command line args for every test
        co.GlobalCLIArgs._Singleton__instance = None

    def teardown_method(self):
        # And cleanup after ourselves too
        co.GlobalCLIArgs._Singleton__instance = None

    def test_get_serialized_batches(self, mocker):
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

        mock_inventory = mocker.MagicMock()
        mock_var_manager = mocker.MagicMock()

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
        assert pbe._get_serialized_batches(play) == [['host0', 'host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7', 'host8', 'host9']]

        playbook = Playbook.load(pbe._playbooks[1], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0', 'host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7', 'host8', 'host9']
        assert pbe._get_serialized_batches(play) == [
            ['host0', 'host1'],
            ['host2', 'host3'],
            ['host4', 'host5'],
            ['host6', 'host7'],
            ['host8', 'host9']
        ]

        playbook = Playbook.load(pbe._playbooks[2], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0', 'host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7', 'host8', 'host9']
        assert pbe._get_serialized_batches(play) == [
            ['host0', 'host1'],
            ['host2', 'host3'],
            ['host4', 'host5'],
            ['host6', 'host7'],
            ['host8', 'host9']
        ]

        playbook = Playbook.load(pbe._playbooks[3], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0', 'host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7', 'host8', 'host9']
        assert pbe._get_serialized_batches(play) == [
            ['host0'],
            ['host1', 'host2'],
            ['host3', 'host4', 'host5'],
            ['host6', 'host7', 'host8'],
            ['host9']
        ]

        playbook = Playbook.load(pbe._playbooks[4], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0', 'host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7', 'host8', 'host9']
        assert pbe._get_serialized_batches(play) == [
            ['host0'],
            ['host1', 'host2'],
            ['host3', 'host4', 'host5', 'host6', 'host7', 'host8', 'host9']
        ]

        # Test when serial percent is under 1.0
        playbook = Playbook.load(pbe._playbooks[2], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0', 'host1', 'host2']
        assert pbe._get_serialized_batches(play) == [['host0'], ['host1'], ['host2']]

        # Test when there is a remainder for serial as a percent
        playbook = Playbook.load(pbe._playbooks[2], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0', 'host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7', 'host8', 'host9', 'host10']
        assert pbe._get_serialized_batches(play) == [
            ['host0', 'host1'],
            ['host2', 'host3'],
            ['host4', 'host5'],
            ['host6', 'host7'],
            ['host8', 'host9'],
            ['host10']
        ]

    def test_generate_retry_inventory_success(self, mocker, tmp_path):
        """Assert that successful creation of the retry file returns True
        and contents are as expected.
        """
        retry_path = tmp_path / 'retry'

        fake_loader = DictDataLoader({})
        mock_inventory = mocker.MagicMock()
        mock_var_manager = mocker.MagicMock()

        pbe = PlaybookExecutor(
            playbooks=[],
            inventory=mock_inventory,
            variable_manager=mock_var_manager,
            loader=fake_loader,
            passwords=[],
        )

        assert pbe._generate_retry_inventory(str(retry_path), ['host1', 'host2'])
        assert retry_path.read_text() == 'host1\nhost2\n'

    def test_generate_retry_inventory_failure(self, mocker):
        """Assert that failure to create the retry file returns False."""
        fake_loader = DictDataLoader({})
        mock_inventory = mocker.MagicMock()
        mock_var_manager = mocker.MagicMock()

        pbe = PlaybookExecutor(
            playbooks=[],
            inventory=mock_inventory,
            variable_manager=mock_var_manager,
            loader=fake_loader,
            passwords=[],
        )

        mocker.patch('os.makedirs', side_effect=OSError)
        assert not pbe._generate_retry_inventory("/some/path", ['host1', 'host2'])
