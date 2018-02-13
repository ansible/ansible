#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.
import botocore

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: aws_glacier_vault
short_description: Manage Glacier vaults in AWS
description:
    - Manage Glacier vaults in AWS
version_added: "2.6"
requirements: [ boto3 ]
author: "Loic Blot <loic.blot@unix-experience.fr>"
options:
  name:
    description:
      - Name of the glacier vault
    required: true
    default: null
  state:
    description:
      - Create or remove the glacier vault
    required: false
    default: present
    choices: [ 'present', 'absent' ]
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create a simple glacier vault
- aws_glacier_vault:
    name: myglaciervault

# Create a simple glacier vault in eu-west-3 region
- aws_glacier_vault:
    name: myglaciervault
    region: eu-west-3

# Remove an glacier vault
- aws_glacier_vault:
    name: myglaciervault
    state: absent
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (ec2_argument_spec, boto3_conn, HAS_BOTO3, get_aws_connection_info,
                                      boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_filter_list,
                                      camel_dict_to_snake_dict)

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass  # caught by imported HAS_BOTO3


class GlacierVaultManager(object):
    def __init__(self, connection, module):
        self.connection = connection
        self.module = module

    def list(self):
        vaults = self.connection.list_vaults()
        if "VaultList" not in vaults:
            self.module.fail_json(msg="Invalid response from Glacier: no VaultList found in response")

        return vaults["VaultList"]

    def exists(self, name):
        for v in self.list():
            if "VaultName" not in v:
                self.module.fail_json(
                    msg="Invalid response from Glacier: no VaultName found in vault object {}".format(v))

            if v["VaultName"] == name:
                return v

        return None

    def create_or_update(self):
        name = self.module.params.get('name')
        vault = self.exists(name)

        if vault is None:
            vault = self.connection.create_vault(vaultName=name)
            self.module.exit_json(vault=vault, changed=True)

        # Vault exists, no change to do
        self.module.exit_json(vault=vault, changed=False)

    def destroy(self):
        name = self.module.params.get('name')
        vault = self.exists(name)
        if vault is None:
            self.module.exit_json(changed=False)

        self.connection.delete_vault(vaultName=name)
        self.module.exit_json(vault=vault, changed=True)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True, type='str'),
            state=dict(default='present', type='str', choices=['present', 'absent']),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        connection = boto3_conn(
            module,
            conn_type='client',
            resource='glacier',
            region=region,
            endpoint=ec2_url,
            **aws_connect_params
        )
    else:
        module.fail_json(msg="region must be specified")

    if connection is None:  # this should never happen
        module.fail_json(msg='Unknown error, failed to create glacier connection, no information from boto.')

    state = module.params.get("state")

    try:
        if state == 'present':
            GlacierVaultManager(connection, module).create_or_update()
        elif state == 'absent':
            GlacierVaultManager(connection, module).destroy()
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg="AWS credential error: {}".format(e))
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="AWS client error: {}".format(e))


if __name__ == '__main__':
    main()
