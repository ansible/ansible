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

from ansible.compat.tests.mock import mock_open, patch, MagicMock

from ansible.plugins import MODULE_CACHE, PATH_CACHE, PLUGIN_PATH_CACHE, PluginLoader

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
        m = MagicMock()
        m.return_value.__file__ = '/path/to/my/test.py'
        pl = PluginLoader('test', 'foo.bar.bam', 'test', 'test_plugin')
        with patch('{0}.__import__'.format(BUILTINS), m):
            self.assertEqual(pl._get_package_paths(), ['/path/to/my/bar/bam'])

    def test_plugins__get_paths(self):
        pl = PluginLoader('test', '', 'test', 'test_plugin')
        pl._paths = ['/path/one', '/path/two']
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

