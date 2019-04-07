# -*- coding: utf-8 -*-

# Copyright (c) 2018, Ansible Project
# Copyright (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.modules.monitoring import icinga2_feature
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args
from units.compat.mock import patch
from ansible.module_utils import basic


def get_bin_path(*args, **kwargs):
    """Function to return path of icinga2 binary."""
    return "/bin/icinga2"


class TestIcinga2Feature(ModuleTestCase):
    """Main class for testing icinga2_feature module."""

    def setUp(self):
        """Setup."""
        super(TestIcinga2Feature, self).setUp()
        self.module = icinga2_feature
        self.mock_get_bin_path = patch.object(basic.AnsibleModule, 'get_bin_path', get_bin_path)
        self.mock_get_bin_path.start()
        self.addCleanup(self.mock_get_bin_path.stop)  # ensure that the patching is 'undone'

    def tearDown(self):
        """Teardown."""
        super(TestIcinga2Feature, self).tearDown()

    def test_without_required_parameters(self):
        """Failure must occurs when all parameters are missing."""
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            self.module.main()

    def test_enable_feature(self):
        """Check that result is changed."""
        set_module_args({
            'name': 'api',
        })
        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.return_value = 0, '', ''  # successful execution, no output
            with self.assertRaises(AnsibleExitJson) as result:
                icinga2_feature.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 2)
        self.assertEqual(run_command.call_args[0][0][-1], 'api')

    def test_enable_feature_with_check_mode(self):
        """Check that result is changed in check mode."""
        set_module_args({
            'name': 'api',
            '_ansible_check_mode': True,
        })
        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.return_value = 0, '', ''  # successful execution, no output
            with self.assertRaises(AnsibleExitJson) as result:
                icinga2_feature.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 1)

    def test_disable_feature(self):
        """Check that result is changed."""
        set_module_args({
            'name': 'api',
            'state': 'absent'
        })
        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.return_value = 0, '', ''  # successful execution, no output
            with self.assertRaises(AnsibleExitJson) as result:
                icinga2_feature.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 2)
        self.assertEqual(run_command.call_args[0][0][-1], 'api')

    def test_disable_feature_with_check_mode(self):
        """Check that result is changed in check mode."""
        set_module_args({
            'name': 'api',
            'state': 'absent',
            '_ansible_check_mode': True,
        })
        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.return_value = 0, '', ''  # successful execution, no output
            with self.assertRaises(AnsibleExitJson) as result:
                icinga2_feature.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 1)
