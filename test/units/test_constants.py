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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pwd
import os

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock

from ansible import constants as C
from ansible.cli import CLI
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.executor.connection_info import ConnectionInformation

from units.mock.loader import DictDataLoader

class TestConstants(unittest.TestCase):

    def setUp(self):
        self.config_file = open('ansible.cfg', 'w')
        self.config_file.write(
        '''[defaults]
system_errors = false
[ssh_connection]
ssh_args = -o StrictHostKeyChecking=no -o ControlPersist=15m -F /etc/ansible/ssh.config -q
scp_if_ssh = True
some_false_value = False
some_other_false_value = false
some_empty_value =
            ''')
        self.config_file.close()

    def tearDown(self):
        os.remove(self.config_file.name)


    def test_get_config(self):
        p, path = C.load_config_file()
        self.assertEqual(path, os.getcwd() + '/ansible.cfg')
        self.assertEqual(C.get_config(p, 'ssh_connection', 'ssh_args', 'ANSIBLE_SSH_ARGS', None), '-o StrictHostKeyChecking=no -o ControlPersist=15m -F /etc/ansible/ssh.config -q')
        os.environ['ANSIBLE_SSH_ARGS'] = '-o StrictHostKeyChecking=yes'
        self.assertEqual(C.get_config(p, 'ssh_connection', 'ssh_args', 'ANSIBLE_SSH_ARGS', None), '-o StrictHostKeyChecking=yes')
        os.environ['ANSIBLE_SSH_ARGS'] = ''
        self.assertEqual(C.get_config(p, 'ssh_connection', 'ssh_args', 'ANSIBLE_SSH_ARGS', None), '-o StrictHostKeyChecking=no -o ControlPersist=15m -F /etc/ansible/ssh.config -q')
        self.assertEqual(C.get_config(p, 'ssh_connection', 'some_false_value', None, None, boolean=True), False)
        os.environ['ANSIBLE_SSH_ARGS'] = 'false'
        self.assertEqual(C.get_config(p, 'ssh_connection', 'some_empty_value', None, None), '')
        self.assertEqual(C.get_config(p, 'ssh_connection', 'some_empty_value', None, None, boolean=True), False)
