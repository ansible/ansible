import json

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch
from ansible.module_utils import basic

from ansible.modules.packaging.language import pip

from ..utils import (set_module_args, AnsibleFailJson, exit_json, fail_json)


class TestPip(unittest.TestCase):

    def setUp(self):
        self.mock_ansible_module = patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)
        self.mock_ansible_module.start()
        self.addCleanup(self.mock_ansible_module.stop)

    @patch.object(basic.AnsibleModule, 'get_bin_path')
    def test_failure_when_pip_absent(self, mock_get_bin_path):

        mock_get_bin_path.return_value = None

        with self.assertRaises(AnsibleFailJson):
            set_module_args({'name': 'six'})
            pip.main()
