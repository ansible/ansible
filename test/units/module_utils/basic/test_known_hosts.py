# -*- coding: utf-8 -*-
# (c) 2015, Michael Scherer <mscherer@redhat.com>
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

from ansible.compat.tests import unittest
from ansible.module_utils import known_hosts

import json
import ansible.module_utils.basic
from ansible.compat.tests.mock import Mock
from units.mock.procenv import swap_stdin_and_argv

class TestAnsibleModuleKnownHosts(unittest.TestCase):
    urls = {
        'ssh://one.example.org/example.git':
            {'is_ssh_url': True, 'get_fqdn': 'one.example.org',
             'add_host_key_cmd': " -t rsa one.example.org",
             'port': known_hosts.SSH_KEYSCAN_DEFAULT_PORT},
        'ssh+git://two.example.org/example.git':
            {'is_ssh_url': True, 'get_fqdn': 'two.example.org',
             'add_host_key_cmd': " -t rsa two.example.org", 
             'port': known_hosts.SSH_KEYSCAN_DEFAULT_PORT},
        'rsync://three.example.org/user/example.git':
            {'is_ssh_url': False, 'get_fqdn': 'three.example.org', 
             'add_host_key_cmd': None, # not called for non-ssh urls
             'port': known_hosts.SSH_KEYSCAN_DEFAULT_PORT},
        'git@four.example.org:user/example.git':
            {'is_ssh_url': True, 'get_fqdn': 'four.example.org',
             'add_host_key_cmd': " -t rsa four.example.org", 
             'port': known_hosts.SSH_KEYSCAN_DEFAULT_PORT},
        'git+ssh://five.example.org/example.git':
            {'is_ssh_url': True, 'get_fqdn': 'five.example.org', 
             'add_host_key_cmd': " -t rsa five.example.org",
             'port': known_hosts.SSH_KEYSCAN_DEFAULT_PORT},
        'ssh://six.example.org:21/example.org': # ssh on FTP Port? 
            {'is_ssh_url': True, 'get_fqdn': 'six.example.org',
             'add_host_key_cmd': " -t rsa six.example.org -p 21", # should add port param, since it's different from default
             'port': "21"},
        'ssh://[2001:DB8::abcd:abcd]/example.git':
            {'is_ssh_url': True, 'get_fqdn': '[2001:DB8::abcd:abcd]',
             'add_host_key_cmd': " -t rsa [2001:DB8::abcd:abcd]",
             'port': known_hosts.SSH_KEYSCAN_DEFAULT_PORT},
        'ssh://[2001:DB8::abcd:abcd]:22/example.git':
            {'is_ssh_url': True, 'get_fqdn': '[2001:DB8::abcd:abcd]',
             'add_host_key_cmd': " -t rsa [2001:DB8::abcd:abcd]", 
             # even though it's explicitly specified we do not add port here (for backwards compatibility)'
             'add_host_key_cmd': " -t rsa [2001:DB8::abcd:abcd]",  
             'port': "22"},
        'username@[2001:DB8::abcd:abcd]/example.git':
            {'is_ssh_url': True, 'get_fqdn': '[2001:DB8::abcd:abcd]',
             'add_host_key_cmd': " -t rsa [2001:DB8::abcd:abcd]", 
             'port': known_hosts.SSH_KEYSCAN_DEFAULT_PORT},
        'username@[2001:DB8::abcd:abcd]:22/example.git':
            {'is_ssh_url': True, 'get_fqdn': '[2001:DB8::abcd:abcd]',
             'add_host_key_cmd': " -t rsa [2001:DB8::abcd:abcd]", 
             'port': "22"},
        'ssh://internal.git.server:7999/repos/repo.git':
            {'is_ssh_url': True, 'get_fqdn': 'internal.git.server',
             'add_host_key_cmd': " -t rsa internal.git.server -p 7999",
             'port': "7999"}
    }

    def test_is_ssh_url(self):
        for u in self.urls:
            self.assertEqual(known_hosts.is_ssh_url(u), self.urls[u]['is_ssh_url'])

    def test_get_fqdn(self):
        for u in self.urls:
            self.assertEqual(known_hosts.get_fqdn(u), self.urls[u]['get_fqdn'])

    def test_get_fqdn_and_port(self):
        for u in self.urls:
            self.assertEqual(known_hosts.get_fqdn_and_port(u), (self.urls[u]['get_fqdn'], self.urls[u]['port']))

    def test_add_host_key(self):

        # Copied
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={}))
        # unittest doesn't have a clean place to use a context manager, so we have to enter/exit manually
        self.stdin_swap = swap_stdin_and_argv(stdin_data=args)
        self.stdin_swap.__enter__()

        ansible.module_utils.basic._ANSIBLE_ARGS = None 
        self.module = ansible.module_utils.basic.AnsibleModule(argument_spec=dict())

        run_command = Mock()
        run_command.return_value = (0, "Needs output, otherwise thinks ssh-keyscan timed out'", "")
        self.module.run_command = run_command

        get_bin_path = Mock()
        get_bin_path.return_value = keyscan_cmd = "/custom/path/ssh-keyscan"
        self.module.get_bin_path = get_bin_path

        for u in self.urls:
            if self.urls[u]['is_ssh_url']:
                known_hosts.add_host_key(self.module, self.urls[u]['get_fqdn'], port=self.urls[u]['port'])
                run_command.assert_called_with(keyscan_cmd + self.urls[u]['add_host_key_cmd'])


