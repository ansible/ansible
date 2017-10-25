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
module: azure_rm_aci
version_added: "2.5"
short_description: Manage an Azure Container Instance (ACI).
description:
    - Create, update and delete an Azure Container Instance.

options:
    resource_group:
        description:
            - Name of resource group.
        required: true
    name:
        description:
            - The name of the container group.
        required: true
        default: null
    os_type:
        description:
            - The OS type of containers.
        choices:
            - linux
            - windows
        default: linux
        required: false
    state:
        description:
            - Assert the state of the ACI. Use 'present' to create or update an ACI and 'absent' to delete it.
        default: present
        choices:
            - absent
            - present
        required: false
    ip_address:
        description:
            - The IP address type of the container group.
        choices:
            - public
        required: false
        default: None
    ports:
        description:
            - List of ports exposed within the container group.
        required: false
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
        default: resource_group location
        required: false
    registry_login_server:
        description:
            - The container image registry login server.
        required: false
    registry_username:
        description:
            - The username to log in container image registry server.
        required: false
    registry_password:
        description:
            - The password to log in container image registry server.
        required: false
    containers:
        description:
            - List of containers.
        required: false
        default: null
        suboptions:
            name:
                description:
                    - The name of the container instance.
                required: true
                default: null
            image:
                description:
                    - The container image name.
                required: true
                default: null
            memory:
                description:
                    - The required memory of the containers in GB.
                default: 1.5
                required: false
            cpu:
                description:
                    - The required number of CPU cores of the containers.
                default: 1
                required: false
            ports:
                description:
                    - List of ports exposed within the container group.
                required: false

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Create sample container group
    azure_rm_aci:
    resource_group: testrg
    name: mynewcontainergroup
    os_type: linux
    ip_address: public
    ports:
      - 80
      - 81
    containers:
      - name: mycontainer1
        image: httpd
        memory: 1.5
        ports:
          - 80
      - name: mycontainer2
        image: httpd
        memory: 1.5
        ports:
          - 81
'''
RETURN = '''
state:
    description: Current state of the azure instance
    returned: always
    type: dict
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.containerinstance.models import (ContainerGroup,
                                                     Container,
                                                     ResourceRequirements,
                                                     ResourceRequests,
                                                     ImageRegistryCredential,
                                                     IpAddress,
                                                     Port,
                                                     ContainerPort)
    from azure.mgmt.containerinstance import ContainerInstanceManagementClient
except ImportError:
    # This is handled in azure_rm_common
    pass


def create_container_dict_from_obj(container):
    '''
    Create a dict from an instance of a Container.

    :param rule: Container
    :return: dict
    '''
    results = dict(
        name=container.name,
        image=container.image,
        memory=container.resources.requests.memory_in_gb,
        cpu=container.resources.requests.cpu
        # command (list of str)
        # ports (list of ContainerPort)
        # environment_variables (list of EnvironmentVariable)
        # resources (ResourceRequirements)
        # volume mounts (list of VolumeMount)
    )

    if container.instance_view is not None:
        # instance_view (ContainerPropertiesInstanceView)
        results["instance_restart_count"] = container.instance_view.restart_count
        if container.instance_view.current_state:
            results["instance_current_state"] = container.instance_view.current_state.state
            results["instance_current_start_time"] = container.instance_view.current_state.start_time
            results["instance_current_exit_code"] = container.instance_view.current_state.exit_code
            results["instance_current_finish_time"] = container.instance_view.current_state.finish_time
            results["instance_current_detail_status"] = container.instance_view.current_state.detail_status
        if container.instance_view.previous_state:
            results["instance_previous_state"] = container.instance_view.previous_state.state
            results["instance_previous_start_time"] = container.instance_view.previous_state.start_time
            results["instance_previous_exit_code"] = container.instance_view.previous_state.exit_code
            results["instance_previous_finish_time"] = container.instance_view.previous_state.finish_time
            results["instance_previous_detail_status"] = container.instance_view.previous_state.detail_status
        # events (list of ContainerEvent)
    return results


def create_aci_dict(aci):
    '''
    Helper method to deserialize a ContainerService to a dict
    :param: aci: Container
    :return: dict with the state on Azure
    '''
    results = dict(
        id=aci.id,
        name=aci.name,
        tags=aci.tags,
        location=aci.location,
        type=aci.type,
        restart_policy=aci.restart_policy,
        provisioning_state=aci.provisioning_state,
        image_registry_credentials=aci.image_registry_credentials,
        volumes=aci.volumes,
        os_type=aci.os_type
    )

    if aci.ip_address:
        results['ip_address'] = dict(type=aci.ip_address.type,
                                     ip=aci.ip_address.ip,
                                     ports=[])

    results['containers'] = []
    if aci.containers:
        for container in aci.containers:
            results['containers'].append(create_container_dict_from_obj(container))

    return results


