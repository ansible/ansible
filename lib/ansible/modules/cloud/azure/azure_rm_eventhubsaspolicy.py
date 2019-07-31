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
module: azure_rm_eventhubsaspolicy
version_added: "2.9"
short_description: Manage Azure Eventhub Namespace SAS policy
description:
    - Create, update and delete an Azure Eventhub Namespace SAS policy.

options:
    resource_group:
        description:
            - Name of resource group.
        type: str
        required: true
    name:
        description:
            - Name of the sas policy.
        type: str
        required: true
    namespace:
        description:
            - Name of the eventhub namespace.
        type: str
        required: true
    state:
        description:
            - State of the sas policy. Use C(present) to create or update and C(absent) to delete.
        type: str
        default: present
        choices:
            - absent
            - present
    eventhub:
        description:
            - Type of the eventhub.
        type: str
    regenerate_primary_key:
        description:
            - Regenerate the SAS policy primary key.
        type: bool
        default: False
    regenerate_secondary_key:
        description:
            - Regenerate the SAS policy secondary key.
        type: bool
        default: False
    rights:
        description:
            - Claim rights of the SAS policy.
        type: str
        required: True
        choices:
            - manage
            - listen
            - send
            - listen_send

extends_documentation_fragment:
    - azure

author:
    - Fan Qiu (@MyronFanQiu)

'''

EXAMPLES = '''
- name: Create a sas policy
  azure_rm_eventhubsaspolicy:
      name: deadbeef
      namespace: testingnamespace
      resource_group: myResourceGroup
      rights: send
'''

RETURN = '''
id:
    description:
        - Current state of the SAS policy.
    returned: Successed
    type: str
keys:
    description:
        - Key dict of the SAS policy.
    returned: Successed
    type: dict
    contains:
        key_name:
            description:
                - Name of the SAS policy.
            returned: Successed
            type: str
        primary_connection_string:
            description:
                - Primary connection string.
            returned: Successed
            type: str
        primary_key:
            description:
                - Primary key.
            returned: Successed
            type: str
        secondary_key:
            description:
                Secondary key.
            returned: Successed
            type: str
        secondary_connection_string:
            description:
                - Secondary connection string.
            returned: Successed
            type: str
name:
    description:
        - Name of the SAS policy.
    returned: Successed
    type: str
rights:
    description:
        - Priviledge of the SAS policy.
    returned: Successed
    type: str
type:
    description:
        - Type of the SAS policy.
    returned: Successed
    type: str
