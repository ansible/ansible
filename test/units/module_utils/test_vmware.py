# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import sys

from units.compat import unittest
from units.compat.mock import patch, MagicMock

from ansible.module_utils.six.moves import builtins
from ansible.module_utils._text import to_native

realimport = builtins.__import__


class TestVmware(unittest.TestCase):
    def clear_modules(self, mods):
        for mod in mods:
            if mod in sys.modules:
                del sys.modules[mod]

    @patch.object(builtins, '__import__')
    def test_vmware_missing_ensure_libs(self, mock_import):
        def _mock_import(name, *args, **kwargs):
            if name in ('pyVmomi', 'requests'):
                raise ImportError
            return realimport(name, *args, **kwargs)

        self.clear_modules(['pyVmomi', 'ansible.module_utils.vmware', 'requests'])
        mock_import.side_effect = _mock_import
        mod = builtins.__import__('ansible.module_utils.vmware')

        self.assertFalse(mod.module_utils.vmware.HAS_PYVMOMI)
        self.assertFalse(mod.module_utils.vmware.HAS_REQUESTS)

        with self.assertRaises(NameError) as context:
            mod.module_utils.vmware.PyVmomi(MagicMock())

        self.assertIn("name 'vim' is not defined", to_native(context.exception))

    @patch.object(builtins, '__import__')
    def test_vmware_found_ensure_libs(self, mock_import):
        def _mock_import(name, *args, **kwargs):
            if 'pyVmomi' in name:
                return MagicMock()
            return realimport(name, *args, **kwargs)

        self.clear_modules(['pyVmomi', 'ansible.module_utils.vmware', 'requests'])
        mock_import.side_effect = _mock_import
        mod = builtins.__import__('ansible.module_utils.vmware')

        self.assertTrue(mod.module_utils.vmware.HAS_PYVMOMI)
        self.assertTrue(mod.module_utils.vmware.HAS_REQUESTS)
