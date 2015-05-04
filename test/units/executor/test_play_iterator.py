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
from ansible.executor.play_iterator import PlayIterator
from ansible.playbook import Playbook

from test.mock.loader import DictDataLoader

class TestPlayIterator(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_play_iterator(self):
        fake_loader = DictDataLoader({
            "test_play.yml": """
            - hosts: all
              gather_facts: false
              roles:
              - test_role
              pre_tasks:
              - debug: msg="this is a pre_task"
              tasks:
              - debug: msg="this is a regular task"
              post_tasks:
              - debug: msg="this is a post_task"
            """,
            '/etc/ansible/roles/test_role/tasks/main.yml': """
            - debug: msg="this is a role task"
            """,
        })

        p = Playbook.load('test_play.yml', loader=fake_loader)

        hosts = []
        for i in range(0, 10):
            host  = MagicMock()
            host.get_name.return_value = 'host%02d' % i
            hosts.append(host)

        inventory = MagicMock()
        inventory.get_hosts.return_value = hosts
        inventory.filter_hosts.return_value = hosts

        itr = PlayIterator(inventory, p._entries[0])
        task = itr.get_next_task_for_host(hosts[0])
        print(task)
        self.assertIsNotNone(task)
        task = itr.get_next_task_for_host(hosts[0])
        print(task)
        self.assertIsNotNone(task)
        task = itr.get_next_task_for_host(hosts[0])
        print(task)
        self.assertIsNotNone(task)
        task = itr.get_next_task_for_host(hosts[0])
        print(task)
        self.assertIsNotNone(task)
        task = itr.get_next_task_for_host(hosts[0])
        print(task)
        self.assertIsNone(task)
