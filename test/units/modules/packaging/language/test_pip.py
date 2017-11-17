import json

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch
from ansible.module_utils import basic

from ansible.modules.packaging.language import pip

from units.modules.utils import set_module_args, AnsibleFailJson, ModuleTestCase


class TestPip(ModuleTestCase):
    def setUp(self):
        super(TestPip, self).setUp()

    @patch.object(basic.AnsibleModule, 'get_bin_path')
    def test_failure_when_pip_absent(self, mock_get_bin_path):

        mock_get_bin_path.return_value = None

        with self.assertRaises(AnsibleFailJson):
            set_module_args({'name': 'six'})
            pip.main()
