#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

try:
    from botocore.exceptions import ClientError, BotoCoreError
    import boto3
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (get_aws_connection_info, boto3_conn)


def create_keypair(module, client, keypair_name):
    """
    Create a keypair to use for your lightsail instance
    """

    try:
        client.create_key_pair(keyPairName=keypair_name)
    except ClientError as e:
        if "Some names are already in use" in e.response['Error']['Message']:
            module.exit_json(changed=False)
        module.fail_json_aws(e)

    module.exit_json(changed=True)


def delete_keypair(module, client, keypair_name):
    """
    Delete a keypair in lightsail
    """

    try:
        client.delete_key_pair(keyPairName=keypair_name)
    except ClientError as e:
        if e.response['Error']['Code'] == "NotFoundException":
            module.exit_json(changed=False)
        module.fail_json_aws(e)

    module.exit_json(changed=True)


def main():

    argument_spec = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)
    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    try:
        client = boto3_conn(module, conn_type='client', resource='lightsail', region=region, endpoint=ec2_url,
                            **aws_connect_params)
    except ClientError as e:
        module.fail_json_aws(e)

    keypair_name = module.params.get('name')
    state = module.params.get('state')

    if state == 'present':
        create_keypair(module, client, keypair_name)
    else:
        delete_keypair(module, client, keypair_name)


if __name__ == '__main__':
    main()
