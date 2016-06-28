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

from ansible.galaxy.token import GalaxyToken
from ansible.cli import CLI
from mock import patch, MagicMock, call
from ansible.errors import AnsibleError, AnsibleOptionsError
import ansible
import os
import shutil
import tarfile

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
        if display_result.find('\n\tgalaxy_info:') == -1:
            self.fail('Expected galaxy_info to be indented once')

    @patch.object(GalaxyToken, "__init__", return_value=None)  # mocks file being opened/created
    def test_parse(self, mocked_token):
        ''' tests that an options parser is created for bin/ansible '''
        for arguments in [[], ["list", "info"], ["bad_arg", "list"], ["bad_arg", "invalid"]]:
            gc = GalaxyCLI(args=arguments)
            first_arg = False
            for arg in arguments:
                if arg in gc.VALID_ACTIONS:
                    first_arg = arg  # used for testing after a parser is created
                    break  # stop after a valid action is identified
            if first_arg == False:  # checking right error is raised
                with patch('sys.argv', ["-c"]):
                    self.assertRaises(AnsibleOptionsError, gc.parse)
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

    @patch.object(GalaxyToken, "__init__", return_value=None)  # mocks file being opened/created
    def test_run(self, mocked_token):
        ''' verifies that the GalaxyCLI object's api is created and that execute() is called. '''
        gc = GalaxyCLI(args=["install"])
        with patch('sys.argv', ["-c", "-v", '--ignore-errors', 'imaginary_role']):
            galaxy_parser = gc.parse()
        gc.execute = MagicMock()
        with patch.object(CLI, "run", return_value=None) as mock_obj:  # to eliminate config or default file used message
            gc.run()
        self.assertTrue(gc.execute.called)
        self.assertTrue(isinstance(gc.api, ansible.galaxy.api.GalaxyAPI))

    @patch.object(GalaxyToken, "__init__", return_value=None)  # mocks file being opened/created
    def test_exit_without_ignore(self, mocked_toekn):
        ''' tests that GalaxyCLI exits with the error specified'''
        gc = GalaxyCLI(args=["install"])
        with patch('sys.argv', ["-c", "-v"]):
            galaxy_parser = gc.parse()
        with patch.object(CLI, "run", return_value=None) as mock_obj:  # to eliminate config or default file used message
            self.assertRaises(AnsibleError, gc.run)

    def test_execute_init(self):
        ''' verifies that execute_init created a skeleton framework of a role that complies with the galaxy metadata format '''
        # testing that an error is raised if no role name is given
        gc = GalaxyCLI(args=self.default_args)
        self.assertRaises(AnsibleError, gc.execute_init)

        # following tests use the role name 'delete_me'
        # testing for cases when the directory doesn't already exist
        gc = GalaxyCLI(args=["init"])
        if os.path.exists('./delete_me'):
            shutil.rmtree('./delete_me')
        with patch('sys.argv', ["-c", "-v", "delete_me"]):
            galaxy_parser = gc.parse()
            with patch.object(CLI, "run", return_value=None): # to eliminate config or default file used message
                with patch.object(ansible.utils.display.Display, "display"):  # eliminates display message for user
                    gc.run()
        
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
            with patch.object(CLI, "run", return_value=None):
                self.assertRaises(AnsibleError, gc.run)
        
        # testing for case when the directory and files are in existence already while using the option: --force
        gc = GalaxyCLI(args=["init"])
        with patch('sys.argv', ["-c", "-v", "delete_me", "--force"]):
            galaxy_parser = gc.parse()
            with patch.object(CLI, "run", return_value=None):  # to eliminate config or default file used message
                with patch.object(ansible.utils.display.Display, "display"):  # eliminates display message for user
                    gc.run()

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

    
    def make_tarfile(self, output_file, source_dir):
        # adding directory into a tar file
        with tarfile.open(output_file, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))
    

    def create_role(self):
        ''' writes a "role" tar.gz directory and a requirements file '''
        if os.path.exists('./delete_me'):
            shutil.rmtree('./delete_me')

        # making the directory for the role
        #os.makedirs('./delete_role')
        os.makedirs('./delete_me')
        os.makedirs('./delete_me/meta')
        
        # making main.yml for meta folder
        fd = open("./delete_me/meta/main.yml", "w")
        fd.write("---\ngalaxy_info:\n  author: 'shertel'\n  company: Ansible\ndependencies: []")
        fd.close()
        
        # making the directory into a tar file
        self.make_tarfile('./delete_me.tar.gz', './delete_me')

        # removing directory
        shutil.rmtree('./delete_me')
        
        # creating requirements.yml for installing the role
        fd = open("./delete_requirements.yml", "w")
        #fd.write("- src: ./delete_me.tar.gz\n  name: delete_me\n  path: /etc/ansible/roles")
        fd.write("- 'src': './delete_me.tar.gz'\n  'name': 'delete_me'\n  'path': '/etc/ansible/roles'")
        fd.close()


    def test_execute_info(self):

        ### testing cases when no role name is given ###
        gc = GalaxyCLI(args=["info"])
        with patch('sys.argv', ["-c", "-v"]):
            galaxy_parser = gc.parse()
            with patch.object(ansible.cli.CLI, "run"):  # eliminate config file message
                self.assertRaises(AnsibleError, gc.run)                

        ### testing case when valid role name is given ###

            # creating a tar.gz file for a fake role
        self.create_role()
        
            # installing role (also, removes tar.gz file)
        gc = GalaxyCLI(args=["install"])
        with patch('sys.argv', ["--offline", "-r", "delete_requirements.yml"]):
            galaxy_parser = gc.parse()
            with patch.object(ansible.utils.display.Display, "display") as mock_obj:
                gc.run()

                # testing correct installation
                calls = [call('- extracting delete_me to /etc/ansible/roles/delete_me'), call('- delete_me was installed successfully')]
                mock_obj.assert_has_calls(calls)

            # data used for testing
            gr = ansible.galaxy.role.GalaxyRole(gc.galaxy, "delete_me")
            install_date = gr.install_info['install_date']

            # testing role for info
        gc.args = ["info"]
        with patch('sys.argv', ["-c", "--offline", "delete_me"]):
            galaxy_parser = gc.parse()
            with patch.object(CLI, "pager") as mock_obj:
                gc.run()
                mock_obj.assert_called_once_with(u"\nRole: delete_me\n\tdescription: \n\tdependencies: []\n\tgalaxy_info:\n\t\tauthor: shertel\n\t\tcompany: Ansible\n\tinstall_date: %s\n\tintalled_version: \n\tpath: [\'/etc/ansible/roles\']\n\tscm: None\n\tsrc: delete_me\n\tversion: " % install_date)                

            # deleting role
        gc.args = ["remove"]
        with patch('sys.argv', ["-c", "delete_me"]):
            galaxy_parser = gc.parse()
            with patch.object(ansible.utils.display.Display, "display") as mock_obj:
                gc.run()
                
                # testing clean up worked
                mock_obj.assert_called_once_with("- successfully removed delete_me")

            # cleaning up requirements file
            if os.path.isfile("delete_requirements.yml"):
                os.remove("delete_requirements.yml")

        ### testing case when an uninstalled role name is given ###
        
            # the role "delete_me" is not installed
        gc = GalaxyCLI(args=["info"])
        with patch('sys.argv', ["-c", "--offline", "delete_me"]):
            galaxy_parser = gc.parse()
        
            # this won't work until GalaxyCLI.execute_info's FIXME is fixed
        with patch.object(CLI, "pager") as mock_obj:
            gc.run()
            #mock_obj.assert_called_once_with(u'\n- the role delete_me was not found')
        

    def test_execute_install(self):
        pass
        
