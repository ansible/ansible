# -*- coding: utf-8 -*-
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
import json
import os
import pytest
import shutil
import stat
import tarfile
import tempfile
import yaml

import ansible.constants as C
from ansible import context
from ansible.cli.galaxy import GalaxyCLI
from ansible.galaxy.api import GalaxyAPI
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.utils import context_objects as co
from units.compat import unittest
from units.compat.mock import patch, MagicMock


@pytest.fixture(autouse='function')
def reset_cli_args():
    co.GlobalCLIArgs._Singleton__instance = None
    yield
    co.GlobalCLIArgs._Singleton__instance = None


class TestGalaxy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        '''creating prerequisites for installing a role; setUpClass occurs ONCE whereas setUp occurs with every method tested.'''
        # class data for easy viewing: role_dir, role_tar, role_name, role_req, role_path

        cls.temp_dir = tempfile.mkdtemp(prefix='ansible-test_galaxy-')
        os.chdir(cls.temp_dir)

        if os.path.exists("./delete_me"):
            shutil.rmtree("./delete_me")

        # creating framework for a role
        gc = GalaxyCLI(args=["ansible-galaxy", "init", "--offline", "delete_me"])
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

        os.chdir('/')
        shutil.rmtree(cls.temp_dir)

    def setUp(self):
        # Reset the stored command line args
        co.GlobalCLIArgs._Singleton__instance = None
        self.default_args = ['ansible-galaxy']

    def tearDown(self):
        # Reset the stored command line args
        co.GlobalCLIArgs._Singleton__instance = None

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
        with patch.object(ansible.cli.CLI, "run", return_value=None) as mock_run:
            gc.run()
            # testing
            self.assertIsInstance(gc.galaxy, ansible.galaxy.Galaxy)
            self.assertEqual(mock_run.call_count, 1)
            self.assertTrue(isinstance(gc.api, ansible.galaxy.api.GalaxyAPI))

    def test_execute_remove(self):
        # installing role
        gc = GalaxyCLI(args=["ansible-galaxy", "install", "-p", self.role_path, "-r", self.role_req, '--force'])
        gc.run()

        # location where the role was installed
        role_file = os.path.join(self.role_path, self.role_name)

        # removing role
        # Have to reset the arguments in the context object manually since we're doing the
        # equivalent of running the command line program twice
        co.GlobalCLIArgs._Singleton__instance = None
        gc = GalaxyCLI(args=["ansible-galaxy", "remove", role_file, self.role_name])
        gc.run()

        # testing role was removed
        removed_role = not os.path.exists(role_file)
        self.assertTrue(removed_role)

    def test_exit_without_ignore_without_flag(self):
        ''' tests that GalaxyCLI exits with the error specified if the --ignore-errors flag is not used '''
        gc = GalaxyCLI(args=["ansible-galaxy", "install", "--server=None", "fake_role_name"])
        with patch.object(ansible.utils.display.Display, "display", return_value=None) as mocked_display:
            # testing that error expected is raised
            self.assertRaises(AnsibleError, gc.run)
            self.assertTrue(mocked_display.called_once_with("- downloading role 'fake_role_name', owned by "))

    def test_exit_without_ignore_with_flag(self):
        ''' tests that GalaxyCLI exits without the error specified if the --ignore-errors flag is used  '''
        # testing with --ignore-errors flag
        gc = GalaxyCLI(args=["ansible-galaxy", "install", "--server=None", "fake_role_name", "--ignore-errors"])
        with patch.object(ansible.utils.display.Display, "display", return_value=None) as mocked_display:
            gc.run()
            self.assertTrue(mocked_display.called_once_with("- downloading role 'fake_role_name', owned by "))

    def test_parse_no_action(self):
        ''' testing the options parser when no action is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", ""])
        self.assertRaises(SystemExit, gc.parse)

    def test_parse_invalid_action(self):
        ''' testing the options parser when an invalid action is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "NOT_ACTION"])
        self.assertRaises(SystemExit, gc.parse)

    def test_parse_delete(self):
        ''' testing the options parser when the action 'delete' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "delete", "foo", "bar"])
        gc.parse()
        self.assertEqual(context.CLIARGS['verbosity'], 0)

    def test_parse_import(self):
        ''' testing the options parser when the action 'import' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "import", "foo", "bar"])
        gc.parse()
        self.assertEqual(context.CLIARGS['wait'], True)
        self.assertEqual(context.CLIARGS['reference'], None)
        self.assertEqual(context.CLIARGS['check_status'], False)
        self.assertEqual(context.CLIARGS['verbosity'], 0)

    def test_parse_info(self):
        ''' testing the options parser when the action 'info' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "info", "foo", "bar"])
        gc.parse()
        self.assertEqual(context.CLIARGS['offline'], False)

    def test_parse_init(self):
        ''' testing the options parser when the action 'init' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "init", "foo"])
        gc.parse()
        self.assertEqual(context.CLIARGS['offline'], False)
        self.assertEqual(context.CLIARGS['force'], False)

    def test_parse_install(self):
        ''' testing the options parser when the action 'install' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "install"])
        gc.parse()
        self.assertEqual(context.CLIARGS['ignore_errors'], False)
        self.assertEqual(context.CLIARGS['no_deps'], False)
        self.assertEqual(context.CLIARGS['role_file'], None)
        self.assertEqual(context.CLIARGS['force'], False)

    def test_parse_list(self):
        ''' testing the options parser when the action 'list' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "list"])
        gc.parse()
        self.assertEqual(context.CLIARGS['verbosity'], 0)

    def test_parse_remove(self):
        ''' testing the options parser when the action 'remove' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "remove", "foo"])
        gc.parse()
        self.assertEqual(context.CLIARGS['verbosity'], 0)

    def test_parse_search(self):
        ''' testing the options parswer when the action 'search' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "search"])
        gc.parse()
        self.assertEqual(context.CLIARGS['platforms'], None)
        self.assertEqual(context.CLIARGS['galaxy_tags'], None)
        self.assertEqual(context.CLIARGS['author'], None)

    def test_parse_setup(self):
        ''' testing the options parser when the action 'setup' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "setup", "source", "github_user", "github_repo", "secret"])
        gc.parse()
        self.assertEqual(context.CLIARGS['verbosity'], 0)
        self.assertEqual(context.CLIARGS['remove_id'], None)
        self.assertEqual(context.CLIARGS['setup_list'], False)


class ValidRoleTests(object):

    expected_role_dirs = ('defaults', 'files', 'handlers', 'meta', 'tasks', 'templates', 'vars', 'tests')

    @classmethod
    def setUpRole(cls, role_name, galaxy_args=None, skeleton_path=None, use_explicit_type=False):
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
        args = ['ansible-galaxy']
        if use_explicit_type:
            args += ['role']
        args += ['init', '-c', '--offline'] + galaxy_args + ['--init-path', cls.test_dir, cls.role_name]

        gc = GalaxyCLI(args=args)
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
        cls.setUpRole('delete_me_skeleton', skeleton_path=role_skeleton_path, use_explicit_type=True)

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
        self.assertEquals(self.role_skeleton_path, context.CLIARGS['role_skeleton'], msg='Skeleton path was not parsed properly from the command line')


@pytest.mark.parametrize('cli_args, expected', [
    (['ansible-galaxy', 'collection', 'init', 'abc.def'], 0),
    (['ansible-galaxy', 'collection', 'init', 'abc.def', '-vvv'], 3),
    (['ansible-galaxy', '-vv', 'collection', 'init', 'abc.def'], 2),
    # Due to our manual parsing we want to verify that -v set in the sub parser takes precedence. This behaviour is
    # deprecated and tests should be removed when the code that handles it is removed
    (['ansible-galaxy', '-vv', 'collection', 'init', 'abc.def', '-v'], 1),
    (['ansible-galaxy', '-vv', 'collection', 'init', 'abc.def', '-vvvv'], 4),
    (['ansible-galaxy', '-vvv', 'init', 'name'], 3),
    (['ansible-galaxy', '-vvvvv', 'init', '-v', 'name'], 1),
])
def test_verbosity_arguments(cli_args, expected, monkeypatch):
    # Mock out the functions so we don't actually execute anything
    for func_name in [f for f in dir(GalaxyCLI) if f.startswith("execute_")]:
        monkeypatch.setattr(GalaxyCLI, func_name, MagicMock())

    cli = GalaxyCLI(args=cli_args)
    cli.run()

    assert context.CLIARGS['verbosity'] == expected


@pytest.fixture()
def collection_skeleton(request, tmp_path_factory):
    name, skeleton_path = request.param

    galaxy_args = ['ansible-galaxy', 'collection', 'init', '-c']

    if skeleton_path is not None:
        galaxy_args += ['--collection-skeleton', skeleton_path]

    test_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections'))
    galaxy_args += ['--init-path', test_dir, name]

    GalaxyCLI(args=galaxy_args).run()
    namespace_name, collection_name = name.split('.', 1)
    collection_dir = os.path.join(test_dir, namespace_name, collection_name)

    return collection_dir


@pytest.mark.parametrize('collection_skeleton', [
    ('ansible_test.my_collection', None),
], indirect=True)
def test_collection_default(collection_skeleton):
    meta_path = os.path.join(collection_skeleton, 'galaxy.yml')

    with open(meta_path, 'r') as galaxy_meta:
        metadata = yaml.safe_load(galaxy_meta)

    assert metadata['namespace'] == 'ansible_test'
    assert metadata['name'] == 'my_collection'
    assert metadata['authors'] == ['your name <example@domain.com>']
    assert metadata['readme'] == 'README.md'
    assert metadata['version'] == '1.0.0'
    assert metadata['description'] == 'your collection description'
    assert metadata['license'] == ['GPL-2.0-or-later']
    assert metadata['tags'] == []
    assert metadata['dependencies'] == {}
    assert metadata['documentation'] == 'http://docs.example.com'
    assert metadata['repository'] == 'http://example.com/repository'
    assert metadata['homepage'] == 'http://example.com'
    assert metadata['issues'] == 'http://example.com/issue/tracker'

    for d in ['docs', 'plugins', 'roles']:
        assert os.path.isdir(os.path.join(collection_skeleton, d)), \
            "Expected collection subdirectory {0} doesn't exist".format(d)


@pytest.mark.parametrize('collection_skeleton', [
    ('ansible_test.delete_me_skeleton', os.path.join(os.path.split(__file__)[0], 'test_data', 'collection_skeleton')),
], indirect=True)
def test_collection_skeleton(collection_skeleton):
    meta_path = os.path.join(collection_skeleton, 'galaxy.yml')

    with open(meta_path, 'r') as galaxy_meta:
        metadata = yaml.safe_load(galaxy_meta)

    assert metadata['namespace'] == 'ansible_test'
    assert metadata['name'] == 'delete_me_skeleton'
    assert metadata['authors'] == ['Ansible Cow <acow@bovineuniversity.edu>', 'Tu Cow <tucow@bovineuniversity.edu>']
    assert metadata['version'] == '0.1.0'
    assert metadata['readme'] == 'README.md'
    assert len(metadata) == 5

    assert os.path.exists(os.path.join(collection_skeleton, 'README.md'))

    # Test empty directories exist and are empty
    for empty_dir in ['plugins/action', 'plugins/filter', 'plugins/inventory', 'plugins/lookup',
                      'plugins/module_utils', 'plugins/modules']:

        assert os.listdir(os.path.join(collection_skeleton, empty_dir)) == []

    # Test files that don't end with .j2 were not templated
    doc_file = os.path.join(collection_skeleton, 'docs', 'My Collection.md')
    with open(doc_file, 'r') as f:
        doc_contents = f.read()
    assert doc_contents.strip() == 'Welcome to my test collection doc for {{ namespace }}.'

    # Test files that end with .j2 but are in the templates directory were not templated
    for template_dir in ['playbooks/templates', 'playbooks/templates/subfolder',
                         'roles/common/templates', 'roles/common/templates/subfolder']:
        test_conf_j2 = os.path.join(collection_skeleton, template_dir, 'test.conf.j2')
        assert os.path.exists(test_conf_j2)

        with open(test_conf_j2, 'r') as f:
            contents = f.read()
        expected_contents = '[defaults]\ntest_key = {{ test_variable }}'

        assert expected_contents == contents.strip()


@pytest.fixture()
def collection_artifact(collection_skeleton, tmp_path_factory):
    ''' Creates a collection artifact tarball that is ready to be published and installed '''
    output_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Output'))

    # Create a file with +x in the collection so we can test the permissions
    execute_path = os.path.join(collection_skeleton, 'runme.sh')
    with open(execute_path, mode='wb') as fd:
        fd.write(b"echo hi")

    # S_ISUID should not be present on extraction.
    os.chmod(execute_path, os.stat(execute_path).st_mode | stat.S_ISUID | stat.S_IEXEC)

    # Because we call GalaxyCLI in collection_skeleton we need to reset the singleton back to None so it uses the new
    # args, we reset the original args once it is done.
    orig_cli_args = co.GlobalCLIArgs._Singleton__instance
    try:
        co.GlobalCLIArgs._Singleton__instance = None
        galaxy_args = ['ansible-galaxy', 'collection', 'build', collection_skeleton, '--output-path', output_dir]
        gc = GalaxyCLI(args=galaxy_args)
        gc.run()

        yield output_dir
    finally:
        co.GlobalCLIArgs._Singleton__instance = orig_cli_args


def test_invalid_skeleton_path():
    expected = "- the skeleton path '/fake/path' does not exist, cannot init collection"

    gc = GalaxyCLI(args=['ansible-galaxy', 'collection', 'init', 'my.collection', '--collection-skeleton',
                         '/fake/path'])
    with pytest.raises(AnsibleError, match=expected):
        gc.run()


@pytest.mark.parametrize("name", [
    "",
    "invalid",
    "hypen-ns.collection",
    "ns.hyphen-collection",
    "ns.collection.weird",
])
def test_invalid_collection_name_init(name):
    expected = "Invalid collection name '%s', name must be in the format <namespace>.<collection>" % name

    gc = GalaxyCLI(args=['ansible-galaxy', 'collection', 'init', name])
    with pytest.raises(AnsibleError, match=expected):
        gc.run()


@pytest.mark.parametrize("name, expected", [
    ("", ""),
    ("invalid", "invalid"),
    ("invalid:1.0.0", "invalid"),
    ("hypen-ns.collection", "hypen-ns.collection"),
    ("ns.hyphen-collection", "ns.hyphen-collection"),
    ("ns.collection.weird", "ns.collection.weird"),
])
def test_invalid_collection_name_install(name, expected, tmp_path_factory):
    install_path = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections'))
    expected = "Invalid collection name '%s', name must be in the format <namespace>.<collection>" % expected

    gc = GalaxyCLI(args=['ansible-galaxy', 'collection', 'install', name, '-p', os.path.join(install_path, 'install')])
    with pytest.raises(AnsibleError, match=expected):
        gc.run()


@pytest.mark.parametrize('collection_skeleton', [
    ('ansible_test.build_collection', None),
], indirect=True)
def test_collection_build(collection_artifact):
    tar_path = os.path.join(collection_artifact, 'ansible_test-build_collection-1.0.0.tar.gz')
    assert tarfile.is_tarfile(tar_path)

    with tarfile.open(tar_path, mode='r') as tar:
        tar_members = tar.getmembers()

        valid_files = ['MANIFEST.json', 'FILES.json', 'roles', 'docs', 'plugins', 'plugins/README.md', 'README.md',
                       'runme.sh']
        assert len(tar_members) == len(valid_files)

        # Verify the uid and gid is 0 and the correct perms are set
        for member in tar_members:
            assert member.name in valid_files

            assert member.gid == 0
            assert member.gname == ''
            assert member.uid == 0
            assert member.uname == ''
            if member.isdir() or member.name == 'runme.sh':
                assert member.mode == 0o0755
            else:
                assert member.mode == 0o0644

        manifest_file = tar.extractfile(tar_members[0])
        try:
            manifest = json.loads(to_text(manifest_file.read()))
        finally:
            manifest_file.close()

        coll_info = manifest['collection_info']
        file_manifest = manifest['file_manifest_file']
        assert manifest['format'] == 1
        assert len(manifest.keys()) == 3

        assert coll_info['namespace'] == 'ansible_test'
        assert coll_info['name'] == 'build_collection'
        assert coll_info['version'] == '1.0.0'
        assert coll_info['authors'] == ['your name <example@domain.com>']
        assert coll_info['readme'] == 'README.md'
        assert coll_info['tags'] == []
        assert coll_info['description'] == 'your collection description'
        assert coll_info['license'] == ['GPL-2.0-or-later']
        assert coll_info['license_file'] is None
        assert coll_info['dependencies'] == {}
        assert coll_info['repository'] == 'http://example.com/repository'
        assert coll_info['documentation'] == 'http://docs.example.com'
        assert coll_info['homepage'] == 'http://example.com'
        assert coll_info['issues'] == 'http://example.com/issue/tracker'
        assert len(coll_info.keys()) == 14

        assert file_manifest['name'] == 'FILES.json'
        assert file_manifest['ftype'] == 'file'
        assert file_manifest['chksum_type'] == 'sha256'
        assert file_manifest['chksum_sha256'] is not None  # Order of keys makes it hard to verify the checksum
        assert file_manifest['format'] == 1
        assert len(file_manifest.keys()) == 5

        files_file = tar.extractfile(tar_members[1])
        try:
            files = json.loads(to_text(files_file.read()))
        finally:
            files_file.close()

        assert len(files['files']) == 7
        assert files['format'] == 1
        assert len(files.keys()) == 2

        valid_files_entries = ['.', 'roles', 'docs', 'plugins', 'plugins/README.md', 'README.md', 'runme.sh']
        for file_entry in files['files']:
            assert file_entry['name'] in valid_files_entries
            assert file_entry['format'] == 1

            if file_entry['name'] in ['plugins/README.md', 'runme.sh']:
                assert file_entry['ftype'] == 'file'
                assert file_entry['chksum_type'] == 'sha256'
                # Can't test the actual checksum as the html link changes based on the version or the file contents
                # don't matter
                assert file_entry['chksum_sha256'] is not None
            elif file_entry['name'] == 'README.md':
                assert file_entry['ftype'] == 'file'
                assert file_entry['chksum_type'] == 'sha256'
                assert file_entry['chksum_sha256'] == '45923ca2ece0e8ce31d29e5df9d8b649fe55e2f5b5b61c9724d7cc187bd6ad4a'
            else:
                assert file_entry['ftype'] == 'dir'
                assert file_entry['chksum_type'] is None
                assert file_entry['chksum_sha256'] is None

            assert len(file_entry.keys()) == 5


@pytest.fixture()
def collection_install(reset_cli_args, tmp_path_factory, monkeypatch):
    mock_install = MagicMock()
    monkeypatch.setattr(ansible.cli.galaxy, 'install_collections', mock_install)

    mock_warning = MagicMock()
    monkeypatch.setattr(ansible.utils.display.Display, 'warning', mock_warning)

    output_dir = to_text((tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Output')))
    yield mock_install, mock_warning, output_dir


def test_collection_install_with_names(collection_install):
    mock_install, mock_warning, output_dir = collection_install

    galaxy_args = ['ansible-galaxy', 'collection', 'install', 'namespace.collection', 'namespace2.collection:1.0.1',
                   '--collections-path', output_dir]
    GalaxyCLI(args=galaxy_args).run()

    collection_path = os.path.join(output_dir, 'ansible_collections')
    assert os.path.isdir(collection_path)

    assert mock_warning.call_count == 1
    assert "The specified collections path '%s' is not part of the configured Ansible collections path" % output_dir \
        in mock_warning.call_args[0][0]

    assert mock_install.call_count == 1
    assert mock_install.call_args[0][0] == [('namespace.collection', '*', None),
                                            ('namespace2.collection', '1.0.1', None)]
    assert mock_install.call_args[0][1] == collection_path
    assert len(mock_install.call_args[0][2]) == 1
    assert mock_install.call_args[0][2][0].api_server == 'https://galaxy.ansible.com'
    assert mock_install.call_args[0][2][0].validate_certs is True
    assert mock_install.call_args[0][3] is True
    assert mock_install.call_args[0][4] is False
    assert mock_install.call_args[0][5] is False
    assert mock_install.call_args[0][6] is False
    assert mock_install.call_args[0][7] is False


def test_collection_install_with_requirements_file(collection_install):
    mock_install, mock_warning, output_dir = collection_install

    requirements_file = os.path.join(output_dir, 'requirements.yml')
    with open(requirements_file, 'wb') as req_obj:
        req_obj.write(b'''---
