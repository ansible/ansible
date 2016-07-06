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
import getpass

from mock import patch, MagicMock, call

from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.module_utils.urls import SSLValidationError
from urllib2 import HTTPError

if PY3:
    raise SkipTest('galaxy is not ported to be py3 compatible yet')

from ansible.cli.galaxy import GalaxyCLI

class TestGalaxy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # some of the tests require authentication from the tester
        # authentication may be declined, and tests inhibited will be skipped
        auth = getpass.getpass("\nWOULD YOU LIKE TO RUN TESTS REQUIRING GALAXY AUTHENTICATION?\nPROVIDING INVALID CREDENTIALS WILL RESULT IN FAILED TESTS.\n (y/n): ")
        if auth.lower() == "y" or auth.lower() == "yes":
            try:
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
        if display_result.find('\n\tgalaxy_info:') == -1:
            self.fail('Expected galaxy_info to be indented once')

    def test_parse(self):
        ''' tests that an options parser is created for bin/ansible; entails creating SortedOptParser instance and Galaxy instance '''
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

    def test_run(self):
        ''' verifies that the GalaxyCLI object's api is created and that execute() is called. '''
        gc = GalaxyCLI(args=["install"])
        with patch('sys.argv', ["-c", "-v", '--ignore-errors', 'imaginary_role']):
            galaxy_parser = gc.parse()
        gc.execute = MagicMock()
        with patch.object(ansible.cli.CLI, "run", return_value=None) as mock_obj:  # to eliminate config or default file used m    essage
            gc.run()
        self.assertTrue(gc.execute.called)
        self.assertTrue(isinstance(gc.api, ansible.galaxy.api.GalaxyAPI))

    def test_exit_without_ignore(self):
        ''' tests that GalaxyCLI exits with the error specified'''
        gc = GalaxyCLI(args=["install"])

        # testing without --ignore-errors flag
        with patch('sys.argv', ["-c", "fake_role_name"]):
            galaxy_parser = gc.parse()
        with patch.object(ansible.utils.display.Display, "display", return_value=None) as mocked_display:
            # testing that error expected is raised
            self.assertRaises(AnsibleError, gc.run)
            self.assertTrue(mocked_display.called_once_with("- downloading role 'fake_role_name', owned by "))
        
        # testing with --ignore-errors flag
        with patch('sys.argv', ["-c", "fake_role_name", "--ignore-errors"]):
            galalxy_parser = gc.parse()
        with patch.object(ansible.utils.display.Display, "display", return_value=None) as mocked_display:
            # testing that error expected is not raised with --ignore-errors flag in use
            gc.run()
            self.assertTrue(mocked_display.called_once_with("- downloading role 'fake_role_name', owned by "))

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
                with patch.object(ansible.utils.display.Display, "display") as mock_obj:  # eliminates display message for user
                    gc.run()
                    self.assertTrue(mock_obj.called_once_with("- delete_me was created successfully"))

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
                with patch.object(ansible.utils.display.Display, "display") as mock_obj:  # eliminates display message for user
                    gc.run()
                    self.assertTrue(mock_obj.called_once_with("- delete_me was created successfully"))

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

        except (SSLValidationError, AnsibleError) as e:
            if "Failed to get data from the API server" or "Failed to validate the SSL certificate" in e.message:
                raise SkipTest('this test requires an internet connection')
            else:
                raise

    def make_tarfile(self, output_file, source_dir):
        ''' used for making a tarfile from an artificial role directory for testing installation with a local tar.gz file '''
        # adding directory into a tar file
        with tarfile.open(output_file, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))

    def create_role(self):
        ''' creates a "role" directory and a requirements file; used for testing installation '''
        if os.path.exists('./delete_me'):
            shutil.rmtree('./delete_me')

        # making the directory for the role
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
        fd.write("- 'src': './delete_me.tar.gz'\n  'name': 'delete_me'\n  'path': '/etc/ansible/roles'")
        fd.close()

    def test_execute_info(self):
        ''' testing that execute_info displays information associated with a role '''
        ### testing cases when no role name is given ###

        gc = GalaxyCLI(args=["info"])
        with patch('sys.argv', ["-c", "-v"]):
            galaxy_parser = gc.parse()
        with patch.object(ansible.utils.display.Display, "display"):
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

            # data used for testing
            gr = ansible.galaxy.role.GalaxyRole(gc.galaxy, "delete_me")
            install_date = gr.install_info['install_date']

            # testing role for info
        gc.args = ["info"]
        with patch('sys.argv', ["-c", "--offline", "delete_me"]):
            galaxy_parser = gc.parse()
        with patch.object(ansible.cli.CLI, "pager") as mock_obj:
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

        ### testing case when the name of a role not installed is given ###

            # the role "delete_me" is not installed now
        gc = GalaxyCLI(args=["info"])
        with patch('sys.argv', ["-c", "--offline", "delete_me"]):
            galaxy_parser = gc.parse()

            # this won't pass until GalaxyCLI.execute_info's FIXME is fixed
        with patch.object(ansible.cli.CLI, "pager") as mock_obj:
            gc.run()
            #mock_obj.assert_called_once_with(u'\n- the role delete_me was not found') # FIXME: Uncomment

    def test_execute_install(self):
        ### testing insufficient information; no role name ###
        gc = GalaxyCLI(args=["install"])
        with patch('sys.argv', ["-c", "-v"]):
            galaxy_parser = gc.parse()
        with patch.object(ansible.cli.CLI, "run"):  # eliminate config file message
            self.assertRaises(AnsibleError, gc.run)

        ### tests installing a role with a local tar file ###
        # creating a tar.gz file for a fake role
        self.create_role()

        # installing role (also, removes tar.gz file)
        gc = GalaxyCLI(args=["install"])
        with patch('sys.argv', ["--offline", "-r", "delete_requirements.yml"]):
            galaxy_parser = gc.parse()
        with patch.object(ansible.utils.display.Display, "display") as mock_obj:
            super(GalaxyCLI, gc).run()
            gc.api = ansible.galaxy.api.GalaxyAPI(gc.galaxy)
            completed_task = gc.execute_install()

            # testing correct installation
            calls = [call('- extracting delete_me to /etc/ansible/roles/delete_me'), call('- delete_me was installed successfully')]
            mock_obj.assert_has_calls(calls)
            self.assertTrue(completed_task == 0)

        # deleting role
        gc.args = ["remove"]
        with patch('sys.argv', ["-c", "delete_me"]):
            galaxy_parser = gc.parse()
        with patch.object(ansible.utils.display.Display, "display") as mock_obj:
            gc.run()

        # cleaning up requirements file
        if os.path.isfile("delete_requirements.yml"):
            os.remove("delete_requirements.yml")

        ### tests downloading a role from ansible-galaxy ###
        # TODO/FIXME

    def test_execute_remove(self):
        ### setup; creating a tar.gz file and installing the role ###

        # creating a tar.gz file for a fake role
        self.create_role()

        # installing role (also, removes tar.gz file)
        gc = GalaxyCLI(args=["install"])
        with patch('sys.argv', ["--offline", "-r", "delete_requirements.yml"]):
            galaxy_parser = gc.parse()
        with patch.object(ansible.utils.display.Display, "display") as mock_obj:
            gc.run()

        ### testing removing the role ###
        
        gc.args = ["remove"]
        with patch('sys.argv', ["-c", "delete_me"]):
            galaxy_parser = gc.parse()
        with patch.object(ansible.utils.display.Display, "display") as mock_obj:
            super(GalaxyCLI, gc).run()
            gc.api = ansible.galaxy.api.GalaxyAPI(gc.galaxy)
            completed_task = gc.execute_remove()
            mock_obj.assert_called_once_with("- successfully removed delete_me")
            self.assertTrue(completed_task == 0)

        # cleaning up requirements file
        if os.path.isfile("delete_requirements.yml"):
            os.remove("delete_requirements.yml")

    def test_execute_list(self):
        ### testing with multiple role names given ###
         gc = GalaxyCLI(args=["list"])
         with patch('sys.argv', ["-c", "role_name_one", "role_name_two"]):
             galaxy_parser = gc.parse()
         self.assertRaises(AnsibleError, gc.run)

         ### testing with a given role name ###
             # set up
         self.create_role()

             # installing role (also, removes tar.gz file)
         gc = GalaxyCLI(args=["install"])
         with patch('sys.argv', ["--offline", "-r", "delete_requirements.yml"]):
             galaxy_parser = gc.parse()
         with patch.object(ansible.utils.display.Display, "display"):
             gc.run()

             # testing
         gc.args = ["list"]
         with patch('sys.argv', ["-c", "delete_me"]):
             galaxy_parser = gc.parse()
         with patch.object(ansible.utils.display.Display, "display") as mock_obj:
             gc.run()
             mock_obj.assert_called_once_with("- delete_me, (unknown version)")

             # cleaning up
         gc.args = ["remove"]
         with patch('sys.argv', ["-c", "delete_me"]):
             galaxy_parser = gc.parse()
         with patch.object(ansible.utils.display.Display, "display") as mock_obj:
             gc.run()
             mock_obj.assert_called_once_with("- successfully removed delete_me")
         if os.path.isfile("delete_requirements.yml"):
             os.remove("delete_requirements.yml")

         ### testing with no role names specified ###
             gc.args = ["list"]
             with patch('sys.argv', ["-c"]):
                 galaxy_parser = gc.parse()
             with patch.object(ansible.utils.display.Display, "display") as mock_obj:
                 super(GalaxyCLI, gc).run()
                 gc.api = ansible.galaxy.api.GalaxyAPI(gc.galaxy)
                 completed_task = gc.execute_list()
                 self.assertTrue(completed_task == 0)
                 self.assertTrue(mock_obj.called)

    def test_execute_search(self):
        # This test requires internet connection. Using try/except to ensure internet is working rather than fail tests requiring connection while offline.
        try:
            gc = GalaxyCLI(args=["search"])

            ### testing isufficient search query ###
            with patch('sys.argv', ["-c"]):
                galaxy_parser = gc.parse()
                self.assertRaises(AnsibleError, gc.run)

            ### testing sufficient search ###
                # searching for 'role' keyword
            with patch('sys.argv', ["-c", "role"]):
                galaxy_parser = gc.parse()
            with patch.object(ansible.cli.CLI, "pager"):  # eliminating display output
                super(GalaxyCLI, gc).run()
                gc.api = ansible.galaxy.api.GalaxyAPI(gc.galaxy)
                completed_task = gc.execute_search()
                self.assertTrue(completed_task == True)

        except (SSLValidationError, AnsibleError) as e:
            if "Failed to get data from the API server" or "Failed to validate the SSL certificate" in e.message:
                raise SkipTest('this test requires an internet connection')
            else:
                raise

    @patch.object(ansible.utils.display.Display, "display")  # eliminating messages flushed to screen
    def test_execute_login(self, mocked_display):

        # This test requires internet connection. Using try/except to ensure internet is working rather than fail tests requiring connection while offline.
        try:

            if self.auth:  # need authentication for these tests

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
            elif "Failed to get data from the API server" or "Failed to validate the SSL certificate" in e.message:
                raise SkipTest('this test requires an internet connection')
            else:
                raise
     
    @patch.object(ansible.utils.display.Display, "display")  # eliminating messages flushed to screen
    def test_execute_import(self, mocked_display):
        # This test requires internet connection. Using try/except to ensure internet is working rather than fail tests requiring connection while offline.
        try:
            # import tests require credentials
            if self.auth:
                logged_in = False

                ### setting up - trying to login; required to test import ###
                gc = GalaxyCLI(args=["login"])
                if self.galaxy_username and self.galaxy_password:
                    with patch('sys.argv', ["-c", self.galaxy_username, self.galaxy_password]):
                        galaxy_parser = gc.parse()
                    # patching because we only ask once for authentication
                    with patch('__builtin__.raw_input', return_value= self.galaxy_username):
                        with patch('getpass.getpass', return_value=self.galaxy_password):
                            gc.run()
                            logged_in = True
                elif self.github_token:
                    with patch('sys.argv', ["-c", "--github-token", self.github_token]):
                        galaxy_parser = gc.parse()
                    gc.run()
                    logged_in = True

                ### running tests if setup was successful ###
                if logged_in:

                    # testing when correct arguments are not provided
                    gc.args = ["import"]
                    with patch('sys.argv', ["-c"]):
                        galaxy_parser = gc.parse()
                    self.assertRaises(AnsibleError, gc.run)

                    # testing with correct arguments if possible
                    if self.galaxy_username and self.import_repo:  # tests fail if invalid credentials are provided by the tester

                        # testing when gc.options.check_status == False and gc.options.wait == True
                        gc.args = ["import"]
                        with patch('sys.argv', ["-c", self.galaxy_username, self.import_repo]):
                            galaxy_parser = gc.parse()
                        super(GalaxyCLI, gc).run()
                        gc.api = ansible.galaxy.api.GalaxyAPI(gc.galaxy)
                        completed = gc.execute_import()
                        self.assertTrue(completed==0)
    
                        # testing when gc.options.check_status == False and gc.options.wait == False
                        gc.args = ["import"]
                        with patch('sys.argv', ["-c", self.galaxy_username, self.import_repo]):
                            galaxy_parser = gc.parse()
                        gc.options.wait = False
                        super(GalaxyCLI, gc).run()
                        gc.api = ansible.galaxy.api.GalaxyAPI(gc.galaxy)
                        completed = gc.execute_import()
                        self.assertTrue(completed==0)

                        # testing when gc.options.check_status == True
                        gc.args = ["import"]
                        with patch('sys.argv', ["-c", self.galaxy_username, self.import_repo]):
                            galaxy_parser = gc.parse()
                        gc.options.check_status = True
                        super(GalaxyCLI, gc).run()
                        gc.api = ansible.galaxy.api.GalaxyAPI(gc.galaxy)
                        completed = gc.execute_import()
                        self.assertTrue(completed==0)

        except (SSLValidationError, AnsibleError) as e:
            if str(e) == "Bad credentials":
                raise
            elif "Failed to get data from the API server" or "Failed to validate the SSL certificate" in e.message:
                raise SkipTest('this test requires an internet connection')
            else:
                raise

