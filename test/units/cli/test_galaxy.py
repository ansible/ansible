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

import ansible
import os
import shutil
import tarfile
import tempfile
import yaml

from ansible.cli.galaxy import GalaxyCLI
from ansible.compat.tests import unittest
from ansible.compat.tests.mock import call, patch
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.module_utils.six import PY3


class TestGalaxy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        '''creating prerequisites for installing a role; setUpClass occurs ONCE whereas setUp occurs with every method tested.'''
        # class data for easy viewing: role_dir, role_tar, role_name, role_req, role_path

        if os.path.exists("./delete_me"):
            shutil.rmtree("./delete_me")

        # creating framework for a role
        gc = GalaxyCLI(args=["ansible-galaxy", "init", "--offline", "delete_me"])
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
        except AttributeError:  # tarfile obj. has no attribute __exit__ prior to python 2.    7
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
        self.default_args = ['ansible-galaxy']

    def test_init(self):
        galaxy_cli = GalaxyCLI(args=self.default_args)
        self.assertTrue(isinstance(galaxy_cli, GalaxyCLI))

    def test_display_min(self):
        gc = GalaxyCLI(args=self.default_args)
        role_info = {'name': 'some_role_name'}
        display_result = gc._display_role_info(role_info)
        self.assertTrue(display_result.find('some_role_name') > -1)

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
        gc = GalaxyCLI(args=["ansible-galaxy", "install", "--ignore-errors", "imaginary_role"])
        gc.parse()
        with patch.object(ansible.cli.CLI, "execute", return_value=None) as mock_ex:
            with patch.object(ansible.cli.CLI, "run", return_value=None) as mock_run:
                gc.run()

                # testing
                self.assertEqual(mock_run.call_count, 1)
                self.assertTrue(isinstance(gc.api, ansible.galaxy.api.GalaxyAPI))
                self.assertEqual(mock_ex.call_count, 1)

    def test_execute_remove(self):
        # installing role
        gc = GalaxyCLI(args=["ansible-galaxy", "install", "-p", self.role_path, "-r", self.role_req, '--force'])
        gc.parse()
        gc.run()

        # location where the role was installed
        role_file = os.path.join(self.role_path, self.role_name)

        # removing role
        gc = GalaxyCLI(args=["ansible-galaxy", "remove", role_file, self.role_name])
        gc.parse()
        gc.run()

        # testing role was removed
        removed_role = not os.path.exists(role_file)
        self.assertTrue(removed_role)

    def test_exit_without_ignore_without_flag(self):
        ''' tests that GalaxyCLI exits with the error specified if the --ignore-errors flag is not used '''
        gc = GalaxyCLI(args=["ansible-galaxy", "install", "--server=None", "fake_role_name"])
        gc.parse()
        with patch.object(ansible.utils.display.Display, "display", return_value=None) as mocked_display:
            # testing that error expected is raised
            self.assertRaises(AnsibleError, gc.run)
            self.assertTrue(mocked_display.called_once_with("- downloading role 'fake_role_name', owned by "))

    def test_exit_without_ignore_with_flag(self):
        ''' tests that GalaxyCLI exits without the error specified if the --ignore-errors flag is used  '''
        # testing with --ignore-errors flag
        gc = GalaxyCLI(args=["ansible-galaxy", "install", "--server=None", "fake_role_name", "--ignore-errors"])
        gc.parse()
        with patch.object(ansible.utils.display.Display, "display", return_value=None) as mocked_display:
            gc.run()
            self.assertTrue(mocked_display.called_once_with("- downloading role 'fake_role_name', owned by "))

    def run_parse_common(self, galaxycli_obj, action):
        with patch.object(ansible.cli.SortedOptParser, "set_usage") as mocked_usage:
            galaxycli_obj.parse()

            # checking that the common results of parse() for all possible actions have been created/called
            self.assertIsInstance(galaxycli_obj.parser, ansible.cli.SortedOptParser)
            self.assertIsInstance(galaxycli_obj.galaxy, ansible.galaxy.Galaxy)
            formatted_call = {
                'import': 'usage: %prog import [options] github_user github_repo',
                'delete': 'usage: %prog delete [options] github_user github_repo',
                'info': 'usage: %prog info [options] role_name[,version]',
                'init': 'usage: %prog init [options] role_name',
                'install': 'usage: %prog install [options] [-r FILE | role_name(s)[,version] | scm+role_repo_url[,version] | tar_file(s)]',
                'list': 'usage: %prog list [role_name]',
                'login': 'usage: %prog login [options]',
                'remove': 'usage: %prog remove role1 role2 ...',
                'search': ('usage: %prog search [searchterm1 searchterm2] [--galaxy-tags galaxy_tag1,galaxy_tag2] [--platforms platform1,platform2] '
                           '[--author username]'),
                'setup': 'usage: %prog setup [options] source github_user github_repo secret',
            }

            first_call = 'usage: %prog [delete|import|info|init|install|list|login|remove|search|setup] [--help] [options] ...'
            second_call = formatted_call[action]
            calls = [call(first_call), call(second_call)]
            mocked_usage.assert_has_calls(calls)

    def test_parse_no_action(self):
        ''' testing the options parser when no action is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", ""])
        self.assertRaises(AnsibleOptionsError, gc.parse)

    def test_parse_invalid_action(self):
        ''' testing the options parser when an invalid action is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "NOT_ACTION"])
        self.assertRaises(AnsibleOptionsError, gc.parse)

    def test_parse_delete(self):
        ''' testing the options parser when the action 'delete' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "delete"])
        self.run_parse_common(gc, "delete")
        self.assertEqual(gc.options.verbosity, 0)

    def test_parse_import(self):
        ''' testing the options parser when the action 'import' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "import"])
        self.run_parse_common(gc, "import")
        self.assertEqual(gc.options.wait, True)
        self.assertEqual(gc.options.reference, None)
        self.assertEqual(gc.options.check_status, False)
        self.assertEqual(gc.options.verbosity, 0)

    def test_parse_info(self):
        ''' testing the options parser when the action 'info' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "info"])
        self.run_parse_common(gc, "info")
        self.assertEqual(gc.options.offline, False)

    def test_parse_init(self):
        ''' testing the options parser when the action 'init' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "init"])
        self.run_parse_common(gc, "init")
        self.assertEqual(gc.options.offline, False)
        self.assertEqual(gc.options.force, False)

    def test_parse_install(self):
        ''' testing the options parser when the action 'install' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "install"])
        self.run_parse_common(gc, "install")
        self.assertEqual(gc.options.ignore_errors, False)
        self.assertEqual(gc.options.no_deps, False)
        self.assertEqual(gc.options.role_file, None)
        self.assertEqual(gc.options.force, False)

    def test_parse_list(self):
        ''' testing the options parser when the action 'list' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "list"])
        self.run_parse_common(gc, "list")
        self.assertEqual(gc.options.verbosity, 0)

    def test_parse_login(self):
        ''' testing the options parser when the action 'login' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "login"])
        self.run_parse_common(gc, "login")
        self.assertEqual(gc.options.verbosity, 0)
        self.assertEqual(gc.options.token, None)

    def test_parse_remove(self):
        ''' testing the options parser when the action 'remove' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "remove"])
        self.run_parse_common(gc, "remove")
        self.assertEqual(gc.options.verbosity, 0)

    def test_parse_search(self):
        ''' testing the options parswer when the action 'search' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "search"])
        self.run_parse_common(gc, "search")
        self.assertEqual(gc.options.platforms, None)
        self.assertEqual(gc.options.galaxy_tags, None)
        self.assertEqual(gc.options.author, None)

    def test_parse_setup(self):
        ''' testing the options parser when the action 'setup' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "setup"])
        self.run_parse_common(gc, "setup")

        self.assertEqual(gc.options.verbosity, 0)
        self.assertEqual(gc.options.remove_id, None)
        self.assertEqual(gc.options.setup_list, False)


