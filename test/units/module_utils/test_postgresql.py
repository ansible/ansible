import json
import sys

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock

from ansible.module_utils import basic
from ansible.module_utils.six.moves import builtins
from ansible.module_utils._text import to_native, to_bytes
from units.mock.procenv import swap_stdin_and_argv


import pprint

realimport = builtins.__import__


class MockCursor(object):
    def execute(self, query, vars=None):
        return query


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
        self.assertFalse(mod.module_utils.postgres.HAS_PSYCOPG2_QUOTE_IDENT)

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
        self.assertTrue(mod.module_utils.postgres.HAS_PSYCOPG2_QUOTE_IDENT)

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

    @patch.object(builtins, '__import__')
    def test_escape_identifier_cursor(self, mock_import):
        self._psycopg2_mock = MagicMock()
        self._psycopg2_mock.__version__ = '2.4.1'
        self._psycopg2_mock.quote_ident.return_value = 'quote_ident'

        def _mock_import(name, *args, **kwargs):
            if 'psycopg2' in name:
                return self._psycopg2_mock
            return realimport(name, *args, **kwargs)

        # module.warning required needed for escape_identifier_cursor
        args = json.dumps({'ANSIBLE_MODULE_ARGS': {}})
        basic._ANSIBLE_ARGS = to_bytes(args)
        module = basic.AnsibleModule({})

        self.clear_modules(['psycopg2.extras', 'psycopg2.extensions', 'psycopg2', 'ansible.module_utils.postgres'])
        mock_import.side_effect = _mock_import
        mod = builtins.__import__('ansible.module_utils.postgres')

        klass = mod.module_utils.postgres.escape_identifier_cursor(module, MockCursor)
        cursor = klass()

        with patch.object(cursor, 'escape_identifier', return_value='escape_identifier',
                          autospec=True) as mock_escape_identifier:

            mod.module_utils.postgres.HAS_PSYCOPG2 = True
            mod.module_utils.postgres.HAS_LIBPQ_QUOTE_IDENT = False
            mod.module_utils.postgres.HAS_PSYCOPG2_QUOTE_IDENT = False
            ret = cursor.execute('select * from ${table}', identifiers={'table': 'users'})
            self.assertEqual(self._psycopg2_mock.quote_ident.call_count, 0)
            self.assertEqual(mock_escape_identifier.call_count, 0)
            self.assertEqual(mock_escape_identifier.call_count, 0)
            self.assertEqual(ret, 'select * from %(table)s')

            mod.module_utils.postgres.HAS_PSYCOPG2 = True
            mod.module_utils.postgres.HAS_LIBPQ_QUOTE_IDENT = True
            mod.module_utils.postgres.HAS_PSYCOPG2_QUOTE_IDENT = True
            ret = cursor.execute('select * from ${table}', identifiers={'table': 'users'})
            self.assertEqual(self._psycopg2_mock.quote_ident.call_count, 1)
            self.assertEqual(mock_escape_identifier.call_count, 0)
            self.assertEqual(ret, 'select * from quote_ident')

            mod.module_utils.postgres.HAS_PSYCOPG2 = True
            mod.module_utils.postgres.HAS_PSYCOPG2_QUOTE_IDENT = False
            mod.module_utils.postgres.HAS_LIBPQ_QUOTE_IDENT = True
            ret = cursor.execute('select * from ${table}', identifiers={'table': 'users'})
            self.assertEqual(self._psycopg2_mock.quote_ident.call_count, 1)
            self.assertEqual(mock_escape_identifier.call_count, 1)
            self.assertEqual(ret, 'select * from escape_identifier')
