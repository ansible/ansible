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
version_added: "2.9"
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
    auto_inflate_enabled:
        description:
            - Value that indicates whether AutoInflate is enabled for eventhub namespace.
            - Default is false when creation.
        type: bool
    maximum_throughput_units:
        description:
            - Upper limit of throughput units when AutoInflate is enabled, value should be within 0 to 20 throughput units. ( '0' if AutoInflateEnabled = false)
            - Only can be set when the C(auto_inflate_enabled) == true
        type: int
    kafka_enabled:
        description:
            - Value that indicates whether Kafka is enabled for eventhub namespace.
            - Default is false when creation.
            - Cannot be updated after the creation
        type: bool

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Fan Qiu (@MyronFanQiu)"

'''

EXAMPLES = '''
    - name: Create event hub namespace with default
      azure_rm_eventhubnamespace:
        name: myEventhubNamespace
        location: eastus
        resource_group: myResourceGroup

    - name: Create event hub namespace when C(kafka_enabled) is set to true
      azure_rm_eventhubnamespace:
        name: myEventhubNamespace02
        location: eastus
        resource_group: myResourceGroup
        kafka_enabled: true

    - name: Update event hub namespace sku basic
      azure_rm_eventhubnamespace:
        name: myEventhubNamespace
        location: eastus
        resource_group: myResourceGroup
        sku: basic

    - name: Update event hub namespace sku standard
      azure_rm_eventhubnamespace:
        name: myEventhubNamespace
        location: eastus
        resource_group: myResourceGroup
        sku: standard

    - name: Update event hub namespace maximum_throughput_units to 8
      azure_rm_eventhubnamespace:
        name: myEventhubNamespace
        location: eastus
        resource_group: myResourceGroup
        auto_inflate_enabled: true
        maximum_throughput_units: 8

    - name: Update event hub namespace auto_inflate_enabled to false
      azure_rm_eventhubnamespace:
        name: myEventhubNamespace
        location: eastus
        resource_group: myResourceGroup
        auto_inflate_enabled: false

    - name: Delete event hub namespace
      azure_rm_eventhubnamespace:
        name: myEventhubNamespace
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
    sample: "/subscriptions/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/resourceGroups/myResourceGroup/providers/Microsoft.EventHub/namespaces/myEventhubNamespace"
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
            auto_inflate_enabled=dict(
                type='bool'
            ),
            maximum_throughput_units=dict(
                type='int'
            ),
            kafka_enabled=dict(
                type='bool'
            )
        )

        self.results = dict(
            changed=False,
            id=dict()
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
        self.sku = None
        self.auto_inflate_enabled = None
        self.maximum_throughput_units = None
        self.kafka_enabled = None
        self.tags = None

        super(AzureRMEventHubNamespace, self).__init__(self.module_arg_spec, supports_tags=True, supports_check_mode=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in self.module_arg_spec.keys():
            setattr(self, key, kwargs[key])

        changed = False
        results = None

        if not self.location:
            # Set default location
            resource_group = self.get_resource_group(self.resource_group)
            self.location = resource_group.location
        self.sku = str.capitalize(self.sku) if self.sku else None
        eventhubnamespace = self.get_namespace() or dict()
        if self.state == 'present':
            if not eventhubnamespace:
                changed = True
                if self.kafka_enabled and self.sku == 'Basic':
                    self.module.warn('kafka_enabled cannot be set to true under basic sku and would be ignored')
                    self.kafka_enabled = None

                if self.sku:
                    self.sku = self.eventhub_models.Sku(name=self.sku, tier=self.sku)

                eventhubnamespace_instance = self.eventhub_models.EHNamespace(location=self.location,
                                                                              sku=self.sku,
                                                                              tags=self.tags,
                                                                              is_auto_inflate_enabled=self.auto_inflate_enabled,
                                                                              maximum_throughput_units=self.maximum_throughput_units,
                                                                              kafka_enabled=self.kafka_enabled)
                if not self.check_mode:
                    eventhubnamespace = self.create_or_update_namespace(eventhubnamespace_instance)
            else:
                changed, eventhubnamespace = self.check_status(changed=changed, eventhubnamespace=eventhubnamespace)

                if changed and not self.check_mode:
                    eventhubnamespace = self.create_or_update_namespace(eventhubnamespace)
            results = self.to_dict(eventhubnamespace)['id'] if eventhubnamespace else None
        elif eventhubnamespace:
            changed = True
            if not self.check_mode:
                self.delete_namespace()

        self.results['id'] = results
        self.results['changed'] = changed
        return self.results

    def create_or_update_namespace(self, eventhubnamespace):
        try:
            self.log('Creating or updating an event hub namespace')
            poller = self.eventhub_client.namespaces.create_or_update(resource_group_name=self.resource_group,
                                                                      namespace_name=self.name,
                                                                      parameters=eventhubnamespace)
            return self.get_poller_result(poller)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Error creating or updating Event Hub Namespace {0}: {1}'.format(self.name, str(exc.inner_exception) or str(exc.message) or str(exc)))

    def check_status(self, changed, eventhubnamespace):
        # Compare sku
        if self.sku and self.sku != eventhubnamespace.sku.name:
            self.log('SKU changed')
            if eventhubnamespace.kafka_enabled and self.sku == 'Basic':
                self.module.warn('kafka_enabled cannot be set under basic sku')
            else:
                eventhubnamespace.sku.name = self.sku
                eventhubnamespace.sku.tier = self.sku
                changed = True

        # Compare is_auto_inflate_enabled
        if self.auto_inflate_enabled is not None and self.auto_inflate_enabled != eventhubnamespace.is_auto_inflate_enabled:
            self.log('auto_inflate_enabled changed')
            eventhubnamespace.is_auto_inflate_enabled = self.auto_inflate_enabled
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

        # Compare tags
        update_tags, eventhubnamespace.tags = self.update_tags(eventhubnamespace.tags)
        if update_tags:
            eventhubnamespace.tags = self.tags
            changed = True

        return changed, eventhubnamespace

    def get_namespace(self):
        try:
            self.log('Getting an event hub namespace')
            return self.eventhub_client.namespaces.get(resource_group_name=self.resource_group, namespace_name=self.name)
        except Exception as exc:
            pass
            return None

    def delete_namespace(self):
        try:
            self.log('Deleting an event hub namespace')
            poller = self.eventhub_client.namespaces.delete(resource_group_name=self.resource_group, namespace_name=self.name)
            return self.get_poller_result(poller)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Error deleting Event Hub Namespace{0}: {1}'.format(self.name, str(exc.inner_exception) or str(exc.message) or str(exc)))
            return False

    def to_dict(self, eventhubnamespace):
        return eventhubnamespace.as_dict()


def main():
    AzureRMEventHubNamespace()


if __name__ == '__main__':
    main()
