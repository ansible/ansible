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
            required: True
        client_id:
            description: client_id of service principal that has access to the provided azure key vault
        secret:
            description: secret of service principal provided above
        tenant_id:
            description: tenant_id of service principal provided above
    notes:
        - If ansible is running on Azure Virtual Machine with MSI enabled, client_id, secret and tenant isn't necessary. For how to enable MSI on Azure Virutal Machine, please refer to this doc https://docs.microsoft.com/en-us/azure/active-directory/managed-service-identity/
        - If this plugin is called on a non-azure virtual machine or it's an azure machine has no access to the desired key vault via MSI, then you have to provide a valid service principal that has access to the key vault. 
"""

EXAMPLE = """
- debug: msg="the value of this secret is {{lookup('azure_keyvault_secret','testSecret/version')}}"

- debug: msg="the value of this secret is {{lookup('azure_keyvault_secret','testSecret/version',vault_url='https://myvault.vault.azure.net', cliend_id='123456789', secret='abcdefg', tenant_id='uvwxyz')}}"

# Example below creates an Azure Virtual Machine with ssh public key from key vault using 'azure_keyvault_secret' lookup plugin.
- name: Create Azure VM
  hosts: localhost
  connection: local
  vars:
    resource_group: myResourceGroup
    vm_name: testvm
    location: eastus
    ssh_key: "{{ lookup('azure_keyvault_secret','myssh_key') }}"
  - name: Create VM
    azure_rm_virtualmachine:
      resource_group: "{{ resource_group }}"
      name: "{{ vm_name }}"
      vm_size: Standard_DS1_v2
      admin_username: azureuser
      ssh_password_enabled: false
      ssh_public_keys:
        - path: /home/azureuser/.ssh/authorized_keys
          key_data: "{{ ssh_key }}"
      network_interfaces: "{{ vm_name }}"
      image:
        offer: UbuntuServer
        publisher: Canonical
        sku: 16.04-LTS
        version: latest
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
except requests.exceptions.RequestException:
    print('Unable to fetch MSI token. Will use service principal if provided.')
    TOKEN_ACQUIRED = False


def lookup_sercret_non_msi(terms, vault_url, kwargs):
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
    secret = kwargs.pop('secret', None)
    tenant_id = kwargs.pop('tenant_id', None)

    try:
        credentials = ServicePrincipalCredentials(
            client_id=client_id,
            secret=secret,
            tenant=tenant_id
        )
        client = KeyVaultClient(credentials)
    except AuthenticationError:
        raise AnsibleError('Invalid credentials provided.')

    ret = []
    for term in terms:
        try:
            secret_val = client.get_secret(vault_url, term, '').value
            ret.append(secret_val)
        except ClientRequestError:
            raise AnsibleError('Error occurred in request')
        except KeyVaultErrorException:
            raise AnsibleError('Failed to fetch secret ' + term + '.')
    return ret


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
                except requests.exceptions.RequestException:
                    raise AnsibleError('Failed to fetch secret: ' + term + ' via MSI endpoint.')
                except KeyError:
                    raise AnsibleError('Failed to fetch secret ' + term + '.')
            return ret
        else:
            return lookup_sercret_non_msi(terms,vault_url,kwargs)
