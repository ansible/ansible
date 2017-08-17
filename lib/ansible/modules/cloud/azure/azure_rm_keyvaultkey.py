#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_keyvaultkey
version_added: "2.4"
short_description: Use Azure KeyVault keys.
description:
    - Create or delete a key within a given keyvault. By using Key Vault, you can encrypt
      keys and secrets (such as authentication keys, storage account keys, data encryption keys, .PFX files, and passwords).
options:
    keyvault_uri:
            description:
                - URI of the keyvault endpoint.
            required: true
    key_name:
        description:
            - Name of the keyvault key.
        required: true
    state:
        description:
            - Assert the state of the key. Use 'present' to create a key and
              'absent' to delete a key.
        required: false
        default: present
        choices:
            - absent
            - present

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Ian Philpot (@tripdubroot)"

'''

EXAMPLES = '''
    - name: Create a key
      azure_rm_keyvaultkey:
        key_name: MyKey
        keyvault_uri: https://contoso.vault.azure.net/

    - name: Delete a key
      azure_rm_keyvaultkey:
        key_name: MyKey
        keyvault_uri: https://contoso.vault.azure.net/
        state: absent
'''

RETURN = '''
state:
    description: Current state of the key.
    returned: success
    type: complex
    contains:
        key_id:
          description: key resource path.
          type: str
          example: https://contoso.vault.azure.net/keys/hello/e924f053839f4431b35bc54393f98423
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from azure.keyvault import KeyVaultClient, KeyVaultAuthentication, KeyVaultId
    from azure.common.credentials import ServicePrincipalCredentials
    from azure.keyvault.models.key_vault_error import KeyVaultErrorException
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMKeyVaultKey(AzureRMModuleBase):
    ''' Module that creates or deletes keys in Azure KeyVault '''

    def __init__(self):

        self.module_arg_spec = dict(
            key_name=dict(type='str', required=True),
            keyvault_uri=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent'])
        )

        self.results = dict(
            changed=False,
            state=dict()
        )

        self.key_name = None
        self.keyvault_uri = None
        self.state = None
        self.client = None
        self.tags = None

        super(AzureRMKeyVaultKey, self).__init__(self.module_arg_spec,
                                                 supports_check_mode=True,
                                                 supports_tags=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        # Create KeyVaultClient
        self.client = KeyVaultClient(self.azure_credentials)

        results = dict()
        changed = False

        try:
            results['key_id'] = self.get_key(self.key_name)

            # Key exists and will be deleted
            if self.state == 'absent':
                changed = True

        except KeyVaultErrorException:
            # Key doesn't exist
            if self.state == 'present':
                changed = True

        self.results['changed'] = changed
        self.results['state'] = results

        if not self.check_mode:

            # Create key
            if self.state == 'present' and changed:
                results['key_id'] = self.create_key(self.key_name, self.tags)
                self.results['state'] = results
                self.results['state']['status'] = 'Created'
            # Delete key
            elif self.state == 'absent' and changed:
                results['key_id'] = self.delete_key(self.key_name)
                self.results['state'] = results
                self.results['state']['status'] = 'Deleted'

        return self.results

    def get_key(self, name, version=''):
        ''' Gets an existing key '''
        key_bundle = self.client.get_key(self.keyvault_uri, name, version)
        if key_bundle:
            key_id = KeyVaultId.parse_key_id(key_bundle.key.kid)
        return key_id.id

    def create_key(self, name, tags, kty='RSA'):
        ''' Creates a key '''
        key_bundle = self.client.create_key(self.keyvault_uri, name, kty, tags=tags)
        key_id = KeyVaultId.parse_key_id(key_bundle.key.kid)
        return key_id.id

    def delete_key(self, name):
        ''' Deletes a key '''
        deleted_key = self.client.delete_key(self.keyvault_uri, name)
        key_id = KeyVaultId.parse_key_id(deleted_key.key.kid)
        return key_id.id


def main():
    AzureRMKeyVaultKey()

if __name__ == '__main__':
    main()
