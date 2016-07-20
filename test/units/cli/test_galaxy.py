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
import shutil
import tarfile
import tempfile

from mock import patch, MagicMock

from ansible.errors import AnsibleError

if PY3:
    raise SkipTest('galaxy is not ported to be py3 compatible yet')

from ansible.cli.galaxy import GalaxyCLI

class TestGalaxy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        '''creating prerequisites for installing a role; setUpClass occurs ONCE whereas setUp occurs with every method tested.'''
        # class data for easy viewing: role_dir, role_tar, role_name, role_req, role_path
        
        if os.path.exists("./delete_me"):
            shutil.rmtree("./delete_me")
        
        # creating framework for a role
        gc = GalaxyCLI(args=["init"])
        with patch('sys.argv', ["-c", "--offline", "delete_me"]):
            gc.parse()
        gc.run()
        cls.role_dir = "./delete_me"
        cls.role_name = "delete_me"

        # making a temp dir for role installation
        cls.role_path = os.path.join(tempfile.mkdtemp(), "roles")
        if not os.path.isdir(cls.role_path):
            os.makedirs(cls.role_path)

        # creating a tar file name for class data
        cls.role_tar = './delete_me.tar.gz'
        cls.makeTar(cls.role_tar, cls.role_dir)

        # creating a temp file with installation requirements
        cls.role_req = './delete_me_requirements.yml'
        fd = open(cls.role_req, "w")
        fd.write("- 'src': '%s'\n  'name': '%s'\n  'path': '%s'" % (cls.role_tar, cls.role_name, cls.role_path))
        fd.close()

    @classmethod
    def makeTar(cls, output_file, source_dir):
        ''' used for making a tarfile from a role directory '''
        # adding directory into a tar file
        try:
            tar = tarfile.open(output_file, "w:gz")
            tar.add(source_dir, arcname=os.path.basename(source_dir))
        except AttributeError: # tarfile obj. has no attribute __exit__ prior to python 2.    7
                pass
        finally:  # ensuring closure of tarfile obj
            tar.close()

    @classmethod
    def tearDownClass(cls):
        '''After tests are finished removes things created in setUpClass'''
        # deleting the temp role directory
        if os.path.exists(cls.role_dir):
            shutil.rmtree(cls.role_dir)
        if os.path.exists(cls.role_req):
            os.remove(cls.role_req)
        if os.path.exists(cls.role_tar):
            os.remove(cls.role_tar)
        if os.path.isdir(cls.role_path):
            shutil.rmtree(cls.role_path)

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

    def test_execute_remove(self):
        # installing role
        gc = GalaxyCLI(args=["install"])
        with patch('sys.argv', ["--offline", "-p", self.role_path, "-r", self.role_req]):
            galaxy_parser = gc.parse()
        gc.run()
        
        # checking that installation worked
        role_file = os.path.join(self.role_path, self.role_name)
        self.assertTrue(os.path.exists(role_file))

        # removing role
        gc = GalaxyCLI(args=["remove"])
        with patch('sys.argv', ["-c", "-p", self.role_path, self.role_name]):
            galaxy_parser = gc.parse()
        super(GalaxyCLI, gc).run()
        gc.api = ansible.galaxy.api.GalaxyAPI(gc.galaxy)
        completed_task = gc.execute_remove()

        # testing role was removed
        self.assertTrue(completed_task == 0)
        self.assertTrue(not os.path.exists(role_file))

    def test_execute_search(self):

        ### testing if no search terms are given
        gc = GalaxyCLI(args=["search"])
        with patch('sys.argv', ["-c"]):
            galaxy_parser = gc.parse()
        self.assertRaises(AnsibleError, gc.run)

        ### testing if the search term found no results
                # setup #
        search_return_val = {'count':0, 'results':[]}

                # running method to test #
        gc = GalaxyCLI(args=["search"])
        with patch('sys.argv', ["-c", "search_example"]):
            galaxy_parser = gc.parse()
        super(GalaxyCLI, gc).run()
        gc.api = ansible.galaxy.api.GalaxyAPI(gc.galaxy)
        with patch.object(ansible.galaxy.api.GalaxyAPI, "search_roles", return_value=search_return_val) as mock_search: # mocks out internet use
            with patch.object(ansible.utils.display.Display, "display") as mocked_display:  # used for checking correct message
                completed_task = gc.execute_search()

                # tests #
                self.assertTrue(completed_task)
                self.assertEqual(mock_search.call_count, 1)
                self.assertEqual(mocked_display.call_count, 1)
                mocked_display.assert_called_once_with('No roles match your search.', color='red')

        ### testing search if there are fewer results than the page size
                # setup #
        role = MagicMock()
        role['username'] = 'username'
        role['name'] = 'role'
        role['description'] = "DESCRIPTION"
        search_return_val = {'count':1, 'results':[role]}
        
                # running method to test #
        gc = GalaxyCLI(args=["search"])
        with patch('sys.argv', ["-c", "search_example"]):
            galaxy_parser = gc.parse()
        super(GalaxyCLI, gc).run()
        gc.api = ansible.galaxy.api.GalaxyAPI(gc.galaxy)
        with patch.object(ansible.galaxy.api.GalaxyAPI, "search_roles", return_value=search_return_val) as mock_search:  # mocks out internet use
            with patch.object(ansible.cli.CLI, "pager") as mock_pager:  # used for checking correct message
                completed_task = gc.execute_search()

                # tests #
                self.assertTrue(completed_task)
                self.assertEqual(mock_search.call_count, 1)
                self.assertEqual(mock_pager.call_count, 1)
                mock_pager.assert_called_with(u'\nFound 1 roles matching your search:\n\n Name Description\n ---- -----------\n %s.%s %s' % (role['username'], role['name'], role['description']))

        ### testing search if there are more results than the page size
                # setup #
        roles = []
        role = MagicMock()
        role['username'] = 'username'
        role['name'] = 'role'
        role['description'] = "DESCRIPTION"
        for i in range(0, 1001): roles.append(role)
        search_return_val = {'count':1001, 'results':roles}

                # running method to test #        
        gc = GalaxyCLI(args=["search"])
        with patch('sys.argv', ["-c", "search_example"]):
            galaxy_parser = gc.parse()
        super(GalaxyCLI, gc).run()
        gc.api = ansible.galaxy.api.GalaxyAPI(gc.galaxy)
        with patch.object(ansible.galaxy.api.GalaxyAPI, "search_roles", return_value=search_return_val) as mock_search:  # mocks out internet use
            with patch.object(ansible.cli.CLI, "pager") as mock_pager:  # used for checkitn correct message
                completed_task = gc.execute_search()
                
                # tests #
                self.assertTrue(completed_task)
                self.assertEqual(mock_search.call_count, 1)
                self.assertEqual(mock_pager.call_count, 1)
                self.assertIn('Found 1001 roles matching your search. Showing first 1000.', str(mock_pager.call_args_list))

