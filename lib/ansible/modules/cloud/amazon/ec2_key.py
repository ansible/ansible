#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
---
module: ec2_key
version_added: "1.5"
short_description: create or delete an ec2 key pair
description:
    - create or delete an ec2 key pair.
options:
  name:
    description:
      - Name of the key pair.
    required: true
  key_material:
    description:
      - Public key material.
    required: false
  force:
    description:
      - Force overwrite of already existing key pair if key has changed.
    required: false
    default: true
    version_added: "2.3"
  state:
    description:
      - create or delete keypair
    required: false
    choices: [ present, absent ]
    default: 'present'
  wait:
    description:
      - Wait for the specified action to complete before returning. This option has no effect since version 2.5.
    required: false
    default: false
    version_added: "1.6"
  wait_timeout:
    description:
      - How long before wait gives up, in seconds. This option has no effect since version 2.5.
    required: false
    default: 300
    version_added: "1.6"

extends_documentation_fragment:
  - aws
  - ec2
requirements: [ boto3 ]
author:
  - "Vincent Viallet (@zbal)"
  - "Prasad Katti (@prasadkatti)"
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: create a new ec2 key pair, returns generated private key
  ec2_key:
    name: my_keypair

- name: create key pair using provided key_material
  ec2_key:
    name: my_keypair
    key_material: 'ssh-rsa AAAAxyz...== me@example.com'

- name: create key pair using key_material obtained using 'file' lookup plugin
  ec2_key:
    name: my_keypair
    key_material: "{{ lookup('file', '/path/to/public_key/id_rsa.pub') }}"

# try creating a key pair with the name of an already existing keypair
# but don't overwrite it even if the key is different (force=false)
- name: try creating a key pair with name of an already existing keypair
  ec2_key:
    name: my_existing_keypair
    key_material: 'ssh-rsa AAAAxyz...== me@example.com'
    force: false

- name: remove key pair by name
  ec2_key:
    name: my_keypair
    state: absent
'''

RETURN = '''
changed:
  description: whether a keypair was created/deleted
  returned: always
  type: bool
  sample: true
msg:
  description: short message describing the action taken
  returned: always
  type: string
  sample: key pair created
key:
  description: details of the keypair (this is set to null when state is absent)
  returned: always
  type: complex
  contains:
    fingerprint:
      description: fingerprint of the key
      returned: when state is present
      type: string
      sample: 'b0:22:49:61:d9:44:9d:0c:7e:ac:8a:32:93:21:6c:e8:fb:59:62:43'
    name:
      description: name of the keypair
      returned: when state is present
      type: string
      sample: my_keypair
    private_key:
      description: private key of a newly created keypair
      returned: when a new keypair is created by AWS (key_material is not provided)
      type: string
      sample: '-----BEGIN RSA PRIVATE KEY-----
        MIIEowIBAAKC...
        -----END RSA PRIVATE KEY-----'
'''

import uuid

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info, boto3_conn
from ansible.module_utils._text import to_bytes

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass


def extract_key_data(key):

    data = {
        'name': key['KeyName'],
        'fingerprint': key['KeyFingerprint']
    }
    if 'KeyMaterial' in key:
        data['private_key'] = key['KeyMaterial']
    return data


def get_key_fingerprint(module, ec2_client, key_material):
    '''
    EC2's fingerprints are non-trivial to generate, so push this key
    to a temporary name and make ec2 calculate the fingerprint for us.
    http://blog.jbrowne.com/?p=23
    https://forums.aws.amazon.com/thread.jspa?messageID=352828
    '''

    # find an unused name
    name_in_use = True
    while name_in_use:
        random_name = "ansible-" + str(uuid.uuid4())
        name_in_use = find_key_pair(module, ec2_client, random_name)

    temp_key = import_key_pair(module, ec2_client, random_name, key_material)
    delete_key_pair(module, ec2_client, random_name, finish_task=False)
    return temp_key['KeyFingerprint']


def find_key_pair(module, ec2_client, name):

    try:
        key = ec2_client.describe_key_pairs(KeyNames=[name])['KeyPairs'][0]
    except ClientError as err:
        if err.response['Error']['Code'] == "InvalidKeyPair.NotFound":
            return None
        module.fail_json_aws(err, msg="error finding keypair")
    return key


def create_key_pair(module, ec2_client, name, key_material, force):

    key = find_key_pair(module, ec2_client, name)
    if key:
        if key_material and force:
            new_fingerprint = get_key_fingerprint(module, ec2_client, key_material)
            if key['KeyFingerprint'] != new_fingerprint:
                if not module.check_mode:
                    delete_key_pair(module, ec2_client, name, finish_task=False)
                    key = import_key_pair(module, ec2_client, name, key_material)
                key_data = extract_key_data(key)
                module.exit_json(changed=True, key=key_data, msg="key pair updated")
        key_data = extract_key_data(key)
        module.exit_json(changed=False, key=key_data, msg="key pair already exists")
    else:
        # key doesn't exist, create it now
        key_data = None
        if not module.check_mode:
            if key_material:
                key = import_key_pair(module, ec2_client, name, key_material)
            else:
                try:
                    key = ec2_client.create_key_pair(KeyName=name)
                except ClientError as err:
                    module.fail_json_aws(err, msg="error creating key")
            key_data = extract_key_data(key)
        module.exit_json(changed=True, key=key_data, msg="key pair created")


def import_key_pair(module, ec2_client, name, key_material):

    try:
        key = ec2_client.import_key_pair(KeyName=name, PublicKeyMaterial=to_bytes(key_material))
    except ClientError as err:
        module.fail_json_aws(err, msg="error importing key")
    return key


def delete_key_pair(module, ec2_client, name, finish_task=True):

    key = find_key_pair(module, ec2_client, name)
    if key:
        if not module.check_mode:
            try:
                ec2_client.delete_key_pair(KeyName=name)
            except ClientError as err:
                module.fail_json_aws(err, msg="error deleting key")
        if not finish_task:
            return
        module.exit_json(changed=True, key=None, msg="key deleted")
    module.exit_json(key=None, msg="key did not exist")


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            key_material=dict(),
            force=dict(type='bool', default=True),
            state=dict(default='present', choices=['present', 'absent']),
            wait=dict(type='bool', default=False),
            wait_timeout=dict(default=300)
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    ec2_client = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)

    name = module.params['name']
    state = module.params.get('state')
    key_material = module.params.get('key_material')
    force = module.params.get('force')

    if state == 'absent':
        delete_key_pair(module, ec2_client, name)
    elif state == 'present':
        create_key_pair(module, ec2_client, name, key_material, force)


if __name__ == '__main__':
    main()
