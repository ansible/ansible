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
module: azure_rm_eventhubgeorecovery_facts
version_added: "2.9"
short_description: Get Azure eventhub alias facts.
description:
    - Get facts for a specific eventhub alias or all eventhub alias.

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
        description:
            - Name of the eventhub alias.
    show_sas_policies:
        description:
            - Whether to show the sas policies
            - Note if enable this option, the facts module will raise two more HTTP call for each resources, need more network overhead.
        type: bool

extends_documentation_fragment:
    - azure

author:
    - "Fan Qiu (@MyronFanQiu)"
'''

EXAMPLES = '''
    - name: Get facts for a specific eventhub alias
      azure_rm_eventhubgeorecovery_facts:
        namespace: myeventhubnamespace
        resource_group: myResourceGroup
        name: myaliastesting

    - name: Get facts for all eventhub alias
      azure_rm_eventhubgeorecovery_facts:
        namespace: myeventhubnamespace
        resource_group: myResourceGroup
        show_authorization_rules: true

'''

RETURN = '''
eventhubalias:
    description: List of eventhub alias dicts.
    returned: always
    type: list
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMEventHubGeoRecoveryFacts(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            namespace=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str'
            ),
            show_sas_policies=dict(
                type='bool'
            )
        )

        self.results = dict(
            changed=False,
            eventhubalias=[]
        )

        self.resource_group = None
        self.namespace = None
        self.name = None
        self.show_sas_policies = None

        super(AzureRMEventHubGeoRecoveryFacts, self).__init__(self.module_arg_spec, facts_module=True, supports_tags=False)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec.keys():
            setattr(self, key, kwargs[key])

        response = []

        if self.name:
            response = self.get_alias()
        else:
            response = self.list_by_namespace()

        self.results['eventhubalias'] = [self.to_dict(x) for x in response]

        if self.show_sas_policies:
            self.results['eventhubalias'] = [self.get_sas_policies(x) for x in self.results['eventhubalias']]

        return self.results

    def get_alias(self):
        alias = None
        try:
            self.log("Getting the Alias(Disaster Recovery configuration)")
            alias = self.eventhub_client.disaster_recovery_configs.get(resource_group_name=self.resource_group,
                                                                       namespace_name=self.namespace,
                                                                       alias=self.name)
        except Exception as exc:
            pass
        return [alias]

    def list_by_namespace(self):
        '''Get all eventhub alias in a namespace'''

        try:
            return self.eventhub_client.disaster_recovery_configs.list(resource_group_name=self.resource_group, namespace_name=self.namespace)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Failed to list eventhub alias in namespace {0}: {1}'.format(self.resource_group,
                                                                                   str(exc.inner_exception) or exc.message or str(exc)))

    def get_sas_policies(self, eventhubalias):
        results = eventhubalias
        name = eventhubalias['name']
        rules = self.list_authorization_rules(resource_group_name=self.resource_group, namespace_name=self.namespace, alias_name=name)
        results['sas_keys'] = [self.list_keys(resource_group_name=self.resource_group,
                                              namespace_name=self.namespace,
                                              alias_name=name,
                                              rule_name=x.name) for x in rules]
        return results

    def list_authorization_rules(self, resource_group_name, namespace_name, alias_name):
        try:
            self.log("Getting authorization rules of an eventhub alias")
            return self.eventhub_client.disaster_recovery_configs.list_authorization_rules(resource_group_name=resource_group_name,
                                                                                           namespace_name=namespace_name,
                                                                                           alias=alias_name)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Failed to list authorization rules of alias {0}: {1}'.format(alias_name, str(exc.inner_exception) or exc.message or str(exc)))

    def list_keys(self, resource_group_name, namespace_name, alias_name, rule_name):
        try:
            self.log("Getting sas keys of an authorization rule of an eventhub alias")
            sas_keys = self.eventhub_client.disaster_recovery_configs.list_keys(resource_group_name=resource_group_name,
                                                                                namespace_name=namespace_name,
                                                                                alias=alias_name,
                                                                                authorization_rule_name=rule_name)
            return sas_keys.as_dict()
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Failed to list keys of authorization rules {0}: {1}'.format(rule_name,
                                                                                   str(exc.inner_exception) or exc.message or str(exc)))

    def to_dict(self, alias):
        return alias.as_dict()


def main():
    AzureRMEventHubGeoRecoveryFacts()


if __name__ == '__main__':
    main()
