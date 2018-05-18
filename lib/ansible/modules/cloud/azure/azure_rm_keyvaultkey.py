#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_keyvaultkey
version_added: 2.5
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
    byok_file:
        description:
            - BYOK file.
    pem_file:
        description:
            - PEM file.
    pem_password:
        description:
            - PEM password.
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
    import re
    import codecs
    from azure.keyvault import KeyVaultClient, KeyVaultId
    from azure.keyvault.models import KeyAttributes, JsonWebKey
    from azure.common.credentials import ServicePrincipalCredentials
    from azure.keyvault.models.key_vault_error import KeyVaultErrorException
    from OpenSSL import crypto
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMKeyVaultKey(AzureRMModuleBase):
    ''' Module that creates or deletes keys in Azure KeyVault '''

    def __init__(self):

        self.module_arg_spec = dict(
            key_name=dict(type='str', required=True),
            keyvault_uri=dict(type='str', required=True),
            pem_file=dict(type='str'),
            pem_password=dict(type='str'),
            byok_file=dict(type='str'),
            state=dict(type='str', default='present', choices=['present', 'absent'])
        )

        self.results = dict(
            changed=False,
            state=dict()
        )

        self.key_name = None
        self.keyvault_uri = None
        self.pem_file = None
        self.pem_password = None
        self.state = None
        self.client = None
        self.tags = None

        required_if = [
            ('pem_password', 'present', ['pem_file'])
        ]

        super(AzureRMKeyVaultKey, self).__init__(self.module_arg_spec,
                                                 supports_check_mode=True,
                                                 required_if=required_if,
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
        else:
            if self.state == 'present' and changed:
                self.results['state']['status'] = 'Created'
            elif self.state == 'absent' and changed:
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

    def import_key(self, key_name, destination=None, key_ops=None, disabled=False, expires=None,
                   not_before=None, tags=None, pem_file=None, pem_password=None, byok_file=None):
        """ Import a private key. Supports importing base64 encoded private keys from PEM files.
            Supports importing BYOK keys into HSM for premium KeyVaults. """

        def _to_bytes(hex_string):
            # zero pads and decodes a hex string
            if len(hex_string) % 2:
                hex_string = '{0}'.format(hex_string)
            return codecs.decode(hex_string, 'hex_codec')

        def _set_rsa_parameters(dest, src):
            # map OpenSSL parameter names to JsonWebKey property names
            conversion_dict = {
                'modulus': 'n',
                'publicExponent': 'e',
                'privateExponent': 'd',
                'prime1': 'p',
                'prime2': 'q',
                'exponent1': 'dp',
                'exponent2': 'dq',
                'coefficient': 'qi'
            }
            # regex: looks for matches that fit the following patterns:
            #   integerPattern: 65537 (0x10001)
            #   hexPattern:
            #      00:a0:91:4d:00:23:4a:c6:83:b2:1b:4c:15:d5:be:
            #      d8:87:bd:c9:59:c2:e5:7a:f5:4a:e7:34:e8:f0:07:
            # The desired match should always be the first component of the match
            regex = re.compile(r'([^:\s]*(:[^\:)]+\))|([^:\s]*(:\s*[0-9A-Fa-f]{2})+))')
            # regex2: extracts the hex string from a format like: 65537 (0x10001)
            regex2 = re.compile(r'(?<=\(0x{1})([0-9A-Fa-f]*)(?=\))')

            key_params = crypto.dump_privatekey(crypto.FILETYPE_TEXT, src).decode('utf-8')
            for match in regex.findall(key_params):
                comps = match[0].split(':', 1)
                name = conversion_dict.get(comps[0], None)
                if name:
                    value = comps[1].replace(' ', '').replace('\n', '').replace(':', '')
                    try:
                        value = _to_bytes(value)
                    except Exception:  # pylint:disable=broad-except
                        # if decoding fails it is because of an integer pattern. Extract the hex
                        # string and retry
                        value = _to_bytes(regex2.findall(value)[0])
                    setattr(dest, name, value)

        key_attrs = KeyAttributes(not disabled, not_before, expires)
        key_obj = JsonWebKey(key_ops=key_ops)
        if pem_file:
            key_obj.kty = 'RSA'
            with open(pem_file, 'r') as f:
                pem_data = f.read()
            # load private key and prompt for password if encrypted
            try:
                pem_password = str(pem_password).encode() if pem_password else None
                # despite documentation saying password should be a string, it needs to actually
                # be UTF-8 encoded bytes
                pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, pem_data, pem_password)
            except crypto.Error:
                pass  # wrong password
            except TypeError:
                pass  # no pass provided
            _set_rsa_parameters(key_obj, pkey)
        elif byok_file:
            with open(byok_file, 'rb') as f:
                byok_data = f.read()
            key_obj.kty = 'RSA-HSM'
            key_obj.t = byok_data

        return self.client.import_key(
            self.keyvault_uri, key_name, key_obj, destination == 'hsm', key_attrs, tags)


def main():
    AzureRMKeyVaultKey()

if __name__ == '__main__':
    main()
