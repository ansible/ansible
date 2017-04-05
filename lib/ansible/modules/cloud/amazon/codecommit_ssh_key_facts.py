#!/usr/bin/python

# -*- coding: utf-8 -*-
#
# (c) 2017, Pat Sharkey <psharkey@cleo.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: codecommit_ssh_key_facts
short_description: Get the AWS SSH Public Key facts
description:
    - Get the AWS CodeCommit SSH Public Key facts for a given user
version_added: "2.4"
author: "Pat Sharkey, (@psharkey)"
options:
  user_name:
    description:
      - The name of the user whose SSH public key will be returned
    required: true
  encoding:
    description:
      - The desired format for the returned key.
    choices:
      - PEM
      - SSH
    required: true
extends_documentation_fragment:
    - aws
    - ec2
requirements:
    - boto3
    - botocore
'''

RETURN = """
ssh_key_facts:
    description: The SSH public key facts for the given user
    returned: always
    type: list
    sample:
      "ssh_public_keys": [
            {
                "Fingerprint": "19:72:05:e0:bf:7e:15:c7:09:8a:c3:65:fc:c1:18:a3",
                "SSHPublicKeyBody": "ssh-rsa ...",
                "SSHPublicKeyId": "APKAIJFT7TINGJTDLAZQ",
                "Status": "Active",
                "UploadDate": "2017-04-03T23:15:20+00:00",
                "UserName": "psharkey"
            },
            {
                "Fingerprint": "84:62:be:70:88:d4:ed:f8:26:58:15:90:f1:4b:27:70",
                "SSHPublicKeyBody": "ssh-rsa ...",
                "SSHPublicKeyId": "APKAI7OSUMJCHQXBILUA",
                "Status": "Active",
                "UploadDate": "2017-04-04T14:20:58+00:00",
                "UserName": "psharkey"
            }
        ]
"""

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
  - name: get SSH public key facts for an IAM user
    codecommit_ssh_key_facts:
      user_name: "psharkey"
      encoding: 'SSH'
    register: ssh_key_facts
'''


import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def get_ssh_public_key_ids(connection, module):
    user_name = module.params.get('user_name')
    changed = False

    args = {}
    if user_name is not None:
        args['UserName'] = user_name
    try:
        response = connection.list_ssh_public_keys(**args)
    except ClientError as e:
        module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

    key_id_array = []
    for ssh_public_key in response['SSHPublicKeys']:
        key_id_array.append(ssh_public_key['SSHPublicKeyId'])

    return key_id_array


def get_ssh_public_key(connection, module, key_id):
    changed = False

    args = {}
    args['UserName'] = module.params.get('user_name')
    args['Encoding'] = module.params.get('encoding')
    args['SSHPublicKeyId'] = key_id

    try:
        response = connection.get_ssh_public_key(**args)
    except ClientError as e:
        module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

    return response['SSHPublicKey']


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            user_name=dict(required=True),
            encoding=dict(required=True, choices=['PEM', 'SSH'])
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    connection = boto3_conn(module, conn_type='client', resource='iam', endpoint=ec2_url, **aws_connect_kwargs)

    key_ids = get_ssh_public_key_ids(connection, module)
    public_key_array = []
    for key_id in key_ids:
        public_key_array.append(get_ssh_public_key(connection, module, key_id))

    module.exit_json(ssh_public_keys=public_key_array)


if __name__ == '__main__':
    main()
