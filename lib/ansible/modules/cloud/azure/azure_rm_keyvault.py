#!/usr/bin/python
#
# Copyright (c) 2017 Ian Philpot, <ian.philpot@microsoft.com>;
# Obezimnaka Boms, <t-ozboms@microsoft.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_keyvault

version_added: "2.5"

short_description: Create, delete and update key vaults.

description:
    - Creates, deletes, and updates key vaults.

options:
    resource_group:
        description:
            - name of resource group.
        required: true
    name:
        description:
            - name of the key vault.
        required: true
    state:
        description:
            - Assert the state of the key vault. Use 'present' to create or update and
              'absent' to delete.
        default: present
        choices:
            - absent
            - present
    enabled_for_deployment:
        description:
            - allow Virtual Machines to retrieve certificates stored as secrets from the vault.
        default: False
    enabled_for_disk_encryption:
        description:
            - allow Disk Encryption to retrieve secrets from the vault and unwrap keys.
        default: False
    enabled_for_template_deployment:
        description:
            - allow Resource Manager to retrieve secrets from the vault.
        default: False
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
        default: resource_group location
    sku:
        description:
            - SKU details.
        default: standard
        choices:
            - premium
            - standard
    vault_uri:
        description:
            - the URI of the vault for performing operations on keys and secrets.
    tenant_id:
        description:
            - the Azure Active Directory tenant ID that should be used for authenticating requests to the key vault.
    object_id:
        description:
            - the object ID of a user, service principal or security group in the Azure Active Directory tenant for the vault.
              the object ID must be unique for the list of access policies.
    application_id:
        description:
            - application ID of the client making request on behalf of a principal.
    permissions:
        description:
            - permission templates for access policy.
        default: Key, Secret, & Certificate Management
        choices:
            - Key, Secret, & Certificate Management
            - Key & Secret Management
            - Secret & Certificate Management
            - Key Management
            - Secret Management
            - Certificate Management
            - SQL Server Connector
            - Azure Backup
            - Azure Data Lake Store

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Obezimnaka Boms (@ozboms)"
    - "Ian Philpot (@tripdubroot)"
'''

EXAMPLES = '''
##put in examples here
- name: Create a key vault
  azure_rm_keyvault:
    resource_group: Testing
    name: example.com
    state: present
    enabled_for_deployment: True
    location: westus
    sku: premium

- name: Create a key secret and certificate management key vault
  azure_rm_keyvault:
    name: "ozikeyvault"
    resource_group: "presentation_rg"
    state: "present"
    enabled_for_deployment: True
    location: "westus2"
    sku: "premium"
    enabled_for_disk_encryption: True
    tenant_id: "72f988bf-86f1-41af-91ab-2d7cd011db47"
    object_id: "0965570e-4e82-45ae-955a-c655dba6c014"

- name: Create a key management key vault
  azure_rm_keyvault:
    name: "ozikeymanagement"
    resource_group: "presentation_rg"
    state: "present"
    enabled_for_deployment: True
    location: "westus2"
    sku: "premium"
    enabled_for_disk_encryption: True
    tenant_id: "72f988bf-86f1-41af-91ab-2d7cd011db47"
    object_id: "0965570e-4e82-45ae-955a-c655dba6c014"
    permissions: "Key Management"

- name: Create a certificate management key vault
  azure_rm_keyvault:
    name: "ozicertmanagement"
    resource_group: "presentation_rg"
    state: "present"
    enabled_for_deployment: True
    location: "westus2"
    sku: "premium"
    enabled_for_disk_encryption: True
    tenant_id: "72f988bf-86f1-41af-91ab-2d7cd011db47"
    object_id: "0965570e-4e82-45ae-955a-c655dba6c014"
    permissions: "Certificate Management"

- name: Delete a key vault
  azure_rm_keyvault:
    resource_group: Testing
    name: example.com
    state: absent
    location: westus