collections:
- namespace.coll
- name: namespace2.coll
  version: '>2.0.1'
''')

    galaxy_args = ['ansible-galaxy', 'collection', 'install', '--requirements-file', requirements_file,
                   '--collections-path', output_dir]
    GalaxyCLI(args=galaxy_args).run()

    collection_path = os.path.join(output_dir, 'ansible_collections')
    assert os.path.isdir(collection_path)

    assert mock_warning.call_count == 1
    assert "The specified collections path '%s' is not part of the configured Ansible collections path" % output_dir \
        in mock_warning.call_args[0][0]

    assert mock_install.call_count == 1
    assert mock_install.call_args[0][0] == [('namespace.coll', '*', None),
                                            ('namespace2.coll', '>2.0.1', None)]
    assert mock_install.call_args[0][1] == collection_path
    assert len(mock_install.call_args[0][2]) == 1
    assert mock_install.call_args[0][2][0].api_server == 'https://galaxy.ansible.com'
    assert mock_install.call_args[0][2][0].validate_certs is True
    assert mock_install.call_args[0][3] is True
    assert mock_install.call_args[0][4] is False
    assert mock_install.call_args[0][5] is False
    assert mock_install.call_args[0][6] is False
    assert mock_install.call_args[0][7] is False


def test_collection_install_with_relative_path(collection_install, monkeypatch):
    mock_install = collection_install[0]

    mock_req = MagicMock()
    mock_req.return_value = {'collections': [('namespace.coll', '*', None)]}
    monkeypatch.setattr(ansible.cli.galaxy.GalaxyCLI, '_parse_requirements_file', mock_req)

    monkeypatch.setattr(os, 'makedirs', MagicMock())

    requirements_file = './requirements.myl'
    collections_path = './ansible_collections'
    galaxy_args = ['ansible-galaxy', 'collection', 'install', '--requirements-file', requirements_file,
                   '--collections-path', collections_path]
    GalaxyCLI(args=galaxy_args).run()

    assert mock_install.call_count == 1
    assert mock_install.call_args[0][0] == [('namespace.coll', '*', None)]
    assert mock_install.call_args[0][1] == os.path.abspath(collections_path)
    assert len(mock_install.call_args[0][2]) == 1
    assert mock_install.call_args[0][2][0].api_server == 'https://galaxy.ansible.com'
    assert mock_install.call_args[0][2][0].validate_certs is True
    assert mock_install.call_args[0][3] is True
    assert mock_install.call_args[0][4] is False
    assert mock_install.call_args[0][5] is False
    assert mock_install.call_args[0][6] is False
    assert mock_install.call_args[0][7] is False

    assert mock_req.call_count == 1
    assert mock_req.call_args[0][0] == os.path.abspath(requirements_file)


def test_collection_install_with_unexpanded_path(collection_install, monkeypatch):
    mock_install = collection_install[0]

    mock_req = MagicMock()
    mock_req.return_value = {'collections': [('namespace.coll', '*', None)]}
    monkeypatch.setattr(ansible.cli.galaxy.GalaxyCLI, '_parse_requirements_file', mock_req)

    monkeypatch.setattr(os, 'makedirs', MagicMock())

    requirements_file = '~/requirements.myl'
    collections_path = '~/ansible_collections'
    galaxy_args = ['ansible-galaxy', 'collection', 'install', '--requirements-file', requirements_file,
                   '--collections-path', collections_path]
    GalaxyCLI(args=galaxy_args).run()

    assert mock_install.call_count == 1
    assert mock_install.call_args[0][0] == [('namespace.coll', '*', None)]
    assert mock_install.call_args[0][1] == os.path.expanduser(os.path.expandvars(collections_path))
    assert len(mock_install.call_args[0][2]) == 1
    assert mock_install.call_args[0][2][0].api_server == 'https://galaxy.ansible.com'
    assert mock_install.call_args[0][2][0].validate_certs is True
    assert mock_install.call_args[0][3] is True
    assert mock_install.call_args[0][4] is False
    assert mock_install.call_args[0][5] is False
    assert mock_install.call_args[0][6] is False
    assert mock_install.call_args[0][7] is False

    assert mock_req.call_count == 1
    assert mock_req.call_args[0][0] == os.path.expanduser(os.path.expandvars(requirements_file))


def test_collection_install_in_collection_dir(collection_install, monkeypatch):
    mock_install, mock_warning, output_dir = collection_install

    collections_path = C.COLLECTIONS_PATHS[0]

    galaxy_args = ['ansible-galaxy', 'collection', 'install', 'namespace.collection', 'namespace2.collection:1.0.1',
                   '--collections-path', collections_path]
    GalaxyCLI(args=galaxy_args).run()

    assert mock_warning.call_count == 0

    assert mock_install.call_count == 1
    assert mock_install.call_args[0][0] == [('namespace.collection', '*', None),
                                            ('namespace2.collection', '1.0.1', None)]
    assert mock_install.call_args[0][1] == os.path.join(collections_path, 'ansible_collections')
    assert len(mock_install.call_args[0][2]) == 1
    assert mock_install.call_args[0][2][0].api_server == 'https://galaxy.ansible.com'
    assert mock_install.call_args[0][2][0].validate_certs is True
    assert mock_install.call_args[0][3] is True
    assert mock_install.call_args[0][4] is False
    assert mock_install.call_args[0][5] is False
    assert mock_install.call_args[0][6] is False
    assert mock_install.call_args[0][7] is False


def test_collection_install_with_url(collection_install):
    mock_install, dummy, output_dir = collection_install

    galaxy_args = ['ansible-galaxy', 'collection', 'install', 'https://foo/bar/foo-bar-v1.0.0.tar.gz',
                   '--collections-path', output_dir]
    GalaxyCLI(args=galaxy_args).run()

    collection_path = os.path.join(output_dir, 'ansible_collections')
    assert os.path.isdir(collection_path)

    assert mock_install.call_count == 1
    assert mock_install.call_args[0][0] == [('https://foo/bar/foo-bar-v1.0.0.tar.gz', '*', None)]
    assert mock_install.call_args[0][1] == collection_path
    assert len(mock_install.call_args[0][2]) == 1
    assert mock_install.call_args[0][2][0].api_server == 'https://galaxy.ansible.com'
    assert mock_install.call_args[0][2][0].validate_certs is True
    assert mock_install.call_args[0][3] is True
    assert mock_install.call_args[0][4] is False
    assert mock_install.call_args[0][5] is False
    assert mock_install.call_args[0][6] is False
    assert mock_install.call_args[0][7] is False


def test_collection_install_name_and_requirements_fail(collection_install):
    test_path = collection_install[2]
    expected = 'The positional collection_name arg and --requirements-file are mutually exclusive.'

    with pytest.raises(AnsibleError, match=expected):
        GalaxyCLI(args=['ansible-galaxy', 'collection', 'install', 'namespace.collection', '--collections-path',
                        test_path, '--requirements-file', test_path]).run()


def test_collection_install_no_name_and_requirements_fail(collection_install):
    test_path = collection_install[2]
    expected = 'You must specify a collection name or a requirements file.'

    with pytest.raises(AnsibleError, match=expected):
        GalaxyCLI(args=['ansible-galaxy', 'collection', 'install', '--collections-path', test_path]).run()


def test_collection_install_path_with_ansible_collections(collection_install):
    mock_install, mock_warning, output_dir = collection_install

    collection_path = os.path.join(output_dir, 'ansible_collections')

    galaxy_args = ['ansible-galaxy', 'collection', 'install', 'namespace.collection', 'namespace2.collection:1.0.1',
                   '--collections-path', collection_path]
    GalaxyCLI(args=galaxy_args).run()

    assert os.path.isdir(collection_path)

    assert mock_warning.call_count == 1
    assert "The specified collections path '%s' is not part of the configured Ansible collections path" \
        % collection_path in mock_warning.call_args[0][0]

    assert mock_install.call_count == 1
    assert mock_install.call_args[0][0] == [('namespace.collection', '*', None),
                                            ('namespace2.collection', '1.0.1', None)]
    assert mock_install.call_args[0][1] == collection_path
    assert len(mock_install.call_args[0][2]) == 1
    assert mock_install.call_args[0][2][0].api_server == 'https://galaxy.ansible.com'
    assert mock_install.call_args[0][2][0].validate_certs is True
    assert mock_install.call_args[0][3] is True
    assert mock_install.call_args[0][4] is False
    assert mock_install.call_args[0][5] is False
    assert mock_install.call_args[0][6] is False
    assert mock_install.call_args[0][7] is False


def test_collection_install_ignore_certs(collection_install):
    mock_install, mock_warning, output_dir = collection_install

    galaxy_args = ['ansible-galaxy', 'collection', 'install', 'namespace.collection', '--collections-path', output_dir,
                   '--ignore-certs']
    GalaxyCLI(args=galaxy_args).run()

    assert mock_install.call_args[0][3] is False


def test_collection_install_force(collection_install):
    mock_install, mock_warning, output_dir = collection_install

    galaxy_args = ['ansible-galaxy', 'collection', 'install', 'namespace.collection', '--collections-path', output_dir,
                   '--force']
    GalaxyCLI(args=galaxy_args).run()

    assert mock_install.call_args[0][6] is True


def test_collection_install_force_deps(collection_install):
    mock_install, mock_warning, output_dir = collection_install

    galaxy_args = ['ansible-galaxy', 'collection', 'install', 'namespace.collection', '--collections-path', output_dir,
                   '--force-with-deps']
    GalaxyCLI(args=galaxy_args).run()

    assert mock_install.call_args[0][7] is True


def test_collection_install_no_deps(collection_install):
    mock_install, mock_warning, output_dir = collection_install

    galaxy_args = ['ansible-galaxy', 'collection', 'install', 'namespace.collection', '--collections-path', output_dir,
                   '--no-deps']
    GalaxyCLI(args=galaxy_args).run()

    assert mock_install.call_args[0][5] is True


def test_collection_install_ignore(collection_install):
    mock_install, mock_warning, output_dir = collection_install

    galaxy_args = ['ansible-galaxy', 'collection', 'install', 'namespace.collection', '--collections-path', output_dir,
                   '--ignore-errors']
    GalaxyCLI(args=galaxy_args).run()

    assert mock_install.call_args[0][4] is True


def test_collection_install_custom_server(collection_install):
    mock_install, mock_warning, output_dir = collection_install

    galaxy_args = ['ansible-galaxy', 'collection', 'install', 'namespace.collection', '--collections-path', output_dir,
                   '--server', 'https://galaxy-dev.ansible.com']
    GalaxyCLI(args=galaxy_args).run()

    assert len(mock_install.call_args[0][2]) == 1
    assert mock_install.call_args[0][2][0].api_server == 'https://galaxy-dev.ansible.com'
    assert mock_install.call_args[0][2][0].validate_certs is True


@pytest.fixture()
def requirements_file(request, tmp_path_factory):
    content = request.param

    test_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Requirements'))
    requirements_file = os.path.join(test_dir, 'requirements.yml')

    if content:
        with open(requirements_file, 'wb') as req_obj:
            req_obj.write(to_bytes(content))

    yield requirements_file


@pytest.fixture()
def requirements_cli(monkeypatch):
    monkeypatch.setattr(GalaxyCLI, 'execute_install', MagicMock())
    cli = GalaxyCLI(args=['ansible-galaxy', 'install'])
    cli.run()
    return cli


@pytest.mark.parametrize('requirements_file', [None], indirect=True)
def test_parse_requirements_file_that_doesnt_exist(requirements_cli, requirements_file):
    expected = "The requirements file '%s' does not exist." % to_native(requirements_file)
    with pytest.raises(AnsibleError, match=expected):
        requirements_cli._parse_requirements_file(requirements_file)


@pytest.mark.parametrize('requirements_file', ['not a valid yml file: hi: world'], indirect=True)
def test_parse_requirements_file_that_isnt_yaml(requirements_cli, requirements_file):
    expected = "Failed to parse the requirements yml at '%s' with the following error" % to_native(requirements_file)
    with pytest.raises(AnsibleError, match=expected):
        requirements_cli._parse_requirements_file(requirements_file)


@pytest.mark.parametrize('requirements_file', [('''
# Older role based requirements.yml
- galaxy.role
- anotherrole
''')], indirect=True)
def test_parse_requirements_in_older_format_illega(requirements_cli, requirements_file):
    expected = "Expecting requirements file to be a dict with the key 'collections' that contains a list of " \
               "collections to install"

    with pytest.raises(AnsibleError, match=expected):
        requirements_cli._parse_requirements_file(requirements_file, allow_old_format=False)


@pytest.mark.parametrize('requirements_file', ['''
collections:
- version: 1.0.0
'''], indirect=True)
def test_parse_requirements_without_mandatory_name_key(requirements_cli, requirements_file):
    expected = "Collections requirement entry should contain the key name."
    with pytest.raises(AnsibleError, match=expected):
        requirements_cli._parse_requirements_file(requirements_file)


@pytest.mark.parametrize('requirements_file', [('''
collections:
- namespace.collection1
- namespace.collection2
'''), ('''
collections:
- name: namespace.collection1
- name: namespace.collection2
''')], indirect=True)
def test_parse_requirements(requirements_cli, requirements_file):
    expected = {
        'roles': [],
        'collections': [('namespace.collection1', '*', None), ('namespace.collection2', '*', None)]
    }
    actual = requirements_cli._parse_requirements_file(requirements_file)

    assert actual == expected


@pytest.mark.parametrize('requirements_file', ['''
collections:
- name: namespace.collection1
  version: ">=1.0.0,<=2.0.0"
  source: https://galaxy-dev.ansible.com
