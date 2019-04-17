#!/usr/bin/python
#
# Copyright (c) 2019 Fan Qiu, <fanqiu@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_eventhubgeorecovery
version_added: "2.9"
short_description: Manage Azure Eventhub Disaster Recovery.
description:
    - Create, update and delete an Azure eventhub alias for disaster recovery.

options:
    resource_group:
        description:
            - Name of a resource group where the eventhub alias exists or will be created.
        required: true
    namespace:
        description:
            - Name of the eventhub namespace.
        required: true
    name:
        decription:
            - Name of the eventhub alias.
    state:
        description:
            - Assert the state of the alias. Use C(present) to create or update an event hub and C(absent) to delete it.
        default: present
        choices:
            - absent
            - present

extends_documentation_fragment:
    - azure

author:
    - "Fan Qiu (@MyronFanQiu)"
'''

EXAMPLES = '''
'''

RETURN = '''
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass

class AzureRMEventHubGeoRecovery(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str',
                required=True
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            ),
            namespace=dict(
                type='str',
                required=True
            ),
            partner_namespace=dict(
                type='str'
            ),
            alternate_name=dict(
                type='str'
            ),
            break_pairing=dict(
                type='bool'
            ),
            fail_over=dict(
                type='bool'
            )
        )

        self.results = dict(
            changed=False,
            state=dict()
        )


        self.resource_group = None
        self.namespace = None
        self.state = None
        self.name = None
        self.partner_namespace = None
        self.alternate_name = None
        self.break_pairing = None
        self.fail_over = None

        super(AzureRMEventHubGeoRecovery, self).__init__(self.module_arg_spec, supports_check_mode=True, supports_tags=False)
    
    def exec_module(self, **kwargs):

        for key in self.module_arg_spec.keys():
            setattr(self, key, kwargs[key])

        changed = False
        results = None

        alias = self.get_alias()

        if self.state == 'present':
            if not alias:
                changed = True

                if not self.check_mode:
                    alias = self.create_or_update_alias()

            else:
                changed = self.check_status(changed=changed, alias=alias)

                if changed and not self.check_mode:
                    alias = self.create_or_update_alias()
            results = self.to_dict(alias) if alias else None
            if self.break_pairing and not self.check_mode:
                changed = True
                self.do_break_pairing()
            if self.fail_over and not self.check_mode:
                changed = True
                self.do_fail_over()
        elif alias:
            changed = True
            if not self.check_mode:
                self.delete_alias()

        self.results['changed'] = changed
        self.results['state'] = results
        return self.results

    def do_break_pairing(self):
        try:
            self.log("Disabling the disaster recovery")
            self.eventhub_client.disaster_recovery_configs.break_pairing(resource_group_name=self.resource_group,
                                                                         namespace_name=self.namespace,
                                                                         alias=self.name)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Fail to disable the disaster recovery {0}: {1}'.format(self.name, str(exc.inner_exception) or exc.message or str(exc)))

    def do_fail_over(self):
        try:
            self.log("Invoking GEO disaster recovery failover")
            self.eventhub_client.disaster_recovery_configs.fail_over(resource_group_name=self.resource_group,
                                                                     namespace_name=self.namespace,
                                                                     alias=self.name)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Fail to invoke the disaster recovery {0} failover: {1}'.format(self.name, str(exc.inner_exception) or exc.message or str(exc)))
    def get_alias(self):
        alias = None
        try:
            self.log("Getting the Alias(Disaster Recovery configuration)")
            alias = self.eventhub_client.disaster_recovery_configs.get(resource_group_name=self.resource_group,
                                                                       namespace_name=self.namespace,
                                                                       alias=self.name)
        except Exception as exc:
            pass
        return alias

    def check_status(self, changed, alias):
        if self.partner_namespace and self.partner_namespace != alias.partner_namespace:
            changed = True

        if self.alternate_name and self.alternate_name != alias.alternate_name:
            changed = True

        return changed

    def create_or_update_alias(self):
        try:
            self.log("Creating or updating the Alias(Disaster Recovery configuration)")
            return self.eventhub_client.disaster_recovery_configs.create_or_update(resource_group_name=self.resource_group,
                                                                                   namespace_name=self.namespace,
                                                                                   alias=self.name,
                                                                                   partner_namespace=self.partner_namespace,
                                                                                   alternate_name=self.alternate_name)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Error creating or updating Alias {0}: {1}'.format(self.name, str(exc.inner_exception) or exc.message or str(exc)))

    def delete_alias(self):
        try:
            self.log("Deleting the Alias(Disaster Recovery configuration)")
            self.eventhub_client.disaster_recovery_configs.delete(resource_group_name=self.resource_group,
                                                                  namespace_name=self.namespace,
                                                                  alias=self.name)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Error deleting Alias {0}: {1}'.format(self.name, str(exc.inner_exception) or exc.message or str(exc)))

    def to_dict(self, alias):
        return alias.as_dict()


def main():
    AzureRMEventHubGeoRecovery()


if __name__ == '__main__':
    main()
