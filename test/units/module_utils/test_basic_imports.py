
import json
import logging
import sys

from units.mock.procenv import swap_stdin_and_argv

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, Mock

log = logging.getLogger(__name__)

realimport = __import__


class TestModuleUtilsBasicImporting(unittest.TestCase):
    builtin_import_name = '__builtin__.__import__'

    def setUp(self):
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={}))
        # unittest doesn't have a clean place to use a context manager, so we have to enter/exit manually
        self.stdin_swap = swap_stdin_and_argv(stdin_data=args)
        self.stdin_swap.__enter__()
        self._imports_before = []
        self._wrapped_imports = []
        self.mods_to_fail = []
        self.mods_to_fake = []
        self.clear_basic()

    def tearDown(self):
        # unittest doesn't have a clean place to use a context manager, so we have to enter/exit manually
        self.stdin_swap.__exit__(None, None, None)
        self.clear_modules(self._wrapped_imports)
        self._wrapped_imports = []
        self.mods_to_fail = []
        self.mods_to_fake = []
        self.clear_basic()

    def clear_modules(self, mods):
        for mod in mods:
            if mod in sys.modules or mod in self.mods_to_fake:
                del sys.modules[mod]

    def clear_basic(self):
        return self.clear_modules(['ansible.module_utils.basic'])

    def _import_wrapper(self, name, *args, **kwargs):
        if name not in sys.modules:
            self._wrapped_imports.append(name)

        return realimport(name, *args, **kwargs)

    def _mock_import(self, name, *args, **kwargs):
        if name in self.mods_to_fail:
            raise ImportError
        if name in self.mods_to_fake:
            mock_module = Mock()
            return mock_module
        return self._import_wrapper(name, *args, **kwargs)

    @patch('__builtin__.__import__')
    def test_import_syslog_has_syslog(self, mock_import):
        mock_import.side_effect = self._mock_import
        self.mods_to_fake = ['syslog']

        import ansible.module_utils.basic as mod
        self.assertTrue(mod.HAS_SYSLOG)

    @patch('__builtin__.__import__')
    def test_import_syslog_no_syslog(self, mock_import):
        mock_import.side_effect = self._mock_import
        self.mods_to_fail = ['syslog']

        import ansible.module_utils.basic as mod
        self.assertFalse(mod.HAS_SYSLOG)

    @patch('__builtin__.__import__')
    def test_import_selinux_has_selinux(self, mock_import):
        # if not HAS_SELINUX:
        #    raise SkipTest('No selinux module to tests import of')
        self.mods_to_fake = ['selinux']

        mock_import.side_effect = self._mock_import

        import ansible.module_utils.basic as mod
        self.assertTrue(mod.HAVE_SELINUX)

    @patch('__builtin__.__import__')
    def test_import_selinux_no_selinux(self, mock_import):
        mock_import.side_effect = self._mock_import
        self.mods_to_fail = ["selinux"]

        import ansible.module_utils.basic as mod
        self.assertFalse(mod.HAVE_SELINUX)

    @patch('__builtin__.__import__')
    def test_import_json_has_json(self, mock_import):
        mock_import.side_effect = self._mock_import

        import ansible.module_utils.basic as mod
        self.assertTrue(hasattr(mod, 'json'))

    @patch('__builtin__.__import__')
    def test_import_json_no_json(self, mock_import):
        mock_import.side_effect = self._mock_import
        self.mods_to_fail = ['json']

        try:
            import ansible.module_utils.basic
            self.assertTrue(ansible.module_utils.basic is not None)
        except SystemExit as e:
            log.debug(e)

    @patch('__builtin__.__import__')
    @unittest.skipIf(sys.version_info[0] >= 3, "literal_eval is available in every version of Python3")
    def test_import_literal_eval(self, mock_import):
        def _mock_import(name, *args, **kwargs):
            try:
                fromlist = kwargs.get('fromlist', args[2])
            except IndexError:
                fromlist = []
            if name == 'ast' and 'literal_eval' in fromlist:
                raise ImportError
            log.debug('name=%s', name)
            return self._import_wrapper(name, *args, **kwargs)

        mock_import.side_effect = _mock_import
        import ansible.module_utils.basic as mod

        # TODO: move tests of literal_eval to a different test class
        self.assertEqual(mod.literal_eval("'1'"), "1")
        self.assertEqual(mod.literal_eval("1"), 1)
        self.assertEqual(mod.literal_eval("-1"), -1)
        self.assertRaises(ValueError, mod.literal_eval, "asdfasdfasdf")
        self.assertEqual(mod.literal_eval("(1,2,3)"), (1,2,3))
        self.assertEqual(mod.literal_eval("[1]"), [1])
        self.assertEqual(mod.literal_eval("True"), True)
        self.assertEqual(mod.literal_eval("False"), False)
        self.assertEqual(mod.literal_eval("None"), None)
        # self.assertEqual(mod.module_utils.basic.literal_eval('{"a": 1}'), dict(a=1))

    @patch('__builtin__.__import__')
    def test_import_has_systemd_journal(self, mock_import):
        mock_import.side_effect = self._mock_import
        self.mods_to_fake = ['systemd', 'systemd.journal']
        import ansible.module_utils.basic as mod
        self.assertTrue(mod.has_journal)

    @patch('__builtin__.__import__')
    def test_import_no_systemd_journal(self, mock_import):
        mock_import.side_effect = self._mock_import
        self.mods_to_fail = ['systemd']

        import ansible.module_utils.basic as mod
        self.assertFalse(mod.has_journal)
