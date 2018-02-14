#!/usr/bin/python
# Copyright (c) 2018 Loic BLOT <loic.blot@unix-experience.fr>
# This module is sponsored by E.T.A.I. (www.etai.fr)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
  tags:
    description:
      - A hash/dictionary of tags to add to the new instance or to add/remove from an existing one.
extends_documentation_fragment:
    - aws
    - ec2
'''

RETURN = '''
vault:
    description: the vault object
    returned: always
    type: complex
    contains:
        creation_date:
            description: The vault creation date.
            returned: always
            type: string
            sample: "2018-02-13T22:10:28.590Z"
        number_of_archives:
            description: Number of archives currently in the vault.
            returned: always
            type: int
            sample: 0
        size_in_bytes:
            description: Current vault size.
            returned: always
            type: int
            sample: 0
        vault_arn:
            description: The vault AWS ARN.
            returned: always
            type: string
            sample: "arn:aws:glacier:eu-west-3:123457788994:vaults/test-vault"
        vault_name:
            description: The vault name.
            returned: always
            type: string
            sample: "test-vault"
tags:
    description: the vault tags
    returned: always
    type: dictionary
    sample: {
        "testtag": "testvalue"
    }
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

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (ec2_argument_spec, boto3_conn, HAS_BOTO3, get_aws_connection_info,
                                      compare_aws_tags, camel_dict_to_snake_dict)

try:
    import botocore
    from botocore.exceptions import ClientError
except ImportError:
    pass  # caught by imported HAS_BOTO3


class GlacierVaultManager(object):
    def __init__(self, connection, module):
        self.connection = connection
        self.module = module
        self.name = self.module.params.get('name')

    def list(self):
        vaults = {}
        try:
            vaults = self.connection.list_vaults()
        except (botocore.exceptions.NoCredentialsError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(exception=e, msg="Failed to list vaults")

        return vaults["VaultList"]

    def get_vault(self, name):
        for v in self.list():
            if v["VaultName"] == name:
                return v

        return None

    def create_or_update(self):
        changed = False
        vault = self.get_vault(self.name)
        if vault is None:
            try:
                vault = self.connection.create_vault(vaultName=self.name)
            except (botocore.exceptions.NoCredentialsError, botocore.exceptions.ClientError) as e:
                self.module.fail_json_aws(exception=e, msg="Failed to create vault")
            changed = True

        changed |= self.manage_tags()

        vault = self.get_vault(self.name)

        # Vault exists, no change to do
        self.module.exit_json(vault=camel_dict_to_snake_dict(vault), tags=self.list_tags(), changed=changed)

    def list_tags(self):
        tags = {}
        try:
            tags = self.connection.list_tags_for_vault(vaultName=self.name)
        except (botocore.exceptions.NoCredentialsError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(exception=e, msg="Failed to list vault tags")

        if "Tags" not in tags:
            self.module.fail_json(msg="Invalid response from Glacier: no Tags found in vault object {0}".format(tags))

        return tags["Tags"]

    def manage_tags(self):
        changed = False
        old_tags = self.list_tags()
        tags_to_set, tags_to_delete = compare_aws_tags(
            old_tags, self.module.params.get('tags') or {},
        )
        if tags_to_set:
            try:
                self.connection.add_tags_to_vault(vaultName=self.name, Tags=tags_to_set)
            except (botocore.exceptions.NoCredentialsError, botocore.exceptions.ClientError,
                    botocore.exceptions.ParamValidationError) as e:
                self.module.fail_json_aws(exception=e, msg="Failed to add vault tags")
            changed |= True
        if tags_to_delete:
            try:
                self.connection.remove_tags_from_vault(vaultName=self.name, TagKeys=tags_to_delete)
            except (botocore.exceptions.NoCredentialsError, botocore.exceptions.ClientError,
                    botocore.exceptions.ParamValidationError) as e:
                self.module.fail_json_aws(exception=e, msg="Failed to remove vault tags")
            changed |= True
        return changed

    def destroy(self):
        name = self.module.params.get('name')
        vault = self.get_vault(name)
        if vault is None:
            self.module.exit_json(changed=False)

        tags = self.list_tags()
        try:
            self.connection.delete_vault(vaultName=name)
        except (botocore.exceptions.NoCredentialsError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(exception=e, msg="Failed to delete vault")

        self.module.exit_json(vault=camel_dict_to_snake_dict(vault), tags=tags, changed=True)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
            tags=dict(type='dict'),
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    connection = boto3_conn(
        module,
        conn_type='client',
        resource='glacier',
        region=region,
        endpoint=ec2_url,
        **aws_connect_params
    )

    if connection is None:  # this should never happen
        module.fail_json(msg='Unknown error, failed to create glacier connection, no information from boto.')

    state = module.params.get("state")

    if state == 'present':
        GlacierVaultManager(connection, module).create_or_update()
    elif state == 'absent':
        GlacierVaultManager(connection, module).destroy()


if __name__ == '__main__':
    main()
