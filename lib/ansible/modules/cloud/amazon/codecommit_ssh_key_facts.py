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

DOCUMENTATION = '''
---
module: codecommit_ssh_key_facts
short_description: Get the AWS CodeCommit SSH Public Key facts for a given user
description:
    - Get the AWS CodeCommit SSH Public Key facts for a given user
version_added: "2.2.1.0"
author: "Pat Sharkey, (@psharkey)"
options:
  user_name:
    description:
      - The name of the user whose SSH public key will be returned
    required: true
  encoding:
    description:
      - The desired format for the returned key PEM | SSH
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
                "SSHPublicKeyBody": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDZu11q42q3RAAzn+2LVvP+rPcgzuFM6hHTLBQjwQL69RnqLvzWNzyafAfyM1JD4wkOlhjw0KY/qNoPjxpikPW5O6VME6Y3rO6mbFbfuAyuj/x+gQrw6WES81/04iO+I/6CiUBHNV/nY8plsz31a2m/Wg1SGTFMxpvhAAQ1qQsUzErrIXlqe2f5qN9/wTTuuHms1kuNP3rHfUku18fjr05V5bUUKc7vyEnkZuuX4BsADIYu4t/X/bveEhhOzjvd6dAmEwTPsamH8ROcwa32F5cdShBu2AFjck9H3hij6TKgYZTHTJA3WZSXFNlXdcgfbHm67gHjCq86PKdObsdUzkq5",
                "SSHPublicKeyId": "APKAIJFT7TINGJTDLAZQ",
                "Status": "Active",
                "UploadDate": "2017-04-03T23:15:20+00:00",
                "UserName": "psharkey"
            },
            {
                "Fingerprint": "84:62:be:70:88:d4:ed:f8:26:58:15:90:f1:4b:27:70",
                "SSHPublicKeyBody": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCNpbiWvkOtiN64cBl7Papp2HfB7Co2RGWG6m5iL8jXafwlqLuKxmNiaNgJ1q1vbcZvczxBzPo2wVQy2ra3Ea9/cjICxoHpl7rpPJ9zAViWQ+4NiudLgyNwvvcfywzzmCMw+vqOi6vlr/iy89Y1AMz7pDP0Ax/OY1yJkkXqL1BQiF1dxNzVjCnRhLbA85e2LDUE30zaJC+9qe6GOhLOkqUSOn0H8WqcJTPqdd1lgPhZKDtnN6GKBaOBqGt7m5EKqUewU13+FOroRQBQsMX6EH4/MHaZNUi8LKAfmY2gPGahTlQLJwypDZ4zD1C6BDvTLLzoL0QkbSEaP6mXYBQ3zMzP",
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
            encoding=dict(required=True)
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


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
