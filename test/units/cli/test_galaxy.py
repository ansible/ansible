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

import os
import shutil
import tarfile
import tempfile

from ansible.compat.six import PY3
from ansible.compat.tests import unittest
from ansible.compat.tests.mock import call, patch

import ansible
from ansible.errors import AnsibleError, AnsibleOptionsError

from ansible.cli.galaxy import GalaxyCLI


class TestGalaxy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        '''creating prerequisites for installing a role; setUpClass occurs ONCE whereas setUp occurs with every method tested.'''
        # class data for easy viewing: role_dir, role_tar, role_name, role_req, role_path

        if os.path.exists("./delete_me"):
            shutil.rmtree("./delete_me")

        # creating framework for a role
        gc = GalaxyCLI(args=["init", "-c", "--offline", "delete_me"])
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
        if display_result.find('\n\tgalaxy_info:') == -1:
            self.fail('Expected galaxy_info to be indented once')

    def test_run(self):
        ''' verifies that the GalaxyCLI object's api is created and that execute() is called. '''
        gc = GalaxyCLI(args=["install"])
        with patch('sys.argv', ["-c", "-v", '--ignore-errors', 'imaginary_role']):
            galaxy_parser = gc.parse()
        with patch.object(ansible.cli.CLI, "execute", return_value=None) as mock_ex:
            with patch.object(ansible.cli.CLI, "run", return_value=None) as mock_run:
                gc.run()
                
                # testing
                self.assertEqual(mock_run.call_count, 1)
                self.assertTrue(isinstance(gc.api, ansible.galaxy.api.GalaxyAPI))
                self.assertEqual(mock_ex.call_count, 1)

    def test_execute_remove(self):
        # installing role
        gc = GalaxyCLI(args=["install", "--offline", "-p", self.role_path, "-r", self.role_req])
        galaxy_parser = gc.parse()
        gc.run()

        # checking that installation worked
        role_file = os.path.join(self.role_path, self.role_name)
        self.assertTrue(os.path.exists(role_file))

        # removing role
        gc = GalaxyCLI(args=["remove", "-c", "-p", self.role_path, self.role_name])
        galaxy_parser = gc.parse()
        super(GalaxyCLI, gc).run()
        gc.api = ansible.galaxy.api.GalaxyAPI(gc.galaxy)
        completed_task = gc.execute_remove()

        # testing role was removed
        self.assertTrue(completed_task == 0)
        self.assertTrue(not os.path.exists(role_file))

    def test_exit_without_ignore(self):
        ''' tests that GalaxyCLI exits with the error specified unless the --ignore-errors flag is used '''
        gc = GalaxyCLI(args=["install", "--server=None", "-c", "fake_role_name"])

        # testing without --ignore-errors flag
        galaxy_parser = gc.parse()
        with patch.object(ansible.utils.display.Display, "display", return_value=None) as mocked_display:
            # testing that error expected is raised
            self.assertRaises(AnsibleError, gc.run)
            self.assertTrue(mocked_display.called_once_with("- downloading role 'fake_role_name', owned by "))

        # testing with --ignore-errors flag
        gc = GalaxyCLI(args=["install", "--server=None", "-c", "fake_role_name", "--ignore-errors"])
        galalxy_parser = gc.parse()
        with patch.object(ansible.utils.display.Display, "display", return_value=None) as mocked_display:
            # testing that error expected is not raised with --ignore-errors flag in use
            gc.run()
            self.assertTrue(mocked_display.called_once_with("- downloading role 'fake_role_name', owned by "))

    def run_parse_common(self, galaxycli_obj, action):
        with patch.object(ansible.cli.SortedOptParser, "set_usage") as mocked_usage:
            galaxycli_obj.parse()

            # checking that the common results of parse() for all possible actions have been created/called
            self.assertIsInstance(galaxycli_obj.parser, ansible.cli.SortedOptParser)
            self.assertIsInstance(galaxycli_obj.galaxy, ansible.galaxy.Galaxy)
            if action in ['import', 'delete']:
                formatted_call = 'usage: %prog ' + action + ' [options] github_user github_repo'
            elif action == 'info':
                formatted_call = 'usage: %prog ' + action + ' [options] role_name[,version]'
            elif action == 'init':
                formatted_call = 'usage: %prog ' + action + ' [options] role_name'
            elif action == 'install':
                formatted_call = 'usage: %prog ' + action + ' [options] [-r FILE | role_name(s)[,version] | scm+role_repo_url[,version] | tar_file(s)]'
            elif action == 'list':
                formatted_call = 'usage: %prog ' + action + ' [role_name]'
            elif action == 'login':
                formatted_call = 'usage: %prog ' + action + ' [options]'
            elif action == 'remove':
                formatted_call = 'usage: %prog ' + action + ' role1 role2 ...'
            elif action == 'search':
                formatted_call = 'usage: %prog ' + action + ' [searchterm1 searchterm2] [--galaxy-tags galaxy_tag1,galaxy_tag2] [--platforms platform1,platform2] [--author username]'
            elif action == 'setup':
                formatted_call = 'usage: %prog ' + action + ' [options] source github_user github_repo secret'
            calls = [call('usage: %prog [delete|import|info|init|install|list|login|remove|search|setup] [--help] [options] ...'), call(formatted_call)]
            mocked_usage.assert_has_calls(calls)

    def test_parse(self):
        ''' systematically testing that the expected options parser is created '''
        # testing no action given
        gc = GalaxyCLI(args=["-c"])
        self.assertRaises(AnsibleOptionsError, gc.parse)

        # testing action that doesn't exist
        gc = GalaxyCLI(args=["NOT_ACTION", "-c"])
        self.assertRaises(AnsibleOptionsError, gc.parse)

        # testing action 'delete'
        gc = GalaxyCLI(args=["delete", "-c"])
        self.run_parse_common(gc, "delete")
        self.assertEqual(gc.options.verbosity, 0)

        # testing action 'import'
        gc = GalaxyCLI(args=["import", "-c"])
        self.run_parse_common(gc, "import")
        self.assertEqual(gc.options.wait, True)
        self.assertEqual(gc.options.reference, None)
        self.assertEqual(gc.options.check_status, False)
        self.assertEqual(gc.options.verbosity, 0)

        # testing action 'info'
        gc = GalaxyCLI(args=["info", "-c"])
        self.run_parse_common(gc, "info")
        self.assertEqual(gc.options.offline, False)

        # testing action 'init'
        gc = GalaxyCLI(args=["init", "-c"])
        self.run_parse_common(gc, "init")
        self.assertEqual(gc.options.offline, False)
        self.assertEqual(gc.options.force, False)

        # testing action 'install'
        gc = GalaxyCLI(args=["install", "-c"])
        self.run_parse_common(gc, "install")
        self.assertEqual(gc.options.ignore_errors, False)
        self.assertEqual(gc.options.no_deps, False)
        self.assertEqual(gc.options.role_file, None)
        self.assertEqual(gc.options.force, False)

        # testing action 'list'
        gc = GalaxyCLI(args=["list", "-c"])
        self.run_parse_common(gc, "list")
        self.assertEqual(gc.options.verbosity, 0)

        # testing action 'login'
        gc = GalaxyCLI(args=["login", "-c"])
        self.run_parse_common(gc, "login")
        self.assertEqual(gc.options.verbosity, 0)
        self.assertEqual(gc.options.token, None)

        # testing action 'remove'
        gc = GalaxyCLI(args=["remove", "-c"])
        self.run_parse_common(gc, "remove")
        self.assertEqual(gc.options.verbosity, 0)

        # testing action 'search'
        gc = GalaxyCLI(args=["search", "-c"])
        self.run_parse_common(gc, "search")
        self.assertEqual(gc.options.platforms, None)
        self.assertEqual(gc.options.galaxy_tags, None)
        self.assertEqual(gc.options.author, None)

        # testing action 'setup'
        gc = GalaxyCLI(args=["setup", "-c"])
        self.run_parse_common(gc, "setup")
        self.assertEqual(gc.options.verbosity, 0)
        self.assertEqual(gc.options.remove_id, None)
        self.assertEqual(gc.options.setup_list, False)
