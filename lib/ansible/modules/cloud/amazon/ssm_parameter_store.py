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
ANSIBLE_METADATA = {'status': ['stableinterface'],
                    'supported_by': 'committer',
                    'version': '1.0'}

DOCUMENTATION = '''
module: ssm_parameter_store
short_description: Manage key-value pairs in aws parameter store.
description:
  - Manage key-vaule pairs in aws parameter store.
version_added: "2.3"
options:
  name:
    description:
      - parameter key name.
    required: true
  description:
    description:
      - parameter key desciption.
    required: false
  value:
    description:
      - Parameter value.
    required: false
  state:
    description:
      - Creates or modifies an existing parameter
      - Deletes a parameter
    required: false
    choices: ['present', 'absent', 'show']
    default: present
  string_type:
    description:
      - Parameter String type
    required: false
    choices: ['String', 'StringList', 'SecureString']
    default: String
  decryption:
    description:
      - Work with SecureString type to get plain text secrets
      - Boolean
    required: false
    default: True
  key_id:
    description:
      - aws KMS key to decrypt the secrets.
    required: false
    default: aws/ssm (this key is automatically generated at the first parameter created).
  overwrite:
    description:
      - Overwrite the value when create or update parameter
      - Boolean
    required: false
    default: True
author: Bill Wang(ozbillwang@gmail.com)
extends_documentation_fragment: aws
requirements: [ botocore, boto3 ]
'''

EXAMPLES = '''
- name: Create or update key/vaule pair in aws parameter store
  ssm_parameter_store:
    name: "Hello"
    description: "This is your first key"
    value: "World"
  register: result

- name: Delete the key
  ssm_parameter_store:
    name: "Hello"
    state: absent
  register: result

- name: Create or update secure key/vaule pair in aws parameter store
  ssm_parameter_store:
    name: "Hello"
    description: "This is your first key"
    string_type: "SecureString"
    value: "World"
  register: result

- name: Retrieving plain-text secret
  ssm_parameter_store:
    name: "Hello"
    state: show
  register: result

- name: Retrieving plain-text secret with custom kms key
  ssm_parameter_store:
    name: "Hello"
    key_id: "aws/ssm"
    state: show
  register: result

- name: Retrieving secret without decrypted
  ssm_parameter_store:
    name: "Hello"
    decryption: False
    state: show
  register: result
'''

try:
    import botocore
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, AnsibleAWSError, ec2_argument_spec, get_aws_connection_info

def create_update_parameter(client, module):
    changed = False

    args = dict(
              Name=module.params.get('name'),
              Value=module.params.get('value'),
              Type=module.params.get('string_type'),
              Overwrite=module.params.get('overwrite')
    )

    if module.params.get('description'):
       args.update(Description=module.params.get('description'))

    if module.params.get('string_type') is 'SecureString':
       args.update(KeyId=module.params.get('key_id'))

    try:
      nacl = client.put_parameter(**args)
      changed = True
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))
    return changed, nacl

def get_parameter(client, module):
    changed = False
    try:
      nacl = client.get_parameters(
                Names=[module.params.get('name')],
                WithDecryption=module.params.get('decryption')
      )
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))
    return changed, nacl['Parameters']

def delete_parameter(client, module):
    changed = False

    nacl = dict()

    get_nacl = client.get_parameters(
                  Names=[module.params.get('name')]
    )
    if get_nacl['Parameters']:
      try:
        nacl = client.delete_parameter(
                Name=module.params.get('name')
        )
        changed = True
      except botocore.exceptions.ClientError as e:
          module.fail_json(msg=str(e))
    return changed, nacl

def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        name =        dict(required=True),
        description = dict(),
        value =       dict(required=False),
        state =       dict(default='present', choices=['present', 'absent', 'show']),
        string_type = dict(default='String', choices=['String', 'StringList', 'SecureString']),
        decryption =  dict(default=True, type='bool'),
        key_id =      dict(default='aws/ssm'),
        overwrite =   dict(default=True, type='bool'),
        ),
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 are required.')
    state = module.params.get('state').lower()
    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        client = boto3_conn(module, conn_type='client', resource='ssm', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg="Can't authorize connection - %s" % str(e))

    invocations = {
      "present": create_update_parameter,
      "absent":  delete_parameter,
      "show":    get_parameter,
    }
    (changed, results) = invocations[state](client, module)
    module.exit_json(changed=changed, nacl_id=results)

if __name__ == '__main__':
    main()
