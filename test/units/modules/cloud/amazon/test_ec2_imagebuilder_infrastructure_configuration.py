# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from units.compat.mock import MagicMock, patch
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

from ansible.module_utils.ec2 import snake_dict_to_camel_dict
from ansible.modules.cloud.amazon import ec2_imagebuilder_infrastructure_configuration

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass


class TestEC2ImageBuilderInfrastructureConfigurationModule(ModuleTestCase):

    mocked_get_caller_identity = {
        "UserId": "AROAJxxxxxxxxxxIPWZY:user.id",
        "Account": "111222333444",
        "Arn": "arn:aws:sts::111222333444:assumed-role/admin/test.user"
    }

    def test_required_parameters(self):
        set_module_args({})
        with pytest.raises(AnsibleFailJson) as context:
            ec2_imagebuilder_infrastructure_configuration.main()

        result = context.value.args[0]

        assert result['failed'] is True
        assert "name" in result['msg']
        assert "state" in result['msg']

    @patch.object(ec2_imagebuilder_infrastructure_configuration.AnsibleAWSModule, 'client')
    def test_absent_when_not_exists(self, client_mock):
        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity

        client_mock.return_value.get_infrastructure_configuration.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetInfrastructureConfiguration')
        set_module_args({
            'name': 'test_infrastructure_configuration',
            'state': 'absent'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_infrastructure_configuration.main()

        result = context.value.args[0]

        assert result['changed'] is False
        assert result['infrastructure_configuration'] is not None
        assert result['infrastructure_configuration']['arn'] is not None

    @patch.object(ec2_imagebuilder_infrastructure_configuration.AnsibleAWSModule, 'client')
    def test_present_when_not_exists(self, client_mock):
        test_infrastructure_configuration = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:infrastructure-configuration/test-infrastructure-configuration",
            "name": "test_infrastructure_configuration",
            "description": "this is a test infrastructure configuration",
            "instance_profile_name": "test_instance_profile",
            "key_pair": "test_key_pair",
            "security_group_ids": [
                "sg-xxxx",
                "sg-yyyy"
            ],
            "subnet_id": "subnet-xxxx",
            "terminate_instance_on_failure": True,
            "date_created": "2020-03-03T00:44:15.092Z",
            "date_updated": "2020-03-03T01:04:05.200Z",
            "tags": {
                "key": "value",
                "another": "tag"
            }
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_infrastructure_configuration.side_effect = [
            ClientError(
                {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetInfrastructureConfiguration'),
            dict(infrastructureConfiguration=snake_dict_to_camel_dict(
                test_infrastructure_configuration))
        ]

        client_mock.return_value.create_infrastructure_configuration.return_value = dict(
            requestId='mock_request_id', clientToken='mock_client_token', infrastructureConfigurationArn=test_infrastructure_configuration['arn'])

        set_module_args({
            **{k: test_infrastructure_configuration[k] for k in ('name', 'description', 'instance_profile_name', 'key_pair', 'security_group_ids', 'subnet_id', 'terminate_instance_on_failure', 'tags')},
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_infrastructure_configuration.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['infrastructure_configuration'] is not None
        assert result['infrastructure_configuration'] == test_infrastructure_configuration
        assert client_mock.return_value.get_infrastructure_configuration.call_count == 2
        assert client_mock.return_value.create_infrastructure_configuration.call_count == 1

    @patch.object(ec2_imagebuilder_infrastructure_configuration.AnsibleAWSModule, 'client')
    def test_present_when_exists(self, client_mock):
        test_infrastructure_configuration = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:infrastructure-configuration/test-infrastructure-configuration",
            "name": "test_infrastructure_configuration",
            "description": "this is a test infrastructure configuration",
            "instance_profile_name": "test_instance_profile",
            "key_pair": "test_key_pair",
            "security_group_ids": [
                "sg-xxxx",
                "sg-yyyy"
            ],
            "subnet_id": "subnet-xxxx",
            "terminate_instance_on_failure": True,
            "date_created": "2020-03-03T00:44:15.092Z",
            "date_updated": "2020-03-03T01:04:05.200Z",
            "tags": {
                "key": "value",
                "another": "tag"
            }
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_infrastructure_configuration.side_effect = [
            dict(infrastructureConfiguration=snake_dict_to_camel_dict(
                test_infrastructure_configuration))
        ]

        set_module_args({
            **{k: test_infrastructure_configuration[k] for k in ('name', 'description', 'instance_profile_name', 'key_pair', 'security_group_ids', 'subnet_id', 'terminate_instance_on_failure', 'tags')},
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_infrastructure_configuration.main()

        result = context.value.args[0]

        assert result['changed'] is False
        assert result['infrastructure_configuration'] is not None
        assert result['infrastructure_configuration'] == test_infrastructure_configuration
        assert client_mock.return_value.get_infrastructure_configuration.call_count == 1
        assert client_mock.return_value.create_infrastructure_configuration.call_count == 0

    @patch.object(ec2_imagebuilder_infrastructure_configuration.AnsibleAWSModule, 'client')
    def test_present_when_infrastructure_configuration_different(self, client_mock):
        test_infrastructure_configuration = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:infrastructure-configuration/test-infrastructure-configuration",
            "name": "test_infrastructure_configuration",
            "description": "this is a test infrastructure configuration",
            "instance_profile_name": "test_instance_profile",
            "key_pair": "test_key_pair",
            "security_group_ids": [
                "sg-xxxx",
                "sg-yyyy"
            ],
            "subnet_id": "subnet-xxxx",
            "terminate_instance_on_failure": True,
            "date_created": "2020-03-03T00:44:15.092Z",
            "date_updated": "2020-03-03T01:04:05.200Z",
            "tags": {
                "key": "value",
                "another": "tag"
            }
        }

        updated_test_infrastructure_configuration = {
            **test_infrastructure_configuration,
            'description': "this is a test infrastructure configuration -- updated!",
            "security_group_ids": [
                "sg-xxxx"
            ],
            "terminate_instance_on_failure": False
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_infrastructure_configuration.side_effect = [
            dict(infrastructureConfiguration=snake_dict_to_camel_dict(
                test_infrastructure_configuration)),
            dict(infrastructureConfiguration=snake_dict_to_camel_dict(
                updated_test_infrastructure_configuration))
        ]

        client_mock.return_value.update_infrastructure_configuration.return_value = dict(
            requestId='mock_request_id', clientToken='mock_client_token', infrastructureConfigurationArn=updated_test_infrastructure_configuration['arn'])

        set_module_args({
            **{k: updated_test_infrastructure_configuration[k] for k in ('name', 'description', 'instance_profile_name', 'key_pair', 'security_group_ids', 'subnet_id', 'terminate_instance_on_failure', 'tags')},
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_infrastructure_configuration.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['infrastructure_configuration'] is not None
        assert result['infrastructure_configuration'] == updated_test_infrastructure_configuration
        assert client_mock.return_value.get_infrastructure_configuration.call_count == 2
        assert client_mock.return_value.update_infrastructure_configuration.call_count == 1

    @patch.object(ec2_imagebuilder_infrastructure_configuration.AnsibleAWSModule, 'client')
    def test_present_when_tags_different(self, client_mock):
        test_infrastructure_configuration = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:infrastructure-configuration/test-infrastructure-configuration",
            "name": "test_infrastructure_configuration",
            "description": "this is a test infrastructure configuration",
            "instance_profile_name": "test_instance_profile",
            "key_pair": "test_key_pair",
            "security_group_ids": [
                "sg-xxxx",
                "sg-yyyy"
            ],
            "subnet_id": "subnet-xxxx",
            "terminate_instance_on_failure": True,
            "date_created": "2020-03-03T00:44:15.092Z",
            "date_updated": "2020-03-03T01:04:05.200Z",
            "tags": {
                "key": "value",
                "another": "tag"
            }
        }

        updated_test_infrastructure_configuration = {
            **test_infrastructure_configuration,
            "tags": {
                "thisis": "adifferenttag"
            }
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_infrastructure_configuration.side_effect = [
            dict(infrastructureConfiguration=snake_dict_to_camel_dict(
                test_infrastructure_configuration)),
            dict(infrastructureConfiguration=snake_dict_to_camel_dict(
                updated_test_infrastructure_configuration))
        ]

        client_mock.return_value.update_infrastructure_configuration.return_value = dict(
            requestId='mock_request_id', clientToken='mock_client_token', infrastructureConfigurationArn=updated_test_infrastructure_configuration['arn'])

        set_module_args({
            **{k: updated_test_infrastructure_configuration[k] for k in ('name', 'description', 'instance_profile_name', 'key_pair', 'security_group_ids', 'subnet_id', 'terminate_instance_on_failure', 'tags')},
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_infrastructure_configuration.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['infrastructure_configuration'] is not None
        assert result['infrastructure_configuration'] == updated_test_infrastructure_configuration
        assert client_mock.return_value.get_infrastructure_configuration.call_count == 2
        assert client_mock.return_value.update_infrastructure_configuration.call_count == 0
        assert client_mock.return_value.tag_resource.call_count == 1
        args, kwargs = client_mock.return_value.tag_resource.call_args
        assert kwargs['tags'] == updated_test_infrastructure_configuration['tags']

    @patch.object(ec2_imagebuilder_infrastructure_configuration.AnsibleAWSModule, 'client')
    def test_absent_when_exists(self, client_mock):
        test_infrastructure_configuration = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:infrastructure-configuration/test-infrastructure-configuration",
            "name": "test_infrastructure_configuration",
            "description": "this is a test infrastructure configuration",
            "instance_profile_name": "test_instance_profile",
            "key_pair": "test_key_pair",
            "security_group_ids": [
                "sg-xxxx",
                "sg-yyyy"
            ],
            "subnet_id": "subnet-xxxx",
            "terminate_instance_on_failure": True,
            "date_created": "2020-03-03T00:44:15.092Z",
            "date_updated": "2020-03-03T01:04:05.200Z",
            "tags": {
                "key": "value",
                "another": "tag"
            }
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_infrastructure_configuration.side_effect = [
            dict(infrastructureConfiguration=snake_dict_to_camel_dict(
                test_infrastructure_configuration))
        ]
        client_mock.return_value.delete_infrastructure_configuration.return_value = dict(
            requestId='mock_request_id', infrastructureConfigurationArn=test_infrastructure_configuration['arn'])

        set_module_args({
            'name': test_infrastructure_configuration['name'],
            'state': 'absent'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_infrastructure_configuration.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['infrastructure_configuration'] is not None
        assert result['infrastructure_configuration'] == dict(
            arn=test_infrastructure_configuration['arn'])
        assert client_mock.return_value.get_infrastructure_configuration.call_count == 1
        assert client_mock.return_value.delete_infrastructure_configuration.call_count == 1
        args, kwargs = client_mock.return_value.delete_infrastructure_configuration.call_args
        assert kwargs['infrastructureConfigurationArn'] == test_infrastructure_configuration['arn']
