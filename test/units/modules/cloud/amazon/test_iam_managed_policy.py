import json
import functools
import pytest
import sys

from ansible.modules.cloud.amazon import iam_managed_policy
from units.compat import unittest
from units.compat.mock import patch
from units.modules.utils import AnsibleExitJson, ModuleTestCase, set_module_args

if sys.version_info < (3, 6):
    pytestmark = pytest.mark.skip('This test requires unittest.mock from Python 3.6+')


def check_mode_flag(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func(check_mode=True, *args, **kwargs)
        func(check_mode=False, *args, **kwargs)
    return wrapper


EXAMPLE_POLICY_OLD = '{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": ["s3:Get*", "s3:List*"], "Resource": "*"}]}'
EXAMPLE_POLICY_NEW = '{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]}'


@patch.object(iam_managed_policy, 'HAS_BOTO3', new=True)
class TestIAMManagedPolicyModule(ModuleTestCase):
    @check_mode_flag
    @patch.object(iam_managed_policy, 'get_aws_connection_info', return_value=('eu-central-1', None, {}))
    @patch.object(iam_managed_policy, 'get_policy_by_name', return_value=None)
    @patch.object(iam_managed_policy, 'boto3_conn')
    def test_create_policy(self, boto3_conn_mock, *args, **kwargs):
        check_mode = kwargs['check_mode']
        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'eu-central-1',
                'policy_name': 'test-policy',
                'policy_description': 'This is a new description',
                'policy': EXAMPLE_POLICY_NEW,
                'state': 'present',
                '_ansible_check_mode': check_mode,
            })
            iam_managed_policy.main()

        if check_mode:
            boto3_conn_mock.return_value.create_policy.assert_not_called()
        else:
            boto3_conn_mock.return_value.create_policy.assert_called_once_with(
                Description='This is a new description',
                Path='/',
                PolicyDocument=EXAMPLE_POLICY_NEW,
                PolicyName='test-policy',
            )

        self.assertTrue('policy' in exec_info.exception.args[0])
        self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @check_mode_flag
    @patch.object(iam_managed_policy, 'get_aws_connection_info', return_value=('eu-central-1', None, {}))
    @patch.object(iam_managed_policy, 'get_policy_by_name', return_value={
        'PolicyName': 'test-policy',
        'PolicyId': 'POL_ID',
        'Arn': 'arn:policy',
        'Path': '/',
        'DefaultVersionId': 'v1',
        'AttachmentCount': 0,
        'PermissionsBoundaryUsageCount': 0,
        'IsAttachable': True,
    })
    @patch.object(iam_managed_policy, 'boto3_conn')
    def test_create_default_policy_version(self, boto3_conn_mock, *args, **kwargs):
        check_mode = kwargs['check_mode']
        boto3_conn_mock.return_value.list_policy_versions.return_value = {
            'Versions': [{'VersionId': 'v1', 'IsDefaultVersion': True}],
        }

        boto3_conn_mock.return_value.get_policy_version.return_value = {
            'PolicyVersion': {
                'Document': json.loads(EXAMPLE_POLICY_OLD),
                'VersionId': 'v1',
                'IsDefaultVersion': True,
            },
        }

        boto3_conn_mock.return_value.create_policy_version.return_value = {
            'PolicyVersion': {
                'VersionId': 'v2',
                'IsDefaultVersion': False,
            }
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'eu-central-1',
                'policy_name': 'test-policy',
                'policy_description': 'This is a new description',
                'policy': EXAMPLE_POLICY_NEW,
                'state': 'present',
                '_ansible_check_mode': check_mode,
            })
            iam_managed_policy.main()

        if check_mode:
            boto3_conn_mock.return_value.create_policy_version.assert_not_called()
        else:
            boto3_conn_mock.return_value.create_policy_version.assert_called_once_with(
                PolicyArn='arn:policy',
                PolicyDocument=EXAMPLE_POLICY_NEW,
            )
            boto3_conn_mock.return_value.set_default_policy_version.assert_called_once()

        self.assertTrue('policy' in exec_info.exception.args[0])
        self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @check_mode_flag
    @patch.object(iam_managed_policy, 'get_aws_connection_info', return_value=('eu-central-1', None, {}))
    @patch.object(iam_managed_policy, 'get_policy_by_name', return_value={
        'PolicyName': 'test-policy',
        'PolicyId': 'POL_ID',
        'Arn': 'arn:policy',
        'Path': '/',
        'DefaultVersionId': 'v1',
        'AttachmentCount': 0,
        'PermissionsBoundaryUsageCount': 0,
        'IsAttachable': True,
    })
    @patch.object(iam_managed_policy, 'boto3_conn')
    def test_only_policy_version(self, boto3_conn_mock, *args, **kwargs):
        check_mode = kwargs['check_mode']
        boto3_conn_mock.return_value.list_policy_versions.side_effect = [{
            'Versions': [{'VersionId': 'v1', 'IsDefaultVersion': True}],
        }, {
            'Versions': [
                {'VersionId': 'v1', 'IsDefaultVersion': False},
                {'VersionId': 'v2', 'IsDefaultVersion': True},
            ],
        }]

        boto3_conn_mock.return_value.get_policy_version.return_value = {
            'PolicyVersion': {
                'Document': json.loads(EXAMPLE_POLICY_OLD),
                'VersionId': 'v1',
                'IsDefaultVersion': True,
            },
        }

        boto3_conn_mock.return_value.create_policy_version.return_value = {
            'PolicyVersion': {
                'VersionId': 'v2',
                'IsDefaultVersion': False,
            }
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'eu-central-1',
                'policy_name': 'test-policy',
                'policy_description': 'This is a new description',
                'policy': EXAMPLE_POLICY_NEW,
                'make_default': False,
                'only_version': True,
                'state': 'present',
                '_ansible_check_mode': check_mode,
            })
            iam_managed_policy.main()

        if check_mode:
            boto3_conn_mock.return_value.create_policy_version.assert_not_called()
        else:
            boto3_conn_mock.return_value.create_policy_version.assert_called_once_with(
                PolicyArn='arn:policy',
                PolicyDocument=EXAMPLE_POLICY_NEW,
            )
            boto3_conn_mock.return_value.set_default_policy_version.assert_not_called()
            boto3_conn_mock.return_value.delete_policy_version.assert_called_once_with(
                PolicyArn='arn:policy',
                VersionId='v1',
            )

        self.assertTrue('policy' in exec_info.exception.args[0])
        self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(iam_managed_policy, 'get_aws_connection_info', return_value=('eu-central-1', None, {}))
    @patch.object(iam_managed_policy, 'get_policy_by_name', return_value={
        'PolicyName': 'test-policy',
        'PolicyId': 'POL_ID',
        'Arn': 'arn:policy',
        'Path': '/',
        'DefaultVersionId': 'v1',
        'AttachmentCount': 0,
        'PermissionsBoundaryUsageCount': 0,
        'IsAttachable': True,
    })
    @patch.object(iam_managed_policy, 'boto3_conn')
    def test_create_policy_version_no_changes(self, boto3_conn_mock, *args):
        boto3_conn_mock.return_value.list_policy_versions.return_value = {
            'Versions': [{'VersionId': 'v1', 'IsDefaultVersion': True}],
        }

        boto3_conn_mock.return_value.get_policy_version.return_value = {
            'PolicyVersion': {
                'Document': json.loads(EXAMPLE_POLICY_NEW),
                'VersionId': 'v1',
                'IsDefaultVersion': True,
            },
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'eu-central-1',
                'policy_name': 'test-policy',
                'policy_description': 'This is a new description',
                'policy': EXAMPLE_POLICY_NEW,
                'state': 'present',
            })
            iam_managed_policy.main()

        boto3_conn_mock.return_value.create_policy_version.assert_not_called()
        boto3_conn_mock.return_value.set_default_policy_version.assert_not_called()
        boto3_conn_mock.return_value.delete_policy_version.assert_not_called()

        self.assertTrue('policy' in exec_info.exception.args[0])
        self.assertEqual(exec_info.exception.args[0]['changed'], False)

    @check_mode_flag
    @patch.object(iam_managed_policy, 'get_aws_connection_info', return_value=('eu-central-1', None, {}))
    @patch.object(iam_managed_policy, 'get_policy_by_name', return_value={
        'PolicyName': 'test-policy',
        'PolicyId': 'POL_ID',
        'Arn': 'arn:policy',
        'Path': '/',
        'DefaultVersionId': 'v1',
        'AttachmentCount': 0,
        'PermissionsBoundaryUsageCount': 0,
        'IsAttachable': True,
    })
    @patch.object(iam_managed_policy, 'boto3_conn')
    def test_delete_policy(self, boto3_conn_mock, *args, **kwargs):
        check_mode = kwargs['check_mode']
        boto3_conn_mock.return_value.list_entities_for_policy.return_value = {
            'PolicyGroups': [{'GroupName': 'group'}],
            'PolicyUsers': [{'UserName': 'user'}],
            'PolicyRoles': [{'RoleName': 'role'}],
            'IsTruncated': False,
        }

        boto3_conn_mock.return_value.list_policy_versions.return_value = {
            'Versions': [
                {'VersionId': 'v1', 'IsDefaultVersion': False},
                {'VersionId': 'v2', 'IsDefaultVersion': True},
            ],
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'eu-central-1',
                'policy_name': 'test-policy',
                'state': 'absent',
                '_ansible_check_mode': check_mode,
            })
            iam_managed_policy.main()

        if check_mode:
            boto3_conn_mock.return_value.create_policy_version.assert_not_called()
        else:
            client = boto3_conn_mock.return_value

            client.detach_group_policy.assert_called_once_with(PolicyArn='arn:policy', GroupName='group')
            client.detach_user_policy.assert_called_once_with(PolicyArn='arn:policy', UserName='user')
            client.detach_role_policy.assert_called_once_with(PolicyArn='arn:policy', RoleName='role')
            client.delete_policy_version.assert_called_once_with(PolicyArn='arn:policy', VersionId='v1')
            client.delete_policy.assert_called_once_with(PolicyArn='arn:policy')

        self.assertTrue('policy' in exec_info.exception.args[0])
        self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(iam_managed_policy, 'get_aws_connection_info', return_value=('eu-central-1', None, {}))
    @patch.object(iam_managed_policy, 'get_policy_by_name', return_value=None)
    @patch.object(iam_managed_policy, 'boto3_conn')
    def test_delete_policy_no_changes(self, boto3_conn_mock, *args):
        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'eu-central-1',
                'policy_name': 'test-policy',
                'state': 'absent',
            })
            iam_managed_policy.main()

        boto3_conn_mock.return_value.delete_policy.assert_not_called()
        self.assertTrue('policy' in exec_info.exception.args[0])
        self.assertEqual(exec_info.exception.args[0]['changed'], False)


if __name__ == '__main__':
    unittest.main()
