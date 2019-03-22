from ansible.module_utils.source_control.bitbucket import BitbucketHelper
from ansible.modules.source_control.bitbucket import bitbucket_pipeline_key_pair
from units.compat import unittest
from units.compat.mock import patch
from units.modules.utils import AnsibleFailJson, AnsibleExitJson, ModuleTestCase, set_module_args


class TestBucketPipelineKeyPairModule(ModuleTestCase):
    def setUp(self):
        super(TestBucketPipelineKeyPairModule, self).setUp()
        self.module = bitbucket_pipeline_key_pair

    def test_missing_keys_with_present_state(self):
        with self.assertRaises(AnsibleFailJson) as exec_info:
            set_module_args({
                'client_id': 'ABC',
                'client_secret': 'XXX',
                'username': 'name',
                'repository': 'repo',
                'state': 'present',
            })
            self.module.main()

        self.assertEqual(exec_info.exception.args[0]['msg'], self.module.error_messages['required_keys'])

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_key_pair, 'get_existing_ssh_key_pair', return_value=None)
    def test_create_keys(self, *args):
        with patch.object(self.module, 'update_ssh_key_pair') as update_ssh_key_pair_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'public_key': 'public',
                    'private_key': 'PRIVATE',
                    'state': 'present',
                })
                self.module.main()

            self.assertEqual(update_ssh_key_pair_mock.call_count, 1)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_key_pair, 'get_existing_ssh_key_pair', return_value=None)
    def test_create_keys_check_mode(self, *args):
        with patch.object(self.module, 'update_ssh_key_pair') as update_ssh_key_pair_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'public_key': 'public',
                    'private_key': 'PRIVATE',
                    'state': 'present',
                    '_ansible_check_mode': True,
                })
                self.module.main()

            self.assertEqual(update_ssh_key_pair_mock.call_count, 0)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_key_pair, 'get_existing_ssh_key_pair', return_value={
        'public_key': 'unknown',
        'type': 'pipeline_ssh_key_pair',
    })
    def test_update_keys(self, *args):
        with patch.object(self.module, 'update_ssh_key_pair') as update_ssh_key_pair_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'public_key': 'public',
                    'private_key': 'PRIVATE',
                    'state': 'present',
                })
                self.module.main()

            self.assertEqual(update_ssh_key_pair_mock.call_count, 1)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_key_pair, 'get_existing_ssh_key_pair', return_value={
        'public_key': 'public',
        'type': 'pipeline_ssh_key_pair',
    })
    def test_dont_update_same_key(self, *args):
        with patch.object(self.module, 'update_ssh_key_pair') as update_ssh_key_pair_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'public_key': 'public',
                    'private_key': 'PRIVATE',
                    'state': 'present',
                })
                self.module.main()

            self.assertEqual(update_ssh_key_pair_mock.call_count, 0)
            self.assertEqual(exec_info.exception.args[0]['changed'], False)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_key_pair, 'get_existing_ssh_key_pair', return_value={
        'public_key': 'unknown',
        'type': 'pipeline_ssh_key_pair',
    })
    def test_update_keys_check_mode(self, *args):
        with patch.object(self.module, 'update_ssh_key_pair') as update_ssh_key_pair_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'public_key': 'public',
                    'private_key': 'PRIVATE',
                    'state': 'present',
                    '_ansible_check_mode': True,
                })
                self.module.main()

            self.assertEqual(update_ssh_key_pair_mock.call_count, 0)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_key_pair, 'get_existing_ssh_key_pair', return_value={
        'public_key': 'public',
        'type': 'pipeline_ssh_key_pair',
    })
    def test_delete_keys(self, *args):
        with patch.object(self.module, 'delete_ssh_key_pair') as delete_ssh_key_pair_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'state': 'absent',
                })
                self.module.main()

            self.assertEqual(delete_ssh_key_pair_mock.call_count, 1)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_key_pair, 'get_existing_ssh_key_pair', return_value=None)
    def test_delete_absent_keys(self, *args):
        with patch.object(self.module, 'delete_ssh_key_pair') as delete_ssh_key_pair_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'state': 'absent',
                })
                self.module.main()

            self.assertEqual(delete_ssh_key_pair_mock.call_count, 0)
            self.assertEqual(exec_info.exception.args[0]['changed'], False)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_key_pair, 'get_existing_ssh_key_pair', return_value={
        'public_key': 'public',
        'type': 'pipeline_ssh_key_pair',
    })
    def test_delete_keys_check_mode(self, *args):
        with patch.object(self.module, 'delete_ssh_key_pair') as delete_ssh_key_pair_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'state': 'absent',
                    '_ansible_check_mode': True,
                })
                self.module.main()

            self.assertEqual(delete_ssh_key_pair_mock.call_count, 0)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)


if __name__ == '__main__':
    unittest.main()
