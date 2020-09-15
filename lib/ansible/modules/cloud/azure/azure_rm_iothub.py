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
short_description: Manage Azure IoT hub
description:
    - Create, delete an Azure IoT hub.
options:
    resource_group:
        description:
            - Name of resource group.
        type: str
        required: true
    name:
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
    location:
        description:
            - Location of the IoT hub.
        type: str
    sku:
        description:
            - Pricing tier for Azure IoT Hub.
            - Note that only one free IoT hub instance is allowed in each subscription. Exception will be thrown if free instances exceed one.
            - Default is C(s1) when creation.
        type: str
        choices:
            - b1
            - b2
            - b3
            - f1
            - s1
            - s2
            - s3
    unit:
        description:
            - Units in your IoT Hub.
            - Default is C(1).
        type: int
    event_endpoint:
        description:
            - The Event Hub-compatible endpoint property.
        type: dict
        suboptions:
            partition_count:
                description:
                    - The number of partitions for receiving device-to-cloud messages in the Event Hub-compatible endpoint.
                    - "See U(https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-messaging#device-to-cloud-messages)."
                    - Default is C(2).
                type: int
            retention_time_in_days:
                description:
                    - The retention time for device-to-cloud messages in days.
                    - "See U(https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-messaging#device-to-cloud-messages)."
                    - Default is C(1).
                type: int
    enable_file_upload_notifications:
        description:
            - File upload notifications are enabled if set to C(True).
        type: bool
    ip_filters:
        description:
            - Configure rules for rejecting or accepting traffic from specific IPv4 addresses.
        type: list
        suboptions:
            name:
                description:
                    - Name of the filter.
                type: str
                required: yes
            ip_mask:
                description:
                    - A string that contains the IP address range in CIDR notation for the rule.
                type: str
                required: yes
            action:
                description:
                    - The desired action for requests captured by this rule.
                type: str
                required: yes
                choices:
                    - accept
                    - reject
    routing_endpoints:
        description:
            - Custom endpoints.
        type: list
        suboptions:
            name:
                description:
                    - Name of the custom endpoint.
                type: str
                required: yes
            resource_group:
                description:
                    - Resource group of the endpoint.
                    - Default is the same as I(resource_group).
                type: str
            subscription:
                description:
                    - Subscription id of the endpoint.
                    - Default is the same as I(subscription).
                type: str
            resource_type:
                description:
                    - Resource type of the custom endpoint.
                type: str
                choices:
                    - eventhub
                    - queue
                    - storage
                    - topic
                required: yes
            connection_string:
                description:
                    - Connection string of the custom endpoint.
                    - The connection string should have send privilege.
                type: str
                required: yes
            container:
                description:
                    - Container name of the custom endpoint when I(resource_type=storage).
                type: str
            encoding:
                description:
                    - Encoding of the message when I(resource_type=storage).
                type: str
    routes:
        description:
            - Route device-to-cloud messages to service-facing endpoints.
        type: list
        suboptions:
            name:
                description:
                    - Name of the route.
                type: str
                required: yes
            source:
                description:
                    - The origin of the data stream to be acted upon.
                type: str
                choices:
                    - device_messages
                    - twin_change_events
                    - device_lifecycle_events
                    - device_job_lifecycle_events
                required: yes
            enabled:
                description:
                    - Whether to enable the route.
                type: bool
                required: yes
            endpoint_name:
                description:
                    - The name of the endpoint in I(routing_endpoints) where IoT Hub sends messages that match the query.
                type: str
                required: yes
            condition:
                description:
                    - "The query expression for the routing query that is run against the message application properties,
                       system properties, message body, device twin tags, and device twin properties to determine if it is a match for the endpoint."
                    - "For more information about constructing a query,
                       see U(https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-devguide-routing-query-syntax)"
                type: str
extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - Yuwei Zhou (@yuwzho)

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
        - Resource ID of the IoT hub.
    sample: "/subscriptions/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/resourceGroups/myResourceGroup/providers/Microsoft.Devices/IotHubs/Testing"
    returned: success
    type: str
name:
    description:
        - Name of the IoT hub.
    sample: Testing
    returned: success
    type: str
resource_group:
    description:
        - Resource group of the IoT hub.
    sample: myResourceGroup.
    returned: success
    type: str
location:
    description:
        - Location of the IoT hub.
    sample: eastus
    returned: success
    type: str
unit:
    description:
        - Units in the IoT Hub.
    sample: 1
    returned: success
    type: int
