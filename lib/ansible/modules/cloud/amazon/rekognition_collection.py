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
module: rekognition_collection
short_description: Manage face collections used with the AWS Rekognition service.
description:
    - Creates/deletes a face collection in AWS Rekognition.
    - You will need to use `rekognition_faces` to index facial data into the collection.
author: "Aaron Smith (@slapula)"
version_added: "2.7"
requirements: [ 'botocore', 'boto3' ]
options:
  name:
    description:
    - ID for the collection that you are creating.
    required: true
  state:
    description:
    - Whether the collection should be exist or not.
    choices: ['present', 'absent']
    default: 'present'
extends_documentation_fragment:
    - ec2
    - aws
'''


EXAMPLES = r'''
- name: Create collection to store faces
  rekognition_collection:
    name: 'myphotos'
    state: present

- name: Delete collection
  rekognition_collection:
    name: 'myphotos'
    state: absent
'''


RETURN = r'''#'''

import locale
from io import BytesIO

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, AWSRetry
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule


def collection_exists(client, module, result):
    try:
        response = client.list_collections()
        for i in response['CollectionIds']:
            if i == module.params.get('name'):
                return True
    except (ClientError, IndexError):
        return False

    return False


def create_collection(client, module, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.create_collection(
            CollectionId=module.params.get('name')
        )
        result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to create collection")

    return result


def delete_collection(client, module, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.delete_collection(
            CollectionId=module.params.get('name')
        )
        result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to delete collection")

    return result


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'name': dict(type='str', required=True),
            'state': dict(type='str', choices=['present', 'absent'], default='present'),
        },
        supports_check_mode=True,
    )

    result = {
        'changed': False
    }

    client = module.client('rekognition')

    collection_status = collection_exists(client, module, result)

    desired_state = module.params.get('state')

    if desired_state == 'present':
        if not collection_status:
            create_collection(client, module, result)

    if desired_state == 'absent':
        if collection_status:
            delete_collection(client, module, result)

    module.exit_json(changed=result['changed'])


if __name__ == '__main__':
    main()
