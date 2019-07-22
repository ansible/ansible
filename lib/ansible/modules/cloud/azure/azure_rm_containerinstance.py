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
short_description: Manage an Azure Container Instance
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
            - Assert the state of the container instance. Use C(present) to create or update an container instance and C(absent) to delete it.
        default: present
        choices:
            - absent
            - present
    ip_address:
        description:
            - The IP address type of the container group.
            - Default is C(none) and creating an instance without public IP.
        choices:
            - public
            - none
        default: 'none'
    dns_name_label:
        description:
            - The Dns name label for the IP.
        type: str
        version_added: "2.8"
    ports:
        description:
            - List of ports exposed within the container group.
            - This option is deprecated, using I(ports) under I(containers)".
        type: list
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
            - Required when creation.
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
                type: float
                default: 1.5
            cpu:
                description:
                    - The required number of CPU cores of the containers.
                type: float
                default: 1
            ports:
                description:
                    - List of ports exposed within the container group.
                type: list
            environment_variables:
                description:
                    - List of container environment variables.
                    - When updating existing container all existing variables will be replaced by new ones.
                type: dict
                suboptions:
                    name:
                        description:
                            - Environment variable name.
                        type: str
                    value:
                        description:
                            - Environment variable value.
                        type: str
                    is_secure:
                        description:
                            - Is variable secure.
                        type: bool
                version_added: "2.8"
            commands:
                description:
                    - List of commands to execute within the container instance in exec form.
                    - When updating existing container all existing commands will be replaced by new ones.
                type: list
                version_added: "2.8"
    restart_policy:
        description:
            - Restart policy for all containers within the container group.
        type: str
        choices:
            - always
            - on_failure
            - never
        version_added: "2.8"
    force_update:
        description:
            - Force update of existing container instance. Any update will result in deletion and recreation of existing containers.
        type: bool
        default: 'no'

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - Zim Kalinowski (@zikalino)

'''

EXAMPLES = '''
  - name: Create sample container group
    azure_rm_containerinstance:
      resource_group: myResourceGroup
      name: myContainerInstanceGroup
      os_type: linux
      ip_address: public
      containers:
        - name: myContainer1
          image: httpd
          memory: 1.5
          ports:
            - 80
            - 81
'''
RETURN = '''
id:
    description:
        - Resource ID.
    returned: always
    type: str
    sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ContainerInstance/containerGroups/aci1b6dd89
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
from ansible.module_utils.common.dict_transformations import _snake_to_camel

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.polling import LROPoller
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


env_var_spec = dict(
    name=dict(type='str', required=True),
    value=dict(type='str', required=True),
    is_secure=dict(type='bool')
)


container_spec = dict(
    name=dict(type='str', required=True),
    image=dict(type='str', required=True),
    memory=dict(type='float', default=1.5),
    cpu=dict(type='float', default=1),
    ports=dict(type='list', elements='int'),
    commands=dict(type='list', elements='str'),
    environment_variables=dict(type='list', elements='dict', options=env_var_spec)
)


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
            dns_name_label=dict(
                type='str',
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
                elements='dict',
                options=container_spec
            ),
            restart_policy=dict(
                type='str',
                choices=['always', 'on_failure', 'never']
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
        self.dns_name_label = None
        self.containers = None
        self.restart_policy = None

        self.tags = None

        self.results = dict(changed=False, state=dict())
        self.cgmodels = None

        required_if = [
            ('state', 'present', ['containers'])
        ]

        super(AzureRMContainerInstance, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                       supports_check_mode=True,
                                                       supports_tags=True,
                                                       required_if=required_if)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        resource_group = None
        response = None
        results = dict()

        # since this client hasn't been upgraded to expose models directly off the OperationClass, fish them out
        self.cgmodels = self.containerinstance_client.container_groups.models

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
                update_tags, newtags = self.update_tags(response.get('tags', dict()))
                if update_tags:
                    self.tags = newtags

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
            self.results['ip_address'] = response['ip_address']['ip'] if 'ip_address' in response else ''

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

        containers = []
        all_ports = set([])
        for container_def in self.containers:
            name = container_def.get("name")
            image = container_def.get("image")
            memory = container_def.get("memory")
            cpu = container_def.get("cpu")
            commands = container_def.get("commands")
            ports = []
            variables = []

            port_list = container_def.get("ports")
            if port_list:
                for port in port_list:
                    all_ports.add(port)
                    ports.append(self.cgmodels.ContainerPort(port=port))

            variable_list = container_def.get("environment_variables")
            if variable_list:
                for variable in variable_list:
                    variables.append(self.cgmodels.EnvironmentVariable(name=variable.get('name'),
                                                                       value=variable.get('value') if not variable.get('is_secure') else None,
                                                                       secure_value=variable.get('value') if variable.get('is_secure') else None))

            containers.append(self.cgmodels.Container(name=name,
                                                      image=image,
                                                      resources=self.cgmodels.ResourceRequirements(
                                                          requests=self.cgmodels.ResourceRequests(memory_in_gb=memory, cpu=cpu)
                                                      ),
                                                      ports=ports,
                                                      command=commands,
                                                      environment_variables=variables))

        if self.ip_address == 'public':
            # get list of ports
            if len(all_ports) > 0:
                ports = []
                for port in all_ports:
                    ports.append(self.cgmodels.Port(port=port, protocol="TCP"))
                ip_address = self.cgmodels.IpAddress(ports=ports, dns_name_label=self.dns_name_label, type='public')

        parameters = self.cgmodels.ContainerGroup(location=self.location,
                                                  containers=containers,
                                                  image_registry_credentials=registry_credentials,
                                                  restart_policy=_snake_to_camel(self.restart_policy, True) if self.restart_policy else None,
                                                  ip_address=ip_address,
                                                  os_type=self.os_type,
                                                  volumes=None,
                                                  tags=self.tags)

        try:
            response = self.containerinstance_client.container_groups.create_or_update(resource_group_name=self.resource_group,
                                                                                       container_group_name=self.name,
                                                                                       container_group=parameters)
            if isinstance(response, LROPoller):
                response = self.get_poller_result(response)
        except CloudError as exc:
            self.fail("Error when creating ACI {0}: {1}".format(self.name, exc.message or str(exc)))

        return response.as_dict()

    def delete_containerinstance(self):
        '''
        Deletes the specified container group instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the container instance {0}".format(self.name))
        try:
            response = self.containerinstance_client.container_groups.delete(resource_group_name=self.resource_group, container_group_name=self.name)
            return True
        except CloudError as exc:
            self.fail('Error when deleting ACI {0}: {1}'.format(self.name, exc.message or str(exc)))
            return False

    def get_containerinstance(self):
        '''
        Gets the properties of the specified container service.

        :return: deserialized container instance state dictionary
        '''
        self.log("Checking if the container instance {0} is present".format(self.name))
        found = False
        try:
            response = self.containerinstance_client.container_groups.get(resource_group_name=self.resource_group, container_group_name=self.name)
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
