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
from ansible.module_utils.common.dict_transformations import _snake_to_camel
import re

try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


ip_filter_spec = dict(
    name=dict(type='str', required=True),
    ip_mask=dict(type='str', required=True),
    action=dict(type='str', required=True, choices=['accept', 'reject'])
)


routing_endpoints_spec = dict(
    connection_string=dict(type='str', required=True),
    name=dict(type='str', required=True),
    resource_group=dict(type='str'),
    subscription=dict(type='str'),
    resource_type=dict(type='str', required=True, choices=['eventhub', 'queue', 'storage', 'topic']),
    container=dict(type='str'),
    encoding=dict(type='str')
)


routing_endpoints_resource_type_mapping = {
    'eventhub': { 'model': 'RoutingEventHubProperties', 'attribute': 'event_hubs'},
    'queue': { 'model': 'RoutingServiceBusQueueEndpointProperties', 'attribute': 'service_bus_queues'},
    'topic': { 'model': 'RoutingServiceBusTopicEndpointProperties', 'attribute': 'service_bus_topics'},
    'storage': { 'model': 'RoutingStorageContainerProperties', 'attribute': 'storage_containers'}
}


routes_spec = dict(
    name=dict(type='str', required=True),
    source=dict(type='str', required=True,  choices=['device_messages', 'twin_change_events', 'device_lifecycle_events', 'device_job_lifecycle_events']),
    enabled=dict(type='bool', required=True),
    endpoint_name=dict(type='str', required=True),
    condition=dict(type='str')
)