- namespace.collection2'''], indirect=True)
def test_parse_requirements_with_extra_info(requirements_cli, requirements_file):
    actual = requirements_cli._parse_requirements_file(requirements_file)

    assert len(actual['roles']) == 0
    assert len(actual['collections']) == 2
    assert actual['collections'][0][0] == 'namespace.collection1'
    assert actual['collections'][0][1] == '>=1.0.0,<=2.0.0'
    assert actual['collections'][0][2].api_server == 'https://galaxy-dev.ansible.com'
    assert actual['collections'][0][2].name == 'explicit_requirement_namespace.collection1'
    assert actual['collections'][0][2].token is None
    assert actual['collections'][0][2].username is None
    assert actual['collections'][0][2].password is None
    assert actual['collections'][0][2].validate_certs is True

    assert actual['collections'][1] == ('namespace.collection2', '*', None)


@pytest.mark.parametrize('requirements_file', ['''
roles:
- username.role_name
- src: username2.role_name2
- src: ssh://github.com/user/repo
  scm: git

collections:
- namespace.collection2
'''], indirect=True)
def test_parse_requirements_with_roles_and_collections(requirements_cli, requirements_file):
    actual = requirements_cli._parse_requirements_file(requirements_file)

    assert len(actual['roles']) == 3
    assert actual['roles'][0].name == 'username.role_name'
    assert actual['roles'][1].name == 'username2.role_name2'
    assert actual['roles'][2].name == 'repo'
    assert actual['roles'][2].src == 'ssh://github.com/user/repo'

    assert len(actual['collections']) == 1
    assert actual['collections'][0] == ('namespace.collection2', '*', None)


@pytest.mark.parametrize('requirements_file', ['''
collections:
- name: namespace.collection
- name: namespace2.collection2
  source: https://galaxy-dev.ansible.com/
