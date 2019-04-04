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
module: azure_rm_eventhubnamespace
version_added: "2.8"
short_description: Manage Azure Eventhub Namespace.
description:
    - Create, update and delete an Azure Eventhub Namespace.

options:
    resource_group:
        description:
            - Name of a resource group where the eventhub namespace exists or will be created.
        required: true
    name:
        description:
            - Name of the eventhub namespace.
        required: true
    state:
        description:
            - Assert the state of the eventhub namespace. Use C(present) to create or update an eventhub namespace and C(absent) to delete it.
        default: present
        choices:
            - absent
            - present
    location:
        description:
            - Location of the eventhub namespace.
    sku:
        description:
            - Pricing tier for Azure eventhub namespace.
            - Note that basic eventhub namespace cannot support kafka_enabled.
            - Default is standard when creation.
        choices:
            - basic
            - standard
    is_auto_inflate_enabled:
        description:
            - Value that indicates whether AutoInflate is enabled for eventhub namespace.
            - Default is false when creation.
        choices:
            - true
            - false
    maximum_throughput_units:
        description:
            - Upper limit of throughput units when AutoInflate is enabled, value should be within 0 to 20 throughput units. ( '0' if AutoInflateEnabled = false)
            - Only can be set when the C(is_auto_inflate_enabled) == true
    kafka_enabled:
        description:
            - Value that indicates whether Kafka is enabled for eventhub namespace.
            - Default is false when creation.
            - Cannot be updated after the creation
        choices:
            - true
            - false

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Fan Qiu (@MyronFanQiu)"

'''

EXAMPLES = '''
    - name: Create event hub namespace with default
      azure_rm_eventhubnamespace:
        name: Testing
        location: eastus
        resource_group: myResourceGroup

    - name: Create event hub namespace when C(kafka_enabled) is set to true
      azure_rm_eventhubnamespace:
        name: Testing02
        location: eastus
        resource_group: myResourceGroup
        kafka_enabled: true

    - name: Update event hub namespace sku basic
      azure_rm_eventhubnamespace:
        name: Testing
        location: eastus
        resource_group: myResourceGroup
        sku: basic

    - name: Update event hub namespace sku standard
      azure_rm_eventhubnamespace:
        name: Testing
        location: eastus
        resource_group: myResourceGroup
        sku: standard

    - name: Update event hub namespace maximum_throughput_units to 8
      azure_rm_eventhubnamespace:
        name: Testing
        location: eastus
        resource_group: myResourceGroup
        is_auto_inflate_enabled: true
        maximum_throughput_units: 8

    - name: Update event hub namespace is_auto_inflate_enabled to false
      azure_rm_eventhubnamespace:
        name: Testing
        location: eastus
        resource_group: myResourceGroup
        is_auto_inflate_enabled: false

    - name: Delete event hub namespace
      azure_rm_eventhubnamespace:
        name: Testing
        location: eastus
        resource_group: myResourceGroup
        state: absent
'''

RETURN = '''
id:
    description:
        - Resource ID of the eventhub namespace.
    returned: always
    type: str
    sample: "/subscriptions/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/resourceGroups/myResourceGroup/providers/Microsoft.EventHub/namespaces/Testing"
name:
    description:
        - Name of the eventhub namespace.
    returned: always
    type: str
    sample: Testing
location:
    description:
        - Location of the eventhub namespace.
    returned: always
    type: str
    sample: eastus
sku:
    description:
        - Pricing tier for Azure eventhub namespace.
    returned: always
    type: str
    sample: standard
is_auto_inflate_enabled:
    description:
        - Value that indicates whether AutoInflate is enabled for eventhub namespace.
    returned: always
    type: bool
    sample: false
kafka_enabled:
    description:
        - Value that indicates whether Kafka is enabled for eventhub namespace.
    returned: always
    type: bool
    sample: false
maximum_throughput_units:
    description:
        - Upper limit of throughput units when AutoInflate is enabled, value should be within 0 to 20 throughput units. ( '0' if AutoInflateEnabled = false)
    returned: always
    type: int
    sample: standard
service_bus_endpoint:
    description:
        - Endpoint you can use to perform Service Bus operations.
    returned: always
    type: str
    sample: https://Testing.servicebus.windows.net:443
metric_id:
    description:
        - Identifier for Azure Insights metrics.
    returned: always
    type: str
    sample: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX:Testing
tags:
    description:
        - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.
    returned: always
    type: dict
