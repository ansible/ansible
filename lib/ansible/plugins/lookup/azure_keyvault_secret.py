# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: azure_keyvault_secret
    author:
        - Hai Cao <t-haicao@microsoft.com>
    version_added: 2.6
    requirements:
        - requests
        - azure
        - msrest
    short_description: read secret from azure key vault.
    description:
      - This lookup returns the content of a secret kept in azure key vault.
    options:
        _terms:
            description: secret name of the secret to retrieve, version can be included like this: secret_name/secret_version, note that if version is not provided, key vault will give the latest version.
            required: True
        vault_url:
            description: url of azure key vault to be retrieved from
            default: 'azure-key-vault'
            required: True
        client_id:
            description: client_id of service principal that has access to the provided azure key vault
        key:
            description: key of service principal provided above
        tenant_id:
            description: tenant_id of service principal provided above
    notes:
        - If this plugin is called on an azure virtual machine and the machine has access to the desired key vault via MSI, then you don't need to provide client_id, key, tenant_id.
        - If this plugin is called on a non-azure virtual machine or it's an azure machine has no access to the desired key vault via MSI, then you have to provide a valid service principal that has access to the key vault. 
"""

EXAMPLE = """
- debug: msg="the value of this secret is {{lookup('azure_keyvault_secret','testSecret/version')}}"

- debug: msg="the value of this secret is {{lookup('azure_keyvault_secret','testSecret/version',vault_url='https://myvault.vault.azure.net', cliend_id='123456789', key='abcdefg', tenant_id='uvwxyz')}}"
"""

RETURN = """
  _raw:
    description: secret content
"""

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
import requests

TOKEN_ACQUIRED = False

token_params = {
    'api-version': '2018-02-01',
    'resource': 'https://vault.azure.net'
}
token_headers = {
    'Metadata': 'true'
}
token = None
try:
    token_res = requests.get('http://169.254.169.254/metadata/identity/oauth2/token', params=token_params, headers=token_headers)
    token = token_res.json()["access_token"]
    TOKEN_ACQUIRED = True
except requests.exceptions.RequestException as e:
    print('Unable to fetch MSI token. Will use service principal if provided.')
    TOKEN_ACQUIRED = False


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        ret = []
        vault_url = kwargs.pop('vault_url', None)
        if TOKEN_ACQUIRED:
            secret_params = {'api-version': '2016-10-01'}
            secret_headers = {'Authorization': 'Bearer ' + token}
            for term in terms:
                try:
                    secret_res = requests.get(vault_url + 'secrets/' + term, params=secret_params, headers=secret_headers)
                    ret.append(secret_res.json()["value"])
                except requests.exceptions.RequestException as e:
                    raise AnsibleError('Failed to fetch secret: ' + term + ' via MSI endpoint.')
                except KeyError:
                    raise AnsibleError('Failed to fetch secret ' + term + '.')
            return ret
        else:
            import logging
            logging.getLogger('msrestazure.azure_active_directory').addHandler(logging.NullHandler())
            logging.getLogger('msrest.service_client').addHandler(logging.NullHandler())

            try:
                from azure.common.credentials import ServicePrincipalCredentials
                from azure.keyvault import KeyVaultClient
                from msrest.exceptions import AuthenticationError, ClientRequestError
                from azure.keyvault.models.key_vault_error import KeyVaultErrorException
            except ImportError:
                raise AnsibleError('The azure_keyvault_secret lookup plugin requires azure.keyvault and azure.common.credentials to be installed.')

            client_id = kwargs.pop('client_id', None)
            key = kwargs.pop('key', None)
            tenant_id = kwargs.pop('tenant_id', None)

            try:
                credentials = ServicePrincipalCredentials(
                    client_id=client_id,
                    secret=key,
                    tenant=tenant_id
                )
                client = KeyVaultClient(credentials)
            except AuthenticationError as e:
                raise AnsibleError('Invalid credentials provided.')

            for term in terms:
                try:
                    secret = client.get_secret(vault_url, term, '').value
                    ret.append(secret)
                except ClientRequestError as e:
                    raise AnsibleError('Error occurred in request')
                except KeyVaultErrorException as e:
                    raise AnsibleError('Failed to fetch secret ' + term + '.')
            return ret
