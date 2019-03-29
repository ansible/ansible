from ansible.module_utils.source_control.bitbucket import BitbucketHelper
from ansible.modules.source_control.bitbucket import bitbucket_access_key
from units.compat import unittest
from units.compat.mock import patch
from units.modules.utils import AnsibleFailJson, AnsibleExitJson, ModuleTestCase, set_module_args


class TestBucketAccessKeyModule(ModuleTestCase):
    def setUp(self):
        super(TestBucketAccessKeyModule, self).setUp()
        self.module = bitbucket_access_key

    def test_missing_key_with_present_state(self):
        with self.assertRaises(AnsibleFailJson) as exec_info:
            set_module_args({
                'client_id': 'ABC',
                'client_secret': 'XXX',
                'username': 'name',
                'repository': 'repo',
                'label': 'key name',
                'state': 'present',
            })
            self.module.main()

        self.assertEqual(exec_info.exception.args[0]['msg'], self.module.error_messages['required_key'])

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_access_key, 'get_existing_deploy_key', return_value=None)
    def test_create_deploy_key(self, *args):
        with patch.object(self.module, 'create_deploy_key') as create_deploy_key_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'key': 'public_key',
                    'label': 'key name',
                    'state': 'present',
                })
                self.module.main()

            self.assertEqual(create_deploy_key_mock.call_count, 1)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_access_key, 'get_existing_deploy_key', return_value=None)
    def test_create_deploy_key_check_mode(self, *args):
        with patch.object(self.module, 'create_deploy_key') as create_deploy_key_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'key': 'public_key',
                    'label': 'key name',
                    'state': 'present',
                    '_ansible_check_mode': True,
                })
                self.module.main()

            self.assertEqual(create_deploy_key_mock.call_count, 0)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_access_key, 'get_existing_deploy_key', return_value={
        "id": 123,
        "label": "mykey",
        "created_on": "2019-03-23T10:15:21.517377+00:00",
        "key": "ssh-rsa AAAAB3NzaC1yc2EAAAADA...AdkTg7HGqL3rlaDrEcWfL7Lu6TnhBdq5",
        "type": "deploy_key",
        "comment": "",
        "last_used": None,
        "repository": {
            "links": {
                "self": {
                    "href": "https://api.bitbucket.org/2.0/repositories/mleu/test"
                },
                "html": {
                    "href": "https://bitbucket.org/mleu/test"
                },
                "avatar": {
                    "href": "..."
                }
            },
            "type": "repository",
            "name": "test",
            "full_name": "mleu/test",
            "uuid": "{85d08b4e-571d-44e9-a507-fa476535aa98}"
        },
        "links": {
            "self": {
                "href": "https://api.bitbucket.org/2.0/repositories/mleu/test/deploy-keys/123"
            }
        },
    })
    def test_update_deploy_key(self, *args):
        with patch.object(self.module, 'delete_deploy_key') as delete_deploy_key_mock:
            with patch.object(self.module, 'create_deploy_key') as create_deploy_key_mock:
                with self.assertRaises(AnsibleExitJson) as exec_info:
                    set_module_args({
                        'client_id': 'ABC',
                        'client_secret': 'XXX',
                        'username': 'name',
                        'repository': 'repo',
                        'key': 'new public key',
                        'label': 'mykey',
                        'state': 'present',
                    })
                    self.module.main()

                self.assertEqual(delete_deploy_key_mock.call_count, 1)
                self.assertEqual(create_deploy_key_mock.call_count, 1)
                self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_access_key, 'get_existing_deploy_key', return_value={
        "id": 123,
        "label": "mykey",
        "created_on": "2019-03-23T10:15:21.517377+00:00",
        "key": "new public key",
        "type": "deploy_key",
        "comment": "",
        "last_used": None,
        "repository": {
            "links": {
                "self": {
                    "href": "https://api.bitbucket.org/2.0/repositories/mleu/test"
                },
                "html": {
                    "href": "https://bitbucket.org/mleu/test"
                },
                "avatar": {
                    "href": "..."
                }
            },
            "type": "repository",
            "name": "test",
            "full_name": "mleu/test",
            "uuid": "{85d08b4e-571d-44e9-a507-fa476535aa98}"
        },
        "links": {
            "self": {
                "href": "https://api.bitbucket.org/2.0/repositories/mleu/test/deploy-keys/123"
            }
        },
    })
    def test_dont_update_same_value(self, *args):
        with patch.object(self.module, 'delete_deploy_key') as delete_deploy_key_mock:
            with patch.object(self.module, 'create_deploy_key') as create_deploy_key_mock:
                with self.assertRaises(AnsibleExitJson) as exec_info:
                    set_module_args({
                        'client_id': 'ABC',
                        'client_secret': 'XXX',
                        'username': 'name',
                        'repository': 'repo',
                        'key': 'new public key',
                        'label': 'mykey',
                        'state': 'present',
                    })
                    self.module.main()

                self.assertEqual(delete_deploy_key_mock.call_count, 0)
                self.assertEqual(create_deploy_key_mock.call_count, 0)
                self.assertEqual(exec_info.exception.args[0]['changed'], False)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_access_key, 'get_existing_deploy_key', return_value={
        "id": 123,
        "label": "mykey",
        "created_on": "2019-03-23T10:15:21.517377+00:00",
        "key": "ssh-rsa AAAAB3NzaC1yc2EAAAADA...AdkTg7HGqL3rlaDrEcWfL7Lu6TnhBdq5",
        "type": "deploy_key",
        "comment": "",
        "last_used": None,
        "repository": {
            "links": {
                "self": {
                    "href": "https://api.bitbucket.org/2.0/repositories/mleu/test"
                },
                "html": {
                    "href": "https://bitbucket.org/mleu/test"
                },
                "avatar": {
                    "href": "..."
                }
            },
            "type": "repository",
            "name": "test",
            "full_name": "mleu/test",
            "uuid": "{85d08b4e-571d-44e9-a507-fa476535aa98}"
        },
        "links": {
            "self": {
                "href": "https://api.bitbucket.org/2.0/repositories/mleu/test/deploy-keys/123"
            }
        },
    })
    def test_update_deploy_key_check_mode(self, *args):
        with patch.object(self.module, 'delete_deploy_key') as delete_deploy_key_mock:
            with patch.object(self.module, 'create_deploy_key') as create_deploy_key_mock:
                with self.assertRaises(AnsibleExitJson) as exec_info:
                    set_module_args({
                        'client_id': 'ABC',
                        'client_secret': 'XXX',
                        'username': 'name',
                        'repository': 'repo',
                        'key': 'new public key',
                        'label': 'mykey',
                        'state': 'present',
                        '_ansible_check_mode': True,
                    })
                    self.module.main()

                self.assertEqual(delete_deploy_key_mock.call_count, 0)
                self.assertEqual(create_deploy_key_mock.call_count, 0)
                self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_access_key, 'get_existing_deploy_key', return_value={
        "id": 123,
        "label": "mykey",
        "created_on": "2019-03-23T10:15:21.517377+00:00",
        "key": "ssh-rsa AAAAB3NzaC1yc2EAAAADA...AdkTg7HGqL3rlaDrEcWfL7Lu6TnhBdq5",
        "type": "deploy_key",
        "comment": "",
        "last_used": None,
        "repository": {
            "links": {
                "self": {
                    "href": "https://api.bitbucket.org/2.0/repositories/mleu/test"
                },
                "html": {
                    "href": "https://bitbucket.org/mleu/test"
                },
                "avatar": {
                    "href": "..."
                }
            },
            "type": "repository",
            "name": "test",
            "full_name": "mleu/test",
            "uuid": "{85d08b4e-571d-44e9-a507-fa476535aa98}"
        },
        "links": {
            "self": {
                "href": "https://api.bitbucket.org/2.0/repositories/mleu/test/deploy-keys/123"
            }
        },
    })
    def test_delete_deploy_key(self, *args):
        with patch.object(self.module, 'delete_deploy_key') as delete_deploy_key_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'label': 'mykey',
                    'state': 'absent',
                })
                self.module.main()

            self.assertEqual(delete_deploy_key_mock.call_count, 1)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_access_key, 'get_existing_deploy_key', return_value=None)
    def test_delete_absent_deploy_key(self, *args):
        with patch.object(self.module, 'delete_deploy_key') as delete_deploy_key_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'label': 'mykey',
                    'state': 'absent',
                })
                self.module.main()

            self.assertEqual(delete_deploy_key_mock.call_count, 0)
            self.assertEqual(exec_info.exception.args[0]['changed'], False)

    @patch.object(BitbucketHelper, 'fetch_access_token', return_value='token')
    @patch.object(bitbucket_access_key, 'get_existing_deploy_key', return_value={
        "id": 123,
        "label": "mykey",
        "created_on": "2019-03-23T10:15:21.517377+00:00",
        "key": "ssh-rsa AAAAB3NzaC1yc2EAAAADA...AdkTg7HGqL3rlaDrEcWfL7Lu6TnhBdq5",
        "type": "deploy_key",
        "comment": "",
        "last_used": None,
        "repository": {
            "links": {
                "self": {
                    "href": "https://api.bitbucket.org/2.0/repositories/mleu/test"
                },
                "html": {
                    "href": "https://bitbucket.org/mleu/test"
                },
                "avatar": {
                    "href": "..."
                }
            },
            "type": "repository",
            "name": "test",
            "full_name": "mleu/test",
            "uuid": "{85d08b4e-571d-44e9-a507-fa476535aa98}"
        },
        "links": {
            "self": {
                "href": "https://api.bitbucket.org/2.0/repositories/mleu/test/deploy-keys/123"
            }
        },
    })
    def test_delete_deploy_key_check_mode(self, *args):
        with patch.object(self.module, 'delete_deploy_key') as delete_deploy_key_mock:
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'client_id': 'ABC',
                    'client_secret': 'XXX',
                    'username': 'name',
                    'repository': 'repo',
                    'label': 'mykey',
                    'state': 'absent',
                    '_ansible_check_mode': True,
                })
                self.module.main()

            self.assertEqual(delete_deploy_key_mock.call_count, 0)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)


if __name__ == '__main__':
    unittest.main()
