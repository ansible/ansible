#!/usr/bin/python
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: aws_ssm_parameter_store
short_description: Manage key-value pairs in aws parameter store.
description:
  - Manage key-value pairs in aws parameter store.
version_added: "2.5"
options:
  name:
    description:
      - Parameter key name.
    required: true
    type: str
  description:
    description:
      - Parameter key description.
    required: false
    type: str
  value:
    description:
      - Parameter value.
    required: false
    type: str
  state:
    description:
      - Creates or modifies an existing parameter.
      - Deletes a parameter.
    required: false
    choices: ['present', 'absent']
    default: present
    type: str
  string_type:
    description:
      - Parameter String type.
    required: false
    choices: ['String', 'StringList', 'SecureString']
    default: String
    type: str
  decryption:
    description:
      - Work with SecureString type to get plain text secrets
    type: bool
    required: false
    default: true
  key_id:
    description:
      - AWS KMS key to decrypt the secrets.
      - The default key (C(alias/aws/ssm)) is automatically generated the first
        time it's requested.
    required: false
    default: alias/aws/ssm
    type: str
  overwrite_value:
    description:
      - Option to overwrite an existing value if it already exists.
    required: false
    version_added: "2.6"
    choices: ['never', 'changed', 'always']
    default: changed
    type: str
author:
  - Nathan Webster (@nathanwebsterdotme)
  - Bill Wang (@ozbillwang) <ozbillwang@gmail.com>
  - Michael De La Rue (@mikedlr)
extends_documentation_fragment:
    - aws
    - ec2
requirements: [ botocore, boto3 ]
'''

EXAMPLES = '''
- name: Create or update key/value pair in aws parameter store
  aws_ssm_parameter_store:
    name: "Hello"
    description: "This is your first key"
    value: "World"

- name: Delete the key
  aws_ssm_parameter_store:
    name: "Hello"
    state: absent

- name: Create or update secure key/value pair with default kms key (aws/ssm)
  aws_ssm_parameter_store:
    name: "Hello"
    description: "This is your first key"
    string_type: "SecureString"
    value: "World"

- name: Create or update secure key/value pair with nominated kms key
  aws_ssm_parameter_store:
    name: "Hello"
    description: "This is your first key"
    string_type: "SecureString"
    key_id: "alias/demo"
    value: "World"

- name: Always update a parameter store value and create a new version
  aws_ssm_parameter_store:
    name: "overwrite_example"
    description: "This example will always overwrite the value"
    string_type: "String"
    value: "Test1234"
    overwrite_value: "always"

- name: recommend to use with aws_ssm lookup plugin
  debug: msg="{{ lookup('aws_ssm', 'hello') }}"
'''

RETURN = '''
put_parameter:
    description: Add one or more parameters to the system.
    returned: success
    type: dict
delete_parameter:
    description: Delete a parameter from the system.
    returned: success
    type: dict
'''

from ansible.module_utils.aws.core import AnsibleAWSModule

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass  # Handled by AnsibleAWSModule


def update_parameter(client, module, args):
    changed = False
    response = {}

    try:
        response = client.put_parameter(**args)
        changed = True
    except ClientError as e:
        module.fail_json_aws(e, msg="setting parameter")

    return changed, response


def create_update_parameter(client, module):
    changed = False
    existing_parameter = None
    response = {}

    args = dict(
        Name=module.params.get('name'),
        Value=module.params.get('value'),
        Type=module.params.get('string_type')
    )

    if (module.params.get('overwrite_value') in ("always", "changed")):
        args.update(Overwrite=True)
    else:
        args.update(Overwrite=False)

    if module.params.get('description'):
        args.update(Description=module.params.get('description'))

    if module.params.get('string_type') == 'SecureString':
        args.update(KeyId=module.params.get('key_id'))

    try:
        existing_parameter = client.get_parameter(Name=args['Name'], WithDecryption=True)
    except Exception:
        pass

    if existing_parameter:
        if (module.params.get('overwrite_value') == 'always'):

            (changed, response) = update_parameter(client, module, args)

        elif (module.params.get('overwrite_value') == 'changed'):
            if existing_parameter['Parameter']['Type'] != args['Type']:
                (changed, response) = update_parameter(client, module, args)

            if existing_parameter['Parameter']['Value'] != args['Value']:
                (changed, response) = update_parameter(client, module, args)

            if args.get('Description'):
                # Description field not available from get_parameter function so get it from describe_parameters
                describe_existing_parameter = None
                try:
                    describe_existing_parameter_paginator = client.get_paginator('describe_parameters')
                    describe_existing_parameter = describe_existing_parameter_paginator.paginate(
                        Filters=[{"Key": "Name", "Values": [args['Name']]}]).build_full_result()

                except ClientError as e:
                    module.fail_json_aws(e, msg="getting description value")

                if describe_existing_parameter['Parameters'][0]['Description'] != args['Description']:
                    (changed, response) = update_parameter(client, module, args)
    else:
        (changed, response) = update_parameter(client, module, args)

    return changed, response


def delete_parameter(client, module):
    response = {}

    try:
        response = client.delete_parameter(
            Name=module.params.get('name')
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            return False, {}
        module.fail_json_aws(e, msg="deleting parameter")

    return True, response


def setup_client(module):
    connection = module.client('ssm')
    return connection


def setup_module_object():
    argument_spec = dict(
        name=dict(required=True),
        description=dict(),
        value=dict(required=False, no_log=True),
        state=dict(default='present', choices=['present', 'absent']),
        string_type=dict(default='String', choices=['String', 'StringList', 'SecureString']),
        decryption=dict(default=True, type='bool'),
        key_id=dict(default="alias/aws/ssm"),
        overwrite_value=dict(default='changed', choices=['never', 'changed', 'always']),
    )

    return AnsibleAWSModule(
        argument_spec=argument_spec,
    )


def main():
    module = setup_module_object()
    state = module.params.get('state')
    client = setup_client(module)

    invocations = {
        "present": create_update_parameter,
        "absent": delete_parameter,
    }
    (changed, response) = invocations[state](client, module)
    module.exit_json(changed=changed, response=response)


if __name__ == '__main__':
    main()
