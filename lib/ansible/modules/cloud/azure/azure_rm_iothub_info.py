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
module: azure_rm_iothub_info

version_added: "2.9"

short_description: Get IoT Hub facts

description:
    - Get facts for a specific IoT Hub or all IoT Hubs.

options:
    name:
        description:
            - Limit results to a specific resource group.
        type: str
    resource_group:
        description:
            - The resource group to search for the desired IoT Hub.
        type: str
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.
        type: list
    show_stats:
        description:
            - Show the statistics for IoT Hub.
            - Note this will have network overhead for each IoT Hub.
        type: bool
    show_quota_metrics:
        description:
            - Get the quota metrics for an IoT hub.
            - Note this will have network overhead for each IoT Hub.
        type: bool
    show_endpoint_health:
        description:
            - Get the health for routing endpoints.
            - Note this will have network overhead for each IoT Hub.
        type: bool
    test_route_message:
        description:
            - Test routes message. It will be used to test all routes.
        type: str
    list_consumer_groups:
        description:
            - List the consumer group of the built-in event hub.
        type: bool
    list_keys:
        description:
            - List the keys of IoT Hub.
            - Note this will have network overhead for each IoT Hub.
        type: bool
extends_documentation_fragment:
    - azure

author:
    - Yuwei Zhou (@yuwzho)
'''

EXAMPLES = '''
    - name: Get facts for one IoT Hub
      azure_rm_iothub_info:
        name: Testing
        resource_group: myResourceGroup

    - name: Get facts for all IoT Hubs
      azure_rm_iothub_info:

    - name: Get facts for all IoT Hubs in a specific resource group
      azure_rm_iothub_info:
        resource_group: myResourceGroup

    - name: Get facts by tags
      azure_rm_iothub_info:
        tags:
          - testing
