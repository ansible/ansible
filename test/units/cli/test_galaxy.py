# (c) 2016, Adrian Likins <alikins@redhat.com>
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

from ansible.compat.six import PY3
from ansible.compat.tests import unittest
from mock import patch

from ansible.errors import AnsibleOptionsError

from nose.plugins.skip import SkipTest
import ansible

if PY3:
    raise SkipTest('galaxy is not ported to be py3 compatible yet')

from ansible.cli.galaxy import GalaxyCLI

class TestGalaxy(unittest.TestCase):
    def setUp(self):
        self.default_args = []

    def test_init(self):
        galaxy_cli = GalaxyCLI(args=self.default_args)
        self.assertTrue(isinstance(galaxy_cli, GalaxyCLI))

    def test_display_min(self):
        gc = GalaxyCLI(args=self.default_args)
        role_info = {'name': 'some_role_name'}
        display_result = gc._display_role_info(role_info)
        self.assertTrue(display_result.find('some_role_name') >-1)

    def test_display_galaxy_info(self):
        gc = GalaxyCLI(args=self.default_args)
        galaxy_info = {}
        role_info = {'name': 'some_role_name',
                     'galaxy_info': galaxy_info}
        display_result = gc._display_role_info(role_info)
        if display_result.find('\t\tgalaxy_tags:') > -1:
            self.fail('Expected galaxy_tags to be indented twice')

    def test_parse(self):
        ''' tests that an options parser is created for bin/ansible; entails creating SortedOptParser instance and Galaxy instance '''
        for arguments in [[], ["list", "info"], ["bad_arg", "list"], ["bad_arg", "invalid"]]:
            # setup
            gc = GalaxyCLI(args=arguments)
            first_arg = False
            for arg in arguments:
                if arg in gc.VALID_ACTIONS:
                    # getting data to use for testing
                    first_arg = arg
                    # stop looking after a valid action is identified
                    break

            # testing case when no valid action is found
            if first_arg == False:
                with patch('sys.argv', ["-c"]):
                    self.assertRaises(AnsibleOptionsError, gc.parse)
            # testing case when valid action is found
            else:
                with patch('sys.argv', ["-c"]):
                    created_parser = gc.parse()
                self.assertTrue(created_parser)
                self.assertTrue(isinstance(gc.parser, ansible.cli.SortedOptParser))
                self.assertTrue(isinstance(gc.galaxy, ansible.galaxy.Galaxy))
                self.assertTrue(gc.action)
                self.assertTrue(gc.options.roles_path == ['/etc/ansible/roles'])
                self.assertTrue(gc.action == first_arg)
                self.assertNotIn(first_arg, arguments)
