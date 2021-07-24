
from units.mock.procenv import ModuleTestCase

from units.compat.mock import patch

import sys

class TestGetUsername(ModuleTestCase):
    def test_module_utils_basic_get_username(self):
        from ansible.module_utils.basic import get_username

        with patch('os.getuid', return_value=(0)):
            self.assertEqual(get_username(), 'root')

        with patch('os.getuid', return_value=sys.maxsize):
            self.assertEqual(get_username(), f"uid={sys.maxsize}")