'''

RETURN = '''
azure_iothubs:
    description:
        - List of IoT Hub dicts.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource ID of the IoT hub.
            type: str
            returned: always
            sample: "/subscriptions/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/resourceGroups/myResourceGroup/providers/Microsoft.Devices/IotHubs/Testing"
        name:
            description:
                - Name of the IoT hub.
            type: str
            returned: always
            sample: Testing
        resource_group:
            description:
                - Resource group of the IoT hub.
            type: str
            returned: always
            sample: myResourceGroup.
        location:
            description:
                - Location of the IoT hub.
            type: str
            returned: always
            sample: eastus
        unit:
            description:
                - Units in the IoT Hub.
            type: int
            returned: always
            sample: 1
        sku:
            description:
                - Pricing tier for Azure IoT Hub.
            type: str
            returned: always
            sample: f1
        cloud_to_device:
            description:
                - Cloud to device message properties.
            type: complex
            returned: always
            contains:
                max_delivery_count:
                    description:
                        - The number of times the IoT hub attempts to deliver a message on the feedback queue.
                        - "See U(https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-messaging#cloud-to-device-messages)."
                    type: int
                    returned: always
                    sample: 10
                ttl_as_iso8601:
                    description:
                        - The period of time for which a message is available to consume before it is expired by the IoT hub.
                        - "See U(https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-messaging#cloud-to-device-messages)."
                    type: str
                    returned: always
                    sample: "1:00:00"
        enable_file_upload_notifications:
            description:
                - Whether file upload notifications are enabled.
            type: str
            returned: always
            sample: True
        event_endpoints:
            description:
                - Built-in endpoint where to deliver device message.
            type: complex
            returned: always
            contains:
                endpoint:
                    description:
                        - The Event Hub-compatible endpoint.
                    type: str
                    returned: always
                    sample: "sb://iothub-ns-testing-1478811-9bbc4a15f0.servicebus.windows.net/"
                partition_count:
                    description:
                        - The number of partitions for receiving device-to-cloud messages in the Event Hub-compatible endpoint.
                        - "See U(https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-messaging#device-to-cloud-messages)."
                    type: int
                    returned: always
                    sample: 2
                retention_time_in_days:
                    description:
                        - The retention time for device-to-cloud messages in days.
                        - "See U(https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-messaging#device-to-cloud-messages)."
                    type: int
                    returned: always
                    sample: 1
                partition_ids:
                    description:
                        - List of the partition id for the event endpoint.
                    type: list
                    returned: always
                    sample: ["0", "1"]
        host_name:
            description:
                - Host of the IoT hub.
            type: str
            returned: always
            sample: "testing.azure-devices.net"
        ip_filters:
            description:
                - Configure rules for rejecting or accepting traffic from specific IPv4 addresses.
            type: complex
            returned: always
            contains:
                name:
                    description:
                        - Name of the filter.
                    type: str
                    returned: always
                    sample: filter
                ip_mask:
                    description:
                        - A string that contains the IP address range in CIDR notation for the rule.
                    type: str
                    returned: always
                    sample: 40.54.7.3
                action:
                    description:
                        - The desired action for requests captured by this rule.
                    type: str
                    returned: always
                    sample: Reject
        routing_endpoints:
            description:
                - Custom endpoints.
            type: complex
            returned: always
            contains:
                event_hubs:
                    description:
                        - List of custom endpoints of event hubs.
                    type: complex
                    returned: always
                    contains:
                        name:
                            description:
                                - Name of the custom endpoint.
                            type: str
                            returned: always
                            sample: foo
                        resource_group:
                            description:
                                - Resource group of the endpoint.
                            type: str
                            returned: always
                            sample: bar
                        subscription:
                            description:
                                - Subscription ID of the endpoint.
                            type: str
                            returned: always
                            sample: "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
                        connection_string:
                            description:
                                - Connection string of the custom endpoint.
                            type: str
                            returned: always
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
                            returned: always
                            sample: foo
                        resource_group:
                            description:
                                - Resource group of the endpoint.
                            type: str
                            returned: always
                            sample: bar
                        subscription:
                            description:
                                - Subscription ID of the endpoint.
                            type: str
                            returned: always
                            sample: "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
                        connection_string:
                            description:
                                - Connection string of the custom endpoint.
                            type: str
                            returned: always
                            sample: "Endpoint=sb://quux.servicebus.windows.net:5671/;SharedAccessKeyName=qux;SharedAccessKey=****;EntityPath=foo"
                service_bus_topics:
                    description:
                        - List of custom endpoints of service bus topic.
                    type: complex
                    returned: always
                    contains:
                        name:
                            description:
                                - Name of the custom endpoint.
                            type: str
                            returned: always
                            sample: foo
                        resource_group:
                            description:
                                - Resource group of the endpoint.
                            type: str
                            returned: always
                            sample: bar
                        subscription:
                            description:
                                - Subscription ID of the endpoint.
                            type: str
                            returned: always
                            sample: "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
                        connection_string:
                            description:
                                - Connection string of the custom endpoint.
                            type: str
                            returned: always
                            sample: "Endpoint=sb://quux.servicebus.windows.net:5671/;SharedAccessKeyName=qux;SharedAccessKey=****;EntityPath=foo"
                storage_containers:
                    description:
                        - List of custom endpoints of storage.
                    type: complex
                    returned: always
                    contains:
                        name:
                            description:
                                - Name of the custom endpoint.
                            type: str
                            returned: always
                            sample: foo
                        resource_group:
                            description:
                                - Resource group of the endpoint.
                            type: str
                            returned: always
                            sample: bar
                        subscription:
                            description:
                                - Subscription ID of the endpoint.
                            type: str
                            returned: always
                            sample: "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
                        connection_string:
                            description:
                                - Connection string of the custom endpoint.
                            type: str
                            returned: always
                            sample: "Endpoint=sb://quux.servicebus.windows.net:5671/;SharedAccessKeyName=qux;SharedAccessKey=****;EntityPath=foo"
        routes:
            description:
                - Route device-to-cloud messages to service-facing endpoints.
            type: complex
            returned: always
            contains:
                name:
                    description:
                        - Name of the route.
                    type: str
                    returned: always
                    sample: route1
                source:
                    description:
                        - The origin of the data stream to be acted upon.
                    type: str
                    returned: always
                    sample: device_messages
                enabled:
                    description:
                        - Whether to enable the route.
                    type: bool
                    returned: always
                    sample: true
                endpoint_name:
                    description:
                        - The name of the endpoint in I(routing_endpoints) where IoT Hub sends messages that match the query.
                    type: str
                    returned: always
                    sample: foo
                condition:
                    description:
                        - "The query expression for the routing query that is run against the message application properties,
                           system properties, message body, device twin tags, and device twin properties to determine if it is a match for the endpoint."
                        - "For more information about constructing a query,
                           see U(https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-devguide-routing-query-syntax)"
                    type: bool
                    returned: always
                    sample: "true"
        tags:
            description:
                - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.
            type: dict
            returned: always
            sample: { 'key1': 'value1' }
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.common.dict_transformations import _camel_to_snake

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.tools import parse_resource_id
    from azure.common import AzureHttpError