'''

RETURN = '''
state:
    description: Current state of the key vault.
    returned: always
    type: dict
    example: {
        "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/presentation_rg/providers/Microsoft.KeyVault/vaults/ozidatamanagement",
        "location": "westus2",
        "name": "keyvault",
        "properties": {
            "access_policies": [
                {
                    "application_id": null,
                    "object_id": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
                    "permissions": {
                        "certificates": [],
                        "keys": [
                            "Get",
                            "List",
                            "UnwrapKey"
                        ],
                        "secrets": []
                    },
                    "tenant_id": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
                }
            ],
            "enabled_for_deployment": true,
            "enabled_for_disk_encryption": true,
            "enabled_for_template_deployment": false,
            "sku": {
                "name": "premium"
            },
            "tenant_id": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
            "vault_uri": "https:/keyvault.vault.azure.net"
        },
        "tags": {},
        "type": "Microsoft.KeyVault/vaults"
    }
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.keyvault.models import Vault, VaultCreateOrUpdateParameters, VaultProperties, AccessPolicyEntry, Sku, Permissions
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMKeyVault(AzureRMModuleBase):

    def __init__(self):

        # define user inputs from playbook
        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(choices=['present', 'absent'], default='present', type='str'),
            enabled_for_deployment=dict(default=False, type='bool'),
            enabled_for_disk_encryption=dict(default=False, type='bool'),
            enabled_for_template_deployment=dict(default=False, type='bool'),
            location=dict(type='str'),
            sku=dict(choices=['standard', 'premium'], default='standard', type='str'),
            vault_uri=dict(type='str'),
            tenant_id=dict(type='str'),
            object_id=dict(type='str'),
            application_id=dict(type='str'),
            permissions=dict(choices=[
                'Key, Secret, & Certificate Management',
                'Key & Secret Management',
                'Key Management',
                'Secret Management',
                'Certificate Management',
                'SQL Server Connector',
                'Azure Backup',
                'Azure Data Lake Store'
            ], default='Key, Secret, & Certificate Management', type='str')
        )

        # store the results of the module operation
        self.results = dict(
            changed=False,
            state=dict()
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.enabled_for_deployment = None
        self.enabled_for_disk_encryption = None
        self.enabled_for_template_deployment = None
        self.location = None
        self.sku = None
        self.vault_uri = None
        self.tenant_id = None
        self.object_id = None
        self.application_id = None
        self.permissions = None
        self.tags = None

        super(AzureRMKeyVault, self).__init__(self.module_arg_spec,
                                              supports_check_mode=True,
                                              supports_tags=True)

    def exec_module(self, **kwargs):

        # create a new vault variable in case the 'try' doesn't find a vault
        vault = None

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        self.results['check_mode'] = self.check_mode

        # retrieve resource group to make sure it exists
        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            # Set default location
            self.location = resource_group.location

        changed = False
        results = dict()

        try:
            self.log('Fetching Vault {0}'.format(self.name))
            vault = self.keyvault_client.vaults.get(self.resource_group, self.name)

            # serialize object into a dictionary
            results = vault.as_dict()

            # don't change anything if creating an existing vault (unless outdated tags), but change if deleting it
            if self.state == 'present':
                changed = False

                update_tags, results['tags'] = self.update_tags(results['tags'])
                if update_tags:
                    changed = True

            elif self.state == 'absent':
                changed = True

        except CloudError:
            # the vault does not exist (it's deleted) so create it
            if self.state == 'present':
                changed = True

            else:
                # you can't delete what is not there
                changed = False

        self.results['changed'] = changed
        self.results['state'] = results

        if self.tenant_id is None:
            self.tenant_id = self.credentials['tenant']
        if self.object_id is None:
            self.object_id = self.credentials['client_id']

        # return the results if your only gathering information
        if self.check_mode:
            return self.results

        if changed:
            if self.state == 'present':
                # if you want to create or update a key vault
                if not vault:
                    # create new vault
                    self.log('Creating vault {0}'.format(self.name))
                    use_sku = Sku(self.sku)
                    permission_preset = create_permissions(self)
                    access_policy_lst = [AccessPolicyEntry(self.tenant_id, self.object_id, permission_preset, application_id=self.application_id)]
                    vault_properties = VaultProperties(self.tenant_id,
                                                       use_sku,
                                                       access_policies=access_policy_lst,
                                                       vault_uri=self.vault_uri,
                                                       enabled_for_deployment=self.enabled_for_deployment,
                                                       enabled_for_disk_encryption=self.enabled_for_disk_encryption,
                                                       enabled_for_template_deployment=self.enabled_for_template_deployment)
                    vault = VaultCreateOrUpdateParameters(self.location, vault_properties, tags=self.tags)
                else:
                    # update the vault
                    vault = VaultCreateOrUpdateParameters(self.location, results['properties'], tags=results['tags'])

                self.results['state'] = self.create_or_update_vault(vault)
            elif self.state == 'absent':
                # delete vault
                self.delete_vault()
                # the delete does not actually return anything. if no exception, then we'll assume
                # it worked.
                self.results['state']['status'] = 'Deleted'
        return self.results

    def create_or_update_vault(self, vault):
        try:
            # create or update the new Vault object we created
            new_vault = self.keyvault_client.vaults.create_or_update(self.resource_group, self.name, vault)
        except Exception as exc:
            self.fail("Error creating or updating vault {0} - {1}".format(self.name, str(exc)))
        return new_vault.as_dict()

    def delete_vault(self):
        try:
            # delete the Vault
            self.keyvault_client.vaults.delete(self.resource_group, self.name)
        except Exception as exc:
            self.fail("Error deleting vault {0} - {1}".format(self.name, str(exc)))
        return None


def create_permissions(self):
    # function takes in presets for permissions and returns a permissions object with the necessary/required permissions
    fin_permissions = None
    k_perm = []
    s_perm = []
    c_perm = []
    # if they want the 'Key, Secret, & Certificate Management' permission preset, create and return a new permissions class with all the necessary information
    if self.permissions == 'Key, Secret, & Certificate Management':
        k_perm = ['Get', 'List', 'Update', 'Create', 'Import',
                  'Delete', 'Recover', 'Backup', 'Restore']
        s_perm = ['Get', 'List', 'Set', 'Delete', 'Recover',
                  'Backup', 'Restore']
        c_perm = ['Get', 'List', 'Update', 'Create', 'Import',
                  'Delete', 'ManageContacts', 'ManageIssuers',
                  'GetIssuers', 'ListIssuers', 'SetIssuers', 'DeleteIssuers']
    elif self.permissions == 'Key & Secret Management':
        k_perm = ['Get', 'List', 'Update', 'Create', 'Import',
                  'Delete', 'Recover', 'Backup', 'Restore']
        s_perm = ['Get', 'List', 'Set', 'Delete', 'Recover',
                  'Backup', 'Restore']
    elif self.permissions == 'Secret & Certificate Management':
        s_perm = ['Get', 'List', 'Set', 'Delete', 'Recover',
                  'Backup', 'Restore']
        c_perm = ['Get', 'List', 'Update', 'Create', 'Import',
                  'Delete', 'ManageContacts', 'ManageIssuers',
                  'GetIssuers', 'ListIssuers', 'SetIssuers', 'DeleteIssuers']
    elif self.permissions == 'Key Management':
        k_perm = ['Get', 'List', 'Update', 'Create', 'Import',
                  'Delete', 'Recover', 'Backup', 'Restore']
    elif self.permissions == 'Secret Management':
        s_perm = ['Get', 'List', 'Set', 'Delete', 'Recover',
                  'Backup', 'Restore']
    elif self.permissions == 'Certificate Management':
        c_perm = ['Get', 'List', 'Update', 'Create', 'Import',
                  'Delete', 'ManageContacts', 'ManageIssuers',
                  'GetIssuers', 'ListIssuers', 'SetIssuers', 'DeleteIssuers']
    elif self.permissions == 'SQL Server Connector':
        k_perm = ['Get', 'List', 'UnwrapKey', 'WrapKey']
    elif self.permissions == 'Azure Backup':
        k_perm = ['Get', 'List', 'Backup']
        s_perm = ['Get', 'List', 'Backup']
    elif self.permissions == 'Azure Data Lake Store':
        k_perm = ['Get', 'List', 'UnwrapKey']
    fin_permissions = Permissions(keys=k_perm, secrets=s_perm, certificates=c_perm)
    return fin_permissions


def main():
    AzureRMKeyVault()

if __name__ == '__main__':
    main()
