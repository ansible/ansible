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

from mock import patch

from ansible.errors import AnsibleError
from ansible.module_utils.urls import SSLValidationError

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

    def test_execute_search(self):
        # regardless of internet connection, tests that execute_search is called and calls necessary methods
        gc = GalaxyCLI(args=["search"])

            ### testing insufficient search query ###
        with patch('sys.argv', ["-c"]):
            galaxy_parser = gc.parse()
            self.assertRaises(AnsibleError, gc.run)

            ### testing search that is successful ###
        gc.args=["search"]
        with patch('sys.argv', ["-c", "role"]):
            galaxy_parser = gc.parse()
        super(GalaxyCLI, gc).run()
        gc.api = ansible.galaxy.api.GalaxyAPI(gc.galaxy)
        # mocking out method that uses the internet
        with patch.object(ansible.galaxy.api.GalaxyAPI, "search_roles"):
            # mocking out method that requires data from internet
            with patch('__builtin__.max', return_value=0):
                # mocking pager to verify what message the user is given
                with patch.object(ansible.cli.CLI, "pager") as mock_pager:
                    completed_task = gc.execute_search()
                    self.assertTrue(completed_task)
                    mock_pager.assert_called_with(u'\nFound 1 roles matching your search. Showing first 1000.\n\n Name Description\n ---- -----------')

            ### testing search that gets no results ###
        gc.args=["search"]
        with patch('sys.argv', ["-c", "role"]):
            galaxy_parser = gc.parse()
        super(GalaxyCLI, gc).run()
        gc.api = ansible.galaxy.api.GalaxyAPI(gc.galaxy)
        # mocking out method that uses the internet + return_value that signifies nothing has been found
        with patch.object(ansible.galaxy.api.GalaxyAPI, "search_roles", return_value={'count': 0}):
            # mocking display to verify what message the user is given
            with patch.object(ansible.utils.display.Display, "display") as mock_display:
                completed_task = gc.execute_search()
                self.assertTrue(completed_task)
                mock_display.assert_called_with("No roles match your search.", color='red')

        # This test requires internet connection. Using try/except to ensure internet is working rather than fail tests requiring connection while offline.
        try:
            gc = GalaxyCLI(args=["search"])

            ### testing sufficient search ###
                # searching for 'role' keyword
            with patch('sys.argv', ["-c", "role"]):
                galaxy_parser = gc.parse()
            with patch.object(ansible.cli.CLI, "pager"):  # eliminating display output
                super(GalaxyCLI, gc).run()
                gc.api = ansible.galaxy.api.GalaxyAPI(gc.galaxy)
                completed_task = gc.execute_search()
                self.assertTrue(completed_task == True)

        except AnsibleError as e:        
            if "Failed to get data from the API server" in e.message:
                raise SkipTest(' there is a test case within this method that requires an internet connection and a valid CA certificate installed; this part of the method is skipped when one or both of these requirements are not provided\n ... ok ')
            else:
                raise
