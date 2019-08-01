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
module: azure_rm_eventhub
version_added: "2.9"
short_description: Manage Azure Event hub
description:
    - Create, update and delete an Azure Event hub.

options:
    resource_group:
        description:
            - Name of a resource group where the Event hub exists or will be created.
        type: str
        required: true
    name:
        description:
            - Name of the Event hub.
        type: str
        required: true
    state:
        description:
            - State of the Event hub. Use C(present) to create or update an event hub and C(absent) to delete it.
        type: str
        default: present
        choices:
            - absent
            - present
    namespace:
        description:
            - The namespace name.
        type: str
        required: true
    message_retention_in_days:
        description:
            - Number of days to retain the events for this Event Hub, value should be C(1) to C(7) days.
        type: int
    partition_count:
        description:
            - Number of partitions created for the Event Hub, allowed values are from C(1) to C(32) partitions.
            - Is not changeable after the creation.
        type: int
    status:
        description:
            - Enumerates the possible values for the status of the Event Hub.
        type: str
        choices:
            - active
            - disabled
            - send_disabled
            - receive_disabled
    capture_description:
        description:
            - Properties of capture description.
        type: dict
        suboptions:
            enabled:
                description:
                    - A value that indicates whether capture description is C(enabled).
                required: true
                type: bool
            encoding:
                description:
                    - Enumerates the possible values for the encoding format of capture description.
                type: str
                required: true
                choices:
                    - avro
                    - avro_deflate
            interval_in_seconds:
                description:
                    - The time window allows you to set the frequency with which the capture to Azure Blobs will happen.
                    - Value should between C(60) to C(900) seconds.
                type: int
            size_limit_in_bytes:
                description:
                    - The size window defines the amount of data built up in your Event Hub before an capture operation.
                    - Value should be between 10485760) to C(524288000) bytes.
                type: int
            destination:
                description:
                    - Properties of estination where capture will be stored. (Storage Account, Blob Names).
                type: dict
                suboptions:
                    provider:
                        description:
                            - Provider for capture destination.
                        type: str
                        choices:
                            - EventHubArchive.AzureBlockBlob
                        required: true
                    storage_account_resource_id:
                        description:
                            - Resource ID of the storage account to be used to create the blobs.
                        type: str
                        required: true
                    blob_container:
                        description:
                            - Blob container name.
                        type: str
                        required: true
                    archive_name_format:
                        description:
                            - Blob naming convention for archive.
                        type: str
            skip_empty_archives:
                description:
                    - A value that indicates whether to Skip Empty Archives.
                type: bool

extends_documentation_fragment:
    - azure

author:
    - Fan Qiu (@MyronFanQiu)

'''

EXAMPLES = '''
    - name: Create an event hub with default
      azure_rm_eventhub:
        name: myEventhub
        resource_group: myResourceGroup
        namespace: myEventhubNamespace

    - name: Create an event hub with partition_count
      azure_rm_eventhub:
        name: myEventhub
        resource_group: myResourceGroup
        namespace: myEventhubNamespace
        partition_count: 8

    - name: Delete the event hub
      azure_rm_eventhub:
        name: myEventhub
        resource_group: myResourceGroup
        namespace: myEventhubNamespace
        state: absent
'''

RETURN = '''
id:
    description:
        - Resource ID of the event hub.
    returned: state is present
    type: str
    sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.EventHub/namespaces/myEventhub"
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass

storage_destination_spec = dict(
    provider=dict(
        type='str',
        required=True,
        choices=['EventHubArchive.AzureBlockBlob']
    ),
    storage_account_resource_id=dict(
        type='str',
        required=True
    ),
    blob_container=dict(
        type='str',
        required=True
    ),
    archive_name_format=dict(
        type='str'
    )
)

