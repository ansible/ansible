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
from ansible.compat.tests.mock import MagicMock

from collections import Counter

from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.playbook import Playbook
from ansible.template import Templar

from units.mock.loader import DictDataLoader

class TestPlaybookExecutor(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

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

            'grouped_serial_useless.yml': '''
            - hosts: all
              gather_facts: no
              serial: 1
              # each host is its own group/slice, which effectively disables serialization!
              # seless, but proper behaviour
              serial_group_by: "{{host}}"
              tasks:
              - debug: var=inventory_hostname
            ''',
            'grouped_serial_int.yml': '''
            - hosts: all
              gather_facts: no
              serial: 1
              serial_group_by: "{{host.testgroup}}"
              tasks:
              - debug: var=inventory_hostname
            ''',
            'grouped_serial_pct.yml': '''
            - hosts: all
              gather_facts: no
              serial: 20%
              serial_group_by: "{{host.testgroup}}"
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

        templar = Templar(loader=fake_loader)

        pbe = PlaybookExecutor(
            playbooks=['no_serial.yml', 'serial_int.yml', 'serial_pct.yml', 'serial_list.yml', 'serial_list_mixed.yml',
                       'grouped_serial_useless.yml', 'grouped_serial_int.yml', 'grouped_serial_pct.yml'],
            inventory=mock_inventory,
            variable_manager=mock_var_manager,
            loader=fake_loader,
            options=mock_options,
            passwords=[],
        )

        playbook = Playbook.load(pbe._playbooks[0], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0','host1','host2','host3','host4','host5','host6','host7','host8','host9']
        self.assertEqual(pbe._get_serialized_batches(play), [['host0','host1','host2','host3','host4','host5','host6','host7','host8','host9']])

        playbook = Playbook.load(pbe._playbooks[1], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0','host1','host2','host3','host4','host5','host6','host7','host8','host9']
        self.assertEqual(pbe._get_serialized_batches(play), [['host0','host1'],['host2','host3'],['host4','host5'],['host6','host7'],['host8','host9']])

        playbook = Playbook.load(pbe._playbooks[2], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0','host1','host2','host3','host4','host5','host6','host7','host8','host9']
        self.assertEqual(pbe._get_serialized_batches(play), [['host0','host1'],['host2','host3'],['host4','host5'],['host6','host7'],['host8','host9']])

        playbook = Playbook.load(pbe._playbooks[3], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0','host1','host2','host3','host4','host5','host6','host7','host8','host9']
        self.assertEqual(pbe._get_serialized_batches(play), [['host0'],['host1','host2'],['host3','host4','host5'],['host6','host7','host8'],['host9']])

        playbook = Playbook.load(pbe._playbooks[4], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0','host1','host2','host3','host4','host5','host6','host7','host8','host9']
        self.assertEqual(pbe._get_serialized_batches(play), [['host0'],['host1','host2'],['host3','host4','host5','host6','host7','host8','host9']])

        # Test when serial percent is under 1.0
        playbook = Playbook.load(pbe._playbooks[2], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0','host1','host2']
        self.assertEqual(pbe._get_serialized_batches(play), [['host0'],['host1'],['host2']])

        # Test when there is a remainder for serial as a percent
        playbook = Playbook.load(pbe._playbooks[2], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0','host1','host2','host3','host4','host5','host6','host7','host8','host9','host10']
        self.assertEqual(pbe._get_serialized_batches(play), [['host0','host1'],['host2','host3'],['host4','host5'],['host6','host7'],['host8','host9'],['host10']])

        # grouping feature, useless implementation detail (see comment in test playbook)
        mock_var_manager.get_vars.return_value = dict()
        playbook = Playbook.load(pbe._playbooks[5], variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = ['host0','host1','host2','host3','host4','host5','host6','host7','host8','host9']
        self.assertItemsEqual(map(Counter, pbe._get_serialized_batches(play)),
                              [Counter(['host0','host1','host2','host3','host4','host5','host6','host7','host8','host9'])])

        # real test of grouping feature: these test case cannot use simple strings as hosts
        # instead, playbooks are tested against several variants of inventory
        playbook_grouping_int = 'grouped_serial_int.yml'
        playbook_grouping_pct = 'grouped_serial_pct.yml'

        grouping_hosts = [
            {'name': 'host' + str(i), 'testgroup': 'even' if (i % 2) == 0 else 'odd'}
            for i in range(10)
        ]
        gh_even = [h for h in grouping_hosts if h['testgroup'] == 'even']
        gh_odd = [h for h in grouping_hosts if h['testgroup'] == 'odd']
        # in the basic cases, one even and one odd host are processed together; this is just like pythonic zip
        #  (except that we require list, not tuples)
        grouping_host_zip_pairs = map(list, zip(gh_even, gh_odd))

        # simple case: with serial=1, it's just like python's zip
        #  and 20% is the same as 1, because both slices have size==5
        for playbook in playbook_grouping_int, playbook_grouping_pct:
            playbook = Playbook.load(playbook, variable_manager=mock_var_manager, loader=fake_loader)
            play = playbook.get_plays()[0]
            play.post_validate(templar)
            mock_inventory.get_hosts.return_value = list(grouping_hosts)
            self.assertEqual(pbe._get_serialized_batches(play), grouping_host_zip_pairs)
        # more complicated case: add some more even hosts, but no odd ones
        gh_even_extra = [{'name': 'extra_host' + str(i), 'testgroup': 'even'} for i in range(10, 20, 2)]
        grouping_hosts.extend(gh_even_extra)
        # with these hosts, serial=1 first processes zip, then the even ones (one by one)
        playbook = Playbook.load(playbook_grouping_int, variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = list(grouping_hosts)
        self.assertEqual(pbe._get_serialized_batches(play),
                         grouping_host_zip_pairs + [[host] for host in gh_even_extra])
        # and even more complicated case: 20% of even hosts are now 2 --> first five batches are of size 3!
        playbook = Playbook.load(playbook_grouping_pct, variable_manager=mock_var_manager, loader=fake_loader)
        play = playbook.get_plays()[0]
        play.post_validate(templar)
        mock_inventory.get_hosts.return_value = list(grouping_hosts)
        self.assertEqual(pbe._get_serialized_batches(play), [
            # these might be generated, but... this is probably better for demonstration
            [gh_even[0], gh_even[1], gh_odd[0]],
            [gh_even[2], gh_even[3], gh_odd[1]],
            [gh_even[4], gh_even_extra[0], gh_odd[2]],
            [gh_even_extra[1], gh_even_extra[2], gh_odd[3]],
            [gh_even_extra[3], gh_even_extra[4], gh_odd[4]],
        ])
