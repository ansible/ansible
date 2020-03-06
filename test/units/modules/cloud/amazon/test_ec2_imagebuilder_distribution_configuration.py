# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from units.compat.mock import MagicMock, patch
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

from ansible.module_utils.ec2 import snake_dict_to_camel_dict
from ansible.modules.cloud.amazon import ec2_imagebuilder_distribution_configuration

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass


class TestEC2ImageBuilderDistributionConfigurationModule(ModuleTestCase):

    mocked_get_caller_identity = {
        "UserId": "AROAJxxxxxxxxxxIPWZY:user.id",
        "Account": "111222333444",
        "Arn": "arn:aws:sts::111222333444:assumed-role/admin/test.user"
    }

    def test_required_parameters(self):
        set_module_args({})
        with pytest.raises(AnsibleFailJson) as context:
            ec2_imagebuilder_distribution_configuration.main()

        result = context.value.args[0]

        assert result['failed'] is True
        assert "name" in result['msg']
        assert "state" in result['msg']

    @patch.object(ec2_imagebuilder_distribution_configuration.AnsibleAWSModule, 'client')
    def test_absent_when_not_exists(self, client_mock):
        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity

        client_mock.return_value.get_distribution_configuration.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetDistributionConfiguration')
        set_module_args({
            'name': 'test_distribution_configuration',
            'state': 'absent'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_distribution_configuration.main()

        result = context.value.args[0]

        assert result['changed'] is False
        assert result['distribution_configuration'] is not None
        assert result['distribution_configuration']['arn'] is not None

    @patch.object(ec2_imagebuilder_distribution_configuration.AnsibleAWSModule, 'client')
    def test_present_when_not_exists(self, client_mock):
        test_distribution_configuration = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:distribution-configuration/test-distribution-configuration",
            "name": "test_distribution_configuration",
            "description": "this is a test distribution configuration",
            "distributions": [
                {
                    "region": "ap-southeast-2",
                    "ami_distribution_configuration": {
                        "name": "amazon_linux_ansible {{imagebuilder:buildDate}}"
                    }
                }
            ],
            "date_created": "2020-02-28T04:20:16.710Z",
            "tags": {
                "this": "isatag"
            }
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_distribution_configuration.side_effect = [
            ClientError(
                {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetDistributionConfiguration'),
            dict(distributionConfiguration=snake_dict_to_camel_dict(test_distribution_configuration))
        ]

        client_mock.return_value.create_distribution_configuration.return_value = dict(
            requestId='mock_request_id', clientToken='mock_client_token', distributionConfigurationArn=test_distribution_configuration['arn'])

        set_module_args({
            **{k: test_distribution_configuration[k] for k in ('name', 'description', 'distributions', 'tags')},
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_distribution_configuration.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['distribution_configuration'] is not None
        assert result['distribution_configuration'] == test_distribution_configuration
        assert client_mock.return_value.get_distribution_configuration.call_count == 2
        assert client_mock.return_value.create_distribution_configuration.call_count == 1

    @patch.object(ec2_imagebuilder_distribution_configuration.AnsibleAWSModule, 'client')
    def test_present_when_exists(self, client_mock):
        test_distribution_configuration = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:distribution-configuration/test-distribution-configuration",
            "name": "test_distribution_configuration",
            "description": "this is a test distribution configuration",
            "distributions": [
                {
                    "region": "ap-southeast-2",
                    "ami_distribution_configuration": {
                        "name": "amazon_linux_ansible {{imagebuilder:buildDate}}"
                    }
                }
            ],
            "date_created": "2020-02-28T04:20:16.710Z",
            "tags": {
                "this": "isatag"
            }
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_distribution_configuration.side_effect = [
            dict(distributionConfiguration=snake_dict_to_camel_dict(test_distribution_configuration))
        ]

        set_module_args({
            **{k: test_distribution_configuration[k] for k in ('name', 'description', 'distributions', 'tags')},
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_distribution_configuration.main()

        result = context.value.args[0]

        assert result['changed'] is False
        assert result['distribution_configuration'] is not None
        assert result['distribution_configuration'] == test_distribution_configuration
        assert client_mock.return_value.get_distribution_configuration.call_count == 1
        assert client_mock.return_value.create_distribution_configuration.call_count == 0

    @patch.object(ec2_imagebuilder_distribution_configuration.AnsibleAWSModule, 'client')
    def test_present_when_distribution_configuration_different(self, client_mock):
        test_distribution_configuration = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:distribution-configuration/test-distribution-configuration",
            "name": "test_distribution_configuration",
            "description": "this is a test distribution configuration",
            "distributions": [
                {
                    "region": "ap-southeast-2",
                    "ami_distribution_configuration": {
                        "name": "amazon_linux_ansible {{imagebuilder:buildDate}}"
                    }
                }
            ],
            "date_created": "2020-02-28T04:20:16.710Z",
            "tags": {
                "this": "isatag"
            }
        }

        updated_test_distribution_configuration = {
            **test_distribution_configuration,
            "distributions": [
                {
                    "region": "ap-southeast-2",
                    "ami_distribution_configuration": {
                        "name": "amazon_linux_ansible {{imagebuilder:buildDate}}"
                    }
                },
                {
                    "region": "us-east-1",
                    "ami_distribution_configuration": {
                        "name": "amazon_linux_ansible {{imagebuilder:buildDate}}"
                    }
                }
            ],
            'description': "this is a test distribution configuration -- updated!"
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_distribution_configuration.side_effect = [
            dict(distributionConfiguration=snake_dict_to_camel_dict(test_distribution_configuration)),
            dict(distributionConfiguration=snake_dict_to_camel_dict(
                updated_test_distribution_configuration))
        ]

        client_mock.return_value.update_distribution_configuration.return_value = dict(
            requestId='mock_request_id', clientToken='mock_client_token', distributionConfigurationArn=updated_test_distribution_configuration['arn'])

        set_module_args({
            **{k: updated_test_distribution_configuration[k] for k in ('name', 'description', 'distributions', 'tags')},
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_distribution_configuration.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['distribution_configuration'] is not None
        assert result['distribution_configuration'] == updated_test_distribution_configuration
        assert client_mock.return_value.get_distribution_configuration.call_count == 2
        assert client_mock.return_value.update_distribution_configuration.call_count == 1

    @patch.object(ec2_imagebuilder_distribution_configuration.AnsibleAWSModule, 'client')
    def test_present_when_tags_different(self, client_mock):
        test_distribution_configuration = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:distribution-configuration/test-distribution-configuration",
            "name": "test_distribution_configuration",
            "description": "this is a test distribution configuration",
            "distributions": [
                {
                    "region": "ap-southeast-2",
                    "ami_distribution_configuration": {
                        "name": "amazon_linux_ansible {{imagebuilder:buildDate}}"
                    }
                }
            ],
            "date_created": "2020-02-28T04:20:16.710Z",
            "tags": {
                "this": "isatag"
            }
        }

        updated_test_distribution_configuration = {
            **test_distribution_configuration,
            "tags": {
                "thisis": "adifferenttag"
            }
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_distribution_configuration.side_effect = [
            dict(distributionConfiguration=snake_dict_to_camel_dict(test_distribution_configuration)),
            dict(distributionConfiguration=snake_dict_to_camel_dict(
                updated_test_distribution_configuration))
        ]

        client_mock.return_value.update_distribution_configuration.return_value = dict(
            requestId='mock_request_id', clientToken='mock_client_token', distributionConfigurationArn=updated_test_distribution_configuration['arn'])

        set_module_args({
            **{k: updated_test_distribution_configuration[k] for k in ('name', 'description', 'distributions', 'tags')},
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_distribution_configuration.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['distribution_configuration'] is not None
        assert result['distribution_configuration'] == updated_test_distribution_configuration
        assert client_mock.return_value.get_distribution_configuration.call_count == 2
        assert client_mock.return_value.update_distribution_configuration.call_count == 0
        assert client_mock.return_value.tag_resource.call_count == 1
        _, kwargs = client_mock.return_value.tag_resource.call_args
        assert kwargs['tags'] == updated_test_distribution_configuration['tags']

    @patch.object(ec2_imagebuilder_distribution_configuration.AnsibleAWSModule, 'client')
    def test_absent_when_exists(self, client_mock):
        test_distribution_configuration = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:distribution-configuration/test-distribution-configuration",
            "name": "test_distribution_configuration",
            "description": "this is a test distribution configuration",
            "distributions": [
                {
                    "region": "ap-southeast-2",
                    "ami_distribution_configuration": {
                        "name": "amazon_linux_ansible {{imagebuilder:buildDate}}"
                    }
                }
            ],
            "date_created": "2020-02-28T04:20:16.710Z",
            "tags": {
                "this": "isatag"
            }
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_distribution_configuration.side_effect = [
            dict(distributionConfiguration=snake_dict_to_camel_dict(test_distribution_configuration))
        ]
        client_mock.return_value.delete_distribution_configuration.return_value = dict(
            requestId='mock_request_id', distributionConfigurationArn=test_distribution_configuration['arn'])

        set_module_args({
            'name': test_distribution_configuration['name'],
            'state': 'absent'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_distribution_configuration.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['distribution_configuration'] is not None
        assert result['distribution_configuration'] == dict(
            arn=test_distribution_configuration['arn'])
        assert client_mock.return_value.get_distribution_configuration.call_count == 1
        assert client_mock.return_value.delete_distribution_configuration.call_count == 1
        _, kwargs = client_mock.return_value.delete_distribution_configuration.call_args
        assert kwargs['distributionConfigurationArn'] == test_distribution_configuration['arn']