class AzureRMIoTHub(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str'),
            sku=dict(type='str', choices=['b1', 'b2', 'b3', 'f1', 's1', 's2', 's3']),
            unit=dict(type='long'),
            event_hub_endpoints=dict(type='dict'),
            enable_file_upload_notifications=dict(type='bool'),
            ip_filters=dict(type='list', elements='dict', options=ip_filter_spec),
            routing_endpoints=dict(type='list', elements='dict', options=routing_endpoints_spec),
            routes=dict(type='list', elements='dict', options=routes_spec)
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
        self.event_hub_endpoints = None
        self.tags = None
        self.enable_file_upload_notifications = None
        self.ip_filters = None
        self.routing_endpoints = None
        self.routes = None

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
                self.sku = self.sku or 'B1'
                self.unit = self.unit or 1
                default_event_hub_endpoints = {
                    'events': {'partition_count': 2, 'retention_time_in_days': 1}
                }

                self.event_hub_endpoints = self.event_hub_endpoints or default_event_hub_endpoints
                event_hub_properties = dict()
                for key in self.event_hub_endpoints.keys():
                    item = self.event_hub_endpoints[key]
                    event_hub_properties[key] = self.IoThub_models.EventHubProperties(partition_count=item.get('partition_count') or 2,
                                                                                      retention_time_in_days=item.get('retention_time_in_days') or 1)
                iothub_property = self.IoThub_models.IotHubProperties(event_hub_endpoints=event_hub_properties)
                if self.enable_file_upload_notifications:
                    iothub_property.enable_file_upload_notifications = self.enable_file_upload_notifications
                if self.ip_filters:
                    ip_filters = [self.IoThub_models.IpFilterRule(filter_name=x.name,
                                                                  action=self.IoThub_models.IpFilterActionType(name=str.capitalize(x.action)),
                                                                  ip_mask=x.ip_mask) for x in self.ip_filters]
                    iothub_property.ip_filter_rules = ip_filters
                routing_endpoints = None
                routes = None
                if self.routing_endpoints:
                    routing_endpoints = self.construct_routing_endpoint(self.routing_endpoints)
                if self.routes:
                    routes = [self.construct_route(x) for x in self.routes]
                if routes or routing_endpoints:
                    routing_property = self.IoThub_models.RoutingProperties(endpoints=routing_endpoints,
                                                                            routes=routes)
                    iothub_property.routing =  routing_property
                iothub = self.IoThub_models.IotHubDescription(location=self.location,
                                                              sku=self.IoThub_models.IotHubSkuInfo(name=self.sku, capacity=self.unit),
                                                              properties=iothub_property,
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
                if self.event_hub_endpoints:
                    for key in self.event_hub_endpoints.keys():
                        item = self.event_hub_endpoints[key]
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
                # compare endpoint
                original_endpoints = iothub.properties.routing.endpoints
                endpoint_changed = False
                if self.routing_endpoints:
                    # find the total length
                    total_length = 0
                    for item in routing_endpoints_resource_type_mapping.values():
                        attribute = item['attribute']
                        array = getattr(original_endpoints, attribute)
                        total_length += len(array or [])
                    if total_length != len(self.routing_endpoints):
                        endpoint_changed = True
                    else:  # If already changed, no need to compare any more
                        for item in self.routing_endpoints:
                            if not self.lookup_endpoint(item, original_endpoints):
                                endpoint_changed = True
                                break
                    if endpoint_changed:
                        iothub.properties.routing.endpoints = self.construct_routing_endpoint(self.routing_endpoints)
                        changed = True
                # comprea tags
                tag_changed, updated_tags = self.update_tags(iothub.tags)
                iothub.tags = updated_tags
                if changed and not self.check_mode:
                    iothub = self.create_or_update_hub(iothub)
                # only tags changed
                if not changed and tag_changed:
                    changed = True
                    if not self.check_mode:
                        iothub = self.update_instance_tags(updated_tags)
            self.results = self.to_dict(iothub)
        elif iothub:
            changed = True
            if not self.check_mode:
                self.delete_hub()
        self.results['changed'] = changed
        return self.results

    def lookup_endpoint(self, target, routing_endpoints):
        resource_type = target['resource_type']
        attribute = routing_endpoints_resource_type_mapping[resource_type]['attribute']
        endpoints = getattr(routing_endpoints, attribute)
        if not endpoints or len(endpoints) == 0:
            return False
        for item in endpoints:
            if item.name == target['name']:
                if target.get('resource_group') and target['resource_group'] != (item.resource_group or self.resource_group):
                    return False
                if target.get('subscription_id') and target['subscription_id'] != (item.subscription_id or self.subscription_id):
                    return False
                connection_string_regex = item.connection_string.replace('****', '.*')
                connection_string_regex = re.sub(r':\d+/;', '/;', connection_string_regex)
                if not re.search(connection_string_regex, target['connection_string']):
                    return False
                if resource_type == 'storage':
                    if target.get('container') and item.container_name != target['container']:
                        return False
                    if target.get('encoding') and item.encoding != target['encoding']:
                        return False
                return True
        return False
                
    def construct_routing_endpoint(self, routing_endpoints):
        if not routing_endpoints or len(routing_endpoints) == 0:
            return None
        result = self.IoThub_models.RoutingEndpoints()
        for endpoint in routing_endpoints:
            resource_type_property = routing_endpoints_resource_type_mapping.get(endpoint['resource_type'])
            resource_type = getattr(self.IoThub_models, resource_type_property['model'])
            array = getattr(result, resource_type_property['attribute']) or []
            array.append(resource_type(**endpoint))
            setattr(result, resource_type_property['attribute'], array)
        return result

    def construct_route(self, route):
        if not route:
            return None
        return self.IoThub_models.RouteProperties(name=route['name'],
                                                  source=_snake_to_camel(snake=route['source'], capitalize_first=True),
                                                  is_enabled=route['enabled'],
                                                  endpoint_names=[route['endpoint_name']],
                                                  condition=route.get('condition'))

    def get_hub(self):
        try:
            return self.IoThub_client.iot_hub_resource.get(self.resource_group, self.name)
        except Exception:
            pass
            return None

    def create_or_update_hub(self, hub):
        try:
            poller = self.IoThub_client.iot_hub_resource.create_or_update(self.resource_group, self.name, hub, if_match=hub.etag)
            return self.get_poller_result(poller)
        except Exception as exc:
            self.fail('Error creating or updating IoT Hub {0}: {1}'.format(self.name, exc.message or str(exc)))

    def update_instance_tags(self, tags):
        try:
            poller = self.IoThub_client.iot_hub_resource.update(self.resource_group, self.name, tags=tags)
            return self.get_poller_result(poller)
        except Exception as exc:
            self.fail('Error updating IoT Hub {0}\'s tag: {1}'.format(self.name, exc.message or str(exc)))

    def delete_hub(self):
        try:
            self.IoThub_client.iot_hub_resource.create_or_update(self.resource_group, self.name)
            return True
        except Exception as exc:
            self.fail('Error deleting IoT Hub {0}: {1}'.format(self.name, exc.message or str(exc)))
            return False

    def to_dict(self, hub):
        return hub.as_dict()


def main():
    AzureRMIoTHub()


if __name__ == '__main__':
    main()