'''  # NOQA

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMEventHubNamespace(AzureRMModuleBase):
    """Configuration class for an Azure RM Event hub resource"""

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
            location=dict(
                type='str'
            ),
            sku=dict(
                type='str',
                choices=['basic', 'standard']
            ),
            is_auto_inflate_enabled=dict(
                type='bool',
                choices=[True, False]
            ),
            maximum_throughput_units=dict(
                type='int'
            ),
            kafka_enabled=dict(
                type='bool',
                choices=[True, False]
            )
        )

        self.results = dict(
            changed=False,
            state=dict()
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
        self.sku = None
        self.is_auto_inflate_enabled = None
        self.maximum_throughput_units = None
        self.kafka_enabled = None
        self.tags = None

        super(AzureRMEventHubNamespace, self).__init__(self.module_arg_spec, supports_check_mode=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        changed = False
        warning = False

        if not self.location:
            # Set default location
            resource_group = self.get_resource_group(self.resource_group)
            self.location = resource_group.location
        self.sku = str.capitalize(self.sku) if self.sku else None
        eventhubnamespace = self.get_namespace()
        if self.state == 'present':
            if not eventhubnamespace:
                changed = True
                self.log('Creating a new event hub namespace')
                if self.kafka_enabled and self.sku == 'Basic':
                    self.module.warn('kafka_enabled cannot be set to true under basic sku and would be ignored')
                    warning = True
                    self.kafka_enabled = None

                if self.sku:
                    self.sku = self.Eventhub_models.Sku(name=self.sku, tier=self.sku)

                eventhubnamespace = self.Eventhub_models.EHNamespace(location=self.location,
                                                                     sku=self.sku,
                                                                     tags=self.tags,
                                                                     is_auto_inflate_enabled=self.is_auto_inflate_enabled,
                                                                     maximum_throughput_units=self.maximum_throughput_units,
                                                                     kafka_enabled=self.kafka_enabled)
                if not self.check_mode:
                    eventhubnamespace = self.create_or_update_namespace(eventhubnamespace)
            else:
                # Compare sku
                if self.sku and self.sku != eventhubnamespace.sku.name:
                    self.log('SKU changed')
                    if eventhubnamespace.kafka_enabled and self.sku == 'Basic':
                        self.module.warn('kafka_enabled cannot be set under basic sku')
                        warning = True
                    else:
                        eventhubnamespace.sku.name = self.sku
                        eventhubnamespace.sku.tier = self.sku
                        changed = True

                # Compare is_auto_inflate_enabled
                if self.is_auto_inflate_enabled is not None and self.is_auto_inflate_enabled != eventhubnamespace.is_auto_inflate_enabled:
                    self.log('is_auto_inflate_enabled changed')
                    eventhubnamespace.is_auto_inflate_enabled = self.is_auto_inflate_enabled
                    changed = True

                # Compare maximum_throughput_units
                if self.maximum_throughput_units and self.maximum_throughput_units != eventhubnamespace.maximum_throughput_units:
                    self.log('maximum_throughput_units changed')
                    eventhubnamespace.maximum_throughput_units = self.maximum_throughput_units
                    changed = True
                else:
                    eventhubnamespace.maximum_throughput_units = None

                # Compare kafka_enabled
                if self.kafka_enabled is not None and self.kafka_enabled != eventhubnamespace.kafka_enabled:
                    self.module.warn('kafka_enabled cannot be updated after creation')
                    warning = True

                # Compare tags
                if self.tags and self.tags != eventhubnamespace.tags:
                    eventhubnamespace.tags = self.tags
                    changed = True

                if changed and not self.check_mode:
                    eventhubnamespace = self.create_or_update_namespace(eventhubnamespace)
            self.results = self.to_dict(eventhubnamespace)
        elif eventhubnamespace:
            changed = True
            if not self.check_mode:
                self.delete_namespace()
        self.results['changed'] = changed
        self.results['warning'] = warning
        return self.results

    def create_or_update_namespace(self, eventhubnamespace):
        try:
            poller = self.eventhub_client.namespaces.create_or_update(self.resource_group, self.name, eventhubnamespace)
            return self.get_poller_result(poller)
        except Exception as exc:
            self.fail('Error creating or updating Event Hub Namespace {0}: {1}'.format(self.name, str(exc)))

    def get_namespace(self):
        try:
            return self.eventhub_client.namespaces.get(self.resource_group, self.name)
        except Exception as exc:
            pass
            return None

    def delete_namespace(self):
        try:
            poller = self.eventhub_client.namespaces.delete(self.resource_group, self.name)
            return self.get_poller_result(poller)
        except Exception as exc:
            self.fail('Error deleting Event Hub Namespace{0}: {1}'.format(self.name, str(exc)))
            return False

    def to_dict(self, eventhubnamespace):
        return eventhubnamespace.as_dict()


def main():
    AzureRMEventHubNamespace()


if __name__ == '__main__':
    main()
