# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, Mock, call
from ansible.modules.cloud.amazon import aws_iot_thing
from ansible.module_utils.aws.core import AnsibleAWSModule
from botocore.exceptions import ClientError, BotoCoreError

boto3 = pytest.importorskip('boto3')

resource_not_found_response = {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Fake Testing Error'}}
operation_name = 'FakeOperation'
resource_not_found_exception = ClientError(resource_not_found_response, operation_name)

fake_response = {'Error': {'Code': 'FakeException', 'Message': 'Fake Texesting Error'}}
generic_client_exception = ClientError(fake_response, operation_name)

boto_core_error = BotoCoreError()


class AnsibleFailJson(Exception):
    pass


def fail_json(*args, **kwargs):
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


def fail_json_aws(*args, **kwargs):
    fail_json(**kwargs)


class AssertModuleFailsContext(object):
    def __init__(self, test_case, msg):
        self.test_case = test_case
        self.msg = msg
        self.context = self.test_case.assertRaises(AnsibleFailJson)

    def __enter__(self):
        self.context.__enter__()
        return self

    def __exit__(self, exc_type, value, traceback):
        if not self.context.__exit__(exc_type, value, traceback):
            return False

        exception_args = self.context.exception.args[0]
        self.test_case.assertEqual(self.msg, exception_args['msg'])
        self.test_case.assertTrue(exception_args['failed'])
        return True


class AwsIotThing(unittest.TestCase):
    def setUp(self):
        client = boto3.client('iot', region_name='us-east-1')
        self.client = Mock(spec=client)
        self.aws_module = Mock(spec=AnsibleAWSModule)
        self.aws_module.params = dict(
            attached_principals=[],
            detached_principals=[],
            attributes=dict(),
            absent_attributes=[]
        )
        self.aws_module.fail_json.side_effect = fail_json
        self.aws_module.fail_json_aws.side_effect = fail_json_aws

    def test_return_thing_changed(self):
        thing = dict(
            thingName='mything',
            attributes=dict(a1='v1'),
            thingTypeName='mytype',
            version=7,
            defaultClientId='mything',
            ResponseMetadata=dict()
        )
        principals = ['principal1', 'principal2']

        expected = dict(
            changed=True,
            thing_name='mything',
            attributes=dict(a1='v1'),
            thing_type_name='mytype',
            version=7,
            default_client_id='mything',
            principals=principals
        )

        result = aws_iot_thing.format_thing(True, thing, principals)

        self.assertEqual(expected, result)

    def test_return_thing_unchanged(self):
        thing = dict(
            thingName='mything',
            attributes=dict(),
            version=11,
            defaultClientId='mything',
            ResponseMetadata=dict()
        )
        principals = []

        expected = dict(
            changed=False,
            thing_name='mything',
            attributes=dict(),
            version=11,
            default_client_id='mything',
            principals=principals
        )

        result = aws_iot_thing.format_thing(False, thing, principals)

        self.assertEqual(expected, result)

    def test_describe_and_format_changed_thing(self):
        thing_name = 'mything'
        additional_details = dict(thing_arn='arn')

        self.client.describe_thing.return_value = dict(
            thingName=thing_name,
            attributes=dict(a1='v1'),
            thingTypeName='mytype',
            version=7,
            defaultClientId='mything',
            ResponseMetadata=dict()
        )

        principals = ['principal']

        expected = dict(
            changed=True,
            thing_name=thing_name,
            attributes=dict(a1='v1'),
            thing_type_name='mytype',
            version=7,
            default_client_id='mything',
            principals=principals,
            thing_arn='arn'
        )

        result = aws_iot_thing.describe_and_format_changed_thing(
            self.aws_module, self.client, thing_name, principals, additional_details)

        self.assertEqual(expected, result)
        self.client.describe_thing.assert_called_once_with(thingName=thing_name)

    def test_describe_and_format_thing_fails_with_client_exception(self):
        thing_name = 'mything'
        self.client.describe_thing.side_effect = resource_not_found_exception
        with self.assert_module_failed('Describing thing'):
            aws_iot_thing.describe_and_format_changed_thing(self.aws_module, self.client, thing_name, [], dict)

    def test_describe_and_format_thing_fails_with_core_error(self):
        thing_name = 'mything'
        self.client.describe_thing.side_effect = boto_core_error
        with self.assert_module_failed('Describing thing'):
            aws_iot_thing.describe_and_format_changed_thing(self.aws_module, self.client, thing_name, [], dict)

    def test_parse_expected_version_when_none_specified(self):
        thing = dict(version=1)
        result = aws_iot_thing.parse_expected_version(self.aws_module, thing)
        self.assertIsNone(result)

    def test_parse_expected_version_match(self):
        thing = dict(version=7)
        self.aws_module.params['expected_version'] = 7
        result = aws_iot_thing.parse_expected_version(self.aws_module, thing)
        self.assertEqual(7, result)

    def test_parse_expected_version_mismatch(self):
        thing = dict(version=7)
        self.aws_module.params['expected_version'] = 8
        with self.assert_module_failed('Expected thing version 8 but actual version is 7'):
            aws_iot_thing.parse_expected_version(self.aws_module, thing)

    def test_detach_principal_success(self):
        aws_iot_thing.detach_principal(self.aws_module, self.client, 'mything', 'principal')
        self.client.detach_thing_principal.assert_called_once_with(thingName='mything', principal='principal')

    def test_detach_principal_client_exception(self):
        self.client.detach_thing_principal.side_effect = resource_not_found_exception
        with self.assert_module_failed('Detaching principal'):
            aws_iot_thing.detach_principal(self.aws_module, self.client, 'mything', 'principal')

    def test_detach_principal_boto_core_error(self):
        self.client.detach_thing_principal.side_effect = boto_core_error
        with self.assert_module_failed('Detaching principal'):
            aws_iot_thing.detach_principal(self.aws_module, self.client, 'mything', 'principal')

    def test_attach_principal_success(self):
        aws_iot_thing.attach_principal(self.aws_module, self.client, 'mything', 'principal')
        self.client.attach_thing_principal.assert_called_once_with(thingName='mything', principal='principal')

    def test_attach_principal_client_exception(self):
        self.client.attach_thing_principal.side_effect = resource_not_found_exception
        with self.assert_module_failed('Attaching principal'):
            aws_iot_thing.attach_principal(self.aws_module, self.client, 'mything', 'principal')

    def test_attach_principal_boto_core_error(self):
        self.client.attach_thing_principal.side_effect = boto_core_error
        with self.assert_module_failed('Attaching principal'):
            aws_iot_thing.attach_principal(self.aws_module, self.client, 'mything', 'principal')

    def test_list_principals(self):
        expected = ['p1', 'p2', 'p3']
        self.client.list_thing_principals.return_value = dict(principals=expected)
        result = aws_iot_thing.list_principals(self.aws_module, self.client, 'mything')
        self.assertEqual(expected, result)
        self.client.list_thing_principals.assert_called_once_with(thingName='mything')

    def test_list_principals_client_exception(self):
        self.client.list_thing_principals.side_effect = resource_not_found_exception
        with self.assert_module_failed('Listing thing principals'):
            aws_iot_thing.list_principals(self.aws_module, self.client, 'mything')

    def test_list_principals_boto_core_error(self):
        self.client.list_thing_principals.side_effect = boto_core_error
        with self.assert_module_failed('Listing thing principals'):
            aws_iot_thing.list_principals(self.aws_module, self.client, 'mything')

    def test_get_absent_attributes(self):
        self.aws_module.params['absent_attributes'] = ['shenzi', 'banzi', 'ed']
        result = aws_iot_thing.get_absent_attributes(self.aws_module)
        self.assertEqual(dict(shenzi='', banzi='', ed=''), result)

    @patch('ansible.modules.cloud.amazon.aws_iot_thing.detach_principal')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.list_principals')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.parse_expected_version')
    def test_delete_thing(self, mock_parse_expected_version, mock_list_principals, mock_detach_principal):
        self.aws_module.check_mode = False
        mock_parse_expected_version.return_value = 7
        mock_list_principals.return_value = ['shenzi', 'banzi', 'ed']
        thing_name = 'mything'

        thing = dict(
            thingName=thing_name,
            attributes=dict(a1='v1'),
            thingTypeName='mytype',
            version=7,
            defaultClientId='mything',
            ResponseMetadata=dict()
        )

        aws_iot_thing.delete_thing(self.aws_module, self.client, thing)

        self.client.delete_thing.assert_called_once_with(**dict(thingName='mything', expectedVersion=7))

        expected_detach_calls = [
            call(self.aws_module, self.client, thing_name, 'shenzi'),
            call(self.aws_module, self.client, thing_name, 'banzi'),
            call(self.aws_module, self.client, thing_name, 'ed')
        ]
        mock_detach_principal.assert_has_calls(expected_detach_calls, any_order=True)

    @patch('ansible.modules.cloud.amazon.aws_iot_thing.detach_principal')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.list_principals')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.parse_expected_version')
    def test_delete_thing_client_exception(
            self, mock_parse_expected_version, mock_list_principals, mock_detach_principal):
        self.aws_module.check_mode = False
        self.client.delete_thing.side_effect = resource_not_found_exception
        mock_parse_expected_version.return_value = 7
        mock_list_principals.return_value = ['shenzi', 'banzi', 'ed']
        thing_name = 'mything'

        thing = dict(
            thingName=thing_name,
            attributes=dict(a1='v1'),
            thingTypeName='mytype',
            version=7,
            defaultClientId='mything',
            ResponseMetadata=dict()
        )

        with self.assert_module_failed('Deleting thing'):
            aws_iot_thing.delete_thing(self.aws_module, self.client, thing)

    @patch('ansible.modules.cloud.amazon.aws_iot_thing.detach_principal')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.list_principals')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.parse_expected_version')
    def test_delete_thing_boto_core_error(
            self, mock_parse_expected_version, mock_list_principals, mock_detach_principal):
        self.aws_module.check_mode = False
        self.client.delete_thing.side_effect = boto_core_error
        mock_parse_expected_version.return_value = 7
        mock_list_principals.return_value = ['shenzi', 'banzi', 'ed']
        thing_name = 'mything'

        thing = dict(
            thingName=thing_name,
            attributes=dict(a1='v1'),
            thingTypeName='mytype',
            version=7,
            defaultClientId='mything',
            ResponseMetadata=dict()
        )

        with self.assert_module_failed('Deleting thing'):
            aws_iot_thing.delete_thing(self.aws_module, self.client, thing)

    @patch('ansible.modules.cloud.amazon.aws_iot_thing.list_principals')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.detach_principal')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.attach_principal')
    def test_change_principals_no_changes(self, mock_attach_principal, mock_detach_principal, mock_list_principals):
        self.aws_module.check_mode = False
        self.aws_module.params['attached_principals'] = ['Pumbaa', 'Timon']
        self.aws_module.params['detached_principals'] = ['Shenzi', 'Banzi']
        mock_list_principals.return_value = ['Pumbaa', 'Timon']

        result = aws_iot_thing.change_principals(self.aws_module, self.client, 'mything')

        self.assertFalse(result[0])
        self.assert_list_equal(['Pumbaa', 'Timon'], result[1])

    @patch('ansible.modules.cloud.amazon.aws_iot_thing.list_principals')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.detach_principal')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.attach_principal')
    def test_change_principals_attach(self, mock_attach_principal, mock_detach_principal, mock_list_principals):
        self.aws_module.check_mode = False
        self.aws_module.params['attached_principals'] = ['Pumbaa', 'Timon']
        self.aws_module.params['detached_principals'] = ['Shenzi', 'Banzi']
        mock_list_principals.return_value = ['Pumbaa']

        result = aws_iot_thing.change_principals(self.aws_module, self.client, 'mything')

        self.assertTrue(result[0])
        self.assert_list_equal(['Pumbaa', 'Timon'], result[1])

    @patch('ansible.modules.cloud.amazon.aws_iot_thing.list_principals')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.detach_principal')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.attach_principal')
    def test_change_principals_dettach(self, mock_attach_principal, mock_detach_principal, mock_list_principals):
        self.aws_module.check_mode = False
        self.aws_module.params['attached_principals'] = ['Pumbaa', 'Timon']
        self.aws_module.params['detached_principals'] = ['Shenzi', 'Banzi']
        mock_list_principals.return_value = ['Pumbaa', 'Banzi', 'Timon']

        result = aws_iot_thing.change_principals(self.aws_module, self.client, 'mything')

        self.assertTrue(result[0])
        self.assert_list_equal(['Pumbaa', 'Timon'], result[1])

    @patch('ansible.modules.cloud.amazon.aws_iot_thing.list_principals')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.detach_principal')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.attach_principal')
    def test_change_principals_attach_and_detach(
            self, mock_attach_principal, mock_detach_principal, mock_list_principals):
        self.aws_module.check_mode = False
        self.aws_module.params['attached_principals'] = ['Pumbaa', 'Timon']
        self.aws_module.params['detached_principals'] = ['Shenzi', 'Banzi']
        mock_list_principals.return_value = ['Banzi', 'Simba', 'Timon', 'Shenzi']

        result = aws_iot_thing.change_principals(self.aws_module, self.client, 'mything')

        self.assertTrue(result[0])
        self.assert_list_equal(['Pumbaa', 'Timon', 'Simba'], result[1])

    def test_change_thing_in_check_mode_type(self):
        thing = dict(version=7)
        update_args = dict(thingTypeName='mytype')
        aws_iot_thing.change_thing_in_check_mode(self.aws_module, thing, update_args)
        self.assertEqual(8, thing['version'])
        self.assertEqual('mytype', thing['thingTypeName'])

    def test_change_thing_in_check_mode_remove_type(self):
        thing = dict(version=7, thingTypeName='mytype')
        update_args = dict(removeThingType=True)
        aws_iot_thing.change_thing_in_check_mode(self.aws_module, thing, update_args)
        self.assertEqual(8, thing['version'])
        self.assertIsNone(thing.get('thingTypeName'))

    def test_change_thing_in_check_mode_attributes(self):
        thing = dict(
            version=10,
            attributes=dict(
                warthog='Pumbaa',
                hyena='Ed',
                meerkat='Timon'
            )
        )
        update_args = dict(attributePayload=dict(attributes=dict(
            king='Simba',
            hyena='',
            warthog='Pumbaa'
        )))
        aws_iot_thing.change_thing_in_check_mode(self.aws_module, thing, update_args)
        self.assertEqual(11, thing['version'])
        self.assertEqual(dict(warthog='Pumbaa', meerkat='Timon', king='Simba'), thing['attributes'])

    def test_change_thing_in_check_mode_wrong_version(self):
        thing = dict(version=2)
        update_args = dict(expectedVersion=1)
        with self.assert_module_failed('Expected thing version 1 but actual version is 2'):
            aws_iot_thing.change_thing_in_check_mode(self.aws_module, thing, update_args)

    def test_change_thing_in_cloud_success(self):
        aws_iot_thing.change_thing_in_cloud(self.aws_module, self.client, dict())
        self.assertEqual(1, self.client.update_thing.call_count)

    def test_change_thing_in_cloud_client_exception(self):
        self.client.update_thing.side_effect = resource_not_found_exception
        with self.assert_module_failed('Updating thing'):
            aws_iot_thing.change_thing_in_cloud(self.aws_module, self.client, dict())

    def test_change_thing_in_cloud_boto_core_error(self):
        self.client.update_thing.side_effect = boto_core_error
        with self.assert_module_failed('Updating thing'):
            aws_iot_thing.change_thing_in_cloud(self.aws_module, self.client, dict())

    def test_set_attribute_delta_no_change(self):
        self.aws_module.params['attributes'] = dict(
            warthog='Pumbaa',
            meerkat='Timon'
        )
        self.aws_module.params['absent_attributes'] = ['hyena']

        thing = dict(attributes=dict(
            warthog='Pumbaa',
            meerkat='Timon'
        ))

        update_args = dict()

        aws_iot_thing.set_attribute_delta(self.aws_module, thing, update_args)

        self.assertIsNone(update_args.get('attributePayload'))

    def test_set_attribute_delta_addition(self):
        self.aws_module.params['attributes'] = dict(
            warthog='Pumbaa',
            meerkat='Timon'
        )

        thing = dict(attributes=dict(
            warthog='Pumbaa'
        ))

        expected = dict(
            attributes=dict(
                meerkat='Timon'
            ),
            merge=True
        )

        update_args = dict()

        aws_iot_thing.set_attribute_delta(self.aws_module, thing, update_args)

        self.assertEqual(expected, update_args.get('attributePayload'))

    def test_set_attribute_delta_change(self):
        self.aws_module.params['attributes'] = dict(
            warthog='Pumbaa',
            lion='Simba'
        )

        thing = dict(attributes=dict(
            warthog='Pumbaa',
            lion='Mufasa'
        ))

        expected = dict(
            attributes=dict(
                lion='Simba'
            ),
            merge=True
        )

        update_args = dict()

        aws_iot_thing.set_attribute_delta(self.aws_module, thing, update_args)

        self.assertEqual(expected, update_args.get('attributePayload'))

    def test_set_attribute_delta_remove(self):
        self.aws_module.params['absent_attributes'] = ['hyena']

        thing = dict(attributes=dict(
            warthog='Pumbaa',
            hyena='Shenzi'
        ))

        expected = dict(
            attributes=dict(
                hyena=''
            ),
            merge=True
        )

        update_args = dict()

        aws_iot_thing.set_attribute_delta(self.aws_module, thing, update_args)

        self.assertEqual(expected, update_args.get('attributePayload'))

    def test_set_type_delta_no_type_no_change(self):
        thing = dict()
        update_args = dict()
        aws_iot_thing.set_type_delta(self.aws_module, thing, update_args)
        self.assertIsNone(update_args.get('thingTypeName'))
        self.assertIsNone(update_args.get('removeThingType'))

    def test_set_type_delta_type_does_not_change(self):
        self.aws_module.params['type'] = 'mytype'
        thing = dict(thingTypeName='mytype')
        update_args = dict()
        aws_iot_thing.set_type_delta(self.aws_module, thing, update_args)
        self.assertIsNone(update_args.get('thingTypeName'))
        self.assertIsNone(update_args.get('removeThingType'))

    def test_set_type_delta_add_type(self):
        self.aws_module.params['type'] = 'mytype'
        thing = dict()
        update_args = dict()
        aws_iot_thing.set_type_delta(self.aws_module, thing, update_args)
        self.assertEqual('mytype', update_args.get('thingTypeName'))
        self.assertIsNone(update_args.get('removeThingType'))

    def test_set_type_delta_change_type(self):
        self.aws_module.params['type'] = 'newtype'
        thing = dict(thingTypeName='oldtype')
        update_args = dict()
        aws_iot_thing.set_type_delta(self.aws_module, thing, update_args)
        self.assertEqual('newtype', update_args.get('thingTypeName'))
        self.assertIsNone(update_args.get('removeThingType'))

    def test_set_type_delta_remove_nothing(self):
        self.aws_module.params['remove_type'] = True
        thing = dict()
        update_args = dict()
        aws_iot_thing.set_type_delta(self.aws_module, thing, update_args)
        self.assertIsNone(update_args.get('thingTypeName'))
        self.assertIsNone(update_args.get('removeThingType'))

    def test_set_type_delta_remove_type(self):
        self.aws_module.params['remove_type'] = True
        thing = dict(thingTypeName='mytype')
        update_args = dict()
        aws_iot_thing.set_type_delta(self.aws_module, thing, update_args)
        self.assertIsNone(update_args.get('thingTypeName'))
        self.assertTrue(update_args.get('removeThingType'))

    @patch('ansible.modules.cloud.amazon.aws_iot_thing.change_thing_in_check_mode')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.change_thing_in_cloud')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.set_attribute_delta')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.set_type_delta')
    def test_change_thing_no_changes(
            self, mock_set_type_delta, mock_set_attribute_delta, mock_change_in_cloud, mock_change_in_check):
        thing = dict()
        thing_name = 'mything'
        expected_version = 1

        changed = aws_iot_thing.change_thing(self.aws_module, self.client, thing, thing_name, expected_version)

        self.assertFalse(changed)
        self.assertEqual(1, mock_set_type_delta.call_count)
        self.assertEqual(1, mock_set_attribute_delta.call_count)
        self.assertFalse(mock_change_in_cloud.called)
        self.assertFalse(mock_change_in_check.called)

    @staticmethod
    def add_dummy_to_update_args(aws_module, thing, update_args):
        update_args['dummy'] = 'dummy'

    @patch('ansible.modules.cloud.amazon.aws_iot_thing.change_thing_in_check_mode')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.change_thing_in_cloud')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.set_attribute_delta')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.set_type_delta')
    def test_change_thing_changes_in_normal_mode(
            self, mock_set_type_delta, mock_set_attribute_delta, mock_change_in_cloud, mock_change_in_check):
        self.aws_module.check_mode = False
        mock_set_type_delta.side_effect = self.add_dummy_to_update_args
        thing = dict()
        thing_name = 'mything'
        expected_version = 1

        expected = dict(
            dummy='dummy',
            thingName=thing_name,
            expectedVersion=expected_version
        )

        changed = aws_iot_thing.change_thing(self.aws_module, self.client, thing, thing_name, expected_version)

        self.assertTrue(changed)
        self.assertEqual(1, mock_set_type_delta.call_count)
        self.assertEqual(1, mock_set_attribute_delta.call_count)
        mock_change_in_cloud.assert_called_once_with(self.aws_module, self.client, expected)
        self.assertFalse(mock_change_in_check.called)

    @patch('ansible.modules.cloud.amazon.aws_iot_thing.change_thing_in_check_mode')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.change_thing_in_cloud')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.set_attribute_delta')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.set_type_delta')
    def test_change_thing_changes_in_check_mode(
            self, mock_set_type_delta, mock_set_attribute_delta, mock_change_in_cloud, mock_change_in_check):
        self.aws_module.check_mode = True
        mock_set_attribute_delta.side_effect = self.add_dummy_to_update_args
        thing = dict()
        thing_name = 'mything'
        expected_version = None

        expected = dict(
            dummy='dummy',
            thingName=thing_name
        )

        changed = aws_iot_thing.change_thing(self.aws_module, self.client, thing, thing_name, expected_version)

        self.assertTrue(changed)
        self.assertEqual(1, mock_set_type_delta.call_count)
        self.assertEqual(1, mock_set_attribute_delta.call_count)
        self.assertFalse(mock_change_in_cloud.called)
        mock_change_in_check.assert_called_once_with(self.aws_module, thing, expected)

    @patch('ansible.modules.cloud.amazon.aws_iot_thing.format_thing')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.describe_and_format_changed_thing')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.change_principals')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.change_thing')
    def test_update_thing_with_change(
            self, mock_change_thing, mock_change_principals, mock_describe_and_format_thing, mock_format_thing):
        self.aws_module.check_mode = False
        mock_change_thing.return_value = True
        mock_change_principals.return_value = (False, [])
        thing = dict(
            thingName='mything'
        )

        aws_iot_thing.update_thing(self.aws_module, thing, self.client)

        self.assertEqual(1, mock_change_thing.call_count)
        self.assertEqual(1, mock_change_principals.call_count)
        mock_describe_and_format_thing.assert_called_once_with(self.aws_module, self.client, 'mything', [], dict())
        self.assertFalse(mock_format_thing.called)

    @patch('ansible.modules.cloud.amazon.aws_iot_thing.format_thing')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.describe_and_format_changed_thing')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.change_principals')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.change_thing')
    def test_update_thing_with_change_in_check_mode(
            self, mock_change_thing, mock_change_principals, mock_describe_and_format_thing, mock_format_thing):
        self.aws_module.check_mode = True
        mock_change_thing.return_value = True
        mock_change_principals.return_value = (True, ['p1'])
        thing = dict(
            thingName='mything'
        )

        aws_iot_thing.update_thing(self.aws_module, thing, self.client)

        self.assertEqual(1, mock_change_thing.call_count)
        self.assertEqual(1, mock_change_principals.call_count)
        self.assertFalse(mock_describe_and_format_thing.called)
        mock_format_thing.assert_called_once_with(True, thing, ['p1'])

    @patch('ansible.modules.cloud.amazon.aws_iot_thing.format_thing')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.describe_and_format_changed_thing')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.change_principals')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.change_thing')
    def test_update_thing_with_changed_principals(
            self, mock_change_thing, mock_change_principals, mock_describe_and_format_thing, mock_format_thing):
        mock_change_thing.return_value = False
        mock_change_principals.return_value = (True, ['p1'])
        thing = dict(
            thingName='mything'
        )

        aws_iot_thing.update_thing(self.aws_module, thing, self.client)

        self.assertEqual(1, mock_change_thing.call_count)
        self.assertEqual(1, mock_change_principals.call_count)
        self.assertFalse(mock_describe_and_format_thing.called)
        mock_format_thing.assert_called_once_with(True, thing, ['p1'])

    @patch('ansible.modules.cloud.amazon.aws_iot_thing.format_thing')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.describe_and_format_changed_thing')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.change_principals')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.change_thing')
    def test_update_thing_with_no_changes(
            self, mock_change_thing, mock_change_principals, mock_describe_and_format_thing, mock_format_thing):
        mock_change_thing.return_value = False
        mock_change_principals.return_value = (False, ['p1'])
        thing = dict(
            thingName='mything'
        )

        aws_iot_thing.update_thing(self.aws_module, thing, self.client)

        self.assertEqual(1, mock_change_thing.call_count)
        self.assertEqual(1, mock_change_principals.call_count)
        self.assertFalse(mock_describe_and_format_thing.called)
        mock_format_thing.assert_called_once_with(False, thing, ['p1'])

    @patch('ansible.modules.cloud.amazon.aws_iot_thing.format_thing')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.describe_and_format_changed_thing')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.attach_principal')
    def test_create_thing_in_check_mode(self, mock_attach_principal, mock_describe_and_format_thing, mock_format_thing):
        self.aws_module.check_mode = True
        self.aws_module.params['type'] = 'mytype'
        self.aws_module.params['attributes'] = dict(
            warthog='Pumbaa',
            meerkat='Timon'
        )
        self.aws_module.params['attached_principals'] = ['p1', 'p2']

        thing_name = 'mything'

        expected = dict(
            thingName=thing_name,
            thingTypeName='mytype',
            attributes=dict(
                meerkat='Timon',
                warthog='Pumbaa'
            ),
            version=1
        )

        aws_iot_thing.create_thing(self.aws_module, thing_name, self.client)

        self.assertFalse(mock_attach_principal.called)
        self.assertFalse(self.client.create_thing.called)
        self.assertFalse(mock_describe_and_format_thing.called)
        mock_format_thing.assert_called_once_with(True, expected, ['p1', 'p2'])

    @patch('ansible.modules.cloud.amazon.aws_iot_thing.format_thing')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.describe_and_format_changed_thing')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.attach_principal')
    def test_create_thing_success(self, mock_attach_principal, mock_describe_and_format_thing, mock_format_thing):
        self.aws_module.check_mode = False
        self.aws_module.params['attributes'] = dict(
            warthog='Pumbaa',
            meerkat='Timon'
        )
        self.aws_module.params['attached_principals'] = ['p1', 'p2']

        self.client.create_thing.return_value = dict(thingArn='arn')

        thing_name = 'mything'

        expected = dict(
            thingName=thing_name,
            attributePayload=dict(
                attributes=dict(
                    meerkat='Timon',
                    warthog='Pumbaa'
                ),
                merge=True
            )
        )

        expected_attach_calls = [
            call(self.aws_module, self.client, thing_name, 'p1'),
            call(self.aws_module, self.client, thing_name, 'p2')
        ]

        aws_iot_thing.create_thing(self.aws_module, thing_name, self.client)

        self.client.create_thing.assert_called_once_with(**expected)
        self.assertEqual(2, mock_attach_principal.call_count)
        mock_attach_principal.assert_has_calls(expected_attach_calls)
        mock_describe_and_format_thing.assert_called_once_with(
            self.aws_module, self.client, thing_name, ['p1', 'p2'], dict(thing_arn='arn'))
        self.assertFalse(mock_format_thing.called)

    @patch('ansible.modules.cloud.amazon.aws_iot_thing.format_thing')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.describe_and_format_changed_thing')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.attach_principal')
    def test_create_thing_client_exception(
            self, mock_attach_principal, mock_describe_and_format_thing, mock_format_thing):
        self.aws_module.check_mode = False
        self.aws_module.params['attached_principals'] = ['p1', 'p2']

        self.client.create_thing.side_effect = generic_client_exception

        thing_name = 'mything'

        with self.assert_module_failed('Creating thing'):
            aws_iot_thing.create_thing(self.aws_module, thing_name, self.client)

        self.assertFalse(mock_attach_principal.called)
        self.assertFalse(mock_describe_and_format_thing.called)
        self.assertFalse(mock_format_thing.called)

    @patch('ansible.modules.cloud.amazon.aws_iot_thing.format_thing')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.describe_and_format_changed_thing')
    @patch('ansible.modules.cloud.amazon.aws_iot_thing.attach_principal')
    def test_create_thing_boto_core_error(
            self, mock_attach_principal, mock_describe_and_format_thing, mock_format_thing):
        self.aws_module.check_mode = False
        self.aws_module.params['attached_principals'] = ['p1', 'p2']

        self.client.create_thing.side_effect = boto_core_error

        thing_name = 'mything'

        with self.assert_module_failed('Creating thing'):
            aws_iot_thing.create_thing(self.aws_module, thing_name, self.client)

        self.assertFalse(mock_attach_principal.called)
        self.assertFalse(mock_describe_and_format_thing.called)
        self.assertFalse(mock_format_thing.called)

    def test_describe_thing_success(self):
        thing = dict(
            thingName='mything',
            attributes=dict(a1='v1'),
            thingTypeName='mytype',
            version=7,
            defaultClientId='mything',
            ResponseMetadata=dict()
        )

        self.client.describe_thing.return_value = thing

        result = aws_iot_thing.describe_thing(self.aws_module, self.client, 'mything')

        self.assertEqual(thing, result)

    def test_describe_thing_not_found(self):
        self.client.describe_thing.side_effect = resource_not_found_exception
        result = aws_iot_thing.describe_thing(self.aws_module, self.client, 'mything')
        self.assertIsNone(result)

    def test_describe_thing_client_exception(self):
        self.client.describe_thing.side_effect = generic_client_exception
        with self.assert_module_failed('Describing thing'):
            aws_iot_thing.describe_thing(self.aws_module, self.client, 'mything')

    def test_describe_thing_client_boto_core_error(self):
        self.client.describe_thing.side_effect = boto_core_error
        with self.assert_module_failed('Describing thing'):
            aws_iot_thing.describe_thing(self.aws_module, self.client, 'mything')

    def assert_module_failed(self, msg):
        return AssertModuleFailsContext(self, msg)

    def assert_list_equal(self, expected, actual):
        self.assertSetEqual(set(expected), set(actual))
