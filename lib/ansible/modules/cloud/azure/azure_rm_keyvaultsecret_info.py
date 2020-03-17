#!/usr/bin/python
#
# Copyright (c) 2019 Jose Angel Munoz, <josea.munoz@gmail.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: azure_rm_keyvaultsecret_info
version_added: "2.10"
short_description: Get Azure Key Vault secret facts
description:
    - Get facts of Azure Key Vault secret.

options:
    vault_uri:
        description:
            - Vault uri where the secret stored in.
        required: True
        type: str
    name:
        description:
            - Secret name. If not set, will list all secrets in vault_uri.
        type: str
    version:
        description:
            - Secret version.
            - Set it to C(current) to show latest version of a secret.
            - Set it to C(all) to list all versions of a secret.
            - Set it to specific version to list specific version of a secret. eg. fd2682392a504455b79c90dd04a1bf46
        default: current
        type: str
    show_deleted_secret:
        description:
            - Set to I(show_delete_secret=true) to show deleted secrets. Set to I(show_deleted_secret=false) to show not deleted secrets.
        type: bool
        default: false
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.
        type: dict

extends_documentation_fragment:
    - azure

author:
    - Jose Angel Munoz (@imjoseangel)

'''

EXAMPLES = '''
  - name: Get latest version of specific secret
    azure_rm_keyvaultsecret_info:
      vault_uri: "https://myVault.vault.azure.net"
      name: mySecret

  - name: List all versions of specific secret
    azure_rm_keyvaultsecret_info:
      vault_uri: "https://myVault.vault.azure.net"
      name: mySecret
      version: all

  - name: List specific version of specific secret
    azure_rm_keyvaultsecret_info:
      vault_uri: "https://myVault.vault.azure.net"
      name: mySecret
      version: fd2682392a504455b79c90dd04a1bf46

  - name: List all secrets in specific key vault
    azure_rm_keyvaultsecret_info:
        vault_uri: "https://myVault.vault.azure.net"

  - name: List deleted secrets in specific key vault
    azure_rm_keyvaultsecret_info:
        vault_uri: "https://myVault.vault.azure.net"
        show_deleted_secret: True
'''

RETURN = '''
keyvaults:
    description:
        - List of secrets in Azure Key Vault.
    returned: always
    type: complex
    contains:
        sid:
            description:
                - Secret identifier.
            returned: always
            type: str
            sample: "https://myVault.vault.azure.net/flexsecret/secret1/fd2682392a504455b79c90dd04a1bf46"
        version:
            description:
                - Secret version.
            type: str
            returned: always
            sample: fd2682392a504455b79c90dd04a1bf46
        secret:
            description: secret value.
            type: str
            returned: always
            sample: mysecretvault
        tags:
            description:
                - Tags of the secret.
            returned: always
            type: dict
            sample: {"delete": "on-exit"}
        type:
            description:
                - Content type (optional)
            returned: always
            type: str
            sample: mysecrettype
        attributes:
            description:
                - Secret attributes.
            type: dict
            contains:
                created:
                    description:
                        - Creation datetime.
                    returned: always
                    type: str
                    sample: "2019-04-25T07:26:49+00:00"
                not_before:
                    description:
                        - Not before datetime.
                    type: str
                    sample: "2019-04-25T07:26:49+00:00"
                expires:
                    description:
                        - Expiration datetime.
                    type: str
                    sample: "2019-04-25T07:26:49+00:00"
                updated:
                    description:
                        - Update datetime.
                    returned: always
                    type: str
                    sample: "2019-04-25T07:26:49+00:00"
                enabled:
                    description:
                        - Indicate whether the secret is enabled.
                    returned: always
                    type: str
                    sample: true
                recovery_level:
                    description:
                        - Reflects the deletion recovery level currently in effect for secrets in the current vault.
                        - If it contains 'Purgeable' the secret can be permanently deleted by a privileged user,
                        - Otherwise, only the system can purge the secret, at the end of the retention interval.
                    returned: always
                    type: str
                    sample: Recoverable+Purgeable
