#!/usr/bin/python
#
# Copyright (c) 2019 Yuwei Zhou, <yuwzho@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_iothubconsumergroup
version_added: "2.9"
short_description: Manage Azure IoT hub
description:
    - Create, delete an Azure IoT hub.
options:
    resource_group:
        description:
            - Name of resource group.
        type: str
        required: true
    hub:
        description:
            - Name of the IoT hub.
        type: str
        required: true
    state:
        description:
            - State of the IoT hub. Use C(present) to create or update an IoT hub and C(absent) to delete an IoT hub.
        type: str
        default: present
        choices:
            - absent
            - present
    event_hub:
        description:
            - Event hub endpoint name.
        type: str
        default: events
    name:
        description:
            - Name of the consumer group.
        type: str
extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - Yuwei Zhou (@yuwzho)

'''

EXAMPLES = '''
- name: Create an IoT hub consumer group
  azure_rm_iothubconsumergroup:
    name: test
    resource_group: myResourceGroup
    hub: Testing
'''

RETURN = '''
id:
    description:
        - Resource ID of the consumer group.
    returned: success
    type: str
    sample: "/subscriptions/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/resourceGroups/myResourceGroup
             /providers/Microsoft.Devices/IotHubs/Testing/events/ConsumerGroups/%24Default"
name:
    description:
        - Name of the consumer group.
    sample: Testing
    returned: success
    type: str
'''  # NOQA

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, format_resource_id
from ansible.module_utils.common.dict_transformations import _snake_to_camel, _camel_to_snake
import re

try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMIoTHubConsumerGroup(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            hub=dict(type='str', required=True),
            event_hub=dict(type='str', default='events')
        )

        self.results = dict(
            changed=False,
            id=None
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.hub = None
        self.event_hub = None

        super(AzureRMIoTHubConsumerGroup, self).__init__(self.module_arg_spec, supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec.keys():
            setattr(self, key, kwargs[key])

        changed = False
        cg = self.get_cg()
        if not cg and self.state == 'present':
            changed = True
            if not self.check_mode:
                cg = self.create_cg()
        elif cg and self.state == 'absent':
            changed = True
            cg = None
            if not self.check_mode:
                self.delete_cg()
        self.results = dict(
            id=cg.id,
            name=cg.name
        ) if cg else dict()
        self.results['changed'] = changed
        return self.results

    def get_cg(self):
        try:
            return self.IoThub_client.iot_hub_resource.get_event_hub_consumer_group(self.resource_group, self.hub, self.event_hub, self.name)
        except Exception:
            pass
            return None

    def create_cg(self):
        try:
            return self.IoThub_client.iot_hub_resource.create_event_hub_consumer_group(self.resource_group, self.hub, self.event_hub, self.name)
        except Exception as exc:
            self.fail('Error when creating the consumer group {0} for IoT Hub {1} event hub {2}: {3}'.format(self.name, self.hub, self.event_hub, str(exc)))

    def delete_cg(self):
        try:
            return self.IoThub_client.iot_hub_resource.delete_event_hub_consumer_group(self.resource_group, self.hub, self.event_hub, self.name)
        except Exception as exc:
            self.fail('Error when deleting the consumer group {0} for IoT Hub {1} event hub {2}: {3}'.format(self.name, self.hub, self.event_hub, str(exc)))


def main():
    AzureRMIoTHubConsumerGroup()


if __name__ == '__main__':
    main()
