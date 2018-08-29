#!/usr/bin/python
#
# Copyright (c) 2017 Zim Kalinowski, <zikalino@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_containerinstance_facts
version_added: "2.7"
short_description: Get Container Group facts.
description:
    - Get facts of Container Group.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    name:
        description:
            - The name of the container group.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get instance of Container Group
    azure_rm_containerinstance_facts:
      resource_group: resource_group_name
      name: container_group_name

  - name: List instances of Container Group
    azure_rm_containerinstance_facts:
      resource_group: resource_group_name
'''

RETURN = '''
container_groups:
    description: A list of Container Instance dictionaries.
    returned: always
    type: complex
    contains:
        id:
            description:
                - The resource id.
            returned: always
            type: str
            sample: "/subscriptions/ae43b1e3-c35d-4c8c-bc0d-f148b4c52b78/resourceGroups/demo/providers/Microsoft.ContainerInstance/containerGroups/my
                    containers"
        name:
            description:
                - The resource name.
            returned: always
            type: str
            sample: mycontainers
        type:
            description:
                - The resource type.
            returned: always
            type: str
            sample: Microsoft.ContainerInstance/containerGroups
        location:
            description:
                - The resource location.
            returned: always
            type: str
            sample: westus
        containers:
            description:
                - The containers within the container group.
            returned: always
            type: complex
            sample: containers
            contains:
                name:
                    description:
                        - The name of the container instance.
                    returned: always
                    type: str
                    sample: "/subscriptions/ae43b1e3-c35d-4c8c-bc0d-f148b4c52b78/resourceGroups/demo/providers/Microsoft.ContainerInstance/containerGroups/my
                            containers"
                image:
                    description:
                        - The container image name.
                    returned: always
                    type: str
                    sample: "/subscriptions/ae43b1e3-c35d-4c8c-bc0d-f148b4c52b78/resourceGroups/demo/providers/Microsoft.ContainerInstance/containerGroups/my
                            containers"
                memory:
                    description:
                        - The required memory of the containers in GB.
                    returned: always
                    type: float
                    sample: 1.5
                cpu:
                    description:
                        - The required number of CPU cores of the containers.
                    returned: always
                    type: int
                    sample: 1
                ports:
                    description:
                        - List of ports exposed within the container group.
                    returned: always
                    type: list
                    sample: [ 80, 81 ]
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_operation import AzureOperationPoller
    from azure.mgmt.containerinstance import ContainerInstanceManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMContainerGroupsFacts(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str'
            )
        )
        # store the results of the module operation
        self.results = dict(
            changed=False,
            ansible_facts=dict()
        )
        self.resource_group = None
        self.name = None
        super(AzureRMContainerGroupsFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if (self.resource_group is not None and
                self.name is not None):
            self.results['containerinstances'] = self.get()
        elif (self.resource_group is not None):
            self.results['containerinstances'] = self.list_by_resource_group()
        return self.results

    def get(self):
        response = None
        results = []
        try:
            response = self.containerinstance_client.container_groups.get(resource_group_name=self.resource_group,
                                                                          container_group_name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for ContainerGroups.')

        if response is not None:
            results.append(self.format_item(response))

        return results

    def list_by_resource_group(self):
        response = None
        results = []
        try:
            response = self.containerinstance_client.container_groups.list_by_resource_group(resource_group_name=self.resource_group)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for ContainerGroups.')

        if response is not None:
            for item in response:
                results.append(self.format_item(item))

        return results

    def format_item(self, item):
        d = item.as_dict()
        containers = d['containers']
        ports = d['ip_address']['ports']

        for port_index in range(len(ports)):
            ports[port_index] = ports[port_index]['port']

        for container_index in range(len(containers)):
            old_container = containers[container_index]
            new_container = {
                'name': old_container['name'],
                'image': old_container['image'],
                'memory': old_container['resources']['requests']['memory_in_gb'],
                'cpu': old_container['resources']['requests']['cpu'],
                'ports': []
            }
            for port_index in range(len(old_container['ports'])):
                new_container['ports'].append(old_container['ports'][port_index]['port'])
            containers[container_index] = new_container

        d = {
            'resource_group': self.resource_group,
            'name': d['name'],
            'os_type': d['os_type'],
            'ip_address': 'public' if d['ip_address']['type'] == 'Public' else 'none',
            'ports': ports,
            'location': d['location'],
            'containers': containers,
            'state': 'present'
        }
        return d


def main():
    AzureRMContainerGroupsFacts()


if __name__ == '__main__':
    main()
