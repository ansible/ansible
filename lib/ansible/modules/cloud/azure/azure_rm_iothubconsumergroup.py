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
module: azure_rm_iothub
version_added: "2.9"
short_description: Manage Azure IoT hub.
description:
    - Create, delete an Azure IoT hub.
options:
    resource_group:
        description:
            - Name of resource group.
        required: true
    hub:
        description:
            - Name of the IoT hub.
        required: true
    state:
        description:
            - Assert the state of the IoT hub. Use C(present) to create or update an IoT hub and C(absent) to delete an IoT hub.
        default: present
        choices:
            - absent
            - present
    event_hub:
        description:
            - Event hub endpoint name.
        default: events
    name:
        description:
            - Name of the consumer group.
extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Yuwei Zhou (@yuwzho)"

'''

EXAMPLES = '''
- name: Create a simplest IoT hub
  azure_rm_iothub:
    name: Testing
    resource_group: myResourceGroup
- name: Create an IoT hub with route
  azure_rm_iothub:
    resource_group: myResourceGroup
    name: Testing
    routing_endpoints:
        - connection_string: "Endpoint=sb://qux.servicebus.windows.net/;SharedAccessKeyName=quux;SharedAccessKey=****;EntityPath=myQueue"
          name: foo
          resource_type: queue
          resource_group: myResourceGroup1
    routes:
        - name: bar
          source: device_messages
          endpoint_name: foo
          enabled: yes
'''

RETURN = '''
id:
    description:
        - Resource ID of the consumer group.
    sample: "/subscriptions/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/resourceGroups/myResourceGroup
             /providers/Microsoft.Devices/IotHubs/Testing/events/ConsumerGroups/%24Default"
name:
    description:
        - Name of the consumer group.
    sample: Testing
tags:
    description:
        - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.
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
        self.results = cg.as_dict() if cg else dict()
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
