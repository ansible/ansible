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
<<<<<<< 370a90f18ef464bc26c495dd3cefb7f9292a2ace

from mock import patch

from ansible.errors import AnsibleError
from ansible.module_utils.urls import SSLValidationError
=======
import tarfile
import tempfile

from mock import patch
>>>>>>> Adding a test for GalaxyCLI and two methods on which it depends. Tes…  (#16651)

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

<<<<<<< 370a90f18ef464bc26c495dd3cefb7f9292a2ace
    def test_execute_init(self):
        ''' verifies that execute_init created a skeleton framework of a role that complies with the galaxy metadata format '''
        # testing that an error is raised if no role name is given
        gc = GalaxyCLI(args=["init"])
        with patch('sys.argv', ["-c"]):
            galaxy_parser = gc.parse()
        self.assertRaises(AnsibleError, gc.execute_init)

        # This test requires internet connection. Using try/except to ensure internet is working rather than fail tests requiring internet while offline.
        try:
            # following tests use the role name 'delete_me'
            # testing for cases when the directory doesn't already exist
            gc = GalaxyCLI(args=["init"])
            if os.path.exists('./delete_me'):
                shutil.rmtree('./delete_me')
            with patch('sys.argv', ["-c", "-v", "delete_me"]):
                galaxy_parser = gc.parse()
            with patch.object(ansible.cli.CLI, "run", return_value=None): # to eliminate config or default file used message
                with patch.object(ansible.utils.display.Display, "display") as mock_display:  # used to test that it was called with the expected message
                    gc.run()
                    self.assertTrue(mock_display.called_once_with("- delete_me was created successfully"))

            # verifying that the expected framework was created
            self.assertTrue(os.path.exists('./delete_me'))
            self.assertTrue(os.path.isfile('./delete_me/README.md'))
            self.assertTrue(os.path.isdir('./delete_me/files'))
            self.assertTrue(os.path.isdir('./delete_me/templates'))
            self.assertTrue(os.path.isfile('./delete_me/handlers/main.yml'))
            self.assertTrue(os.path.isfile('./delete_me/tasks/main.yml'))
            self.assertTrue(os.path.isfile('./delete_me/vars/main.yml'))
            self.assertTrue(os.path.isfile('./delete_me/tests/inventory'))
            self.assertTrue(os.path.isfile('./delete_me/tests/test.yml'))
            self.assertTrue(os.path.isfile('./delete_me/meta/main.yml'))

            # testing for case when the directory and files are in existence already
            gc = GalaxyCLI(args=["init"])
            with patch('sys.argv', ["-c", "-v", "delete_me"]):
                galaxy_parser = gc.parse()
            with patch.object(ansible.cli.CLI, "run", return_value=None):
                self.assertRaises(AnsibleError, gc.run)

            # testing for case when the directory and files are in existence already while using the option: --force
            gc = GalaxyCLI(args=["init"])
            with patch('sys.argv', ["-c", "-v", "delete_me", "--force"]):
                galaxy_parser = gc.parse()
            with patch.object(ansible.cli.CLI, "run", return_value=None):  # to eliminate config or default file used message
                with patch.object(ansible.utils.display.Display, "display") as mock_display:  # used to test that it was called with the expected message
                    gc.run()
                    self.assertTrue(mock_display.called_once_with("- delete_me was created successfully"))

            # verifying that the files expected were created
            self.assertTrue(os.path.exists('./delete_me'))
            self.assertTrue(os.path.isfile('./delete_me/README.md'))
            self.assertTrue(os.path.isdir('./delete_me/files'))
            self.assertTrue(os.path.isdir('./delete_me/templates'))
            self.assertTrue(os.path.isfile('./delete_me/handlers/main.yml'))
            self.assertTrue(os.path.isfile('./delete_me/tasks/main.yml'))
            self.assertTrue(os.path.isfile('./delete_me/vars/main.yml'))
            self.assertTrue(os.path.isfile('./delete_me/tests/inventory'))
            self.assertTrue(os.path.isfile('./delete_me/tests/test.yml'))
            self.assertTrue(os.path.isfile('./delete_me/meta/main.yml'))

            # removing the files we created
            shutil.rmtree('./delete_me')

        except AnsibleError as e:
            if "Failed to get data from the API server" in e.message:
                raise SkipTest(' there is a test case within this method that requires an internet connection and a valid CA cert    ificate installed; this part of the method is skipped when one or both of these requirements are not provided\n ... ok')
            else:
                raise
=======
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
>>>>>>> Adding a test for GalaxyCLI and two methods on which it depends. Tes…  (#16651)
