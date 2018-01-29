from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
  lookup: azure_key_vault
  author: James Johnson <james.johnson@hmcts.net>
  short_description: Retrieve secrets from an Azure Key-Vault.
  requirements:
    - azure-keyvault (python library)
  description:
    - Retrieve secrets from an Azure Key-Vault.
  options:
    secret_name:
      description: The name of the secret requested.
      required: True
    vault_uri:
      description: The URI of the Azure vault.
      required: True
      env:
        - name: AZURE_VAULT_URI
    azure_client_id:
      description: The URI of the vault to query.
      required: True
      env:
        - name: AZURE_CLIENT_ID
    azure_client_secret:
      description: Your Azure Active Directory Service Principal AppId.
      required: True
      env:
        - name: AZURE_SECRET                
    azure_tenant_id:
      description: Your Azure Active Directory Application Key.
      required: True
      env:
        - name: AZURE_TENANT
    secret_version:
      description: your Azure Active Directory tenant id or domain.
      default: 'latest'
"""

EXAMPLES = """
- name: Return a secret.
  debug:
    msg: "{{ lookup('azure_key_vault', 'secret_name=someSecretName') }}"

- name: Return a secret from a specified vault_uri.
  debug:
    msg: "{{ lookup('azure_key_vault', 'secret_name=someSecretName vault_uri=https://anothervault.vault.azure.net/') }}"
    
- name: Return a specific version of a secret.
  debug:
    msg: "{{ lookup('azure_key_vault', 'secret_name=someSecretName secret_version=169591fbe36742beb109478459f426ce') }}" 

 - name: Return a specific version of a secret from a specified vault_uri.
  debug:
    msg: "{{ lookup('azure_key_vault', 'secret_name=someSecretName secret_version=169591fbe36742beb109478459f426ce vault_uri=https://anothervault.vault.azure.net/') }}"
"""

RETURN = """
_raw:
  description:
    - the secret requested.
"""

import os

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

try:
    from azure.common.credentials import ServicePrincipalCredentials
    from azure.keyvault import KeyVaultClient

except ImportError:
    raise AnsibleError(
        "Please run 'pip install azure-keyvault' to use the azure_key_vault lookup module.")


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        ret = []

        accepted_params = {
            'secret_name': None,
            'vault_uri': os.environ.get('AZURE_VAULT_URI', None),
            'secret_version': '',
            'azure_client_id': os.environ.get('AZURE_CLIENT_ID', None),
            'azure_client_secret': os.environ.get('AZURE_SECRET', None),
            'azure_tenant_id': os.environ.get('AZURE_TENANT', None),
        }

        input_args = terms[0].split(' ')

        for param in input_args:
            try:
                key, value = param.split('=')
                if key not in accepted_params:
                    raise AnsibleError('%s not an accepted parameter' % key)
                accepted_params[key] = value
            except (ValueError, AssertionError):
                raise AnsibleError(
                    "azure_key_vault lookup plugin needs key=value pairs, but received %s" %
                    terms)
        try:
            if accepted_params['azure_client_id'] is None:
                raise AnsibleError(
                "Please set AZURE_CLIENT_ID environment variable or provide azure_client_id value in the form azure_client_id=some_value")

            if accepted_params['azure_client_secret'] is None:
                raise AnsibleError("Please set AZURE_SECRET environment variable or provide azure_client_secret value in the form azure_client_secret=some_value")

            if accepted_params['azure_tenant_id'] is None:
                raise AnsibleError("Please set AZURE_TENANT environment variable or provide azure_tenant_id value in the form azure_tenant_id=some_value")

            if accepted_params['secret_name'] is None:
                raise AnsibleError(
                    "Please provide a secret_name value in the form secret_name=some_value")

            if accepted_params['vault_uri'] is None:
                raise AnsibleError(
                    "Please set AZURE_VAULT_URI environment variable or provide vault_uri value in the form vault_uri=https://myvault.vault.azure.net/")

            credentials = ServicePrincipalCredentials(
                client_id=accepted_params['azure_client_id'],
                secret=accepted_params['azure_client_secret'],
                tenant=accepted_params['azure_tenant_id'])

            key_vault_client = KeyVaultClient(credentials)

            secret_bundle = key_vault_client.get_secret(
                accepted_params['vault_uri'],
                accepted_params['secret_name'],
                secret_version=accepted_params['secret_version'])
            ret.append(secret_bundle.value)
        except (ValueError, AssertionError) as exception:
            raise AnsibleError("Error retrieving secret " + exception)

        return ret
