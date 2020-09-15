#!/usr/bin/python
#
# Copyright (c) 2019 Yunge Zhu, <yungez@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_keyvault_info
version_added: "2.9"
short_description: Get Azure Key Vault facts
description:
    - Get facts of Azure Key Vault.

options:
    resource_group:
        description:
            - The name of the resource group to which the key vault belongs.
    name:
        description:
            - The name of the key vault.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - Yunge Zhu (@yungezz)

'''

EXAMPLES = '''
  - name: Get Key Vault by name
    azure_rm_keyvault_info:
      resource_group: myResourceGroup
      name: myVault

  - name: List Key Vaults in specific resource group
    azure_rm_keyvault_info:
      resource_group: myResourceGroup

  - name: List Key Vaults in current subscription
    azure_rm_keyvault_info:
'''

RETURN = '''
keyvaults:
    description: List of Azure Key Vaults.
    returned: always
    type: list
    contains:
        name:
            description:
                - Name of the vault.
            returned: always
            type: str
            sample: myVault
        id:
            description:
                - Resource Id of the vault.
            returned: always
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.KeyVault/vaults/myVault
        vault_uri:
            description:
                - Vault uri.
            returned: always
            type: str
            sample: https://myVault.vault.azure.net/
        location:
            description:
                - Location of the vault.
            returned: always
            type: str
            sample: eastus
        enabled_for_deployments:
            description:
                - Whether Azure Virtual Machines are permitted to retrieve certificates stored as secrets from the key vault.
            returned: always
            type: bool
            sample: False
        enabled_for_disk_encryption:
            description:
                - Whether Azure Disk Encryption is permitted to retrieve secrets from the vault and unwrap keys.
            returned: always
            type: bool
            sample: False
        enabled_for_template_deployment:
            description:
                - Whether Azure Resource Manager is permitted to retrieve secrets from the key vault.
            returned: always
            type: bool
            sample: False
        tags:
            description:
                - List of tags.
            type: list
            sample:
                - foo
        sku:
            description:
                - Sku of the vault.
            returned: always
            type: dict
            contains:
                family:
                    description: Sku family name.
                    type: str
                    returned: always
                    sample: A
                name:
                    description: Sku name.
                    type: str
                    returned: always
                    sample: standard
        access_policies:
            description:
                - Location of the vault.
            returned: always
            type: list
            contains:
                object_id:
                    description: The object if of a user, service principal or security group in AAD for the vault.
                    type: str
                    returned: always
                    sample: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
                tenant_id:
                    description: The AAD tenant iD that should be used for authenticating requests to the key vault.
                    type: str
                    returned: always
                    sample: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
                permissions:
                    description: Permissions the identity has for keys, secrets and certificates.
                    type: complex
                    returned: always
                    contains:
                        keys:
                            description:
                                Permissions to keys.
                            type: list
                            returned: always
                            sample:
                                - get
                                - create
                        secrets:
                            description:
                                Permissions to secrets.
                            type: list
                            returned: always
                            sample:
                                - list
                                - set
                        certificates:
                            description:
                                Permissions to secrets.
                            type: list
                            returned: always
                            sample:
                                - get
                                - import
'''


from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from azure.mgmt.keyvault import KeyVaultManagementClient
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


def keyvault_to_dict(vault):
    return dict(
        id=vault.id,
        name=vault.name,
        location=vault.location,
        tags=vault.tags,
        vault_uri=vault.properties.vault_uri,
        enabled_for_deployment=vault.properties.enabled_for_deployment,
        enabled_for_disk_encryption=vault.properties.enabled_for_disk_encryption,
        enabled_for_template_deployment=vault.properties.enabled_for_template_deployment,
        access_policies=[dict(
            tenant_id=policy.tenant_id,
            object_id=policy.object_id,
            permissions=dict(
                keys=[kp.lower() for kp in policy.permissions.keys] if policy.permissions.keys else None,
                secrets=[sp.lower() for sp in policy.permissions.secrets] if policy.permissions.secrets else None,
                certificates=[cp.lower() for cp in policy.permissions.certificates] if policy.permissions.certificates else None
            ) if policy.permissions else None,
        ) for policy in vault.properties.access_policies] if vault.properties.access_policies else None,
        sku=dict(
            family=vault.properties.sku.family,
            name=vault.properties.sku.name.name
        )
    )


class AzureRMKeyVaultInfo(AzureRMModuleBase):

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(type='str'),
            name=dict(type='str'),
            tags=dict(type='list')
        )

        self.resource_group = None
        self.name = None
        self.tags = None

        self.results = dict(changed=False)
        self._client = None

        super(AzureRMKeyVaultInfo, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                  supports_check_mode=False,
                                                  supports_tags=False)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

        self._client = self.get_mgmt_svc_client(KeyVaultManagementClient,
                                                base_url=self._cloud_environment.endpoints.resource_manager,
                                                api_version="2018-02-14")

        if self.name:
            if self.resource_group:
                self.results['keyvaults'] = self.get_by_name()
            else:
                self.fail("resource_group is required when filtering by name")
        elif self.resource_group:
            self.results['keyvaults'] = self.list_by_resource_group()
        else:
            self.results['keyvaults'] = self.list()

        return self.results

    def get_by_name(self):
        '''
        Gets the properties of the specified key vault.

        :return: deserialized key vaultstate dictionary
        '''
        self.log("Get the key vault {0}".format(self.name))

        results = []
        try:
            response = self._client.vaults.get(resource_group_name=self.resource_group,
                                               vault_name=self.name)
            self.log("Response : {0}".format(response))

            if response and self.has_tags(response.tags, self.tags):
                results.append(keyvault_to_dict(response))
        except CloudError as e:
            self.log("Did not find the key vault {0}: {1}".format(self.name, str(e)))
        return results

    def list_by_resource_group(self):
        '''
        Lists the properties of key vaults in specific resource group.

        :return: deserialized key vaults state dictionary
        '''
        self.log("Get the key vaults in resource group {0}".format(self.resource_group))

        results = []
        try:
            response = list(self._client.vaults.list_by_resource_group(resource_group_name=self.resource_group))
            self.log("Response : {0}".format(response))

            if response:
                for item in response:
                    if self.has_tags(item.tags, self.tags):
                        results.append(keyvault_to_dict(item))
        except CloudError as e:
            self.log("Did not find key vaults in resource group {0} : {1}.".format(self.resource_group, str(e)))
        return results

    def list(self):
        '''
        Lists the properties of key vaults in specific subscription.

        :return: deserialized key vaults state dictionary
        '''
        self.log("Get the key vaults in current subscription")

        results = []
        try:
            response = list(self._client.vaults.list())
            self.log("Response : {0}".format(response))

            if response:
                for item in response:
                    if self.has_tags(item.tags, self.tags):
                        results.append(keyvault_to_dict(item))
        except CloudError as e:
            self.log("Did not find key vault in current subscription {0}.".format(str(e)))
        return results


def main():
    """Main execution"""
    AzureRMKeyVaultInfo()


if __name__ == '__main__':
    main()
