#!/usr/bin/python
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: dynamodb_ttl
short_description: set TTL for a given DynamoDB table.
description:
- Uses boto3 to set TTL.
- requires botocore version 1.5.24 or higher.
version_added: "2.4"
options:
  state:
    description:
    - state to set DynamoDB table to
    choices: ['enable', 'disable']
    required: false
    default: enable
  table_name:
    description:
    - name of the DynamoDB table to work on
    required: true
  attribute_name:
    description:
    - the name of the Time to Live attribute used to store the expiration time for items in the table
    - this appears to be required by the API even when disabling TTL.
    required: true

author: "Ted (@tedder)"
extends_documentation_fragment:
- aws
- ec2
requirements: [ botocore>=1.5.24, boto3 ]
'''

EXAMPLES = '''
- name: enable TTL on my cowfacts table
  dynamodb_ttl:
    state: enable
    table_name: cowfacts
    attribute_name: cow_deleted_date

- name: disable TTL on my cowfacts table
  dynamodb_ttl:
    state: disable
    table_name: cowfacts
    attribute_name: cow_deleted_date
'''

RETURN = '''
current_status:
  description: current or new TTL specification.
  type: dict
  returned: always
  sample:
  - { "AttributeName": "deploy_timestamp", "TimeToLiveStatus": "ENABLED" }
  - { "AttributeName": "deploy_timestamp", "Enabled": true }
'''

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, camel_dict_to_snake_dict, HAS_BOTO3

# import a class, otherwise we'll use a fully qualified path
import ansible.module_utils.ec2

import traceback
import distutils.version

try:
    import botocore
except ImportError:
    pass


def get_current_ttl_state(c, table_name):
    '''Fetch the state dict for a table.'''
    current_state = c.describe_time_to_live(TableName=table_name)
    return current_state.get('TimeToLiveDescription')


def does_state_need_changing(attribute_name, desired_state, current_spec):
    '''Run checks to see if the table needs to be modified. Basically a dirty check.'''
    if not current_spec:
        # we don't have an entry (or a table?)
        return True

    if desired_state.lower() == 'enable' and current_spec.get('TimeToLiveStatus') not in ['ENABLING', 'ENABLED']:
        return True
    if desired_state.lower() == 'disable' and current_spec.get('TimeToLiveStatus') not in ['DISABLING', 'DISABLED']:
        return True
    if attribute_name != current_spec.get('AttributeName'):
        return True

    return False


def set_ttl_state(c, table_name, state, attribute_name):
    '''Set our specification. Returns the update_time_to_live specification dict,
       which is different than the describe_* call.'''
    is_enabled = False
    if state.lower() == 'enable':
        is_enabled = True

    ret = c.update_time_to_live(
        TableName=table_name,
        TimeToLiveSpecification={
            'Enabled': is_enabled,
            'AttributeName': attribute_name
        }
    )

    return ret.get('TimeToLiveSpecification')


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(choices=['enable', 'disable']),
        table_name=dict(required=True),
        attribute_name=dict(required=True))
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')
    elif distutils.version.StrictVersion(botocore.__version__) < distutils.version.StrictVersion('1.5.24'):
        # TTL was added in this version.
        module.fail_json(msg='Found botocore in version {0}, but >= {1} is required for TTL support'.format(botocore.__version__, '1.5.24'))

    try:
        region, ec2_url, aws_connect_kwargs = ansible.module_utils.ec2.get_aws_connection_info(module, boto3=True)
        dbclient = ansible.module_utils.ec2.boto3_conn(module, conn_type='client', resource='dynamodb', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg=str(e))

    result = {'changed': False}
    state = module.params['state']

    # wrap all our calls to catch the standard exceptions. We don't pass `module` in to the
    # methods so it's easier to do here.
    try:
        current_state = get_current_ttl_state(dbclient, module.params['table_name'])

        if does_state_need_changing(module.params['attribute_name'], module.params['state'], current_state):
            # changes needed
            new_state = set_ttl_state(dbclient, module.params['table_name'], module.params['state'], module.params['attribute_name'])
            result['current_status'] = new_state
            result['changed'] = True
        else:
            # no changes needed
            result['current_status'] = current_state

    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.ParamValidationError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc())
    except ValueError as e:
        module.fail_json(msg=str(e))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
