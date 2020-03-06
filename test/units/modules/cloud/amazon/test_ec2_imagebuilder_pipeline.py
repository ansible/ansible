# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from units.compat.mock import MagicMock, patch
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

from ansible.module_utils.ec2 import snake_dict_to_camel_dict
from ansible.modules.cloud.amazon import ec2_imagebuilder_pipeline

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass


class TestEC2ImageBuilderPipelineModule(ModuleTestCase):

    mocked_get_caller_identity = {
        "UserId": "AROAJxxxxxxxxxxIPWZY:user.id",
        "Account": "111222333444",
        "Arn": "arn:aws:sts::111222333444:assumed-role/admin/test.user"
    }

    def test_required_parameters(self):
        set_module_args({})
        with pytest.raises(AnsibleFailJson) as context:
            ec2_imagebuilder_pipeline.main()

        result = context.value.args[0]

        assert result['failed'] is True
        assert "name" in result['msg']
        assert "state" in result['msg']

    @patch.object(ec2_imagebuilder_pipeline.AnsibleAWSModule, 'client')
    def test_absent_when_not_exists(self, client_mock):
        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity

        client_mock.return_value.get_image_pipeline.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetImagePipeline')
        set_module_args({
            'name': 'test_pipeline',
            'state': 'absent'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_pipeline.main()

        result = context.value.args[0]

        assert result['changed'] is False
        assert result['pipeline'] is not None
        assert result['pipeline']['arn'] is not None

    @patch.object(ec2_imagebuilder_pipeline.AnsibleAWSModule, 'client')
    def test_present_when_not_exists(self, client_mock):
        test_pipeline = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:image-pipeline/test-pipeline",
            "name": "test_pipeline",
            "description": "this is a test pipeline",
            "platform": "Linux",
            "image_recipe_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:image-recipe/test-recipe/1.0.0",
            "infrastructure_configuration_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:infrastructure-configuration/test",
            "distribution_configuration_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:distribution-configuration/test",
            "image_tests_configuration": {
                "image_tests_enabled": True,
                "timeout_minutes": 720
            },
            "schedule": {
                "schedule_expression": "cron(0 12 1 * *)",
                "pipeline_execution_start_condition": "EXPRESSION_MATCH_ONLY"
            },
            "status": "ENABLED",
            "date_created": "2020-02-28T04:20:18.997Z",
            "date_updated": "2020-03-03T05:50:13.787Z",
            "tags": {}
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_image_pipeline.side_effect = [
            ClientError(
                {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetInfrastructureConfiguration'),
            dict(imagePipeline=snake_dict_to_camel_dict(test_pipeline))
        ]

        client_mock.return_value.create_image_pipeline.return_value = dict(
            requestId='mock_request_id', clientToken='mock_client_token', imagePipelineArn=test_pipeline['arn'])

        set_module_args({
            **{k: test_pipeline[k] for k in ('name', 'description', 'infrastructure_configuration_arn', 'distribution_configuration_arn', 'image_tests_configuration', 'schedule', 'status', 'tags')},
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_pipeline.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['pipeline'] is not None
        assert result['pipeline'] == test_pipeline
        assert client_mock.return_value.get_image_pipeline.call_count == 2
        assert client_mock.return_value.create_image_pipeline.call_count == 1

    @patch.object(ec2_imagebuilder_pipeline.AnsibleAWSModule, 'client')
    def test_present_when_exists(self, client_mock):
        test_pipeline = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:image-pipeline/test-pipeline",
            "name": "test_pipeline",
            "description": "this is a test pipeline",
            "platform": "Linux",
            "image_recipe_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:image-recipe/test-recipe/1.0.0",
            "infrastructure_configuration_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:infrastructure-configuration/test",
            "distribution_configuration_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:distribution-configuration/test",
            "image_tests_configuration": {
                "image_tests_enabled": True,
                "timeout_minutes": 720
            },
            "schedule": {
                "schedule_expression": "cron(0 12 1 * *)",
                "pipeline_execution_start_condition": "EXPRESSION_MATCH_ONLY"
            },
            "status": "ENABLED",
            "date_created": "2020-02-28T04:20:18.997Z",
            "date_updated": "2020-03-03T05:50:13.787Z",
            "tags": {}
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_image_pipeline.return_value = dict(
            imagePipeline=snake_dict_to_camel_dict(test_pipeline))

        set_module_args({
            **{k: test_pipeline[k] for k in ('name', 'description', 'image_recipe_arn', 'infrastructure_configuration_arn', 'distribution_configuration_arn', 'image_tests_configuration', 'schedule', 'status', 'tags')},
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_pipeline.main()

        result = context.value.args[0]

        assert result['changed'] is False
        assert result['pipeline'] is not None
        assert result['pipeline'] == test_pipeline
        assert client_mock.return_value.get_image_pipeline.call_count == 1
        assert client_mock.return_value.create_image_pipeline.call_count == 0

    @patch.object(ec2_imagebuilder_pipeline.AnsibleAWSModule, 'client')
    def test_present_when_pipeline_different(self, client_mock):
        test_pipeline = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:image-pipeline/test-pipeline",
            "name": "test_pipeline",
            "description": "this is a test pipeline",
            "platform": "Linux",
            "image_recipe_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:image-recipe/test-recipe/1.0.0",
            "infrastructure_configuration_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:infrastructure-configuration/test",
            "distribution_configuration_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:distribution-configuration/test",
            "image_tests_configuration": {
                "image_tests_enabled": True,
                "timeout_minutes": 720
            },
            "schedule": {
                "schedule_expression": "cron(0 12 1 * *)",
                "pipeline_execution_start_condition": "EXPRESSION_MATCH_ONLY"
            },
            "status": "ENABLED",
            "date_created": "2020-02-28T04:20:18.997Z",
            "date_updated": "2020-03-03T05:50:13.787Z",
            "tags": {}
        }

        updated_test_pipeline = {
            **test_pipeline,
            'description': "this is a test pipeline -- updated!",
            "image_recipe_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:image-recipe/test-recipe/1.0.1",
            "infrastructure_configuration_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:infrastructure-configuration/test-2",
            "distribution_configuration_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:distribution-configuration/test-2",
            "status": "DISABLED"
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_image_pipeline.side_effect = [
            dict(imagePipeline=snake_dict_to_camel_dict(test_pipeline)),
            dict(imagePipeline=snake_dict_to_camel_dict(
                updated_test_pipeline))
        ]

        client_mock.return_value.update_image_pipeline.return_value = dict(
            requestId='mock_request_id', clientToken='mock_client_token', imagePipelineArn=updated_test_pipeline['arn'])

        set_module_args({
            **{k: updated_test_pipeline[k] for k in ('name', 'description', 'image_recipe_arn', 'infrastructure_configuration_arn', 'distribution_configuration_arn', 'image_tests_configuration', 'schedule', 'status', 'tags')},
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_pipeline.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['pipeline'] is not None
        assert result['pipeline'] == updated_test_pipeline
        assert client_mock.return_value.get_image_pipeline.call_count == 2
        assert client_mock.return_value.update_image_pipeline.call_count == 1

    @patch.object(ec2_imagebuilder_pipeline.AnsibleAWSModule, 'client')
    def test_present_when_tags_different(self, client_mock):
        test_pipeline = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:image-pipeline/test-pipeline",
            "name": "test_pipeline",
            "description": "this is a test pipeline",
            "platform": "Linux",
            "image_recipe_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:image-recipe/test-recipe/1.0.0",
            "infrastructure_configuration_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:infrastructure-configuration/test",
            "distribution_configuration_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:distribution-configuration/test",
            "image_tests_configuration": {
                "image_tests_enabled": True,
                "timeout_minutes": 720
            },
            "schedule": {
                "schedule_expression": "cron(0 12 1 * *)",
                "pipeline_execution_start_condition": "EXPRESSION_MATCH_ONLY"
            },
            "status": "ENABLED",
            "date_created": "2020-02-28T04:20:18.997Z",
            "date_updated": "2020-03-03T05:50:13.787Z",
            "tags": {
                "thisis": "atag"
            }
        }

        updated_test_pipeline = {
            **test_pipeline,
            "tags": {
            }
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_image_pipeline.side_effect = [
            dict(imagePipeline=snake_dict_to_camel_dict(test_pipeline)),
            dict(imagePipeline=snake_dict_to_camel_dict(
                updated_test_pipeline))
        ]

        client_mock.return_value.untag_resource.return_value = {}
        client_mock.return_value.tag_resource.return_value = {}

        set_module_args({
            **{k: updated_test_pipeline[k] for k in ('name', 'description', 'image_recipe_arn', 'infrastructure_configuration_arn', 'distribution_configuration_arn', 'image_tests_configuration', 'schedule', 'status', 'tags')},
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_pipeline.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['pipeline'] is not None
        assert result['pipeline'] == updated_test_pipeline
        assert client_mock.return_value.get_image_pipeline.call_count == 2
        assert client_mock.return_value.update_image_pipeline.call_count == 0
        assert client_mock.return_value.untag_resource.call_count == 1
        args, kwargs = client_mock.return_value.untag_resource.call_args
        assert kwargs['tagKeys'] == list(test_pipeline['tags'])

    @patch.object(ec2_imagebuilder_pipeline.AnsibleAWSModule, 'client')
    def test_absent_when_exists(self, client_mock):
        test_pipeline = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:image-pipeline/test-pipeline",
            "name": "test_pipeline",
            "description": "this is a test pipeline",
            "platform": "Linux",
            "image_recipe_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:image-recipe/test-recipe/1.0.0",
            "infrastructure_configuration_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:infrastructure-configuration/test",
            "distribution_configuration_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:distribution-configuration/test",
            "image_tests_configuration": {
                "image_tests_enabled": True,
                "timeout_minutes": 720
            },
            "schedule": {
                "schedule_expression": "cron(0 12 1 * *)",
                "pipeline_execution_start_condition": "EXPRESSION_MATCH_ONLY"
            },
            "status": "ENABLED",
            "date_created": "2020-02-28T04:20:18.997Z",
            "date_updated": "2020-03-03T05:50:13.787Z",
            "tags": {
                "thisis": "atag"
            }
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_image_pipeline.return_value = dict(
            imagePipeline=snake_dict_to_camel_dict(test_pipeline))
        client_mock.return_value.delete_image_pipeline.return_value = dict(
            requestId='mock_request_id', imagePipelineArn=test_pipeline['arn'])

        set_module_args({
            'name': test_pipeline['name'],
            'state': 'absent'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_pipeline.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['pipeline'] is not None
        assert result['pipeline'] == dict(
            arn=test_pipeline['arn'])
        assert client_mock.return_value.get_image_pipeline.call_count == 1
        assert client_mock.return_value.delete_image_pipeline.call_count == 1
        args, kwargs = client_mock.return_value.delete_image_pipeline.call_args
        assert kwargs['imagePipelineArn'] == test_pipeline['arn']
