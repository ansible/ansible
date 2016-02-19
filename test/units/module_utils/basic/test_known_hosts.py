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


class TestAnsibleModuleKnownHosts(unittest.TestCase):
    urls = {
        'ssh://one.example.org/example.git':
            {'is_ssh_url': True, 'get_fqdn': 'one.example.org', 'get_port': None},
        'ssh+git://two.example.org/example.git':
            {'is_ssh_url': True, 'get_fqdn': 'two.example.org', 'get_port': None},
        'rsync://three.example.org/user/example.git':
            {'is_ssh_url': False, 'get_fqdn': 'three.example.org', 'get_port': None},
        'git@four.example.org:user/example.git':
            {'is_ssh_url': True, 'get_fqdn': 'four.example.org', 'get_port': None},
        'git+ssh://five.example.org/example.git':
            {'is_ssh_url': True, 'get_fqdn': 'five.example.org', 'get_port': None},
        'ssh://six.example.org:21/example.org':
            {'is_ssh_url': True, 'get_fqdn': 'six.example.org', 'get_port': '21'},
        'git@[seven.example.org:443]/example.git':
            {'is_ssh_url': True, 'get_fqdn': 'seven.example.org', 'get_port': '443'},
        'git+ssh://git@eight.example.org:443/example.git':
            {'is_ssh_url': True, 'get_fqdn': 'eight.example.org', 'get_port': '443'},
        'git+ssh://git@[nine.example.org:443]/example.git':
            {'is_ssh_url': True, 'get_fqdn': 'nine.example.org', 'get_port': '443'},
        'git+ssh://git@[ten.example.org]/example.git':
            {'is_ssh_url': True, 'get_fqdn': 'ten.example.org', 'get_port': None},
        'ssh://[2001:DB8::abcd:abcd]/example.git':
            {'is_ssh_url': True, 'get_fqdn': '[2001:DB8::abcd:abcd]', 'get_port': None},
        'ssh://[2001:DB8::abcd:abcd]:22/example.git':
            {'is_ssh_url': True, 'get_fqdn': '[2001:DB8::abcd:abcd]', 'get_port': '22'},
        'ssh://[2001:DB8::abcd:abcd]:21/example.git':
            {'is_ssh_url': True, 'get_fqdn': '[2001:DB8::abcd:abcd]', 'get_port': '21'},
        'username@[2001:DB8::abcd:abcd]/example.git':
            {'is_ssh_url': True, 'get_fqdn': '[2001:DB8::abcd:abcd]', 'get_port': None},
    }

    def test_is_ssh_url(self):
        for u in self.urls:
            self.assertEqual(known_hosts.is_ssh_url(u), self.urls[u]['is_ssh_url'])

    def test_get_fqdn(self):
        for u in self.urls:
            self.assertEqual(known_hosts.get_fqdn(u), self.urls[u]['get_fqdn'])

    def test_get_port(self):
        for u in self.urls:
            self.assertEqual(known_hosts.get_port(u), self.urls[u]['get_port'], "%s != %s for %s"
                             % (known_hosts.get_port(u), self.urls[u]['get_port'], u))