- name: namespace3.collection3
  source: server
'''], indirect=True)
def test_parse_requirements_with_collection_source(requirements_cli, requirements_file):
    galaxy_api = GalaxyAPI(requirements_cli.api, 'server', 'https://config-server')
    requirements_cli.api_servers.append(galaxy_api)

    actual = requirements_cli._parse_requirements_file(requirements_file)

    assert actual['roles'] == []
    assert len(actual['collections']) == 3
    assert actual['collections'][0] == ('namespace.collection', '*', None)

    assert actual['collections'][1][0] == 'namespace2.collection2'
    assert actual['collections'][1][1] == '*'
    assert actual['collections'][1][2].api_server == 'https://galaxy-dev.ansible.com/'
    assert actual['collections'][1][2].name == 'explicit_requirement_namespace2.collection2'
    assert actual['collections'][1][2].token is None

    assert actual['collections'][2] == ('namespace3.collection3', '*', galaxy_api)


@pytest.mark.parametrize('requirements_file', ['''
- username.included_role
- src: https://github.com/user/repo
'''], indirect=True)
def test_parse_requirements_roles_with_include(requirements_cli, requirements_file):
    reqs = [
        'ansible.role',
        {'include': requirements_file},
    ]
    parent_requirements = os.path.join(os.path.dirname(requirements_file), 'parent.yaml')
    with open(to_bytes(parent_requirements), 'wb') as req_fd:
        req_fd.write(to_bytes(yaml.safe_dump(reqs)))

    actual = requirements_cli._parse_requirements_file(parent_requirements)

    assert len(actual['roles']) == 3
    assert actual['collections'] == []
    assert actual['roles'][0].name == 'ansible.role'
    assert actual['roles'][1].name == 'username.included_role'
    assert actual['roles'][2].name == 'repo'
    assert actual['roles'][2].src == 'https://github.com/user/repo'


@pytest.mark.parametrize('requirements_file', ['''
- username.role
- include: missing.yml
'''], indirect=True)
def test_parse_requirements_roles_with_include_missing(requirements_cli, requirements_file):
    expected = "Failed to find include requirements file 'missing.yml' in '%s'" % to_native(requirements_file)

    with pytest.raises(AnsibleError, match=expected):
        requirements_cli._parse_requirements_file(requirements_file)
