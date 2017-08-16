#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_keyvaultsecret
version_added: "2.4"
short_description: Use Azure KeyVault Secrets.
description:
    - Create or delete a secret within a given keyvault. By using Key Vault, you can encrypt
      keys and secrets (such as authentication keys, storage account keys, data encryption keys, .PFX files, and passwords).
options:
    keyvault_uri:
            description:
                - URI of the keyvault endpoint.
            required: true
    secret_name:
        description:
            - Name of the keyvault secret.
        required: true
    secret_value:
        description:
            - Secret to be secured by keyvault.
        required: false
        aliases:
            - secret
    state:
        description:
            - Assert the state of the subnet. Use 'present' to create or update a secret and
              'absent' to delete a secret .
        required: false
        default: present
        choices:
            - absent
            - present

extends_documentation_fragment:
    - azure

author:
    - "Ian Philpot (@tripdubroot)"

'''

EXAMPLES = '''
    - name: Create a secret
      azure_rm_keyvaultsecret:
        secret_name: MySecret
        secret_value: My_Pass_Sec
        keyvault_uri: https://contoso.vault.azure.net/

    - name: Delete a secret
      azure_rm_keyvaultsecret:
        secret_name: MySecret
        keyvault_uri: https://contoso.vault.azure.net/
        state: absent
'''

RETURN = '''
state:
    description: Current state of the secret.
    returned: success
    type: complex
    contains:
        secret_id:
          description: Secret resource path.
          type: str
          example: https://contoso.vault.azure.net/secrets/hello/e924f053839f4431b35bc54393f98423
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from azure.keyvault import KeyVaultClient, KeyVaultAuthentication, KeyVaultId
    from azure.common.credentials import ServicePrincipalCredentials
    from azure.keyvault.models.key_vault_error import KeyVaultErrorException
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMKeyVaultSecret(AzureRMModuleBase):
    ''' Module that creates or deletes secrets in Azure KeyVault '''

    def __init__(self):

        self.module_arg_spec = dict(
            secret_name=dict(type='str', required=True),
            secret_value=dict(type='str', aliases=['secret'], no_log=True),
            keyvault_uri=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent'])
        )

        required_if = [
            ('state', 'present', ['secret_value'])
        ]

        self.results = dict(
            changed=False,
            state=dict()
        )

        self.secret_name = None
        self.secret_value = None
        self.keyvault_uri = None
        self.state = None
        self.data_creds = None
        self.client = None

        super(AzureRMKeyVaultSecret, self).__init__(self.module_arg_spec,
                                                    supports_check_mode=True,
                                                    required_if=required_if)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        # Need to override base to add resource argument
        self.azure_credentials = \
            ServicePrincipalCredentials(client_id=self.credentials['client_id'],
                                        secret=self.credentials['secret'],
                                        tenant=self.credentials['tenant'],
                                        resource='https://vault.azure.net')

        # Create KeyVault Client using KeyVault auth class and auth_callback
        self.client = KeyVaultClient(KeyVaultAuthentication(self.auth_callback))

        results = dict()
        changed = False

        try:
            results['secret_id'] = self.get_secret(self.secret_name)

            # Secret exists and will be deleted
            if self.state == 'absent':
                changed = True

        except KeyVaultErrorException:
            # Secret doesn't exist
            if self.state == 'present':
                changed = True

        self.results['changed'] = changed
        self.results['state'] = results

        # Create secret
        if self.state == 'present' and changed:
            results['secret_id'] = self.create_secret(self.secret_name, self.secret_value)
            self.results['state'] = results
            self.results['state']['status'] = 'Created'
        # Delete secret
        elif self.state == 'absent' and changed:
            results['secret_id'] = self.delete_secret(self.secret_name)
            self.results['state'] = results
            self.results['state']['status'] = 'Deleted'

        return self.results

    def auth_callback(self, server, resource, scope):
        ''' Used by KeyVaultAuth to get token info '''
        self.data_creds = self.data_creds or self.azure_credentials
        token = self.data_creds.token
        return token['token_type'], token['access_token']

    def get_secret(self, name, version=''):
        ''' Gets an existing secret '''
        secret_bundle = self.client.get_secret(self.keyvault_uri, name, version)
        if secret_bundle:
            secret_id = KeyVaultId.parse_secret_id(secret_bundle.id)
        return secret_id.id

    def create_secret(self, name, secret):
        ''' Creates a secret '''
        secret_bundle = self.client.set_secret(self.keyvault_uri, name, secret)
        secret_id = KeyVaultId.parse_secret_id(secret_bundle.id)
        return secret_id.id

    def delete_secret(self, name):
        ''' Deletes a secret '''
        deleted_secret = self.client.delete_secret(self.keyvault_uri, name)
        secret_id = KeyVaultId.parse_secret_id(deleted_secret.id)
        return secret_id.id


def main():
    AzureRMKeyVaultSecret()

if __name__ == '__main__':
    main()
