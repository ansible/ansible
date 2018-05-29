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
module: azure_rm_containerinstance
version_added: "2.5"
short_description: Manage an Azure Container Instance.
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
    os_type:
        description:
            - The OS type of containers.
        choices:
            - linux
            - windows
        default: linux
    state:
        description:
            - Assert the state of the container instance. Use 'present' to create or update an container instance and 'absent' to delete it.
        default: present
        choices:
            - absent
            - present
    ip_address:
        description:
            - The IP address type of the container group (default is 'none')
        choices:
            - public
            - none
        default: 'none'
    ports:
        description:
            - List of ports exposed within the container group.
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
    registry_login_server:
        description:
            - The container image registry login server.
    registry_username:
        description:
            - The username to log in container image registry server.
    registry_password:
        description:
            - The password to log in container image registry server.
    containers:
        description:
            - List of containers.
        suboptions:
            name:
                description:
                    - The name of the container instance.
                required: true
            image:
                description:
                    - The container image name.
                required: true
            memory:
                description:
                    - The required memory of the containers in GB.
                default: 1.5
            cpu:
                description:
                    - The required number of CPU cores of the containers.
                default: 1
            ports:
                description:
                    - List of ports exposed within the container group.
    force_update:
        description:
            - Force update of existing container instance. Any update will result in deletion and recreation of existing containers.
        type: bool
        default: 'no'

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Create sample container group
    azure_rm_containerinstance:
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
'''
RETURN = '''
id:
    description:
        - Resource ID
    returned: always
    type: str
    sample: /subscriptions/ffffffff-ffff-ffff-ffff-ffffffffffff/resourceGroups/TestGroup/providers/Microsoft.ContainerInstance/containerGroups/aci1b6dd89
provisioning_state:
    description:
        - Provisioning state of the container.
    returned: always
    type: str
    sample: Creating
ip_address:
    description:
        - Public IP Address of created container group.
    returned: if address is public
    type: str
    sample: 175.12.233.11
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_operation import AzureOperationPoller
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
                default='linux',
                choices=['linux', 'windows']
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            ),
            location=dict(
                type='str',
            ),
            ip_address=dict(
                type='str',
                default='none',
                choices=['public', 'none']
            ),
            ports=dict(
                type='list',
                default=[]
            ),
            registry_login_server=dict(
                type='str',
                default=None
            ),
            registry_username=dict(
                type='str',
                default=None
            ),
            registry_password=dict(
                type='str',
                default=None,
                no_log=True
            ),
            containers=dict(
                type='list',
                required=True
            ),
            force_update=dict(
                type='bool',
                default=False
            ),
        )

        self.resource_group = None
        self.name = None
        self.location = None
        self.state = None
        self.ip_address = None

        self.containers = None

        self.results = dict(changed=False, state=dict())
        self.client = None
        self.cgmodels = None

        super(AzureRMContainerInstance, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                       supports_check_mode=True,
                                                       supports_tags=False)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()):
            setattr(self, key, kwargs[key])

        resource_group = None
        response = None
        results = dict()

        self.client = self.get_mgmt_svc_client(ContainerInstanceManagementClient)

        # since this client hasn't been upgraded to expose models directly off the OperationClass, fish them out
        self.cgmodels = self.client.container_groups.models

        resource_group = self.get_resource_group(self.resource_group)

        if not self.location:
            self.location = resource_group.location

        response = self.get_containerinstance()

        if not response:
            self.log("Container Group doesn't exist")

            if self.state == 'absent':
                self.log("Nothing to delete")
            else:
                self.force_update = True
        else:
            self.log("Container instance already exists")

            if self.state == 'absent':
                if not self.check_mode:
                    self.delete_containerinstance()
                self.results['changed'] = True
                self.log("Container instance deleted")
            elif self.state == 'present':
                self.log("Need to check if container group has to be deleted or may be updated")
                if self.force_update:
                    self.log('Deleting container instance before update')
                    if not self.check_mode:
                        self.delete_containerinstance()

        if self.state == 'present':

            self.log("Need to Create / Update the container instance")

            if self.force_update:
                self.results['changed'] = True
                if self.check_mode:
                    return self.results
                response = self.create_update_containerinstance()

            self.results['id'] = response['id']
            self.results['provisioning_state'] = response['provisioning_state']
            self.results['ip_address'] = response['ip_address']['ip']

            self.log("Creation / Update done")

        return self.results

    def create_update_containerinstance(self):
        '''
        Creates or updates a container service with the specified configuration of orchestrator, masters, and agents.

        :return: deserialized container instance state dictionary
        '''
        self.log("Creating / Updating the container instance {0}".format(self.name))

        registry_credentials = None

        if self.registry_login_server is not None:
            registry_credentials = [self.cgmodels.ImageRegistryCredential(server=self.registry_login_server,
                                                                          username=self.registry_username,
                                                                          password=self.registry_password)]

        ip_address = None

        if self.ip_address == 'public':
            # get list of ports
            if self.ports:
                ports = []
                for port in self.ports:
                    ports.append(self.cgmodels.Port(port=port, protocol="TCP"))
                ip_address = self.cgmodels.IpAddress(ports=ports, ip=self.ip_address)

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
                    ports.append(self.cgmodels.ContainerPort(port=port))

            containers.append(self.cgmodels.Container(name=name,
                                                      image=image,
                                                      resources=self.cgmodels.ResourceRequirements(
                                                          requests=self.cgmodels.ResourceRequests(memory_in_gb=memory, cpu=cpu)
                                                      ),
                                                      ports=ports))

        parameters = self.cgmodels.ContainerGroup(location=self.location,
                                                  containers=containers,
                                                  image_registry_credentials=registry_credentials,
                                                  restart_policy=None,
                                                  ip_address=ip_address,
                                                  os_type=self.os_type,
                                                  volumes=None)

        response = self.client.container_groups.create_or_update(resource_group_name=self.resource_group,
                                                                 container_group_name=self.name,
                                                                 container_group=parameters)

        if isinstance(response, AzureOperationPoller):
            response = self.get_poller_result(response)

        return response.as_dict()

    def delete_containerinstance(self):
        '''
        Deletes the specified container group instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the container instance {0}".format(self.name))
        response = self.client.container_groups.delete(resource_group_name=self.resource_group, container_group_name=self.name)
        return True

    def get_containerinstance(self):
        '''
        Gets the properties of the specified container service.

        :return: deserialized container instance state dictionary
        '''
        self.log("Checking if the container instance {0} is present".format(self.name))
        found = False
        try:
            response = self.client.container_groups.get(resource_group_name=self.resource_group, container_group_name=self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("Container instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the container instance.')
        if found is True:
            return response.as_dict()

        return False


def main():
    """Main execution"""
    AzureRMContainerInstance()

if __name__ == '__main__':
    main()
