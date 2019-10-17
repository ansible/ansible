#!/usr/bin/python
#
# Copyright (c) 2018 Yuwei Zhou, <yuwzho@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_servicebussaspolicy
version_added: "2.8"
short_description: Manage Azure Service Bus SAS policy
description:
    - Create, update or delete an Azure Service Bus SAS policy.
options:
    resource_group:
        description:
            - Name of resource group.
        required: true
    name:
        description:
            - Name of the SAS policy.
        required: true
    state:
        description:
            - Assert the state of the route. Use C(present) to create or update and C(absent) to delete.
        default: present
        choices:
            - absent
            - present
    namespace:
        description:
            - Manage SAS policy for a namespace without C(queue) or C(topic) set.
            - Manage SAS policy for a queue or topic under this namespace.
        required: true
    queue:
        description:
            - Type of the messaging queue.
            - Cannot set C(topc) when this field set.
    topic:
        description:
            - Name of the messaging topic.
            - Cannot set C(queue) when this field set.
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
        required: True
        choices:
            - manage
            - listen
            - send
            - listen_send

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - Yuwei Zhou (@yuwzho)

'''

EXAMPLES = '''
- name: Create a namespace
  azure_rm_servicebussaspolicy:
      name: deadbeef
      queue: qux
      namespace: bar
      resource_group: myResourceGroup
      rights: send
'''
RETURN = '''
id:
    description:
        - Current state of the SAS policy.
    returned: Successed
    type: str
    sample: "/subscriptions/xxx...xxx/resourceGroups/myResourceGroup/providers/Microsoft.ServiceBus/
            namespaces/nsb57dc95979/topics/topicb57dc95979/authorizationRules/testpolicy"
keys:
    description:
        - Key dict of the SAS policy.
    returned: Successed
    type: complex
    contains:
        key_name:
            description:
                - Name of the SAS policy.
            returned: Successed
            type: str
            sample: testpolicy
        primary_connection_string:
            description:
                - Primary connection string.
            returned: Successed
            type: str
            sample: "Endpoint=sb://nsb57dc95979.servicebus.windows.net/;SharedAccessKeyName=testpolicy;
                    SharedAccessKey=r+HD3es/9aOOq0XjQtkx5KXROH1MIHDs0WxCgR23gMc=;EntityPath=topicb57dc95979"
        primary_key:
            description:
                - Primary key.
            returned: Successed
            type: str
            sample: "r+HD3es/9aOOq0XjQtkx5KXROH1MIHDs0WxCgR23gMc="
        secondary_key:
            description:
                - Secondary key.
            returned: Successed
            type: str
            sample: "/EcGztJBv72VD0Dy14bdsxi30rl+pSZMtKcs4KV3JWU="
        secondary_connection_string:
            description:
                - Secondary connection string.
            returned: Successed
            type: str
            sample: "Endpoint=sb://nsb57dc95979.servicebus.windows.net/;SharedAccessKeyName=testpolicy;
                    SharedAccessKey=/EcGztJBv72VD0Dy14bdsxi30rl+pSZMtKcs4KV3JWU=;EntityPath=topicb57dc95979"
name:
    description:
        - Name of the SAS policy.
    returned: Successed
    type: str
    sample: testpolicy
rights:
    description:
        - Priviledge of the SAS policy.
    returned: Successed
    type: str
    sample: manage
type:
    description:
        - Type of the SAS policy.
    returned: Successed
    type: str
    sample: "Microsoft.ServiceBus/Namespaces/Topics/AuthorizationRules"
