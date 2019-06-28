import pytest

from ansible.module_utils.source_control.bitbucket import BitbucketHelper
from ansible.modules.source_control.bitbucket import bitbucket_pipeline_known_host
from ansible.modules.source_control.bitbucket.bitbucket_pipeline_known_host import HAS_PARAMIKO
from units.compat import unittest
from units.compat.mock import patch
from units.modules.utils import AnsibleExitJson, ModuleTestCase, set_module_args


class TestBucketPipelineKnownHostModule(ModuleTestCase):
    def setUp(self):
        super(TestBucketPipelineKnownHostModule, self).setUp()
        self.module = bitbucket_pipeline_known_host

    @pytest.mark.skipif(not HAS_PARAMIKO, reason='paramiko must be installed to test key creation')
    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_known_host, 'get_existing_known_host', return_value=None)
    def test_create_known_host(self, *args):
        with patch.object(self.module, 'create_known_host') as create_known_host_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'name': 'bitbucket.org',
                    'state': 'present',
                })
                self.module.main()

            self.assertEqual(create_known_host_mock.call_count, 1)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(BitbucketHelper, 'request', return_value=(dict(status=201), dict()))
    @patch.object(bitbucket_pipeline_known_host, 'get_existing_known_host', return_value=None)
    def test_create_known_host_with_key(self, *args):
        with patch.object(self.module, 'get_host_key') as get_host_key_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'name': 'bitbucket.org',
                    'key': 'ssh-rsa public',
                    'state': 'present',
                })
                self.module.main()

            self.assertEqual(get_host_key_mock.call_count, 0)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @pytest.mark.skipif(not HAS_PARAMIKO, reason='paramiko must be installed to test key creation')
    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_known_host, 'get_existing_known_host', return_value={
        'type': 'pipeline_known_host',
        'uuid': '{21cc0590-bebe-4fae-8baf-03722704119a7}',
        'hostname': 'bitbucket.org',
        'public_key': {
            'type': 'pipeline_ssh_public_key',
            'md5_fingerprint': 'md5:97:8c:1b:f2:6f:14:6b:4b:3b:ec:aa:46:46:74:7c:40',
            'sha256_fingerprint': 'SHA256:zzXQOXSFBEiUtuE8AikoYKwbHaxvSc0ojez9YXaGp1A',
            'key_type': 'ssh-rsa',
            'key': 'AAAAB3NzaC1yc2EAAAABIwAAAQEAubiN81eDcafrgMeLzaFPsw2kN...seeFVBoGqzHM9yXw=='
        }
    })
    def test_dont_create_same_value(self, *args):
        with patch.object(self.module, 'create_known_host') as create_known_host_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'name': 'bitbucket.org',
                    'state': 'present',
                })
                self.module.main()

            self.assertEqual(create_known_host_mock.call_count, 0)
            self.assertEqual(exec_info.exception.args[0]['changed'], False)

    @pytest.mark.skipif(not HAS_PARAMIKO, reason='paramiko must be installed to test key creation')
    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_known_host, 'get_existing_known_host', return_value=None)
    def test_create_known_host_check_mode(self, *args):
        with patch.object(self.module, 'create_known_host') as create_known_host_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'name': 'bitbucket.org',
                    'state': 'present',
                    '_ansible_check_mode': True,
                })
                self.module.main()

            self.assertEqual(create_known_host_mock.call_count, 0)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @pytest.mark.skipif(not HAS_PARAMIKO, reason='paramiko must be installed to test key creation')
    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_known_host, 'get_existing_known_host', return_value={
        'type': 'pipeline_known_host',
        'uuid': '{21cc0590-bebe-4fae-8baf-03722704119a7}',
        'hostname': 'bitbucket.org',
        'public_key': {
            'type': 'pipeline_ssh_public_key',
            'md5_fingerprint': 'md5:97:8c:1b:f2:6f:14:6b:4b:3b:ec:aa:46:46:74:7c:40',
            'sha256_fingerprint': 'SHA256:zzXQOXSFBEiUtuE8AikoYKwbHaxvSc0ojez9YXaGp1A',
            'key_type': 'ssh-rsa',
            'key': 'AAAAB3NzaC1yc2EAAAABIwAAAQEAubiN81eDcafrgMeLzaFPsw2kN...seeFVBoGqzHM9yXw=='
        }
    })
    def test_delete_known_host(self, *args):
        with patch.object(self.module, 'delete_known_host') as delete_known_host_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'name': 'bitbucket.org',
                    'state': 'absent',
                })
                self.module.main()

            self.assertEqual(delete_known_host_mock.call_count, 1)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @pytest.mark.skipif(not HAS_PARAMIKO, reason='paramiko must be installed to test key creation')
    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_known_host, 'get_existing_known_host', return_value=None)
    def test_delete_absent_known_host(self, *args):
        with patch.object(self.module, 'delete_known_host') as delete_known_host_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'name': 'bitbucket.org',
                    'state': 'absent',
                })
                self.module.main()

            self.assertEqual(delete_known_host_mock.call_count, 0)
            self.assertEqual(exec_info.exception.args[0]['changed'], False)

    @pytest.mark.skipif(not HAS_PARAMIKO, reason='paramiko must be installed to test key creation')
    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_pipeline_known_host, 'get_existing_known_host', return_value={
        'type': 'pipeline_known_host',
        'uuid': '{21cc0590-bebe-4fae-8baf-03722704119a7}',
        'hostname': 'bitbucket.org',
        'public_key': {
            'type': 'pipeline_ssh_public_key',
            'md5_fingerprint': 'md5:97:8c:1b:f2:6f:14:6b:4b:3b:ec:aa:46:46:74:7c:40',
            'sha256_fingerprint': 'SHA256:zzXQOXSFBEiUtuE8AikoYKwbHaxvSc0ojez9YXaGp1A',
            'key_type': 'ssh-rsa',
            'key': 'AAAAB3NzaC1yc2EAAAABIwAAAQEAubiN81eDcafrgMeLzaFPsw2kN...seeFVBoGqzHM9yXw=='
        }
    })
    def test_delete_known_host_check_mode(self, *args):
        with patch.object(self.module, 'delete_known_host') as delete_known_host_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'name': 'bitbucket.org',
                    'state': 'absent',
                    '_ansible_check_mode': True,
                })
                self.module.main()

            self.assertEqual(delete_known_host_mock.call_count, 0)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)


if __name__ == '__main__':
    unittest.main()
