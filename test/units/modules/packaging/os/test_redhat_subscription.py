# (c) 2018, Sean Myers <sean.myers@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import call, patch
from ansible.modules.packaging.os import redhat_subscription

from units.modules.utils import (AnsibleExitJson, ModuleTestCase, set_module_args)


class RedHatSubscriptionModuleTestCase(ModuleTestCase):
    module = redhat_subscription

    def setUp(self):
        super(RedHatSubscriptionModuleTestCase, self).setUp()

        # Mainly interested that the subscription-manager calls are right
        # based on the module args, so patch out run_command in the module.
        # returns (rc, out, err) structure
        self.mock_run_command = patch('ansible.modules.packaging.os.redhat_subscription.'
                                      'AnsibleModule.run_command')
        self.module_main_command = self.mock_run_command.start()

        # Module does a get_bin_path check before every run_command call
        self.mock_get_bin_path = patch('ansible.modules.packaging.os.redhat_subscription.'
                                       'AnsibleModule.get_bin_path')
        self.get_bin_path = self.mock_get_bin_path.start()
        self.get_bin_path.return_value = '/testbin/subscription-manager'

        self.mock_redhat_repo = patch('ansible.modules.packaging.os.redhat_subscription.RegistrationBase.REDHAT_REPO')
        self.redhat_repo = self.mock_redhat_repo.start()

        self.mock_is_file = patch('os.path.isfile', return_value=False)
        self.is_file = self.mock_is_file.start()

        self.mock_unlink = patch('os.unlink', return_value=True)
        self.unlink = self.mock_unlink.start()

    def tearDown(self):
        self.mock_run_command.stop()
        self.mock_get_bin_path.stop()
        super(RedHatSubscriptionModuleTestCase, self).tearDown()

    def module_main(self, exit_exc):
        with self.assertRaises(exit_exc) as exc:
            self.module.main()
        return exc.exception.args[0]

    def test_already_registered_system(self):
        """
        Test what happens, when the system is already registered
        """
        set_module_args(
            {
                'state': 'present',
                'server_hostname': 'subscription.rhsm.redhat.com',
                'username': 'admin',
                'password': 'admin',
                'org_id': 'admin'
            })
        self.module_main_command.side_effect = [
            # first call "identity" returns 0. It means that system is regisetred.
            (0, '', ''),
        ]

        result = self.module_main(AnsibleExitJson)

        self.assertFalse(result['changed'])
        self.module_main_command.assert_has_calls([
            call(['/testbin/subscription-manager', 'identity'], check_rc=False),
        ])

    def test_registeration_of_system(self):
        """
        Test registration using username and password
        """
        set_module_args(
            {
                'state': 'present',
                'server_hostname': 'subscription.rhsm.redhat.com',
                'username': 'admin',
                'password': 'admin',
                'org_id': 'admin'
            })
        self.module_main_command.side_effect = [
            # First call: "identity" returns 1. It means that system is not registered.
            (1, 'This system is not yet registered.', ''),
            # Second call: "config" server hostname
            (0, '', ''),
            # Third call: "register"
            (0, '', ''),
        ]

        result = self.module_main(AnsibleExitJson)

        self.assertTrue(result['changed'])
        self.module_main_command.assert_has_calls([
            call(
                [
                    '/testbin/subscription-manager',
                    'identity'
                ], check_rc=False),
            call(
                [
                    '/testbin/subscription-manager',
                    'config',
                    '--server.hostname=subscription.rhsm.redhat.com'
                ], check_rc=True),
            call(
                [
                    '/testbin/subscription-manager',
                    'register',
                    '--serverurl', 'subscription.rhsm.redhat.com',
                    '--org', 'admin',
                    '--username', 'admin',
                    '--password', 'admin'
                ], check_rc=True, expand_user_and_vars=False)
        ])
