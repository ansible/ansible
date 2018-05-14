# -*- coding: utf-8 -*-

# Copyright (c) 2018, Ansible Project
# Copyright (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.modules.system import launchd
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args
from ansible.compat.tests.mock import patch
from ansible.module_utils import basic


def get_bin_path(*args, **kwargs):
    """Function to return path of launchctl binary."""
    return "/bin/launchctl"


class TestLaunchd(ModuleTestCase):
    """Main class for testing launchd module."""

    def setUp(self):
        """Setup."""
        super(TestLaunchd, self).setUp()
        self.module = launchd
        self.mock_get_bin_path = patch.object(basic.AnsibleModule, 'get_bin_path', get_bin_path)
        self.mock_get_bin_path.start()
        self.addCleanup(self.mock_get_bin_path.stop)  # ensure that the patching is 'undone'

    def tearDown(self):
        """Teardown."""
        super(TestLaunchd, self).tearDown()

    def test_without_required_parameters(self):
        """Failure must occurs when all parameters are missing."""
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            self.module.main()

    def test_start_service(self):
        """Check that result is changed for service start."""
        set_module_args({
            'name': 'com.apple.safaridavclient',
            'state': 'started',
        })

        commands_results = [
            (0, "\n".join(['-	0	com.apple.safaridavclient']), ''),
            (0, '', ''),
            (0, "\n".join(['1200	0	com.apple.safaridavclient']), ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                launchd.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 3)

    def test_start_already_started_service(self):
        """Check that result is not changed for already service start."""
        set_module_args({
            'name': 'com.apple.safaridavclient',
            'state': 'started',
        })

        commands_results = [
            (0, "\n".join(['1200	0	com.apple.safaridavclient']), ''),
            (0, "\n".join(['1200	0	com.apple.safaridavclient']), ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                launchd.main()
                self.assertEqual(result.exception.args[0]['changed'], False)

        self.assertEqual(run_command.call_count, 2)

    def test_start_service_check_mode(self):
        """Check that result is changed in check mode for service start."""
        set_module_args({
            'name': 'com.apple.safaridavclient',
            'state': 'started',
            '_ansible_check_mode': True,
        })

        commands_results = [
            (0, "\n".join(['-	0	com.apple.safaridavclient']), ''),
            (0, "\n".join(['1200	0	com.apple.safaridavclient']), ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                launchd.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 2)

    def test_start_unknown_service(self):
        """Check that result is not changed for unknown service."""
        set_module_args({
            'name': 'blah blah',
            'state': 'started',
        })

        commands_results = [
            (0, '', ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleFailJson) as result:
                launchd.main()
                self.assertFalse(result.exception.args[0]['changed'])
                self.assertEqual(result.exception.args[0]['msg'],
                                 'Unable to find the service blah blah among active services.')

        self.assertEqual(run_command.call_count, 1)

    def test_stop_service(self):
        """Check that result is changed for service stop."""
        set_module_args({
            'name': 'com.apple.safaridavclient',
            'state': 'stopped',
        })

        commands_results = [
            (0, "\n".join(['1200	0	com.apple.safaridavclient']), ''),
            (0, '', ''),
            (0, "\n".join(['-	0	com.apple.safaridavclient']), ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                launchd.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 3)

    def test_stop_already_stopped_service(self):
        """Check that result is not changed for already service stopped."""
        set_module_args({
            'name': 'com.apple.safaridavclient',
            'state': 'stopped',
        })

        commands_results = [
            (0, "\n".join(['-	0	com.apple.safaridavclient']), ''),
            (0, "\n".join(['-	0	com.apple.safaridavclient']), ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                launchd.main()
                self.assertEqual(result.exception.args[0]['changed'], False)

        self.assertEqual(run_command.call_count, 2)

    def test_stop_service_check_mode(self):
        """Check that result is changed in check mode for service stop."""
        set_module_args({
            'name': 'com.apple.safaridavclient',
            'state': 'stopped',
            '_ansible_check_mode': True,
        })

        commands_results = [
            (0, "\n".join(['1200	0	com.apple.safaridavclient']), ''),
            (0, "\n".join(['-	0	com.apple.safaridavclient']), ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                launchd.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 2)

    def test_restart_service(self):
        """Check that result is changed for service restart."""
        set_module_args({
            'name': 'com.apple.safaridavclient',
            'state': 'restarted',
        })

        commands_results = [
            (0, "\n".join(['1200	0	com.apple.safaridavclient']), ''),
            (0, '', ''),
            (0, '', ''),
            (0, "\n".join(['1200	0	com.apple.safaridavclient']), ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                launchd.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 4)

    def test_reloaded_service(self):
        """Check that result is changed for service reloaded."""
        set_module_args({
            'name': 'com.apple.safaridavclient',
            'state': 'reloaded',
        })

        commands_results = [
            (0, "\n".join(['1200	0	com.apple.safaridavclient']), ''),
            (0, '', ''),
            (0, '', ''),
            (0, "\n".join(['1200	0	com.apple.safaridavclient']), ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                launchd.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 4)
