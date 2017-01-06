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
from ansible.compat.tests import unittest
from ansible.compat.tests import BUILTINS

from ansible.compat.tests.mock import patch, MagicMock

from ansible.plugins import loader
from ansible.plugins import loaders


# FIXME: Most of these tests don't assert anything yet
# FIXME: These tests are somewhat intrusive and look in default configured module paths
#        and import (and run module scope) code found there.
# TODO: Mock out file access
class BasePluginLoader:
    class_under_test = None

    def setUp(self):
        self.pl = self.class_under_test()

    def test_get_paths(self):
        ret = self.pl._get_paths()
        subdir = self.class_under_test.subdir
        pkg = self.class_under_test.package.split('.')[-1]
        for path in ret:
            if subdir in path or pkg in path:
                continue
            self.fail('The subdir (%s) or pkg string (%s) were not found in path (%s)' %
                      (subdir, pkg, path))

    def test_print_paths(self):
        self.pl.print_paths()
        #print(ret)

    def test_package_paths(self):
        ret = self.pl._get_package_paths()
        self.assertIsInstance(ret, list)

    def test_add_directory(self):
        self.pl.add_directory(os.path.join(os.getcwd(), '../'))
        self.pl._get_paths()

    def test_add_directory_with_subdir(self):
        self.pl.add_directory(os.path.join(os.getcwd(), '../'), with_subdir=True)
        self.pl._get_paths()

    def test_add_directory_doesnt_exit(self):
        self.pl.add_directory('/dev/null/doesnt/exist')
        self.pl._get_paths()

    def test_find_plugin_doesnt_exist(self):
        ret = self.pl.find_plugin('adsfimapoi345tawe478tyzdfgmha478trasdfadf')
        self.assertIsNone(ret)

    def test_find_plugin_alias_doesnt_exist(self):
        ret = self.pl.find_plugin('_adsfimapoi345tawe478tyzdfgmha478trasdfadf')
        self.assertIsNone(ret)

    def test_has_plugin_doesnt_exist(self):
        ret = self.pl.has_plugin('adsfimapoi345tawe478tyzdfgmha478trasdfadf')
        self.assertFalse(ret)

    def test_get_doesnt_exist(self):
        ret = self.pl.get('asf4tascgtatr', ['foo', 'bar'], {})
        self.assertIsNone(ret)

    # Each loader type's .get() will want a different set of args depending on the loader
    # type and the plugin itself, so skip the general case for now.
#    def test_get_debug_might_exist(self):
#        ret = self.pl.get('debug')
#        print(ret)

    def test_all(self):
        ret_iterator = self.pl.all(class_only=True, base_class=self.pl.required_base_class)
        for ret in ret_iterator:
            self.assertIsInstance(ret, type)

    def test_all_path_only(self):
        ret_iterator = self.pl.all(class_only=True, base_class=self.pl.required_base_class,
                                   path_only=True)
        for ret in ret_iterator:
            self.assertIsInstance(ret, str)

    def test_getstate(self):
        self.pl.__getstate__()

    def test_setstate(self):
        state_data = self.pl.__getstate__()
        self.pl.__setstate__(state_data)


class TestPluginInfo(unittest.TestCase):
    def test(self):
        pi = loader.PluginInfo()
        print(pi)

    def test_from_full_path(self):
        pi = loader.PluginInfo.from_full_path(os.getcwd())
        print(pi)


class TestPluginPath(unittest.TestCase):
    def test(self):
        pp = loader.PluginPath()
        print(pp)

    def test_glob(self):
        pp = loader.PluginPath()
        ret = pp.glob('doesnt_matter_yet_*')
        self.assertEquals(ret, [])


class TestPluginPaths(unittest.TestCase):
    def test(self):
        loader.PluginPaths()


class TestCachedPluginPaths(unittest.TestCase):
    def test(self):
        loader.CachedPluginPaths()


class TestChainedPluginPaths(unittest.TestCase):
    def test(self):
        loader.ChainedPluginPaths()


