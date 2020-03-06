# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from units.compat.mock import MagicMock, patch
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

from ansible.module_utils.ec2 import snake_dict_to_camel_dict
from ansible.modules.cloud.amazon import ec2_imagebuilder_recipe

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass


class TestEC2ImageBuilderRecipeModule(ModuleTestCase):

    mocked_get_caller_identity = {
        "UserId": "AROAJxxxxxxxxxxIPWZY:user.id",
        "Account": "111222333444",
        "Arn": "arn:aws:sts::111222333444:assumed-role/admin/test.user"
    }

    def test_required_parameters(self):
        set_module_args({})
        with pytest.raises(AnsibleFailJson) as context:
            ec2_imagebuilder_recipe.main()

        result = context.value.args[0]

        assert result['failed'] is True
        assert "name" in result['msg']
        assert "semantic_version" in result['msg']
        assert "state" in result['msg']

    @patch.object(ec2_imagebuilder_recipe.AnsibleAWSModule, 'client')
    def test_absent_when_not_exists(self, client_mock):
        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity

        client_mock.return_value.get_image_recipe.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetImageRecipe')
        set_module_args({
            'name': 'test_recipe',
            'semantic_version': '1.0.0',
            'state': 'absent'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_recipe.main()

        result = context.value.args[0]

        assert result['changed'] is False
        assert result['recipe'] is not None
        assert result['recipe']['arn'] is not None

    @patch.object(ec2_imagebuilder_recipe.AnsibleAWSModule, 'client')
    def test_present_when_not_exists(self, client_mock):
        test_recipe = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:image-recipe/test-recipe/1.0.0",
            "description": "this is a test recipe",
            "name": "test_recipe",
            "platform": "Linux",
            "owner": "111222333444",
            "version": "1.0.0",
            "components": [
                {
                    "component_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:component/test-component/1.0.0/1"
                }
            ],
            "parent_image": "arn:aws:imagebuilder:ap-southeast-2:aws:image/amazon-linux-2-x86/x.x.x",
            "date_created": "2020-02-26T04:34:07.168Z",
            "tags": {
                "this": "isatag"
            }
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_image_recipe.side_effect = [
            ClientError(
                {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetImageRecipe'),
            dict(imageRecipe=snake_dict_to_camel_dict(test_recipe))
        ]

        client_mock.return_value.create_image_recipe.return_value = dict(
            requestId='mock_request_id', clientToken='mock_client_token', imageRecipeArn=test_recipe['arn'])

        set_module_args({
            **{k: test_recipe[k] for k in ('name', 'description', 'components', 'parent_image', 'tags')},
            'semantic_version': test_recipe['version'],  # thanks aws
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_recipe.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['recipe'] is not None
        assert result['recipe'] == test_recipe
        assert client_mock.return_value.get_image_recipe.call_count == 2
        assert client_mock.return_value.create_image_recipe.call_count == 1

    @patch.object(ec2_imagebuilder_recipe.AnsibleAWSModule, 'client')
    def test_present_when_exists(self, client_mock):
        test_recipe = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:image-recipe/test-recipe/1.0.0",
            "description": "this is a test recipe",
            "name": "test_recipe",
            "platform": "Linux",
            "owner": "111222333444",
            "version": "1.0.0",
            "components": [
                {
                    "component_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:component/test-component/1.0.0/1"
                }
            ],
            "parent_image": "arn:aws:imagebuilder:ap-southeast-2:aws:image/amazon-linux-2-x86/x.x.x",
            "date_created": "2020-02-26T04:34:07.168Z",
            "tags": {
                "this": "isatag"
            }
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_image_recipe.side_effect = [
            dict(imageRecipe=snake_dict_to_camel_dict(test_recipe))
        ]

        set_module_args({
            **{k: test_recipe[k] for k in ('name', 'description', 'components', 'parent_image', 'tags')},
            'semantic_version': test_recipe['version'],  # thanks aws
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_recipe.main()

        result = context.value.args[0]

        assert result['changed'] is False
        assert result['recipe'] is not None
        assert result['recipe'] == test_recipe
        assert client_mock.return_value.get_image_recipe.call_count == 1
        assert client_mock.return_value.create_image_recipe.call_count == 0

    @patch.object(ec2_imagebuilder_recipe.AnsibleAWSModule, 'client')
    def test_present_when_recipe_different(self, client_mock):
        test_recipe = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:image-recipe/test-recipe/1.0.0",
            "description": "this is a test recipe",
            "name": "test_recipe",
            "platform": "Linux",
            "owner": "111222333444",
            "version": "1.0.0",
            "components": [
                {
                    "component_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:component/test-component/1.0.0/1"
                }
            ],
            "parent_image": "arn:aws:imagebuilder:ap-southeast-2:aws:image/amazon-linux-2-x86/x.x.x",
            "date_created": "2020-02-26T04:34:07.168Z",
            "tags": {
                "this": "isatag"
            }
        }

        updated_test_recipe = {
            **test_recipe,
            "components": [
                {
                    "component_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:component/test-component/1.0.1/1"
                },
                {
                    "component_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:component/test-componen-2/1.0.0/1"
                }
            ],
            'version': "1.0.1",
            'description': "this is a test recipe -- updated!"
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_image_recipe.side_effect = [
            dict(imageRecipe=snake_dict_to_camel_dict(test_recipe)),
            dict(imageRecipe=snake_dict_to_camel_dict(updated_test_recipe))
        ]

        client_mock.return_value.create_image_recipe.return_value = dict(
            requestId='mock_request_id', clientToken='mock_client_token', imageRecipeArn=updated_test_recipe['arn'])

        set_module_args({
            **{k: updated_test_recipe[k] for k in ('name', 'description', 'components', 'parent_image', 'tags')},
            'semantic_version': updated_test_recipe['version'],  # thanks aws
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_recipe.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['recipe'] is not None
        assert result['recipe'] == updated_test_recipe
        assert client_mock.return_value.get_image_recipe.call_count == 2
        assert client_mock.return_value.create_image_recipe.call_count == 1

    @patch.object(ec2_imagebuilder_recipe.AnsibleAWSModule, 'client')
    def test_present_when_tags_different(self, client_mock):
        test_recipe = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:image-recipe/test-recipe/1.0.0",
            "description": "this is a test recipe",
            "name": "test_recipe",
            "platform": "Linux",
            "owner": "111222333444",
            "version": "1.0.0",
            "components": [
                {
                    "component_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:component/test-component/1.0.0/1"
                }
            ],
            "parent_image": "arn:aws:imagebuilder:ap-southeast-2:aws:image/amazon-linux-2-x86/x.x.x",
            "date_created": "2020-02-26T04:34:07.168Z",
            "tags": {
                "this": "isatag"
            }
        }

        updated_test_recipe = {
            **test_recipe,
            "tags": {
                "thisis": "adifferenttag"
            }
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_image_recipe.side_effect = [
            dict(imageRecipe=snake_dict_to_camel_dict(test_recipe)),
            dict(imageRecipe=snake_dict_to_camel_dict(updated_test_recipe))
        ]

        client_mock.return_value.create_image_recipe.return_value = dict(
            requestId='mock_request_id', clientToken='mock_client_token', imageRecipeArn=updated_test_recipe['arn'])

        set_module_args({
            **{k: updated_test_recipe[k] for k in ('name', 'description', 'components', 'parent_image', 'tags')},
            'semantic_version': updated_test_recipe['version'],  # thanks aws
            'state': 'present'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_recipe.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['recipe'] is not None
        assert result['recipe'] == updated_test_recipe
        assert client_mock.return_value.get_image_recipe.call_count == 2
        assert client_mock.return_value.create_image_recipe.call_count == 0
        assert client_mock.return_value.tag_resource.call_count == 1
        _, kwargs = client_mock.return_value.tag_resource.call_args
        assert kwargs['tags'] == updated_test_recipe['tags']

    @patch.object(ec2_imagebuilder_recipe.AnsibleAWSModule, 'client')
    def test_absent_when_exists(self, client_mock):
        test_recipe = {
            "arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:image-recipe/test-recipe/1.0.0",
            "description": "this is a test recipe",
            "name": "test_recipe",
            "platform": "Linux",
            "owner": "111222333444",
            "version": "1.0.0",
            "components": [
                {
                    "component_arn": "arn:aws:imagebuilder:ap-southeast-2:111222333444:component/test-component/1.0.0/1"
                }
            ],
            "parent_image": "arn:aws:imagebuilder:ap-southeast-2:aws:image/amazon-linux-2-x86/x.x.x",
            "date_created": "2020-02-26T04:34:07.168Z",
            "tags": {
                "this": "isatag"
            }
        }

        client_mock.return_value.get_caller_identity.return_value = self.mocked_get_caller_identity
        client_mock.return_value.get_image_recipe.side_effect = [
            dict(imageRecipe=snake_dict_to_camel_dict(test_recipe))
        ]
        client_mock.return_value.delete_image_recipe.return_value = dict(
            requestId='mock_request_id', imageRecipeArn=test_recipe['arn'])

        set_module_args({
            'name': test_recipe['name'],
            'semantic_version': test_recipe['version'],  # thanks aws
            'state': 'absent'
        })
        with pytest.raises(AnsibleExitJson) as context:
            ec2_imagebuilder_recipe.main()

        result = context.value.args[0]

        assert result['changed'] is True
        assert result['recipe'] is not None
        assert result['recipe'] == dict(arn=test_recipe['arn'])
        assert client_mock.return_value.get_image_recipe.call_count == 1
        assert client_mock.return_value.delete_image_recipe.call_count == 1
        _, kwargs = client_mock.return_value.delete_image_recipe.call_args
        assert kwargs['imageRecipeArn'] == test_recipe['arn']