class AzureRMContainerInstance(AzureRMModuleBase):
    """Configuration class for an Azure RM container instance resource"""

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
            os_type=dict(
                type='str',
                required=False,
                default='linux',
                choices=['linux', 'windows']
            ),
            state=dict(
                type='str',
                required=False,
                default='present',
                choices=['present', 'absent']
            ),
            location=dict(
                type='str',
                required=False
            ),
            ip_address=dict(
                type='str',
                required=False,
                default=None,
                choices=['public']
            ),
            ports=dict(
                type='list',
                required=False
            ),
            registry_login_server=dict(
                type='str',
                required=False,
                default=None
            ),
            registry_username=dict(
                type='str',
                required=False,
                default=None
            ),
            registry_password=dict(
                type='str',
                required=False,
                default=None
            ),
            containers=dict(
                type='list',
                required=True
            )
        )

        self.resource_group = None
        self.name = None
        self.location = None
        self.tags = None
        self.state = None
        self.ip_address = None

        self.containers = None

        self.results = dict(changed=False, state=dict())
        self.mgmt_client = None

        super(AzureRMContainerInstance, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                       supports_check_mode=True,
                                                       supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        resource_group = None
        response = None
        results = dict()
        to_be_updated = False

        self.mgmt_client = self.get_mgmt_svc_client(ContainerInstanceManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        try:
            resource_group = self.get_resource_group(self.resource_group)
        except CloudError:
            self.fail('resource group {} not found'.format(self.resource_group))
        if not self.location:
            self.location = resource_group.location

        response = self.get_aci()

        if not response:
            self.log("Container Group doesn't exist")

            if self.state == 'absent':
                self.log("Nothing to delete")
            else:
                to_be_updated = True
        else:
            self.log("Container instance already exists")

            if self.state == 'absent':
                self.delete_aci()
                self.results['changed'] = True
                self.log("ACI instance deleted")
            elif self.state == 'present':
                self.log("Need to check if container group has to be deleted or may be updated")
                to_be_updated = self.check_need_update(response)
                if to_be_updated:
                    self.log('Deleting ACI instance before update')
                    if not self.check:
                        self.delete_aci()

        if self.state == 'present':

            self.log("Need to Create / Update the ACI instance")

            if self.check_mode:
                return self.results

            if to_be_updated:
                self.results['state'] = self.create_update_aci()
                self.results['changed'] = True
            else:
                self.results['state'] = response

            self.log("Creation / Update done")

        return self.results

    def create_update_aci(self):
        '''
        Creates or updates a container service with the specified configuration of orchestrator, masters, and agents.

        :return: deserialized ACI instance state dictionary
        '''
        self.log("Creating / Updating the ACI instance {0}".format(self.name))

        registry_credentials = None

        if self.registry_login_server is not None:
            registry_credentials = ImageRegistryCredential(self.registry_login_server,
                                                           self.registry_username,
                                                           self.registry_password)

        ip_address = None

        if self.ip_address is not None:
            # get list of ports
            if self.ports:
                ports = []
                for port in self.ports:
                    ports.append(Port(port, "TCP"))
                ip_address = IpAddress(ports, self.ip_address)

        containers = []

        for container_def in self.containers:
            name = container_def.get("name")
            image = container_def.get("image")
            memory = container_def.get("memory", 1.5)
            cpu = container_def.get("cpu", 1)
            ports = []

            port_list = container_def.get("ports")
            if port_list:
                for port in port_list:
                    ports.append(ContainerPort(port))

            containers.append(Container(name, image, ResourceRequirements(ResourceRequests(memory, cpu)), None, ports))

        parameters = ContainerGroup(location=self.location,
                                    tags=self.tags,
                                    containers=containers,
                                    image_registry_credentials=registry_credentials,
                                    restart_policy=None,
                                    ip_address=ip_address,
                                    os_type=self.os_type,
                                    volumes=None)

        try:
            response = self.mgmt_client.container_groups.create_or_update(self.resource_group, self.name, parameters)

        except CloudError as exc:
            self.log('Error attempting to create the container instance.')
            self.fail("Error creating the ACI instance: {0}".format(str(exc)))
        return create_aci_dict(response)

    def delete_aci(self):
        '''
        Deletes the specified container group instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the ACI instance {0}".format(self.name))
        try:
            response = self.mgmt_client.container_groups.delete(self.resource_group, self.name)
        except CloudError as e:
            self.log('Error attempting to delete the ACI instance.')
            self.fail("Error deleting the ACI instance: {0}".format(str(e)))

        return True

    def get_aci(self):
        '''
        Gets the properties of the specified container service.

        :return: deserialized ACI instance state dictionary
        '''
        self.log("Checking if the ACI instance {0} is present".format(self.name))
        found = False
        try:
            response = self.mgmt_client.container_groups.get(self.resource_group, self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("ACI instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the ACI instance.')
        if found is True:
            return create_aci_dict(response)

        return False

    def check_need_update(self, cg):

        if self.location.lower() != cg["location"].lower():
            self.log('Location has changed -- need to delete')
            return True
        if self.os_type.lower() != cg["os_type"].lower():
            self.log('OS Type has changed -- need to delete')
            return True

        # check if container list has changed
        if len(cg["containers"]) != len(self.containers):
            self.log('Number of containers has changed -- need to delete')
            return True

        for i in range(len(self.containers)):
            if cg["containers"][i]["image"] != self.containers[i]["image"]:
                self.log('Container image has changed -- need to delete')
                return True
            if cg["containers"][i]["memory"] != self.containers[i]["memory"]:
                self.log('Container memory has changed -- need to delete')
                return True
            if cg["containers"][i]["name"] != self.containers[i]["name"]:
                self.log('Container name has changed -- need to delete')
                return True

        self.log('No need to update')
        return False


def main():
    """Main execution"""
    AzureRMContainerInstance()

if __name__ == '__main__':
    main()
