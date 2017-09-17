from ansible.compat.tests import mock
from ansible.compat.tests import unittest
from ansible.modules.packaging.os import opkg


class TestOpkgInstall(unittest.TestCase):

    def setUp(self):
        self.module_names = [
            'bash',
            'g++',
        ]

    @mock.patch('ansible.modules.packaging.os.opkg.AnsibleModule')
    def test_already_installed(self, mock_module):
        for module_name in self.module_names:
            command_output = module_name + '-2.0.0-r1 < 3.0.0-r2 '
            mock_module.run_command.return_value = (0, command_output, None)
            command_result = opkg.is_installed(mock_module, module_name)
            self.assertTrue(command_result)

    @mock.patch('ansible.modules.packaging.os.opkg.AnsibleModule')
    def test_get_opkg_path(self, mock_module):
        for module_name in self.module_names:
            mock_module.run_command.return_value = (0, "", None)
            mock_module.get_bin_path.return_value = "/bin/opkg"
            command_result = opkg.is_installed(mock_module, module_name)
            self.assertTrue(command_result)