'''

from ansible_collections.azure.azcollection.plugins.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from azure.keyvault import KeyVaultClient, KeyVaultId, KeyVaultAuthentication
    from azure.common.credentials import ServicePrincipalCredentials
    from azure.keyvault.models.key_vault_error import KeyVaultErrorException
    from msrestazure.azure_active_directory import MSIAuthentication
except ImportError:
    # This is handled in azure_rm_common
    pass


def secretbundle_to_dict(bundle):
    return dict(tags=bundle.tags,
                attributes=dict(
                    enabled=bundle.attributes.enabled,
                    not_before=bundle.attributes.not_before,
                    expires=bundle.attributes.expires,
                    created=bundle.attributes.created,
                    updated=bundle.attributes.updated,
                    recovery_level=bundle.attributes.recovery_level),
                sid=bundle.id,
                version=KeyVaultId.parse_secret_id(bundle.id).version,
                type=bundle.content_type,
                secret=bundle.value)


def deletedsecretbundle_to_dict(bundle):
    secretbundle = secretbundle_to_dict(bundle)
    secretbundle['recovery_id'] = bundle.recovery_id,
    secretbundle['scheduled_purge_date'] = bundle.scheduled_purge_date,
    secretbundle['deleted_date'] = bundle.deleted_date
    return secretbundle


def secretitem_to_dict(secretitem):
    return dict(sid=secretitem.id,
                version=KeyVaultId.parse_secret_id(secretitem.id).version,
                tags=secretitem.tags,
                attributes=dict(
                    enabled=secretitem.attributes.enabled,
                    not_before=secretitem.attributes.not_before,
                    expires=secretitem.attributes.expires,
                    created=secretitem.attributes.created,
                    updated=secretitem.attributes.updated,
                    recovery_level=secretitem.attributes.recovery_level))


def deletedsecretitem_to_dict(secretitem):
    item = secretitem_to_dict(secretitem)
    item['recovery_id'] = secretitem.recovery_id,
    item['scheduled_purge_date'] = secretitem.scheduled_purge_date,
    item['deleted_date'] = secretitem.deleted_date
    return item


class AzureRMKeyVaultSecretInfo(AzureRMModuleBase):
    def __init__(self):
        self.module_arg_spec = dict(version=dict(type='str',
                                                 default='current'),
                                    name=dict(type='str'),
                                    vault_uri=dict(type='str', required=True),
                                    show_deleted_secret=dict(type='bool',
                                                             default=False),
                                    tags=dict(type='dict'))

        self.vault_uri = None
        self.name = None
        self.version = None
        self.show_deleted_secret = False
        self.tags = None

        self.results = dict(changed=False)
        self._client = None

        super(AzureRMKeyVaultSecretInfo,
              self).__init__(derived_arg_spec=self.module_arg_spec,
                             supports_check_mode=False,
                             supports_tags=False)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for secret in list(self.module_arg_spec.keys()):
            if hasattr(self, secret):
                setattr(self, secret, kwargs[secret])

        self._client = self.get_keyvault_client()

        if self.name:
            if self.show_deleted_secret:
                self.results['secrets'] = self.get_deleted_secret()
            else:
                if self.version == 'all':
                    self.results['secrets'] = self.get_secret_versions()
                else:
                    self.results['secrets'] = self.get_secret()
        else:
            if self.show_deleted_secret:
                self.results['secrets'] = self.list_deleted_secrets()
            else:
                self.results['secrets'] = self.list_secrets()

        return self.results

    def get_keyvault_client(self):
        try:
            self.log("Get KeyVaultClient from MSI")
            credentials = MSIAuthentication(resource='https://vault.azure.net')
            return KeyVaultClient(credentials)
        except Exception:
            self.log("Get KeyVaultClient from service principal")

        # Create KeyVault Client using KeyVault auth class and auth_callback
        def auth_callback(server, resource, scope):
            if self.credentials['client_id'] is None or self.credentials[
                    'secret'] is None:
                self.fail(
                    'Please specify client_id, secret and tenant to access azure Key Vault.'
                )

            tenant = self.credentials.get('tenant')
            if not self.credentials['tenant']:
                tenant = "common"

            authcredential = ServicePrincipalCredentials(
                client_id=self.credentials['client_id'],
                secret=self.credentials['secret'],
                tenant=tenant,
                cloud_environment=self._cloud_environment,
                resource="https://vault.azure.net")

            token = authcredential.token
            return token['token_type'], token['access_token']

        return KeyVaultClient(KeyVaultAuthentication(auth_callback))

    def get_secret(self):
        '''
        Gets the properties of the specified secret in key vault.

        :return: deserialized secret state dictionary
        '''
        self.log("Get the secret {0}".format(self.name))

        results = []
        try:
            if self.version == 'current':
                response = self._client.get_secret(
                    vault_base_url=self.vault_uri,
                    secret_name=self.name,
                    secret_version='')
            else:
                response = self._client.get_secret(
                    vault_base_url=self.vault_uri,
                    secret_name=self.name,
                    secret_version=self.version)

            if response and self.has_tags(response.tags, self.tags):
                self.log("Response : {0}".format(response))
                results.append(secretbundle_to_dict(response))

        except KeyVaultErrorException as e:
            self.log("Did not find the key vault secret {0}: {1}".format(
                self.name, str(e)))
        return results

    def get_secret_versions(self):
        '''
        Lists secrets versions.

        :return: deserialized versions of secret, includes secret identifier, attributes and tags
        '''
        self.log("Get the secret versions {0}".format(self.name))

        results = []
        try:
            response = self._client.get_secret_versions(
                vault_base_url=self.vault_uri, secret_name=self.name)
            self.log("Response : {0}".format(response))

            if response:
                for item in response:
                    if self.has_tags(item.tags, self.tags):
                        results.append(secretitem_to_dict(item))
        except KeyVaultErrorException as e:
            self.log("Did not find secret versions {0} : {1}.".format(
                self.name, str(e)))
        return results

    def list_secrets(self):
        '''
        Lists secrets in specific key vault.

        :return: deserialized secrets, includes secret identifier, attributes and tags.
        '''
        self.log("Get the key vaults in current subscription")

        results = []
        try:
            response = self._client.get_secrets(vault_base_url=self.vault_uri)
            self.log("Response : {0}".format(response))

            if response:
                for item in response:
                    if self.has_tags(item.tags, self.tags):
                        results.append(secretitem_to_dict(item))
        except KeyVaultErrorException as e:
            self.log(
                "Did not find key vault in current subscription {0}.".format(
                    str(e)))
        return results

    def get_deleted_secret(self):
        '''
        Gets the properties of the specified deleted secret in key vault.

        :return: deserialized secret state dictionary
        '''
        self.log("Get the secret {0}".format(self.name))

        results = []
        try:
            response = self._client.get_deleted_secret(
                vault_base_url=self.vault_uri, secret_name=self.name)

            if response and self.has_tags(response.tags, self.tags):
                self.log("Response : {0}".format(response))
                results.append(deletedsecretbundle_to_dict(response))

        except KeyVaultErrorException as e:
            self.log("Did not find the key vault secret {0}: {1}".format(
                self.name, str(e)))
        return results

    def list_deleted_secrets(self):
        '''
        Lists deleted secrets in specific key vault.

        :return: deserialized secrets, includes secret identifier, attributes and tags.
        '''
        self.log("Get the key vaults in current subscription")

        results = []
        try:
            response = self._client.get_deleted_secrets(
                vault_base_url=self.vault_uri)
            self.log("Response : {0}".format(response))

            if response:
                for item in response:
                    if self.has_tags(item.tags, self.tags):
                        results.append(deletedsecretitem_to_dict(item))
        except KeyVaultErrorException as e:
            self.log(
                "Did not find key vault in current subscription {0}.".format(
                    str(e)))
        return results


def main():
    """Main execution"""
    AzureRMKeyVaultSecretInfo()


if __name__ == '__main__':
    main()
