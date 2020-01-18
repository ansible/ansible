# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from units.compat.mock import MagicMock, patch
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args
from ansible.module_utils.ec2 import HAS_BOTO3


if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("ec2_asg_scheduled_action.py requires the `boto3` and `botocore` modules")
else:
    import boto3
    from ansible.modules.cloud.amazon import ec2_asg_scheduled_action as scheduled_action
    from botocore.exceptions import ClientError


class TestModule(ModuleTestCase):

    def get_valid_args(self):
        return dict({
            'autoscaling_group_name': 'foo',
            'desired_capacity': '2',
            'recurrence': "daily",
            'region': 'up-north-1',
            'scheduled_action_name': 'bar',
        })

    def get_error(self):
        error_response = {"Error": {"Code": "Bad"}}
        return ClientError(error_response, "test")

    def test_module_fail_when_required_args_missing(self):
        with pytest.raises(AnsibleFailJson):
            set_module_args({})
            scheduled_action.main()

    @patch('ansible.modules.cloud.amazon.ec2_asg_scheduled_action.AnsibleAWSModule.client')
    def test_module_exit_when_required_args_present(self, aws_client):
        with pytest.raises(AnsibleExitJson):
            set_module_args(self.get_valid_args())
            scheduled_action.main()

    @patch('ansible.module_utils.aws.core.HAS_BOTO3', new=False)
    @patch('ansible.modules.cloud.amazon.ec2_asg_scheduled_action.AnsibleAWSModule.client')
    def test_module_fail_when_boto_absent(self, aws_client):
        with pytest.raises(AnsibleFailJson):
            set_module_args(self.get_valid_args())
            scheduled_action.main()

    @patch('ansible.modules.cloud.amazon.ec2_asg_scheduled_action.AnsibleAWSModule.client')
    def test_module_fail_when_client_error(self, client):
        client.side_effect = self.get_error()
        with pytest.raises(AnsibleFailJson):
            set_module_args(self.get_valid_args())
            scheduled_action.main()

    def test_get_common_params(self):
        module = MagicMock()
        module.params = {
            'autoscaling_group_name': 'group',
            'scheduled_action_name': 'action'
        }
        result = scheduled_action.get_common_params(module)
        assert result['AutoScalingGroupName'] == 'group'
        assert result['ScheduledActionName'] == 'action'
        assert result['aws_retry'] is True

    @patch.object(scheduled_action, 'get_common_params')
    def test_describe_scheduled_actions(self, get_common_params_mock):
        params = {
            'ScheduledActionName': 'foo'
        }
        describe = {
            'ScheduledActionNames': [params['ScheduledActionName']]
        }
        actions = ['action']
        get_common_params_mock.return_value = params
        module = MagicMock()
        client = MagicMock()
        client.describe_scheduled_actions.return_value = actions
        result = scheduled_action.describe_scheduled_actions(client, module)
        assert result == actions
        client.describe_scheduled_actions.assert_called_once_with(**describe)

    @patch.object(scheduled_action, 'get_common_params')
    def test_describe_scheduled_actions_empty(self, get_common_params_mock):
        params = {
            'ScheduledActionName': 'foo'
        }
        describe = {
            'ScheduledActionNames': [params['ScheduledActionName']]
        }
        get_common_params_mock.return_value = params
        module = MagicMock()
        client = MagicMock()
        client.describe_scheduled_actions.side_effect = self.get_error()
        result = scheduled_action.describe_scheduled_actions(client, module)
        assert result == {}
        client.describe_scheduled_actions.assert_called_once_with(**describe)

    @patch.object(scheduled_action, 'describe_scheduled_actions')
    def test_delete_scheduled_action_empty(self, describe_scheduled_actions_mock):
        describe_scheduled_actions_mock.return_value = {}
        module = MagicMock()
        client = MagicMock()
        (changed, results) = scheduled_action.delete_scheduled_action(client, module)
        assert changed is False
        assert results == []
        assert client.describe_scheduled_actions.call_count == 0

    @patch.object(scheduled_action, 'describe_scheduled_actions')
    def test_delete_scheduled_action_no_actions(self, describe_scheduled_actions_mock):
        describe_scheduled_actions_mock.return_value = {'ScheduledUpdateGroupActions': []}
        module = MagicMock()
        client = MagicMock()
        (changed, results) = scheduled_action.delete_scheduled_action(client, module)
        assert changed is False
        assert results == []
        assert client.describe_scheduled_actions.call_count == 0

    @patch.object(scheduled_action, 'describe_scheduled_actions')
    @patch.object(scheduled_action, 'get_common_params')
    def test_delete_scheduled_action_deleted(self, get_common_params_mock, describe_scheduled_actions_mock):
        params = {
            'ScheduledActionName': 'bar'
        }
        describe = {
            'ScheduledUpdateGroupActions': [params['ScheduledActionName']]
        }
        expect = {'client': 'success'}
        get_common_params_mock.return_value = params
        describe_scheduled_actions_mock.return_value = describe
        module = MagicMock()
        client = MagicMock()
        client.delete_scheduled_action.return_value = expect
        (changed, results) = scheduled_action.delete_scheduled_action(client, module)
        assert changed is True
        assert results == expect
        client.delete_scheduled_action.assert_called_once_with(**params)

    @patch.object(scheduled_action, 'describe_scheduled_actions')
    @patch.object(scheduled_action, 'get_common_params')
    def test_delete_scheduled_action_fail(self, get_common_params_mock, describe_scheduled_actions_mock):
        params = {
            'ScheduledActionName': 'bar'
        }
        describe = {
            'ScheduledUpdateGroupActions': [params['ScheduledActionName']]
        }
        get_common_params_mock.return_value = params
        describe_scheduled_actions_mock.return_value = describe
        module = MagicMock()
        client = MagicMock()
        error = self.get_error()
        client.delete_scheduled_action.side_effect = error
        scheduled_action.delete_scheduled_action(client, module)
        client.delete_scheduled_action.assert_called_once_with(**params)
        module.fail_json.assert_called_once_with(msg=str(error))

    @patch.object(scheduled_action, 'describe_scheduled_actions')
    @patch.object(scheduled_action, 'get_common_params')
    def test_put_scheduled_update_group_action_params(self, get_common_params_mock, describe_scheduled_actions_mock):
        get_common_params_mock.return_value = {'aws_retry': True}
        module = MagicMock()
        module.params = {
            'autoscaling_group_name': 'group',
            'scheduled_action_name': 'action',
            'recurrence': 'daily',
            'desired_capacity': '1',
            'min_size': '0',
            'max_size': '2',
            'start_time': 'now',
            'end_time': 'never'
        }
        expect = {
            'aws_retry': True,
            'Recurrence': module.params['recurrence'],
            'DesiredCapacity': module.params['desired_capacity'],
            'MinSize': module.params['min_size'],
            'MaxSize': module.params['max_size'],
            'StartTime': module.params['start_time'],
            'EndTime': module.params['end_time']
        }
        client = MagicMock()
        (changed, results) = scheduled_action.put_scheduled_update_group_action(client, module)
        client.put_scheduled_update_group_action.assert_called_once_with(**expect)
        assert changed is True

    @patch.object(scheduled_action, 'describe_scheduled_actions')
    @patch.object(scheduled_action, 'get_common_params')
    def test_put_scheduled_update_group_action_unchanged(self, get_common_params_mock, describe_scheduled_actions_mock):
        get_common_params_mock.return_value = {}
        describe_scheduled_actions_mock.return_value = {'ScheduledUpdateGroupActions': ['existing']}
        module = MagicMock()
        client = MagicMock()
        (changed, results) = scheduled_action.put_scheduled_update_group_action(client, module)
        assert describe_scheduled_actions_mock.call_count == 2
        assert changed is False

    @patch.object(scheduled_action, 'describe_scheduled_actions')
    @patch.object(scheduled_action, 'get_common_params')
    def test_put_scheduled_update_group_action_error(self, get_common_params_mock, describe_scheduled_actions_mock):
        get_common_params_mock.return_value = {}
        describe_scheduled_actions_mock.return_value = {'ScheduledUpdateGroupActions': []}
        module = MagicMock()
        client = MagicMock()
        error = self.get_error()
        client.put_scheduled_update_group_action.side_effect = error
        scheduled_action.put_scheduled_update_group_action(client, module)
        module.fail_json.assert_called_once_with(msg=str(error))