sku:
    description:
        - Pricing tier for Azure IoT Hub.
    sample: f1
    returned: success
    type: str
cloud_to_device:
    description:
        - Cloud to device message properties.
    contains:
        max_delivery_count:
            description:
                - The number of times the IoT hub attempts to deliver a message on the feedback queue.
                - "See U(https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-messaging#cloud-to-device-messages)."
            type: int
            returned: success
            sample: 10
        ttl_as_iso8601:
            description:
                - The period of time for which a message is available to consume before it is expired by the IoT hub.
                - "See U(https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-messaging#cloud-to-device-messages)."
            type: str
            returned: success
            sample: "1:00:00"
    returned: success
    type: complex
enable_file_upload_notifications:
    description:
        - Whether file upload notifications are enabled.
    sample: True
    returned: success
    type: bool
event_endpoints:
    description:
        - Built-in endpoint where to deliver device message.
    contains:
        endpoint:
            description:
                - The Event Hub-compatible endpoint.
            type: str
            returned: success
            sample: "sb://iothub-ns-testing-1478811-9bbc4a15f0.servicebus.windows.net/"
        partition_count:
            description:
                - The number of partitions for receiving device-to-cloud messages in the Event Hub-compatible endpoint.
                - "See U(https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-messaging#device-to-cloud-messages)."
            type: int
            returned: success
            sample: 2
        retention_time_in_days:
            description:
                - The retention time for device-to-cloud messages in days.
                - "See U(https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-messaging#device-to-cloud-messages)."
            type: int
            returned: success
            sample: 1
        partition_ids:
            description:
                - List of the partition id for the event endpoint.
            type: list
            returned: success
            sample: ["0", "1"]
    returned: success
    type: complex
host_name:
    description:
        - Host of the IoT hub.
    sample: "testing.azure-devices.net"
    returned: success
    type: str
ip_filters:
    description:
        - Configure rules for rejecting or accepting traffic from specific IPv4 addresses.
    contains:
        name:
            description:
                - Name of the filter.
            type: str
            returned: success
            sample: filter
        ip_mask:
            description:
                - A string that contains the IP address range in CIDR notation for the rule.
            type: str
            returned: success
            sample: 40.54.7.3
        action:
            description:
                - The desired action for requests captured by this rule.
            type: str
            returned: success
            sample: Reject
    returned: success
    type: complex
routing_endpoints:
    description:
        - Custom endpoints.
    contains:
        event_hubs:
            description:
                - List of custom endpoints of event hubs.
            type: complex
            returned: success
            contains:
                name:
                    description:
                        - Name of the custom endpoint.
                    type: str
                    returned: success
                    sample: foo
                resource_group:
                    description:
                        - Resource group of the endpoint.
                    type: str
                    returned: success
                    sample: bar
                subscription:
                    description:
                        - Subscription id of the endpoint.
                    type: str
                    returned: success
                    sample: "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
                connection_string:
                    description:
                        - Connection string of the custom endpoint.
                    type: str
                    returned: success
                    sample: "Endpoint=sb://quux.servicebus.windows.net:5671/;SharedAccessKeyName=qux;SharedAccessKey=****;EntityPath=foo"
        service_bus_queues:
            description:
                - List of custom endpoints of service bus queue.
            type: complex
            returned: always
            contains:
                name:
                    description:
                        - Name of the custom endpoint.
                    type: str
                    returned: success
                    sample: foo
                resource_group:
                    description:
                        - Resource group of the endpoint.
                    type: str
                    returned: success
                    sample: bar
                subscription:
                    description:
                        - Subscription ID of the endpoint.
                    type: str
                    returned: success
                    sample: "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
                connection_string:
                    description:
                        - Connection string of the custom endpoint.
                    type: str
                    returned: success
                    sample: "Endpoint=sb://quux.servicebus.windows.net:5671/;SharedAccessKeyName=qux;SharedAccessKey=****;EntityPath=foo"
        service_bus_topics:
            description:
                - List of custom endpoints of service bus topic.
            type: complex
            returned: success
            contains:
                name:
                    description:
                        - Name of the custom endpoint.
                    type: str
                    returned: success
                    sample: foo
                resource_group:
                    description:
                        - Resource group of the endpoint.
                    type: str
                    returned: success
                    sample: bar
                subscription:
                    description:
                        - Subscription ID of the endpoint.
                    type: str
                    returned: success
                    sample: "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
                connection_string:
                    description:
                        - Connection string of the custom endpoint.
                    type: str
                    returned: success
                    sample: "Endpoint=sb://quux.servicebus.windows.net:5671/;SharedAccessKeyName=qux;SharedAccessKey=****;EntityPath=foo"
        storage_containers:
            description:
                - List of custom endpoints of storage
            type: complex
            returned: success
            contains:
                name:
                    description:
                        - Name of the custom endpoint.
                    type: str
                    returned: success
                    sample: foo
                resource_group:
                    description:
                        - Resource group of the endpoint.
                    type: str
                    returned: success
                    sample: bar
                subscription:
                    description:
                        - Subscription ID of the endpoint.
                    type: str
                    returned: success
                    sample: "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
                connection_string:
                    description:
                        - Connection string of the custom endpoint.
                    type: str
                    returned: success
                    sample: "Endpoint=sb://quux.servicebus.windows.net:5671/;SharedAccessKeyName=qux;SharedAccessKey=****;EntityPath=foo"
    returned: success
    type: complex
