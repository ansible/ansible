# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from units.compat.mock import MagicMock, patch
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

from ansible.module_utils.ec2 import snake_dict_to_camel_dict
from ansible.modules.cloud.amazon import ec2_imagebuilder_component

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass


class TestEC2ImageBuilderComponentModule(ModuleTestCase):

    mocked_get_caller_identity = {
        "UserId": "AROAJxxxxxxxxxxIPWZY:user.id",
        "Account": "111222333444",
        "Arn": "arn:aws:sts::111222333444:assumed-role/admin/test.user"
    }

    def test_required_parameters(self):
        set_module_args({})
        with pytest.raises(AnsibleFailJson) as context:
            ec2_imagebuilder_component.main()

        result = context.value.args[0]

        assert result['failed'] is True
        assert "name" in result['msg']
        assert "semantic_version" in result['msg']
        assert "state" in result['msg']

    @patch.object(ec2_imagebuilder_component.AnsibleAWSModule, 'client')
    def test_absent_when_not_exists(self, client_mock):
        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity

        client_mock.return_value.get_component.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetComponent')
        set_module_args({
            'name': 'test_component',
            'semantic_version': '1.0.0',
            'state': 'absent'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_component.main()

        result = context.value.args[0]

        assert result['changed'] is False
        assert result['component'] is not None
        assert result['component']['arn'] is not None

    @patch.object(ec2_imagebuilder_component.AnsibleAWSModule, 'client')
    def test_present_when_not_exists(self, client_mock):
        test_component = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:component/test-component/1.0.0/1",
            "name": "test_component",
            "version": "1.0.0",
            "description": "this is a test component",
            "type": "BUILD",
            "platform": "Linux",
            "owner": "111222333444",
            "data": "{'schemaVersion': '1.0', 'phases': [{'name': 'build', 'steps': [{'name': 'RunScript', 'action': 'ExecuteBash', 'timeoutSeconds': 120, 'onFailure': 'Abort', 'maxAttempts': 3, 'inputs': {'commands': [\"echo 'scripty things!'\\n\"]}}]}]}",
            "encrypted": True,
            "date_created": "2020-03-04T05:41:55.939Z",
            "tags": {
                "this": "isatag"
            }
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_component.side_effect = [
            ClientError(
                {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetComponent'),
            dict(component=snake_dict_to_camel_dict(test_component))
        ]

        client_mock.return_value.create_component.return_value = dict(
            requestId='mock_request_id', clientToken='mock_client_token', componentBuildVersionArn=test_component['arn'])

        set_module_args({
            **{k: test_component[k] for k in ('name', 'description', 'platform', 'data', 'tags')},
            'semantic_version': test_component['version'],  # thanks aws
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_component.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['component'] is not None
        assert result['component'] == test_component
        assert client_mock.return_value.get_component.call_count == 2
        assert client_mock.return_value.create_component.call_count == 1

    @patch.object(ec2_imagebuilder_component.AnsibleAWSModule, 'client')
    def test_present_when_exists(self, client_mock):
        test_component = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:component/test-component/1.0.0/1",
            "name": "test_component",
            "version": "1.0.0",
            "description": "this is a test component",
            "type": "BUILD",
            "platform": "Linux",
            "owner": "111222333444",
            "data": "{'schemaVersion': '1.0', 'phases': [{'name': 'build', 'steps': [{'name': 'RunScript', 'action': 'ExecuteBash', 'timeoutSeconds': 120, 'onFailure': 'Abort', 'maxAttempts': 3, 'inputs': {'commands': [\"echo 'scripty things!'\\n\"]}}]}]}",
            "encrypted": True,
            "date_created": "2020-03-04T05:41:55.939Z",
            "tags": {
                "this": "isatag"
            }
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_component.return_value = dict(
            component=snake_dict_to_camel_dict(test_component))

        set_module_args({
            **{k: test_component[k] for k in ('name', 'description', 'platform', 'data', 'tags')},
            'semantic_version': test_component['version'],  # thanks aws
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_component.main()

        result = context.value.args[0]

        assert result['changed'] is False
        assert result['component'] is not None
        assert result['component'] == test_component
        assert client_mock.return_value.get_component.call_count == 1

    @patch.object(ec2_imagebuilder_component.AnsibleAWSModule, 'client')
    def test_present_when_component_different(self, client_mock):
        test_component = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:component/test-component/1.0.0/1",
            "name": "test_component",
            "version": "1.0.0",
            "description": "this is a test component",
            "type": "BUILD",
            "platform": "Linux",
            "owner": "111222333444",
            "data": "{'schemaVersion': '1.0', 'phases': [{'name': 'build', 'steps': [{'name': 'RunScript', 'action': 'ExecuteBash', 'timeoutSeconds': 120, 'onFailure': 'Abort', 'maxAttempts': 3, 'inputs': {'commands': [\"echo 'scripty things!'\\n\"]}}]}]}",
            "encrypted": True,
            "date_created": "2020-03-04T05:41:55.939Z",
            "tags": {
                "this": "isatag"
            }
        }

        updated_test_component = {
            **test_component,
            'version': "1.0.1",
            'description': "this is a test component -- updated!"
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_component.side_effect = [
            dict(
                component=snake_dict_to_camel_dict(test_component)),
            dict(
                component=snake_dict_to_camel_dict(updated_test_component)),
        ]
        client_mock.return_value.create_component.return_value = dict(
            requestId='mock_request_id', clientToken='mock_client_token', componentBuildVersionArn=updated_test_component['arn'])

        set_module_args({
            **{k: updated_test_component[k] for k in ('name', 'description', 'platform', 'data', 'tags')},
            'semantic_version': updated_test_component['version'],  # thanks aws
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_component.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['component'] is not None
        assert result['component'] == updated_test_component
        assert client_mock.return_value.get_component.call_count == 2
        assert client_mock.return_value.create_component.call_count == 1

    @patch.object(ec2_imagebuilder_component.AnsibleAWSModule, 'client')
    def test_present_when_tags_different(self, client_mock):
        test_component = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:component/test-component/1.0.0/1",
            "name": "test_component",
            "version": "1.0.0",
            "description": "this is a test component",
            "type": "BUILD",
            "platform": "Linux",
            "owner": "111222333444",
            "data": "{'schemaVersion': '1.0', 'phases': [{'name': 'build', 'steps': [{'name': 'RunScript', 'action': 'ExecuteBash', 'timeoutSeconds': 120, 'onFailure': 'Abort', 'maxAttempts': 3, 'inputs': {'commands': [\"echo 'scripty things!'\\n\"]}}]}]}",
            "encrypted": True,
            "date_created": "2020-03-04T05:41:55.939Z",
            "tags": {
                "this": "isatag"
            }
        }

        updated_test_component = {
            **test_component,
            'tags': {
                'thisis': 'adifferenttag'
            }
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_component.side_effect = [
            dict(
                component=snake_dict_to_camel_dict(test_component)),
            dict(
                component=snake_dict_to_camel_dict(updated_test_component)),
        ]
        client_mock.return_value.create_component.return_value = dict(
            requestId='mock_request_id', clientToken='mock_client_token', componentBuildVersionArn=updated_test_component['arn'])
        client_mock.return_value.untag_resource.return_value = {}
        client_mock.return_value.tag_resource.return_value = {}

        set_module_args({
            **{k: updated_test_component[k] for k in ('name', 'description', 'platform', 'data', 'tags')},
            'semantic_version': updated_test_component['version'],  # thanks aws
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_component.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['component'] is not None
        assert result['component'] == updated_test_component
        assert client_mock.return_value.get_component.call_count == 2
        assert client_mock.return_value.create_component.call_count == 0
        assert client_mock.return_value.tag_resource.call_count == 1
        args, kwargs = client_mock.return_value.tag_resource.call_args
        assert kwargs['tags'] == updated_test_component['tags']

    @patch.object(ec2_imagebuilder_component.AnsibleAWSModule, 'client')
    def test_absent_when_exists(self, client_mock):
        test_component = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:component/test-component/1.0.0/1",
            "name": "test_component",
            "version": "1.0.0",
            "description": "this is a test component",
            "type": "BUILD",
            "platform": "Linux",
            "owner": "111222333444",
            "data": "{'schemaVersion': '1.0', 'phases': [{'name': 'build', 'steps': [{'name': 'RunScript', 'action': 'ExecuteBash', 'timeoutSeconds': 120, 'onFailure': 'Abort', 'maxAttempts': 3, 'inputs': {'commands': [\"echo 'scripty things!'\\n\"]}}]}]}",
            "encrypted": True,
            "date_created": "2020-03-04T05:41:55.939Z",
            "tags": {
                "this": "isatag"
            }
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_component.side_effect = [
            dict(
                component=snake_dict_to_camel_dict(test_component)),
        ]
        client_mock.return_value.delete_component.return_value = dict(
            requestId='mock_request_id', componentBuildVersionArn=test_component['arn'])

        set_module_args({
            'name': test_component['name'],
            'semantic_version': test_component['version'],  # thanks aws
            'state': 'absent'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_component.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['component'] is not None
        assert result['component'] == dict(arn=test_component['arn'])
        assert client_mock.return_value.get_component.call_count == 1
        assert client_mock.return_value.delete_component.call_count == 1
        args, kwargs = client_mock.return_value.delete_component.call_args
        assert kwargs['componentBuildVersionArn'] == test_component['arn']