capture_description_spec = dict(
    enabled=dict(
        type='bool',
        required=True
    ),
    encoding=dict(
        type='str',
        required=True,
        choices=['avro', 'avro_deflate']
    ),
    interval_in_seconds=dict(
        type='int'
    ),
    size_limit_in_bytes=dict(
        type='int'
    ),
    destination=dict(
        type='dict',
        options=storage_destination_spec
    ),
    skip_empty_archives=dict(
        type='bool'
    )
)


class AzureRMEventHub(AzureRMModuleBase):
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
            namespace=dict(
                type='str',
                required=True
            ),
            message_retention_in_days=dict(
                type='int'
            ),
            partition_count=dict(
                type='int'
            ),
            status=dict(
                type='str',
                choices=['active', 'disabled', 'send_disabled', 'receive_disabled']
            ),
            capture_description=dict(
                type='dict',
                options=capture_description_spec
            )
        )

        self.results = dict(
            changed=False,
            id=None
        )

        # TODO: Add support for capture_description
        self.resource_group = None
        self.name = None
        self.state = None
        self.namespace = None
        self.message_retention_in_days = None
        self.partition_count = None
        self.status = None
        self.capture_description = None

        super(AzureRMEventHub, self).__init__(self.module_arg_spec, supports_check_mode=True, supports_tags=False)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in self.module_arg_spec.keys():
            setattr(self, key, kwargs[key])

        changed = False
        results = None

        self.status = self.eventhub_models.EntityStatus[self.status] if self.status else None
        event_hub = self.get_event_hub()

        if self.state == 'present':
            # TODO: Add support for capture_description
            if not event_hub:
                changed = True
                capture_property = None
                if self.capture_description:
                    capture_property = self.construct_capture_decription()
                event_hub_instance = self.eventhub_models.Eventhub(message_retention_in_days=self.message_retention_in_days,
                                                                   partition_count=self.partition_count,
                                                                   status=self.status,
                                                                   capture_description=capture_property)
                if not self.check_mode:
                    event_hub = self.create_or_update_event_hub(event_hub_instance)

            else:
                changed, event_hub = self.check_status(changed=changed, event_hub=event_hub)

                if changed and not self.check_mode:
                    event_hub = self.create_or_update_event_hub(event_hub)
            results = self.to_dict(event_hub)['id'] if event_hub else None
        elif event_hub:
            changed = True
            if not self.check_mode:
                self.delete_event_hub()

        self.results['changed'] = changed
        self.results['id'] = results
        return self.results

    def get_event_hub(self):
        try:
            self.log('Getting an event hub')
            return self.eventhub_client.event_hubs.get(resource_group_name=self.resource_group, namespace_name=self.namespace, event_hub_name=self.name)
        except Exception as exc:
            pass
            return None

    def construct_capture_decription(self):
        destination_property = None
        capture_property = None
        if self.capture_description.get('enabled'):
            destination = self.capture_description.get('destination')
            if destination is None:
                self.fail("Destination must be set when enable the capture function")
            destination_property = self.eventhub_models.Destination(name=destination.get('provider'),
                                                                    storage_account_resource_id=destination['storage_account_resource_id'],
                                                                    blob_container=destination['blob_container'],
                                                                    archive_name_format=destination.get('archive_name_format'))
        encoding_type = None
        if self.capture_description.get('encoding'):
            encoding_type = self.eventhub_models.EncodingCaptureDescription[self.capture_description.get('encoding')]
        capture_property = self.eventhub_models.CaptureDescription(enabled=self.capture_description.get('enabled'),
                                                                   encoding=encoding_type,
                                                                   interval_in_seconds=self.capture_description.get('interval_in_seconds'),
                                                                   size_limit_in_bytes=self.capture_description.get('size_limit_in_bytes'),
                                                                   destination=destination_property,
                                                                   skip_empty_archives=self.capture_description.get('skip_empty_archives'))
        return capture_property

    def check_status(self, changed, event_hub):
        # Compare message_retention_in_days
        if self.message_retention_in_days and self.message_retention_in_days != event_hub.message_retention_in_days:
            changed = True
            event_hub.message_retention_in_days = self.message_retention_in_days

        # Compare partition_count
        if self.partition_count and self.partition_count != event_hub.partition_count:
            self.module.warn("partition_count is not changeable after the creation!")
            event_hub.partition_count = None

        # Compare status
        if self.status and self.status != event_hub.status:
            changed = True
            event_hub.status = self.status

        # Compare capture description
        if self.capture_description:
            if self.capture_description.get('enabled') != event_hub.capture_description.enabled:
                changed = True
                event_hub.capture_description.enabled = self.capture_description.get('enabled')
            if event_hub.capture_description.enabled:
                changed, event_hub.capture_description.destination = self.check_destination(changed=changed,
                                                                                            destination=event_hub.capture_description.destination)

                if self.capture_description.get('encoding') is not None:
                    encoding_type = self.eventhub_models.EncodingCaptureDescription[self.capture_description.get('encoding')]
                    if encoding_type != event_hub.capture_description.encoding:
                        changed = True
                        event_hub.capture_description.encoding = encoding_type

                if self.capture_description.get('interval_in_seconds') is not None:
                    if self.capture_description.get('interval_in_seconds') != event_hub.capture_description.interval_in_seconds:
                        changed = True
                        event_hub.capture_description.interval_in_seconds = self.capture_description.get('interval_in_seconds')

                if self.capture_description.get('size_limit_in_bytes') is not None:
                    if self.capture_description.get('size_limit_in_bytes') != event_hub.capture_description.size_limit_in_bytes:
                        changed = True
                        event_hub.capture_description.size_limit_in_bytes = self.capture_description.get('size_limit_in_bytes')

                if self.capture_description.get('skip_empty_archives') is not None:
                    if self.capture_description.get('skip_empty_archives') != event_hub.capture_description.skip_empty_archives:
                        changed = True
                        event_hub.capture_description.skip_empty_archives = self.capture_description.get('skip_empty_archives')
        return changed, event_hub

    def check_destination(self, changed, destination):
        destination_settings = self.capture_description.get('destination')

        if not destination_settings:
            return changed, destination

        if destination_settings.get('provider'):
            if destination_settings.get('provider') != destination.name:
                changed = True
                destination.name = destination_settings.get('provider')

        if destination_settings.get('storage_account_resource_id'):
            if destination_settings.get('storage_account_resource_id') != destination.storage_account_resource_id:
                changed = True
                destination.storage_account_resource_id = destination_settings.get('storage_account_resource_id')

        if destination_settings.get('blob_container'):
            if destination_settings.get('blob_container') != destination.blob_container:
                changed = True
                destination.blob_container = destination_settings.get('blob_container')

        if destination_settings.get('archive_name_format'):
            if destination_settings.get('archive_name_format') != destination.archive_name_format:
                changed = True
                destination.archive_name_format = destination_settings.get('archive_name_format')

        return changed, destination

    def create_or_update_event_hub(self, event_hub):
        try:
            self.log('Creating or updating an event hub')
            return self.eventhub_client.event_hubs.create_or_update(resource_group_name=self.resource_group,
                                                                    namespace_name=self.namespace,
                                                                    event_hub_name=self.name,
                                                                    parameters=event_hub)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Error creating or updating Event Hub{0}: {1}'.format(self.name, str(exc.inner_exception) or exc.message or str(exc)))

    def delete_event_hub(self):
        try:
            self.log('Deleting an event hub')
            return self.eventhub_client.event_hubs.delete(resource_group_name=self.resource_group,
                                                          namespace_name=self.namespace,
                                                          event_hub_name=self.name)
        except self.eventhub_models.ErrorResponseException as exc:
            self.fail('Error deleting Event Hub{0}: {1}'.format(self.name, str(exc.inner_exception) or exc.message or str(exc)))

    def to_dict(self, event_hub):
        return event_hub.as_dict()


def main():
    AzureRMEventHub()


if __name__ == '__main__':
    main()