class TestActionLoader(BasePluginLoader, unittest.TestCase):
    class_under_test = loaders.ActionLoader


class TestCacheLoader(BasePluginLoader, unittest.TestCase):
    class_under_test = loaders.CacheLoader


class TestCallbackLoader(BasePluginLoader, unittest.TestCase):
    class_under_test = loaders.CallbackLoader


class TestConnectionLoader(BasePluginLoader, unittest.TestCase):
    class_under_test = loaders.ConnectionLoader


class TestShellLoader(BasePluginLoader, unittest.TestCase):
    class_under_test = loaders.ShellLoader


class TestModuleLoader(BasePluginLoader, unittest.TestCase):
    class_under_test = loaders.ModuleLoader

    def test_all(self):
        # ModuleLoader throws a ton of warnings if we try 'all()' on it
        # FIXME: ModuleLoader needs it's own all() impl so we dont have to un-inherit methods
        pass

    def test_all_path_only(self):
        pass


class TestLookupLoader(BasePluginLoader, unittest.TestCase):
    class_under_test = loaders.LookupLoader


class TestVarsLoader(BasePluginLoader, unittest.TestCase):
    class_under_test = loaders.VarsLoader


class TestFilterLoader(BasePluginLoader, unittest.TestCase):
    class_under_test = loaders.FilterLoader


class TestTestLoader(BasePluginLoader, unittest.TestCase):
    class_under_test = loaders.TestLoader


class TestFragmentLoader(BasePluginLoader, unittest.TestCase):
    class_under_test = loaders.FragmentLoader


class TestStrategyLoader(BasePluginLoader, unittest.TestCase):
    class_under_test = loaders.StrategyLoader


class TestTerminalLoader(BasePluginLoader, unittest.TestCase):
    class_under_test = loaders.TerminalLoader


class TestOldPluginLoader(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_paths(self):
        pl = loader.PluginLoader('ShellModule', 'ansible.plugins.shell', 'shell_plugins', 'shell_plugins')
        pl._get_paths()

    @patch.object(loader.PluginLoader, '_get_paths')
    def test_print_paths(self, mock_method):
        mock_method.return_value = ['/path/one', '/path/two', '/path/three']
        pl = loader.PluginLoader('foo', 'foo', '', 'test_plugins')
        paths = pl.print_paths()
        expected_paths = os.pathsep.join(['/path/one', '/path/two', '/path/three'])
        self.assertEqual(paths, expected_paths)

    def test_plugins__get_package_paths_no_package(self):
        pl = loader.PluginLoader('test', '', 'test', 'test_plugin')
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
        pl = loader.PluginLoader('test', 'foo.bar.bam', 'test', 'test_plugin')
        with patch('{0}.__import__'.format(BUILTINS), foo):
            self.assertEqual(pl._get_package_paths(), ['/path/to/my/foo/bar/bam'])

    def test_plugins__get_paths(self):
        pl = loader.PluginLoader('test', '', 'test', 'test_plugin')
        pl._path_cache = ['/path/one', '/path/two']
        self.assertEqual(pl._get_paths(), ['/path/one', '/path/two'])

        # NOT YET WORKING
        #def fake_glob(path):
        #    if path == 'test/*':
        #        return ['test/foo', 'test/bar', 'test/bam']
        #    elif path == 'test/*/*'
        #m._paths = None
        #mock_glob = MagicMock()
        #mock_glob.return_value = []
        #with patch('glob.glob', mock_glob):
        #    pass

    def assertPluginLoaderConfigBecomes(self, arg, expected):
        pl = loader.PluginLoader('test', '', arg, 'test_plugin')
        self.assertEqual(pl.config, expected)

    def test_plugin__init_config_list(self):
        config = ['/one', '/two']
        self.assertPluginLoaderConfigBecomes(config, config)

    def test_plugin__init_config_str(self):
        self.assertPluginLoaderConfigBecomes('test', ['test'])

    def test_plugin__init_config_none(self):
        self.assertPluginLoaderConfigBecomes(None, [])
