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
import ansible
import os
import getpass

from mock import patch

from ansible.errors import AnsibleError
from ansible.module_utils.urls import SSLValidationError
from urllib2 import HTTPError

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

    @patch.object(ansible.utils.display.Display, "display")  # eliminating messages flushed to screen
    def test_execute_login(self, mocked_display):

        ### regardless of credentials/internet, tests that execute_login is called and behaves in an expected manner ###
        gc = GalaxyCLI(args=["login"])
                
            # testing when self.options.token is None:
        with patch('sys.argv', ["-c"]):
            galaxy_parser = gc.parse()
        with patch.object(ansible.galaxy.token.GalaxyToken, "__init__", return_value=None) as mocked_GalaxyToken:  # to test token object is created
            with patch.object(GalaxyCLI, "execute_login", return_value=0) as mocked_login:
                gc.run()
                self.assertTrue(mocked_login.call_count, 1)
                self.assertTrue(mocked_login.return_value==0)
                self.assertTrue(mocked_GalaxyToken.call_count, 1) 

            # testing when self.options.token is not None
        with patch('sys.argv', ["-c", "--github-token", "imaginary_token"]):
            galaxy_parser = gc.parse()
        with patch.object(ansible.galaxy.token.GalaxyToken, "__init__", return_value=None) as mocked_GalaxyToken:
            with patch.object(GalaxyCLI, "execute_login", return_value=0) as mocked_login:
                gc.run()
                self.assertTrue(mocked_login.call_count, 1)
                self.assertTrue(mocked_login.return_value==0)
                self.assertTrue(mocked_GalaxyToken.call_count, 1)

        ### These (optional) tests requires internet connection. Using try/except to ensure internet is working rather than fail tests requiring connection while offline. If connection seems to fail a SkipTest will be raised, informing the tester that internet is required. ###
        try:
            # if authentication is provided more thorough tests can verify execute_login's behavior
            if self.auth:

                # testing login with username and password if possible
                gc = GalaxyCLI(args=["login"])
                with patch('sys.argv', ["-c"]):
                    galaxy_parser = gc.parse()
                # patches because we only ask tester for authentication once
                with patch('__builtin__.raw_input', return_value= self.galaxy_username):
                    with patch('getpass.getpass', return_value=self.galaxy_password):
                        if not self.galaxy_username or not self.galaxy_password:  # if an empty string for username or password
                            self.assertRaises(AnsibleError, gc.run)
                        else:  # if user provided bad credentials "Bad credentials" error will be raised
                            super(GalaxyCLI, gc).run()
                            gc.api = ansible.galaxy.api.GalaxyAPI(gc.galaxy)
                            completed_task = gc.execute_login()
                            self.assertTrue(completed_task == 0)

                # testing login with token if possible
                gc = GalaxyCLI(args=["login"])
                if not self.github_token:
                    with patch('sys.argv', ["-c", "--github-token"]):
                        self.assertRaisesRegexp( SystemExit, '2', gc.parse)
                else:  # if user provided bad credentials this will fail
                    display = ansible.utils.display.Display()
                    display.display(u"self.github_token is true. Value is: %s" % self.github_token)
                    with patch('sys.argv', ["-c", "--github-token", self.github_token]):
                        galaxy_parser = gc.parse()
                    super(GalaxyCLI, gc).run()
                    gc.api = ansible.galaxy.api.GalaxyAPI(gc.galaxy)
                    completed_task = gc.execute_login()
                    self.assertTrue(completed_task == 0)

            # if internet is functioning more thorough tests can verify execute_login's behavior 
            # testing login with insufficient credentials
            gc = GalaxyCLI(args=["login"])
            with patch('sys.argv', ["-c"]):
                galaxy_parser = gc.parse()
            with patch('__builtin__.raw_input', return_value=None):
                with patch('getpass.getpass', return_value=None):
                    self.assertRaises(AnsibleError, gc.run)
            with patch('__builtin__.raw_input', return_value="invalid_username"):
                with patch('getpass.getpass', return_value='invalid_password'):
                    self.assertRaises(AnsibleError, gc.run)

            # testing token login with insufficient token
            gc = GalaxyCLI(args=["login"])
            with patch('sys.argv', ["-c", "--github-token", "invalid_token"]):  # with invalid token
                galaxy_parser = gc.parse()
            self.assertRaises(HTTPError, gc.run)
            with patch('sys.argv', ["-c", "--github-token"]):  # without token argument
                self.assertRaisesRegexp( SystemExit, '2', gc.parse)

        except (SSLValidationError, AnsibleError) as e:
            if str(e) == "Bad credentials":
                raise
            elif "Failed to validate the SSL certificate" in e.message:
                raise SkipTest(' there is a test case within this method that requires an internet connection and a valid CA certificate installed; this part of the method is skipped when one or both of these requirements are not provided\n ... ok ')
            else:
                raise