class ValidRoleTests(object):

    expected_role_dirs = ('defaults', 'files', 'handlers', 'meta', 'tasks', 'templates', 'vars', 'tests')

    @classmethod
    def setUpRole(cls, role_name, galaxy_args=None, skeleton_path=None):
        if galaxy_args is None:
            galaxy_args = []

        if skeleton_path is not None:
            cls.role_skeleton_path = skeleton_path
            galaxy_args += ['--role-skeleton', skeleton_path]

        # Make temp directory for testing
        cls.test_dir = tempfile.mkdtemp()
        if not os.path.isdir(cls.test_dir):
            os.makedirs(cls.test_dir)

        cls.role_dir = os.path.join(cls.test_dir, role_name)
        cls.role_name = role_name

        # create role using default skeleton
        gc = GalaxyCLI(args=['ansible-galaxy', 'init', '-c', '--offline'] + galaxy_args + ['--init-path', cls.test_dir, cls.role_name])
        gc.parse()
        gc.run()
        cls.gc = gc

        if skeleton_path is None:
            cls.role_skeleton_path = gc.galaxy.default_role_skeleton_path

    @classmethod
    def tearDownClass(cls):
        if os.path.isdir(cls.test_dir):
            shutil.rmtree(cls.test_dir)

    def test_metadata(self):
        with open(os.path.join(self.role_dir, 'meta', 'main.yml'), 'r') as mf:
            metadata = yaml.safe_load(mf)
        self.assertIn('galaxy_info', metadata, msg='unable to find galaxy_info in metadata')
        self.assertIn('dependencies', metadata, msg='unable to find dependencies in metadata')

    def test_readme(self):
        readme_path = os.path.join(self.role_dir, 'README.md')
        self.assertTrue(os.path.exists(readme_path), msg='Readme doesn\'t exist')

    def test_main_ymls(self):
        need_main_ymls = set(self.expected_role_dirs) - set(['meta', 'tests', 'files', 'templates'])
        for d in need_main_ymls:
            main_yml = os.path.join(self.role_dir, d, 'main.yml')
            self.assertTrue(os.path.exists(main_yml))
            expected_string = "---\n# {0} file for {1}".format(d, self.role_name)
            with open(main_yml, 'r') as f:
                self.assertEqual(expected_string, f.read().strip())

    def test_role_dirs(self):
        for d in self.expected_role_dirs:
            self.assertTrue(os.path.isdir(os.path.join(self.role_dir, d)), msg="Expected role subdirectory {0} doesn't exist".format(d))

    def test_travis_yml(self):
        with open(os.path.join(self.role_dir, '.travis.yml'), 'r') as f:
            contents = f.read()

        with open(os.path.join(self.role_skeleton_path, '.travis.yml'), 'r') as f:
            expected_contents = f.read()

        self.assertEqual(expected_contents, contents, msg='.travis.yml does not match expected')

    def test_readme_contents(self):
        with open(os.path.join(self.role_dir, 'README.md'), 'r') as readme:
            contents = readme.read()

        with open(os.path.join(self.role_skeleton_path, 'README.md'), 'r') as f:
            expected_contents = f.read()

        self.assertEqual(expected_contents, contents, msg='README.md does not match expected')

    def test_test_yml(self):
        with open(os.path.join(self.role_dir, 'tests', 'test.yml'), 'r') as f:
            test_playbook = yaml.safe_load(f)
        print(test_playbook)
        self.assertEqual(len(test_playbook), 1)
        self.assertEqual(test_playbook[0]['hosts'], 'localhost')
        self.assertEqual(test_playbook[0]['remote_user'], 'root')
        self.assertListEqual(test_playbook[0]['roles'], [self.role_name], msg='The list of roles included in the test play doesn\'t match')


