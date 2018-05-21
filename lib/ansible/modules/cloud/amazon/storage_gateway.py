#!/usr/bin/python

# Copyright: (c) 2018, Aaron Smith <ajsmith10381@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: storage_gateway
short_description: Manage AWS Storage Gateway resources
description:
    - Module manages AWS Config resources
    - Supported resource types include gateway.
version_added: "2.6"
requirements: [ 'botocore', 'boto3' ]
author:
    - "Aaron Smith (@slapula)"
options:
  name:
    description:
    - The name you configured for your gateway.
    required: true
  state:
    description:
    - Whether the resource should be present or absent.
    default: present
    choices: ['present', 'absent']
  activation_key:
    description:
    - Your gateway activation key. See AWS documentation on how to acquire this key.
    required: true
  timezone:
    description:
    - A value that indicates the time zone you want to set for the gateway.
    required: true
  gateway_region:
    description:
    - A value that indicates the region where you want to store your data.
    required: true
  gateway_type:
    description:
    - A value that defines the type of gateway to activate.
    - The type specified is critical to all later functions of the gateway and cannot be changed after activation.
    default: 'STORED'
    choices: ['STORED', 'CACHED', 'VTL', 'FILE_S3']
  tape_drive_type:
    description:
    - The value that indicates the type of tape drive to use for tape gateway.
    choices: ['IBM-ULT3580-TD5']
  medium_changer_type:
    description:
    - The value that indicates the type of medium changer to use for tape gateway.
    choices: ['STK-L700', 'AWS-Gateway-VTL']
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = r'''
  - name: Activate file gateway
    storage_gateway:
      name: "example-file-gateway"
      state: present
      activation_key: "{{ activation_code.stdout }}"
      timezone: 'GMT-6:00'
      gateway_region: "{{ aws_region }}"
      gateway_type: 'FILE_S3'
'''

RETURN = r'''
gateway_arn:
    description: The ARN of the gateway you just created or updated.
    returned: always
    type: string
'''

import time
import ast

try:
    import botocore
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, AWSRetry
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict


def gateway_exists(client, module, params, result):
    try:
        gateway_list = client.list_gateways()
        for i in gateway_list['Gateways']:
            if i['GatewayName'] == params['GatewayName']:
                disks_response = client.list_local_disks(
                    GatewayARN=i['GatewayARN']
                )
                result['GatewayARN'] = i['GatewayARN']
                result['Disks'] = disks_response['Disks']
                return True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError):
        return False

    return False


def create_gateway(client, module, params, result):
    try:
        gw_response = client.activate_gateway(**params)
        time.sleep(15)  # Need a waiter here but it doesn't exist yet in the StorageGateway API
        disks_response = client.list_local_disks(
            GatewayARN=gw_response['GatewayARN']
        )
        if disks_response['Disks']:
            if params['GatewayType'] == 'FILE_S3':
                vol_response = client.add_cache(
                    GatewayARN=gw_response['GatewayARN'],
                    DiskIds=[disks_response['Disks'][0]['DiskId']]
                )
            if params['GatewayType'] == 'CACHED' or params['GatewayType'] == 'VTL':
                vol_response = client.add_cache(
                    GatewayARN=gw_response['GatewayARN'],
                    DiskIds=[disks_response['Disks'][0]['DiskId']]
                )
                vol_response = client.add_upload_buffer(
                    GatewayARN=gw_response['GatewayARN'],
                    DiskIds=[disks_response['Disks'][1]['DiskId']]
                )
            if params['GatewayType'] == 'STORED':
                vol_response = client.add_upload_buffer(
                    GatewayARN=gw_response['GatewayARN'],
                    DiskIds=[disks_response['Disks'][0]['DiskId']]
                )
        result['GatewayARN'] = gw_response['GatewayARN']
        result['Disks'] = disks_response['Disks']
        result['changed'] = True
        return result
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't activate storage gateway instance")

    return result


def update_gateway(client, module, params, result):
    current_params = client.describe_gateway_information(
        GatewayARN=result['GatewayARN']
    )

    if params['GatewayName'] != current_params['GatewayName'] or params['GatewayTimezone'] != current_params['GatewayTimezone']:
        try:
            response = client.update_gateway_information(
                GatewayARN=result['GatewayARN'],
                GatewayName=params['GatewayName'],
                GatewayTimezone=params['GatewayTimezone']
            )
            disks_response = client.list_local_disks(
                GatewayARN=result['GatewayARN']
            )
            result['GatewayARN'] = response['GatewayARN']
            result['Disks'] = disks_response['Disks']
            result['changed'] = True
            return result
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't update storage gateway")

    return result


def delete_gateway(client, module, result):
    try:
        response = client.delete_gateway(
            GatewayARN=result['GatewayARN']
        )
        result['changed'] = True
        return result
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't delete storage gateway")

    return result


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'name': dict(type='str', required=True),
            'state': dict(type='str', choices=['present', 'absent'], default='present'),
            'activation_key': dict(type='str', required=True),
            'timezone': dict(type='str', required=True),
            'gateway_region': dict(type='str', required=True),
            'gateway_type': dict(type='str', default='STORED', choices=['STORED', 'CACHED', 'VTL', 'FILE_S3']),
            'tape_drive_type': dict(type='str', choices=['IBM-ULT3580-TD5']),
            'medium_changer_type': dict(type='str', choices=['STK-L700', 'AWS-Gateway-VTL']),
        },
        supports_check_mode=False,
    )

    result = {
        'changed': False
    }

    desired_state = module.params.get('state')

    params = {}
    params['GatewayName'] = module.params.get('name')
    params['ActivationKey'] = module.params.get('activation_key')
    params['GatewayTimezone'] = module.params.get('timezone')
    params['GatewayRegion'] = module.params.get('gateway_region')
    params['GatewayType'] = module.params.get('gateway_type')
    if module.params.get('tape_drive_type'):
        params['TapeDriveType'] = module.params.get('tape_drive_type')
    if module.params.get('medium_changer_type'):
        params['MediumChangerType'] = module.params.get('medium_changer_type')

    client = module.client('storagegateway')

    gateway_status = gateway_exists(client, module, params, result)

    if desired_state == 'present':
        if not gateway_status:
            create_gateway(client, module, params, result)
        if gateway_status:
            update_gateway(client, module, params, result)

    if desired_state == 'absent':
        if gateway_status:
            delete_gateway(client, module, result)

    module.exit_json(changed=result['changed'], output=result)


if __name__ == '__main__':
    main()