'''  # NOQA

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMEventHubSASPolicy(AzureRMModuleBase):

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
            eventhub=dict(
                type='str'
            ),
            regenerate_primary_key=dict(
                type='bool',
                default=False
            ),
            regenerate_secondary_key=dict(
                type='bool',
                default=False
            ),
            rights=dict(
                type='str',
                choices=['manage', 'listen', 'send', 'listen_send']
            )
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.namespace = None
        self.eventhub = None
        self.regenerate_primary_key = None
        self.regenerate_secondary_key = None
        self.rights = None

        self.results = dict(
            changed=False,
            state=dict()
        )

        super(AzureRMEventHubSASPolicy, self).__init__(self.module_arg_spec, supports_check_mode=True, supports_tags=False)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()):
            setattr(self, key, kwargs[key])

        changed = False

        policy = self.get_auth_rule()
        if self.state == 'present':
            if not policy:  # Create a new one
                changed = True
                if not self.check_mode:
                    policy = self.create_or_update_sas_policy()
            else:
                if self.rights != self.policy_to_dict(policy)['rights'] and not self.check_mode:
                    changed = True
                    policy = self.create_or_update_sas_policy()
                changed = changed | self.regenerate_primary_key | self.regenerate_secondary_key
                if self.regenerate_primary_key and not self.check_mode:
                    self.regenerate_sas_key('primary')
                if self.regenerate_secondary_key and not self.check_mode:
                    self.regenerate_sas_key('secondary')
            policy = self.policy_to_dict(policy) if policy else None
            self.results['keys'] = self.get_sas_key().as_dict()
        elif policy:
            changed = True
            if not self.check_mode:
                self.delete_sas_policy()
            policy = True

        self.results['changed'] = changed
        self.results['state'] = policy
        return self.results

    def _get_client(self):
        if self.eventhub:
            return self.eventhub_client.event_hubs
        return self.eventhub_client.namespaces

    def create_or_update_sas_policy(self):
        if self.rights == 'listen_send':
            rights = ['Listen', 'Send']
        elif self.rights == 'manage':
            rights = ['Listen', 'Send', 'Manage']
        else:
            rights = [str.capitalize(self.rights)]
        try:
            client = self._get_client()
            self.log('Create or update a sas policy')
            if self.eventhub:
                rule = client.create_or_update_authorization_rule(resource_group_name=self.resource_group,
                                                                  namespace_name=self.namespace,
                                                                  event_hub_name=self.eventhub,
                                                                  authorization_rule_name=self.name,
                                                                  rights=rights)
            else:
                rule = client.create_or_update_authorization_rule(resource_group_name=self.resource_group,
                                                                  namespace_name=self.namespace,
                                                                  authorization_rule_name=self.name,
                                                                  rights=rights)
            return rule
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Error when creating or updating SAS policy {0} - {1}'.format(self.name, str(exc.inner_exception) or str(exc.message) or str(exc)))
        return None

    def get_auth_rule(self):
        rule = None
        try:
            client = self._get_client()
            self.log('Gather facts for a sas policy')
            if self.eventhub:
                rule = client.get_authorization_rule(resource_group_name=self.resource_group,
                                                     namespace_name=self.namespace,
                                                     event_hub_name=self.eventhub,
                                                     authorization_rule_name=self.name)
            else:
                rule = client.get_authorization_rule(resource_group_name=self.resource_group,
                                                     namespace_name=self.namespace,
                                                     authorization_rule_name=self.name)
        except Exception:
            pass
        return rule

    def delete_sas_policy(self):
        try:
            client = self._get_client()
            self.log('Delete a sas policy')
            if self.eventhub:
                client.delete_authorization_rule(resource_group_name=self.resource_group,
                                                 namespace_name=self.namespace,
                                                 event_hub_name=self.eventhub,
                                                 authorization_rule_name=self.name)
            else:
                client.delete_authorization_rule(resource_group_name=self.resource_group,
                                                 namespace_name=self.namespace,
                                                 authorization_rule_name=self.name)
            return True
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Error when deleting SAS policy {0} - {1}'.format(self.name, str(exc.inner_exception) or str(exc.message) or str(exc)))

    def regenerate_sas_key(self, key_type):
        try:
            client = self._get_client()
            key = str.capitalize(key_type) + 'Key'
            self.log('Regenerate the {0} for a sas policy'.format(key))
            if self.eventhub:
                client.regenerate_keys(resource_group_name=self.resource_group,
                                       namespace_name=self.namespace,
                                       event_hub_name=self.eventhub,
                                       authorization_rule_name=self.name,
                                       key_type=key)
            else:
                client.regenerate_keys(resource_group_name=self.resource_group,
                                       namespace_name=self.namespace,
                                       authorization_rule_name=self.name,
                                       key_type=key)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Error when generating SAS policy {0}\'s key - {1}'.format(self.name, str(exc.inner_exception) or str(exc.message) or str(exc)))
        return None

    def get_sas_key(self):
        try:
            client = self._get_client()
            self.log('Gather sas keys for an authorization rule')
            if self.eventhub:
                return client.list_keys(resource_group_name=self.resource_group,
                                        namespace_name=self.namespace,
                                        event_hub_name=self.eventhub,
                                        authorization_rule_name=self.name)
            else:
                return client.list_keys(resource_group_name=self.resource_group,
                                        namespace_name=self.namespace,
                                        authorization_rule_name=self.name)
        except Exception:
            pass
        return None

    def policy_to_dict(self, rule):
        result = rule.as_dict()
        rights = result['rights']
        if 'Manage' in rights:
            result['rights'] = 'manage'
        elif 'Listen' in rights and 'Send' in rights:
            result['rights'] = 'listen_send'
        else:
            result['rights'] = rights[0].lower()
        return result


def main():
    AzureRMEventHubSASPolicy()


if __name__ == '__main__':
    main()