class TestGalaxyInitDefault(unittest.TestCase, ValidRoleTests):

    @classmethod
    def setUpClass(cls):
        cls.setUpRole(role_name='delete_me')

    def test_metadata_contents(self):
        with open(os.path.join(self.role_dir, 'meta', 'main.yml'), 'r') as mf:
            metadata = yaml.safe_load(mf)
        self.assertEqual(metadata.get('galaxy_info', dict()).get('author'), 'your name', msg='author was not set properly in metadata')


class TestGalaxyInitAPB(unittest.TestCase, ValidRoleTests):

    @classmethod
    def setUpClass(cls):
        cls.setUpRole('delete_me_apb', galaxy_args=['--type=apb'])

    def test_metadata_apb_tag(self):
        with open(os.path.join(self.role_dir, 'meta', 'main.yml'), 'r') as mf:
            metadata = yaml.safe_load(mf)
        self.assertIn('apb', metadata.get('galaxy_info', dict()).get('galaxy_tags', []), msg='apb tag not set in role metadata')

    def test_metadata_contents(self):
        with open(os.path.join(self.role_dir, 'meta', 'main.yml'), 'r') as mf:
            metadata = yaml.safe_load(mf)
        self.assertEqual(metadata.get('galaxy_info', dict()).get('author'), 'your name', msg='author was not set properly in metadata')

    def test_apb_yml(self):
        self.assertTrue(os.path.exists(os.path.join(self.role_dir, 'apb.yml')), msg='apb.yml was not created')

    def test_test_yml(self):
        with open(os.path.join(self.role_dir, 'tests', 'test.yml'), 'r') as f:
            test_playbook = yaml.safe_load(f)
        print(test_playbook)
        self.assertEqual(len(test_playbook), 1)
        self.assertEqual(test_playbook[0]['hosts'], 'localhost')
        self.assertFalse(test_playbook[0]['gather_facts'])
        self.assertEqual(test_playbook[0]['connection'], 'local')
        self.assertIsNone(test_playbook[0]['tasks'], msg='We\'re expecting an unset list of tasks in test.yml')