'''

try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.common.dict_transformations import _snake_to_camel, _camel_to_snake
from ansible.module_utils._text import to_native
from datetime import datetime, timedelta


class AzureRMServiceBusSASPolicy(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            namespace=dict(type='str', required=True),
            queue=dict(type='str'),
            topic=dict(type='str'),
            regenerate_primary_key=dict(type='bool', default=False),
            regenerate_secondary_key=dict(type='bool', default=False),
            rights=dict(type='str', choices=['manage', 'listen', 'send', 'listen_send'])
        )

        mutually_exclusive = [
            ['queue', 'topic']
        ]

        required_if = [('state', 'present', ['rights'])]

        self.resource_group = None
        self.name = None
        self.state = None
        self.namespace = None
        self.queue = None
        self.topic = None
        self.regenerate_primary_key = None
        self.regenerate_secondary_key = None
        self.rights = None

        self.results = dict(
            changed=False,
            id=None
        )

        super(AzureRMServiceBusSASPolicy, self).__init__(self.module_arg_spec,
                                                         mutually_exclusive=mutually_exclusive,
                                                         required_if=required_if,
                                                         supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()):
            setattr(self, key, kwargs[key])

        changed = False

        policy = self.get_auth_rule()
        if self.state == 'present':
            if not policy:  # Create a new one
                changed = True
                if not self.check_mode:
                    policy = self.create_sas_policy()
            else:
                changed = changed | self.regenerate_primary_key | self.regenerate_secondary_key
                if self.regenerate_primary_key and not self.check_mode:
                    self.regenerate_sas_key('primary')
                if self.regenerate_secondary_key and not self.check_mode:
                    self.regenerate_sas_key('secondary')
            self.results = self.policy_to_dict(policy)
            self.results['keys'] = self.get_sas_key()
        elif policy:
            changed = True
            if not self.check_mode:
                self.delete_sas_policy()

        self.results['changed'] = changed
        return self.results

    def _get_client(self):
        if self.queue:
            return self.servicebus_client.queues
        elif self.topic:
            return self.servicebus_client.topics
        return self.servicebus_client.namespaces

    # SAS policy
    def create_sas_policy(self):
        if self.rights == 'listen_send':
            rights = ['Listen', 'Send']
        elif self.rights == 'manage':
            rights = ['Listen', 'Send', 'Manage']
        else:
            rights = [str.capitalize(self.rights)]
        try:
            client = self._get_client()
            if self.queue or self.topic:
                rule = client.create_or_update_authorization_rule(self.resource_group, self.namespace, self.queue or self.topic, self.name, rights)
            else:
                rule = client.create_or_update_authorization_rule(self.resource_group, self.namespace, self.name, rights)
            return rule
        except Exception as exc:
            self.fail('Error when creating or updating SAS policy {0} - {1}'.format(self.name, exc.message or str(exc)))
        return None

    def get_auth_rule(self):
        rule = None
        try:
            client = self._get_client()
            if self.queue or self.topic:
                rule = client.get_authorization_rule(self.resource_group, self.namespace, self.queue or self.topic, self.name)
            else:
                rule = client.get_authorization_rule(self.resource_group, self.namespace, self.name)
        except Exception:
            pass
        return rule

    def delete_sas_policy(self):
        try:
            client = self._get_client()
            if self.queue or self.topic:
                client.delete_authorization_rule(self.resource_group, self.namespace, self.queue or self.topic, self.name)
            else:
                client.delete_authorization_rule(self.resource_group, self.namespace, self.name)
            return True
        except Exception as exc:
            self.fail('Error when deleting SAS policy {0} - {1}'.format(self.name, exc.message or str(exc)))

    def regenerate_sas_key(self, key_type):
        try:
            client = self._get_client()
            key = str.capitalize(key_type) + 'Key'
            if self.queue or self.topic:
                client.regenerate_keys(self.resource_group, self.namespace, self.queue or self.topic, self.name, key)
            else:
                client.regenerate_keys(self.resource_group, self.namespace, self.name, key)
        except Exception as exc:
            self.fail('Error when generating SAS policy {0}\'s key - {1}'.format(self.name, exc.message or str(exc)))
        return None

    def get_sas_key(self):
        try:
            client = self._get_client()
            if self.queue or self.topic:
                return client.list_keys(self.resource_group, self.namespace, self.queue or self.topic, self.name).as_dict()
            else:
                return client.list_keys(self.resource_group, self.namespace, self.name).as_dict()
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
    AzureRMServiceBusSASPolicy()


if __name__ == '__main__':
    main()
