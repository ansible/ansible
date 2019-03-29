from ansible.module_utils.source_control.bitbucket import BitbucketHelper
from ansible.modules.source_control.bitbucket import bitbucket_pipeline_variable
from units.compat import unittest
from units.compat.mock import patch
from units.modules.utils import AnsibleFailJson, AnsibleExitJson, ModuleTestCase, set_module_args


class TestBucketPipelineVariableModule(ModuleTestCase):
    def setUp(self):
        super(TestBucketPipelineVariableModule, self).setUp()
        self.module = bitbucket_pipeline_variable

    def test_without_required_parameters(self):
        with self.assertRaises(AnsibleFailJson) as exec_info:
            set_module_args({
                'username': 'name',
                'repository': 'repo',
                'name': 'PIPELINE_VAR_NAME',
                'state': 'absent',
            })
            self.module.main()

        self.assertEqual(exec_info.exception.args[0]['msg'], BitbucketHelper.error_messages['required_client_id'])

    def test_missing_value_with_present_state(self):
        with self.assertRaises(AnsibleFailJson) as exec_info:
            set_module_args({
                'client_id': 'ABC',
                'client_secret': 'XXX',
                'username': 'name',
                'repository': 'repo',
                'name': 'PIPELINE_VAR_NAME',
                'state': 'present',
            })
            self.module.main()

        self.assertEqual(exec_info.exception.args[0]['msg'], self.module.error_messages['required_value'])

    @patch.dict('os.environ', {
        'BITBUCKET_CLIENT_ID': 'ABC',
        'BITBUCKET_CLIENT_SECRET': 'XXX',
    })
    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_variable, 'get_existing_pipeline_variable', return_value=None)
    def test_env_vars_params(self, *args):
        with self.assertRaises(AnsibleExitJson):
            set_module_args({
                'username': 'name',
                'repository': 'repo',
                'name': 'PIPELINE_VAR_NAME',
                'state': 'absent',
            })
            self.module.main()

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_variable, 'get_existing_pipeline_variable', return_value=None)
    def test_create_variable(self, *args):
        with patch.object(self.module, 'create_pipeline_variable') as create_pipeline_variable_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'name': 'PIPELINE_VAR_NAME',
                    'value': '42',
                    'state': 'present',
                })
                self.module.main()

            self.assertEqual(create_pipeline_variable_mock.call_count, 1)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_variable, 'get_existing_pipeline_variable', return_value=None)
    def test_create_variable_check_mode(self, *args):
        with patch.object(self.module, 'create_pipeline_variable') as create_pipeline_variable_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'name': 'PIPELINE_VAR_NAME',
                    'value': '42',
                    'state': 'present',
                    '_ansible_check_mode': True,
                })
                self.module.main()

            self.assertEqual(create_pipeline_variable_mock.call_count, 0)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_variable, 'get_existing_pipeline_variable', return_value={
        'name': 'PIPELINE_VAR_NAME',
        'value': 'Im alive',
        'type': 'pipeline_variable',
        'secured': False,
        'uuid': '{9ddb0507-439a-495a- 99f3 - 564f15138127}'
    })
    def test_update_variable(self, *args):
        with patch.object(self.module, 'update_pipeline_variable') as update_pipeline_variable_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'name': 'PIPELINE_VAR_NAME',
                    'value': '42',
                    'state': 'present',
                })
                self.module.main()

            self.assertEqual(update_pipeline_variable_mock.call_count, 1)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_variable, 'get_existing_pipeline_variable', return_value={
        'name': 'PIPELINE_VAR_NAME',
        'type': 'pipeline_variable',
        'secured': True,
        'uuid': '{9ddb0507-439a-495a- 99f3 - 564f15138127}'
    })
    def test_update_secured_variable(self, *args):
        with patch.object(self.module, 'update_pipeline_variable') as update_pipeline_variable_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'name': 'PIPELINE_VAR_NAME',
                    'value': '42',
                    'secured': True,
                    'state': 'present',
                })
                self.module.main()

            self.assertEqual(update_pipeline_variable_mock.call_count, 1)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_variable, 'get_existing_pipeline_variable', return_value={
        'name': 'PIPELINE_VAR_NAME',
        'value': '42',
        'type': 'pipeline_variable',
        'secured': False,
        'uuid': '{9ddb0507-439a-495a- 99f3 - 564f15138127}'
    })
    def test_update_secured_state(self, *args):
        with patch.object(self.module, 'update_pipeline_variable') as update_pipeline_variable_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'name': 'PIPELINE_VAR_NAME',
                    'value': '42',
                    'secured': True,
                    'state': 'present',
                })
                self.module.main()

            self.assertEqual(update_pipeline_variable_mock.call_count, 1)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_variable, 'get_existing_pipeline_variable', return_value={
        'name': 'PIPELINE_VAR_NAME',
        'value': '42',
        'type': 'pipeline_variable',
        'secured': False,
        'uuid': '{9ddb0507-439a-495a- 99f3 - 564f15138127}'
    })
    def test_dont_update_same_value(self, *args):
        with patch.object(self.module, 'update_pipeline_variable') as update_pipeline_variable_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'name': 'PIPELINE_VAR_NAME',
                    'value': '42',
                    'state': 'present',
                })
                self.module.main()

            self.assertEqual(update_pipeline_variable_mock.call_count, 0)
            self.assertEqual(exec_info.exception.args[0]['changed'], False)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_variable, 'get_existing_pipeline_variable', return_value={
        'name': 'PIPELINE_VAR_NAME',
        'value': 'Im alive',
        'type': 'pipeline_variable',
        'secured': False,
        'uuid': '{9ddb0507-439a-495a- 99f3 - 564f15138127}'
    })
    def test_update_variable_check_mode(self, *args):
        with patch.object(self.module, 'update_pipeline_variable') as update_pipeline_variable_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'name': 'PIPELINE_VAR_NAME',
                    'value': '42',
                    'state': 'present',
                    '_ansible_check_mode': True,
                })
                self.module.main()

            self.assertEqual(update_pipeline_variable_mock.call_count, 0)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_variable, 'get_existing_pipeline_variable', return_value={
        'name': 'PIPELINE_VAR_NAME',
        'value': 'Im alive',
        'type': 'pipeline_variable',
        'secured': False,
        'uuid': '{9ddb0507-439a-495a- 99f3 - 564f15138127}'
    })
    def test_delete_variable(self, *args):
        with patch.object(self.module, 'delete_pipeline_variable') as delete_pipeline_variable_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'name': 'PIPELINE_VAR_NAME',
                    'state': 'absent',
                })
                self.module.main()

            self.assertEqual(delete_pipeline_variable_mock.call_count, 1)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_variable, 'get_existing_pipeline_variable', return_value=None)
    def test_delete_absent_variable(self, *args):
        with patch.object(self.module, 'delete_pipeline_variable') as delete_pipeline_variable_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'name': 'PIPELINE_VAR_NAME',
                    'state': 'absent',
                })
                self.module.main()

            self.assertEqual(delete_pipeline_variable_mock.call_count, 0)
            self.assertEqual(exec_info.exception.args[0]['changed'], False)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_variable, 'get_existing_pipeline_variable', return_value={
        'name': 'PIPELINE_VAR_NAME',
        'value': 'Im alive',
        'type': 'pipeline_variable',
        'secured': False,
        'uuid': '{9ddb0507-439a-495a- 99f3 - 564f15138127}'
    })
    def test_delete_variable_check_mode(self, *args):
        with patch.object(self.module, 'delete_pipeline_variable') as delete_pipeline_variable_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'name': 'PIPELINE_VAR_NAME',
                    'state': 'absent',
                    '_ansible_check_mode': True,
                })
                self.module.main()

            self.assertEqual(delete_pipeline_variable_mock.call_count, 0)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)


if __name__ == '__main__':
    unittest.main()
