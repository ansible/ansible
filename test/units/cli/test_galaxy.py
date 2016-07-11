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

from nose.plugins.skip import SkipTest
import os
import getpass

if PY3:
    raise SkipTest('galaxy is not ported to be py3 compatible yet')

from ansible.cli.galaxy import GalaxyCLI

class TestGalaxy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Prompting the testing to provide credentials will not happen by default and is not required for most tests. This is simply an option to improve the thoroughness of testing.
        if 'GALAXY_CREDS_PROMPT' in os.environ.keys():
            try:
                #authentication may be declined and tests inhibited will be avoided
                cls.auth = True
                # using getpass to ensure tester sees message (unlike raw_input)
                cls.galaxy_username = getpass.getpass("\nPress ENTER to opt out of any of the authentication prompts.\nYour information will not be displayed.\nEnter your Ansible-Galaxy/Github username: ")
                cls.galaxy_password = getpass.getpass("Enter your Ansible-Galaxy/Github password: ")
                cls.github_token = getpass.getpass("Enter/Copy + paste Github Personal Access Token to login to Ansible-Galaxy: ")
                cls.import_repo = getpass.getpass("To test importing a role please provide the name of a valid github repo (containing a role) belonging to the username provided above: ")
            except getpass.GetPassWarning:
                cls.auth = False
        else:
            cls.auth = False    
    
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