except Exception:
    # handled in azure_rm_common
    pass


class AzureRMIoTHubFacts(AzureRMModuleBase):
    """Utility class to get IoT Hub facts"""

    def __init__(self):

        self.module_args = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list'),
            show_stats=dict(type='bool'),
            show_quota_metrics=dict(type='bool'),
            show_endpoint_health=dict(type='bool'),
            list_keys=dict(type='bool'),
            test_route_message=dict(type='str'),
            list_consumer_groups=dict(type='bool')
        )

        self.results = dict(
            changed=False,
            azure_iothubs=[]
        )

        self.name = None
        self.resource_group = None
        self.tags = None
        self.show_stats = None
        self.show_quota_metrics = None
        self.show_endpoint_health = None
        self.list_keys = None
        self.test_route_message = None
        self.list_consumer_groups = None

        super(AzureRMIoTHubFacts, self).__init__(
            derived_arg_spec=self.module_args,
            supports_tags=False,
            facts_module=True
        )

    def exec_module(self, **kwargs):

        for key in self.module_args:
            setattr(self, key, kwargs[key])

        response = []
        if self.name:
            response = self.get_item()
        elif self.resource_group:
            response = self.list_by_resource_group()
        else:
            response = self.list_all()
        self.results['iothubs'] = [self.to_dict(x) for x in response if self.has_tags(x.tags, self.tags)]
        return self.results

    def get_item(self):
        """Get a single IoT Hub"""

        self.log('Get properties for {0}'.format(self.name))

        item = None

        try:
            item = self.IoThub_client.iot_hub_resource.get(self.resource_group, self.name)
            return [item]
        except Exception as exc:
            self.fail('Error when getting IoT Hub {0}: {1}'.format(self.name, exc.message or str(exc)))

    def list_all(self):
        """Get all IoT Hubs"""

        self.log('List all IoT Hubs')

        try:
            return self.IoThub_client.iot_hub_resource.list_by_subscription()
        except Exception as exc:
            self.fail('Failed to list all IoT Hubs - {0}'.format(str(exc)))

    def list_by_resource_group(self):
        try:
            return self.IoThub_client.iot_hub_resource.list(self.resource_group)
        except Exception as exc:
            self.fail('Failed to list IoT Hub in resource group {0} - {1}'.format(self.resource_group, exc.message or str(exc)))

    def show_hub_stats(self, resource_group, name):
        try:
            return self.IoThub_client.iot_hub_resource.get_stats(resource_group, name).as_dict()
        except Exception as exc:
            self.fail('Failed to getting statistics for IoT Hub {0}/{1}: {2}'.format(resource_group, name, str(exc)))

    def show_hub_quota_metrics(self, resource_group, name):
        result = []
        try:
            resp = self.IoThub_client.iot_hub_resource.get_quota_metrics(resource_group, name)
            while True:
                result.append(resp.next().as_dict())
        except StopIteration:
            pass
        except Exception as exc:
            self.fail('Failed to getting quota metrics for IoT Hub {0}/{1}: {2}'.format(resource_group, name, str(exc)))
        return result

    def show_hub_endpoint_health(self, resource_group, name):
        result = []
        try:
            resp = self.IoThub_client.iot_hub_resource.get_endpoint_health(resource_group, name)
            while True:
                result.append(resp.next().as_dict())
        except StopIteration:
            pass
        except Exception as exc:
            self.fail('Failed to getting health for IoT Hub {0}/{1} routing endpoint: {2}'.format(resource_group, name, str(exc)))
        return result

    def test_all_routes(self, resource_group, name):
        try:
            return self.IoThub_client.iot_hub_resource.test_all_routes(self.test_route_message, resource_group, name).routes.as_dict()
        except Exception as exc:
            self.fail('Failed to getting statistics for IoT Hub {0}/{1}: {2}'.format(resource_group, name, str(exc)))

    def list_hub_keys(self, resource_group, name):
        result = []
        try:
            resp = self.IoThub_client.iot_hub_resource.list_keys(resource_group, name)
            while True:
                result.append(resp.next().as_dict())
        except StopIteration:
            pass
        except Exception as exc:
            self.fail('Failed to getting health for IoT Hub {0}/{1} routing endpoint: {2}'.format(resource_group, name, str(exc)))
        return result

    def list_event_hub_consumer_groups(self, resource_group, name, event_hub_endpoint='events'):
        result = []
        try:
            resp = self.IoThub_client.iot_hub_resource.list_event_hub_consumer_groups(resource_group, name, event_hub_endpoint)
            while True:
                cg = resp.next()
                result.append(dict(
                    id=cg.id,
                    name=cg.name
                ))
        except StopIteration:
            pass
        except Exception as exc:
            self.fail('Failed to listing consumer group for IoT Hub {0}/{1} routing endpoint: {2}'.format(resource_group, name, str(exc)))
        return result

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
        for key in instance_dict.keys():
            result[key] = instance_dict[key].as_dict()
        return result

    def to_dict(self, hub):
        result = dict()
        properties = hub.properties
        result['id'] = hub.id
        result['name'] = hub.name
        result['resource_group'] = parse_resource_id(hub.id).get('resource_group')
        result['location'] = hub.location
        result['tags'] = hub.tags
        result['unit'] = hub.sku.capacity
        result['sku'] = hub.sku.name.lower()
        result['cloud_to_device'] = dict(
            max_delivery_count=properties.cloud_to_device.feedback.max_delivery_count,
            ttl_as_iso8601=str(properties.cloud_to_device.feedback.ttl_as_iso8601)
        )
        result['enable_file_upload_notifications'] = properties.enable_file_upload_notifications
        result['event_hub_endpoints'] = self.instance_dict_to_dict(properties.event_hub_endpoints)
        result['host_name'] = properties.host_name
        result['ip_filters'] = [x.as_dict() for x in properties.ip_filter_rules]
        result['routing_endpoints'] = properties.routing.endpoints.as_dict()
        result['routes'] = [self.route_to_dict(x) for x in properties.routing.routes]
        result['fallback_route'] = self.route_to_dict(properties.routing.fallback_route)
        result['status'] = properties.state
        result['storage_endpoints'] = self.instance_dict_to_dict(properties.storage_endpoints)

        # network overhead part
        if self.show_stats:
            result['statistics'] = self.show_hub_stats(result['resource_group'], hub.name)
        if self.show_quota_metrics:
            result['quota_metrics'] = self.show_hub_quota_metrics(result['resource_group'], hub.name)
        if self.show_endpoint_health:
            result['endpoint_health'] = self.show_hub_endpoint_health(result['resource_group'], hub.name)
        if self.list_keys:
            result['keys'] = self.list_hub_keys(result['resource_group'], hub.name)
        if self.test_route_message:
            result['test_route_result'] = self.test_all_routes(result['resource_group'], hub.name)
        if self.list_consumer_groups:
            result['consumer_groups'] = self.list_event_hub_consumer_groups(result['resource_group'], hub.name)
        return result


def main():
    """Main module execution code path"""

    AzureRMIoTHubFacts()


if __name__ == '__main__':
    main()
