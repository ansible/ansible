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
module: polly_lexicon
short_description: Manage lexicons on AWS Polly.
description:
    - Add or delete lexicons for AWS Polly test-to-speech processing.
author: "Aaron Smith (@slapula)"
version_added: "2.7"
requirements: [ 'botocore', 'boto3' ]
options:
  name:
    description:
     - Name of the lexicon.
    required: true
  state:
    description:
     - Whether the lexicon should be exist or not.
    required: true
    choices: ['present', 'absent']
  content:
    description:
     - Content of the PLS lexicon as string data.
    required: true
extends_documentation_fragment:
    - ec2
    - aws
'''


EXAMPLES = r'''
- name: create Polly lexicon
  polly_lexicon:
    name: 'ivona'
    state: present
    content: "{{ lookup('file', 'tmp/ivona.pls') }}"
- name: delete Polly lexicon
  polly_lexicon:
    name: 'ivona'
    state: absent
    content: "{{ lookup('file', 'tmp/ivona.pls') }}"
'''


RETURN = r'''#'''


from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, AWSRetry
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule


def lexicon_exists(client, module, result):
    try:
        response = client.list_lexicons()
        for i in response['Lexicons']:
            if i['Name'] == module.params.get('name'):
                lex_data = client.get_lexicon(
                    Name=module.params.get('name')
                )
                result['lexicon_content'] = lex_data['Lexicon']
                return True
    except (ClientError, IndexError):
        return False

    return False


def create_lexicon(client, module, params, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.put_lexicon(**params)
        result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to create lexicon")

    return result


def update_lexicon(client, module, params, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        if params['Content'] != result['lexicon_content']['Content']:
            response = client.delete_lexicon(
                Name=module.params.get('name')
            )
            response = client.put_lexicon(**params)
            result['changed'] = True
            return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to update lexicon")

    return result


def delete_lexicon(client, module, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.delete_lexicon(
            Name=module.params.get('name')
        )
        result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to delete lexicon")

    return result


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'name': dict(type='str', required=True),
            'state': dict(type='str', choices=['present', 'absent'], required=True),
            'content': dict(type='str', required=True),
        },
        supports_check_mode=True,
    )

    result = {
        'changed': False
    }

    params = {}
    params['Name'] = module.params.get('name')
    params['Content'] = module.params.get('content')

    desired_state = module.params.get('state')

    client = module.client('polly')

    lexicon_status = lexicon_exists(client, module, result)

    if desired_state == 'present':
        if not lexicon_status:
            create_lexicon(client, module, params, result)
        if lexicon_status:
            update_lexicon(client, module, params, result)

    if desired_state == 'absent':
        if lexicon_status:
            delete_lexicon(client, module, result)

    module.exit_json(changed=result['changed'])


if __name__ == '__main__':
    main()