class TestGalaxyInitContainer(unittest.TestCase, ValidRoleTests):

    @classmethod
    def setUpClass(cls):
        cls.setUpRole('delete_me_container', galaxy_args=['--type=container'])

    def test_metadata_container_tag(self):
        with open(os.path.join(self.role_dir, 'meta', 'main.yml'), 'r') as mf:
            metadata = yaml.safe_load(mf)
        self.assertIn('container', metadata.get('galaxy_info', dict()).get('galaxy_tags', []), msg='container tag not set in role metadata')

    def test_metadata_contents(self):
        with open(os.path.join(self.role_dir, 'meta', 'main.yml'), 'r') as mf:
            metadata = yaml.safe_load(mf)
        self.assertEqual(metadata.get('galaxy_info', dict()).get('author'), 'your name', msg='author was not set properly in metadata')

    def test_meta_container_yml(self):
        self.assertTrue(os.path.exists(os.path.join(self.role_dir, 'meta', 'container.yml')), msg='container.yml was not created')

    def test_test_yml(self):
        with open(os.path.join(self.role_dir, 'tests', 'test.yml'), 'r') as f:
            test_playbook = yaml.safe_load(f)
        print(test_playbook)
        self.assertEqual(len(test_playbook), 1)
        self.assertEqual(test_playbook[0]['hosts'], 'localhost')
        self.assertFalse(test_playbook[0]['gather_facts'])
        self.assertEqual(test_playbook[0]['connection'], 'local')
        self.assertIsNone(test_playbook[0]['tasks'], msg='We\'re expecting an unset list of tasks in test.yml')


class TestGalaxyInitSkeleton(unittest.TestCase, ValidRoleTests):

    @classmethod
    def setUpClass(cls):
        role_skeleton_path = os.path.join(os.path.split(__file__)[0], 'test_data', 'role_skeleton')
        cls.setUpRole('delete_me_skeleton', skeleton_path=role_skeleton_path)

    def test_empty_files_dir(self):
        files_dir = os.path.join(self.role_dir, 'files')
        self.assertTrue(os.path.isdir(files_dir))
        self.assertListEqual(os.listdir(files_dir), [], msg='we expect the files directory to be empty, is ignore working?')

    def test_template_ignore_jinja(self):
        test_conf_j2 = os.path.join(self.role_dir, 'templates', 'test.conf.j2')
        self.assertTrue(os.path.exists(test_conf_j2), msg="The test.conf.j2 template doesn't seem to exist, is it being rendered as test.conf?")
        with open(test_conf_j2, 'r') as f:
            contents = f.read()
        expected_contents = '[defaults]\ntest_key = {{ test_variable }}'
        self.assertEqual(expected_contents, contents.strip(), msg="test.conf.j2 doesn't contain what it should, is it being rendered?")

    def test_template_ignore_jinja_subfolder(self):
        test_conf_j2 = os.path.join(self.role_dir, 'templates', 'subfolder', 'test.conf.j2')
        self.assertTrue(os.path.exists(test_conf_j2), msg="The test.conf.j2 template doesn't seem to exist, is it being rendered as test.conf?")
        with open(test_conf_j2, 'r') as f:
            contents = f.read()
        expected_contents = '[defaults]\ntest_key = {{ test_variable }}'
        self.assertEqual(expected_contents, contents.strip(), msg="test.conf.j2 doesn't contain what it should, is it being rendered?")

    def test_template_ignore_similar_folder(self):
        self.assertTrue(os.path.exists(os.path.join(self.role_dir, 'templates_extra', 'templates.txt')))

    def test_skeleton_option(self):
        self.assertEquals(self.role_skeleton_path, self.gc.options.role_skeleton, msg='Skeleton path was not parsed properly from the command line')
