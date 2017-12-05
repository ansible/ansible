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
    from azure.mgmt.keyvault.models import (
        Vault, VaultCreateOrUpdateParameters, VaultProperties, AccessPolicyEntry,
        Sku, Permissions, KeyPermissions, SecretPermissions, CertificatePermissions, SkuName
    )
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

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        self.results['check_mode'] = self.check_mode

        # check if tenant or object id is passed via args if not pull from auth creds
        if self.tenant_id is None:
            if self.credentials['tenant'] is None:
                self.fail("Please supply a tenant id")
            else:
                self.tenant_id = self.credentials['tenant']
        if self.object_id is None:
            if self.credentials['client_id'] is None:
                self.fail("Please supply a client id")
            else:
                self.object_id = self.credentials['client_id']

        try:
            resource_group = self.get_resource_group(self.resource_group)
        except CloudError:
            self.fail('Unable to retrieve resource group')

        self.location = self.location or resource_group.location

        try:
            vault = self.keyvault_client.vaults.get(self.resource_group, self.name)
            exists = True
        except CloudError as exc:
            exists = False

        if self.state == 'absent':
            if exists:
                if self.check_mode:
                    self.results['changed'] = True
                    return self.results
                try:
                    self.delete_vault()
                    self.results['state']['status'] = 'Deleted'
                    self.results['changed'] = True
                except CloudError as exc:
                    self.fail('Faulure while deleting keyvault: {}'.format(exc))
            else:
                self.results['changed'] = False
        else:
            try:
                use_sku = Sku(self.sku)
                permission_preset = self.create_permissions(self.permissions)
                access_policy_lst = [AccessPolicyEntry(self.tenant_id,
                                                       self.object_id,
                                                       permission_preset,
                                                       application_id=self.application_id)]
                vault_properties = VaultProperties(self.tenant_id,
                                                   use_sku,
                                                   access_policies=access_policy_lst,
                                                   vault_uri=self.vault_uri,
                                                   enabled_for_deployment=self.enabled_for_deployment,
                                                   enabled_for_disk_encryption=self.enabled_for_disk_encryption,
                                                   enabled_for_template_deployment=self.enabled_for_template_deployment)
                vault = VaultCreateOrUpdateParameters(self.location,
                                                      vault_properties, tags=self.tags)
                self.results['changed'] = True

                if self.check_mode:
                    self.results['state'] = vault.as_dict()
                    return self.results
                else:
                    self.results['state'] = self.create_or_update_vault(vault)
            except CloudError as exc:
                self.fail('Failure while creating or updating keyvault: {}'.format(exc))

        return self.results

    def create_or_update_vault(self, vault):
        try:
            # create or update the new Vault object we created
            new_vault = self.keyvault_client.vaults.create_or_update(
                self.resource_group, self.name, vault
            )
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

    def create_permissions(self, permissions):
        # function takes in presets for permissions and returns a permissions object with the necessary/required permissions
        k_perm = []
        s_perm = []
        c_perm = []
        if permissions == 'Key, Secret, & Certificate Management':
            k_perm = [KeyPermissions.get, KeyPermissions.list, KeyPermissions.update, KeyPermissions.import_enum,
                      KeyPermissions.create, KeyPermissions.delete, KeyPermissions.recover,
                      KeyPermissions.backup, KeyPermissions.restore]
            s_perm = [SecretPermissions.get, SecretPermissions.list, SecretPermissions.set, SecretPermissions.delete,
                      SecretPermissions.recover, SecretPermissions.backup, SecretPermissions.restore]
            c_perm = [CertificatePermissions.get, CertificatePermissions.list, CertificatePermissions.update,
                      CertificatePermissions.create, CertificatePermissions.import_enum, CertificatePermissions.delete,
                      CertificatePermissions.managecontacts, CertificatePermissions.manageissuers, CertificatePermissions.getissuers,
                      CertificatePermissions.listissuers, CertificatePermissions.setissuers, CertificatePermissions.deleteissuers]
        elif permissions == 'Key & Secret Management':
            k_perm = [KeyPermissions.get, KeyPermissions.list, KeyPermissions.update, KeyPermissions.import_enum,
                      KeyPermissions.create, KeyPermissions.delete, KeyPermissions.recover,
                      KeyPermissions.backup, KeyPermissions.restore]
            s_perm = [SecretPermissions.get, SecretPermissions.list, SecretPermissions.set, SecretPermissions.delete,
                      SecretPermissions.recover, SecretPermissions.backup, SecretPermissions.restore]
        elif permissions == 'Secret & Certificate Management':
            s_perm = [SecretPermissions.get, SecretPermissions.list, SecretPermissions.set, SecretPermissions.delete,
                      SecretPermissions.recover, SecretPermissions.backup, SecretPermissions.restore]
            c_perm = [CertificatePermissions.get, CertificatePermissions.list, CertificatePermissions.update,
                      CertificatePermissions.create, CertificatePermissions.import_enum, CertificatePermissions.delete,
                      CertificatePermissions.managecontacts, CertificatePermissions.manageissuers, CertificatePermissions.getissuers,
                      CertificatePermissions.listissuers, CertificatePermissions.setissuers, CertificatePermissions.deleteissuers]
        elif permissions == 'Key Management':
            k_perm = [KeyPermissions.get, KeyPermissions.list, KeyPermissions.update, KeyPermissions.import_enum,
                      KeyPermissions.create, KeyPermissions.delete, KeyPermissions.recover,
                      KeyPermissions.backup, KeyPermissions.restore]
        elif permissions == 'Secret Management':
            s_perm = [SecretPermissions.get, SecretPermissions.list, SecretPermissions.set, SecretPermissions.delete,
                      SecretPermissions.recover, SecretPermissions.backup, SecretPermissions.restore]
        elif permissions == 'Certificate Management':
            c_perm = [CertificatePermissions.get, CertificatePermissions.list, CertificatePermissions.update,
                      CertificatePermissions.create, CertificatePermissions.import_enum, CertificatePermissions.delete,
                      CertificatePermissions.managecontacts, CertificatePermissions.manageissuers, CertificatePermissions.getissuers,
                      CertificatePermissions.listissuers, CertificatePermissions.setissuers, CertificatePermissions.deleteissuers]
        elif permissions == 'SQL Server Connector':
            k_perm = [KeyPermissions.get, KeyPermissions.list, KeyPermissions.backup, KeyPermissions.unwrapkey,
                      KeyPermissions.wrapkey]
        elif permissions == 'Azure Backup':
            k_perm = [KeyPermissions.get, KeyPermissions.list, KeyPermissions.backup]
            s_perm = [SecretPermissions.get, SecretPermissions.list, SecretPermissions.backup]
        elif permissions == 'Azure Data Lake Store':
            k_perm = [KeyPermissions.get, KeyPermissions.list, KeyPermissions.backup, KeyPermissions.unwrapkey]
        return Permissions(keys=k_perm, secrets=s_perm, certificates=c_perm)


def main():
    AzureRMKeyVault()

if __name__ == '__main__':
    main()