routes:
    description:
        - Route device-to-cloud messages to service-facing endpoints.
    type: complex
    returned: success
    contains:
        name:
            description:
                - Name of the route.
            type: str
            returned: success
            sample: route1
        source:
            description:
                - The origin of the data stream to be acted upon.
            type: str
            returned: success
            sample: device_messages
        enabled:
            description:
                - Whether to enable the route.
            type: str
            returned: success
            sample: true
        endpoint_name:
            description:
                - The name of the endpoint in C(routing_endpoints) where IoT Hub sends messages that match the query.
            type: str
            returned: success
            sample: foo
        condition:
            description:
                - "The query expression for the routing query that is run against the message application properties,
                    system properties, message body, device twin tags, and device twin properties to determine if it is a match for the endpoint."
                - "For more information about constructing a query,
                    see I(https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-devguide-routing-query-syntax)"
            type: bool
            returned: success
            sample: "true"
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
    'eventhub': {'model': 'RoutingEventHubProperties', 'attribute': 'event_hubs'},
    'queue': {'model': 'RoutingServiceBusQueueEndpointProperties', 'attribute': 'service_bus_queues'},
    'topic': {'model': 'RoutingServiceBusTopicEndpointProperties', 'attribute': 'service_bus_topics'},
    'storage': {'model': 'RoutingStorageContainerProperties', 'attribute': 'storage_containers'}
}


routes_spec = dict(
    name=dict(type='str', required=True),
    source=dict(type='str', required=True, choices=['device_messages', 'twin_change_events', 'device_lifecycle_events', 'device_job_lifecycle_events']),
    enabled=dict(type='bool', required=True),
    endpoint_name=dict(type='str', required=True),
    condition=dict(type='str')
)


event_endpoint_spec = dict(
    partition_count=dict(type='int'),
    retention_time_in_days=dict(type='int')
)


