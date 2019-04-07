# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import sys

from units.compat import unittest
from units.compat.mock import patch, MagicMock

from ansible.module_utils.six.moves import builtins
from ansible.module_utils._text import to_native


import pprint

realimport = builtins.__import__


class TestPostgres(unittest.TestCase):
    def clear_modules(self, mods):
        for mod in mods:
            if mod in sys.modules:
                del sys.modules[mod]

    @patch.object(builtins, '__import__')
    def test_postgres_pg2_missing_ensure_libs(self, mock_import):
        def _mock_import(name, *args, **kwargs):
            if name == 'psycopg2':
                raise ImportError
            return realimport(name, *args, **kwargs)

        self.clear_modules(['psycopg2', 'ansible.module_utils.postgres'])
        mock_import.side_effect = _mock_import
        mod = builtins.__import__('ansible.module_utils.postgres')

        self.assertFalse(mod.module_utils.postgres.HAS_PSYCOPG2)

        with self.assertRaises(mod.module_utils.postgres.LibraryError) as context:
            mod.module_utils.postgres.ensure_libs(sslrootcert=None)
        self.assertIn('psycopg2 is not installed', to_native(context.exception))

    @patch.object(builtins, '__import__')
    def test_postgres_pg2_found_ensure_libs(self, mock_import):
        def _mock_import(name, *args, **kwargs):
            if 'psycopg2' in name:
                return MagicMock()
            return realimport(name, *args, **kwargs)

        self.clear_modules(['psycopg2', 'ansible.module_utils.postgres'])
        mock_import.side_effect = _mock_import
        mod = builtins.__import__('ansible.module_utils.postgres')

        self.assertTrue(mod.module_utils.postgres.HAS_PSYCOPG2)

        ensure_ret = mod.module_utils.postgres.ensure_libs(sslrootcert=None)
        self.assertFalse(ensure_ret)
        pprint.pprint(ensure_ret)

    @patch.object(builtins, '__import__')
    def test_postgres_pg2_found_ensure_libs_old_version(self, mock_import):
        def _mock_import(name, *args, **kwargs):
            if 'psycopg2' in name:
                m = MagicMock()
                m.__version__ = '2.4.1'
                return m
            return realimport(name, *args, **kwargs)

        self.clear_modules(['psycopg2', 'ansible.module_utils.postgres'])
        mock_import.side_effect = _mock_import
        mod = builtins.__import__('ansible.module_utils.postgres')

        self.assertTrue(mod.module_utils.postgres.HAS_PSYCOPG2)

        with self.assertRaises(mod.module_utils.postgres.LibraryError) as context:
            mod.module_utils.postgres.ensure_libs(sslrootcert='yes')
        self.assertIn('psycopg2 must be at least 2.4.3 in order to use', to_native(context.exception))
