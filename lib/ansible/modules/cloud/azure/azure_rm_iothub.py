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
    name:
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

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Yuwei Zhou (@yuwzho)"

'''

EXAMPLES = '''
'''

RETURN = '''
id:
    description: Image resource path.
    type: str
    returned: success
    example: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Compute/images/myImage"
'''  # NOQA

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, format_resource_id

try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMIoTHub(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str'),
            sku=dict(type='str', choices=['b1', 'b2', 'b3', 'f1', 's1', 's2', 's3']),
            unit=dict(type='long'),
            event_hub_property = dict(type='dict')
        )

        self.results = dict(
            changed=False,
            id=None
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
        self.sku = None
        self.unit = None
        self.event_hub_property = None
        self.tags = None

        super(AzureRMIoTHub, self).__init__(self.module_arg_spec, supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        changed = False

        if not self.location:
            # Set default location
            resource_group = self.get_resource_group(self.resource_group)
            self.location = resource_group.location
        self.sku = str.capitalize(self.sku) if self.sku else None
        iothub = self.get_hub()
        if self.state == 'present':
            if not iothub:
                changed = True
                self.sku = self.sku or 'F1'
                self.unit = self.unit or 1
                default_event_hub_property = {
                    'events': {'partition_count': 2, 'retention_time_in_days': 1}
                }

                self.event_hub_property = self.event_hub_property or default_event_hub_property
                event_hub_properties = dict()
                for key in self.event_hub_property.keys():
                    item = self.event_hub_property[key]
                    event_hub_properties[key] = self.IoThub_models.EventHubProperties(partition_count=item.get('partition_count') or 2,
                                                                                      retention_time_in_days=item.get('retention_time_in_days') or 1)
                iothub = self.IoThub_models.IotHubDescription(location=self.location,
                                                              sku=self.IoThub_models.IotHubSkuInfo(name=self.sku, capacity=self.unit),
                                                              properties=self.IoThub_models.IotHubProperties(event_hub_endpoints=event_hub_properties),
                                                              tags=self.tags)
                if not self.check_mode:
                    iothub = self.create_or_update_hub(iothub)
            else:
                # compare sku
                original_sku = iothub.sku
                if self.sku and self.sku != original_sku.name:
                    self.log('SKU changed')
                    iothub.sku.name = self.sku
                    changed = True
                if self.unit and self.unit != original_sku.capacity:
                    self.log('Unit count changed')
                    iothub.sku.capacity = self.unit
                    changed = True
                # compare event hub property
                event_hub = iothub.properties.event_hub_endpoints or dict()
                if self.event_hub_property:
                    for key in self.event_hub_property.keys():
                        item = self.event_hub_property[key]
                        original_item = event_hub.get(key)
                        if not original_item:
                            changed = True
                            event_hub[key] = self.IoThub_models.EventHubProperties(partition_count=item.get('partition_count') or 2,
                                                                                   retention_time_in_days=item.get('retention_time_in_days') or 1)
                        elif item.get('partition_count') and original_item.partition_count != item['partition_count']:
                            changed = True
                            original_item.partition_count = item['partition_count']
                        elif item.get('retention_time_in_days') and original_item.retention_time_in_days != item['retention_time_in_days']:
                            changed = True
                            original_item.retention_time_in_days = item['retention_time_in_days']
                # comprea tags
                tag_changed, updated_tags = self.update_tags(iothub.tags)
                iothub.tags = updated_tags
                if changed and not self.check_mode:
                    iothub = self.create_or_update_hub(iothub)
                # only tags changed
                if not changed and tag_changed:
                    changed = True
                    if not self.check_mode:
                        iothub = self.update_tags(updated_tags)
            self.results = self.to_dict(iothub)
        elif iothub:
            changed = True
            if not self.check_mode:
                self.delete_hub()
        self.results['changed'] = changed
        return self.results

    def get_hub(self):
        try:
            return self.IoThub_client.iot_hub_resource.get(self.resource_group, self.name)
        except CloudError as exc:
            self.fail('Error getting IoT Hub {0}: {1}'.format(self.name, str(exc.inner_exception) or exc.message or str(exc)))

    def create_or_update_hub(self, hub):
        try:
            poller = self.IoThub_client.iot_hub_resource.create_or_update(self.resource_group, self.name, hub, if_match=hub.etag)
            return self.get_poller_result(poller)
        except CloudError as exc:
            self.fail('Error creating or updating IoT Hub {0}: {1}'.format(self.name, str(exc.inner_exception) or exc.message or str(exc)))

    def update_tags(self, tags):
        try:
            poller = self.IoThub_client.iot_hub_resource.update(self.resource_group, self.name, tags=tags)
            return self.get_poller_result(poller)
        except CloudError as exc:
            self.fail('Error updating IoT Hub {0}\'s tag: {1}'.format(self.name, str(exc.inner_exception) or exc.message or str(exc)))

    def delete_hub(self):
        try:
            self.IoThub_client.iot_hub_resource.create_or_update(self.resource_group, self.name)
            return True
        except CloudError as exc:
            self.fail('Error deleting IoT Hub {0}: {1}'.format(self.name, str(exc.inner_exception) or exc.message or str(exc)))
            return False

    def to_dict(self, hub):
        return hub.as_dict()


def main():
    AzureRMIoTHub()


if __name__ == '__main__':
    main()