class AzureRMIoTHub(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str'),
            sku=dict(type='str', choices=['b1', 'b2', 'b3', 'f1', 's1', 's2', 's3']),
            unit=dict(type='int'),
            event_endpoint=dict(type='dict', options=event_endpoint_spec),
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
        self.event_endpoint = None
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
                self.sku = self.sku or 'S1'
                self.unit = self.unit or 1
                self.event_endpoint = self.event_endpoint or {}
                self.event_endpoint['partition_count'] = self.event_endpoint.get('partition_count') or 2
                self.event_endpoint['retention_time_in_days'] = self.event_endpoint.get('retention_time_in_days') or 1
                event_hub_properties = dict()
                event_hub_properties['events'] = self.IoThub_models.EventHubProperties(**self.event_endpoint)
                iothub_property = self.IoThub_models.IotHubProperties(event_hub_endpoints=event_hub_properties)
                if self.enable_file_upload_notifications:
                    iothub_property.enable_file_upload_notifications = self.enable_file_upload_notifications
                if self.ip_filters:
                    iothub_property.ip_filter_rules = self.construct_ip_filters()
                routing_endpoints = None
                routes = None
                if self.routing_endpoints:
                    routing_endpoints = self.construct_routing_endpoint(self.routing_endpoints)
                if self.routes:
                    routes = [self.construct_route(x) for x in self.routes]
                if routes or routing_endpoints:
                    routing_property = self.IoThub_models.RoutingProperties(endpoints=routing_endpoints,
                                                                            routes=routes)
                    iothub_property.routing = routing_property
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
                if self.event_endpoint:
                    item = self.event_endpoint
                    original_item = event_hub.get('events')
                    if not original_item:
                        changed = True
                        event_hub['events'] = self.IoThub_models.EventHubProperties(partition_count=item.get('partition_count') or 2,
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
                # compare routes
                original_routes = iothub.properties.routing.routes
                routes_changed = False
                if self.routes:
                    if len(self.routes) != len(original_routes or []):
                        routes_changed = True
                    else:
                        for item in self.routes:
                            if not self.lookup_route(item, original_routes):
                                routes_changed = True
                                break
                    if routes_changed:
                        changed = True
                        iothub.properties.routing.routes = [self.construct_route(x) for x in self.routes]
                # compare IP filter
                ip_filter_changed = False
                original_ip_filter = iothub.properties.ip_filter_rules
                if self.ip_filters:
                    if len(self.ip_filters) != len(original_ip_filter or []):
                        ip_filter_changed = True
                    else:
                        for item in self.ip_filters:
                            if not self.lookup_ip_filter(item, original_ip_filter):
                                ip_filter_changed = True
                                break
                    if ip_filter_changed:
                        changed = True
                        iothub.properties.ip_filter_rules = self.construct_ip_filters()

                # compare tags
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

    def lookup_ip_filter(self, target, ip_filters):
        if not ip_filters or len(ip_filters) == 0:
            return False
        for item in ip_filters:
            if item.filter_name == target['name']:
                if item.ip_mask != target['ip_mask']:
                    return False
                if item.action.lower() != target['action']:
                    return False
                return True
        return False

    def lookup_route(self, target, routes):
        if not routes or len(routes) == 0:
            return False
        for item in routes:
            if item.name == target['name']:
                if target['source'] != _camel_to_snake(item.source):
                    return False
                if target['enabled'] != item.is_enabled:
                    return False
                if target['endpoint_name'] != item.endpoint_names[0]:
                    return False
                if target.get('condition') and target['condition'] != item.condition:
                    return False
                return True
        return False

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

    def construct_ip_filters(self):
        return [self.IoThub_models.IpFilterRule(filter_name=x['name'],
                                                action=self.IoThub_models.IpFilterActionType[x['action']],
                                                ip_mask=x['ip_mask']) for x in self.ip_filters]

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
            self.IoThub_client.iot_hub_resource.delete(self.resource_group, self.name)
            return True
        except Exception as exc:
            self.fail('Error deleting IoT Hub {0}: {1}'.format(self.name, exc.message or str(exc)))
            return False

    def route_to_dict(self, route):
        return dict(
            name=route.name,
            source=_camel_to_snake(route.source),
            endpoint_name=route.endpoint_names[0],
            enabled=route.is_enabled,
            condition=route.condition
        )

    def instance_dict_to_dict(self, instance_dict):
        result = dict()
        if not instance_dict:
            return result
        for key in instance_dict.keys():
            result[key] = instance_dict[key].as_dict()
        return result

    def to_dict(self, hub):
        result = dict()
        properties = hub.properties
        result['id'] = hub.id
        result['name'] = hub.name
        result['resource_group'] = self.resource_group
        result['location'] = hub.location
        result['tags'] = hub.tags
        result['unit'] = hub.sku.capacity
        result['sku'] = hub.sku.name.lower()
        result['cloud_to_device'] = dict(
            max_delivery_count=properties.cloud_to_device.feedback.max_delivery_count,
            ttl_as_iso8601=str(properties.cloud_to_device.feedback.ttl_as_iso8601)
        ) if properties.cloud_to_device else dict()
        result['enable_file_upload_notifications'] = properties.enable_file_upload_notifications
        result['event_endpoint'] = properties.event_hub_endpoints.get('events').as_dict() if properties.event_hub_endpoints.get('events') else None
        result['host_name'] = properties.host_name
        result['ip_filters'] = [x.as_dict() for x in properties.ip_filter_rules]
        if properties.routing:
            result['routing_endpoints'] = properties.routing.endpoints.as_dict()
            result['routes'] = [self.route_to_dict(x) for x in properties.routing.routes]
            result['fallback_route'] = self.route_to_dict(properties.routing.fallback_route)
        result['status'] = properties.state
        result['storage_endpoints'] = self.instance_dict_to_dict(properties.storage_endpoints)
        return result


def main():
    AzureRMIoTHub()


if __name__ == '__main__':
    main()
