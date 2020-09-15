# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

from units.compat import unittest
from units.compat.builtins import BUILTINS
from units.compat.mock import patch, MagicMock
from ansible.plugins.loader import PluginLoader


class TestErrors(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch.object(PluginLoader, '_get_paths')
    def test_print_paths(self, mock_method):
        mock_method.return_value = ['/path/one', '/path/two', '/path/three']
        pl = PluginLoader('foo', 'foo', '', 'test_plugins')
        paths = pl.print_paths()
        expected_paths = os.pathsep.join(['/path/one', '/path/two', '/path/three'])
        self.assertEqual(paths, expected_paths)

    def test_plugins__get_package_paths_no_package(self):
        pl = PluginLoader('test', '', 'test', 'test_plugin')
        self.assertEqual(pl._get_package_paths(), [])

    def test_plugins__get_package_paths_with_package(self):
        # the _get_package_paths() call uses __import__ to load a
        # python library, and then uses the __file__ attribute of
        # the result for that to get the library path, so we mock
        # that here and patch the builtin to use our mocked result
        foo = MagicMock()
        bar = MagicMock()
        bam = MagicMock()
        bam.__file__ = '/path/to/my/foo/bar/bam/__init__.py'
        bar.bam = bam
        foo.return_value.bar = bar
        pl = PluginLoader('test', 'foo.bar.bam', 'test', 'test_plugin')
        with patch('{0}.__import__'.format(BUILTINS), foo):
            self.assertEqual(pl._get_package_paths(), ['/path/to/my/foo/bar/bam'])

    def test_plugins__get_paths(self):
        pl = PluginLoader('test', '', 'test', 'test_plugin')
        pl._paths = ['/path/one', '/path/two']
        self.assertEqual(pl._get_paths(), ['/path/one', '/path/two'])

        # NOT YET WORKING
        # def fake_glob(path):
        #     if path == 'test/*':
        #         return ['test/foo', 'test/bar', 'test/bam']
        #     elif path == 'test/*/*'
        # m._paths = None
        # mock_glob = MagicMock()
        # mock_glob.return_value = []
        # with patch('glob.glob', mock_glob):
        #     pass

    def assertPluginLoaderConfigBecomes(self, arg, expected):
        pl = PluginLoader('test', '', arg, 'test_plugin')
        self.assertEqual(pl.config, expected)

    def test_plugin__init_config_list(self):
        config = ['/one', '/two']
        self.assertPluginLoaderConfigBecomes(config, config)

    def test_plugin__init_config_str(self):
        self.assertPluginLoaderConfigBecomes('test', ['test'])

    def test_plugin__init_config_none(self):
        self.assertPluginLoaderConfigBecomes(None, [])

    def test__load_module_source_no_duplicate_names(self):
        '''
        This test simulates importing 2 plugins with the same name,
        and validating that the import is short circuited if a file with the same name
        has already been imported
        '''

        fixture_path = os.path.join(os.path.dirname(__file__), 'loader_fixtures')

        pl = PluginLoader('test', '', 'test', 'test_plugin')
        one = pl._load_module_source('import_fixture', os.path.join(fixture_path, 'import_fixture.py'))
        # This line wouldn't even succeed if we didn't short circuit on finding a duplicate name
        two = pl._load_module_source('import_fixture', '/path/to/import_fixture.py')

        self.assertEqual(one, two)

    @patch('ansible.plugins.loader.glob')
    @patch.object(PluginLoader, '_get_paths')
    def test_all_no_duplicate_names(self, gp_mock, glob_mock):
        '''
        This test goes along with ``test__load_module_source_no_duplicate_names``
        and ensures that we ignore duplicate imports on multiple paths
        '''

        fixture_path = os.path.join(os.path.dirname(__file__), 'loader_fixtures')

        gp_mock.return_value = [
            fixture_path,
            '/path/to'
        ]

        glob_mock.glob.side_effect = [
            [os.path.join(fixture_path, 'import_fixture.py')],
            ['/path/to/import_fixture.py']
        ]

        pl = PluginLoader('test', '', 'test', 'test_plugin')
        # Aside from needing ``list()`` so we can do a len, ``PluginLoader.all`` returns a generator
        # so ``list()`` actually causes ``PluginLoader.all`` to run.
        plugins = list(pl.all())
        self.assertEqual(len(plugins), 1)

        self.assertIn(os.path.join(fixture_path, 'import_fixture.py'), pl._module_cache)
        self.assertNotIn('/path/to/import_fixture.py', pl._module_cache)
