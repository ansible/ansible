# -*- coding: utf-8 -*-
# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
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
from ansible.module_utils.basic import heuristic_log_sanitize


class TestHeuristicLogSanitize(unittest.TestCase):
    def setUp(self):
        self.URL_SECRET = 'http://username:pas:word@foo.com/data'
        self.SSH_SECRET = 'username:pas:word@foo.com/data'
        self.clean_data = repr(self._gen_data(3, True, True, 'no_secret_here'))
        self.url_data = repr(self._gen_data(3, True, True, self.URL_SECRET))
        self.ssh_data = repr(self._gen_data(3, True, True, self.SSH_SECRET))

    def _gen_data(self, records, per_rec, top_level, secret_text):
        hostvars = {'hostvars': {}}
        for i in range(1, records, 1):
            host_facts = {
                'host%s' % i: {
                    'pstack': {
                        'running': '875.1',
                        'symlinked': '880.0',
                        'tars': [],
                        'versions': ['885.0']
                    },
                }
            }
            if per_rec:
                host_facts['host%s' % i]['secret'] = secret_text
            hostvars['hostvars'].update(host_facts)
        if top_level:
            hostvars['secret'] = secret_text
        return hostvars

    def test_did_not_hide_too_much(self):
        self.assertEqual(heuristic_log_sanitize(self.clean_data), self.clean_data)

    def test_hides_url_secrets(self):
        url_output = heuristic_log_sanitize(self.url_data)
        # Basic functionality: Successfully hid the password
        self.assertNotIn('pas:word', url_output)

        # Slightly more advanced, we hid all of the password despite the ":"
        self.assertNotIn('pas', url_output)

        # In this implementation we replace the password with 8 "*" which is
        # also the length of our password.  The url fields should be able to
        # accurately detect where the password ends so the length should be
        # the same:
        self.assertEqual(len(url_output), len(self.url_data))

    def test_hides_ssh_secrets(self):
        ssh_output = heuristic_log_sanitize(self.ssh_data)
        self.assertNotIn('pas:word', ssh_output)

        # Slightly more advanced, we hid all of the password despite the ":"
        self.assertNotIn('pas', ssh_output)

        # ssh checking is harder as the heuristic is overzealous in many
        # cases.  Since the input will have at least one ":" present before
        # the password we can tell some things about the beginning and end of
        # the data, though:
        self.assertTrue(ssh_output.startswith("{'"))
        self.assertTrue(ssh_output.endswith("}"))
        self.assertIn(":********@foo.com/data'", ssh_output)

    def test_hides_parameter_secrets(self):
        output = heuristic_log_sanitize('token="secret", user="person", token_entry="test=secret"', frozenset(['secret']))
        self.assertNotIn('secret', output)

    def test_no_password(self):
        self.assertEqual(heuristic_log_sanitize('foo@bar'), 'foo@bar')
