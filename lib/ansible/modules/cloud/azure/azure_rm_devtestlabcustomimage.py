#!/usr/bin/python
#
# Copyright (c) 2019 Zim Kalinowski, (@zikalino)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_devtestlabcustomimage
version_added: "2.8"
short_description: Manage Azure DevTest Lab Custom Image instance.
description:
    - Create, update and delete instance of Azure DevTest Lab Custom Image.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    lab_name:
        description:
            - The name of the lab.
        required: True
    name:
        description:
            - The name of the custom image.
        required: True
    source_vm:
        description:
            - Source DevTest Lab virtual machine name.
    windows_os_state:
        description:
            - The state of the Windows OS.
        choices:
            - 'non_sysprepped'
            - 'sysprep_requested'
            - 'sysprep_applied'
    linux_os_state:
        description:
            - The state of the Linux OS.
        choices:
            - 'non_deprovisioned'
            - 'deprovision_requested'
            - 'deprovision_applied'
    description:
        description:
            - The description of the custom image.
    author:
        description:
            - The author of the custom image.
    state:
      description:
        - Assert the state of the Custom Image.
        - Use C(present) to create or update an Custom Image and C(absent) to delete it.
      default: present
      choices:
        - absent
        - present

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
- name: Create instance of DevTest Lab Image
  azure_rm_devtestlabcustomimage:
    resource_group: myResourceGroup
    lab_name: myLab
    name: myImage
    source_vm: myDevTestLabVm
    linux_os_state: non_deprovisioned
'''

RETURN = '''
id:
    description:
        - The identifier of the resource.
    returned: always
    type: str
    sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourcegroups/myResourceGroup/providers/microsoft.devtestlab/labs/myLab/images/myImage"
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.common.dict_transformations import _snake_to_camel

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.polling import LROPoller
    from msrestazure.azure_operation import AzureOperationPoller
    from azure.mgmt.devtestlabs import DevTestLabsClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMDtlCustomImage(AzureRMModuleBase):
    """Configuration class for an Azure RM Custom Image resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            lab_name=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str',
                required=True
            ),
            source_vm=dict(
                type='str'
            ),
            windows_os_state=dict(
                type='str',
                choices=['non_sysprepped',
                         'sysprep_requested',
                         'sysprep_applied']
            ),
            linux_os_state=dict(
                type='str',
                choices=['non_deprovisioned',
                         'deprovision_requested',
                         'deprovision_applied']
            ),
            description=dict(
                type='str'
            ),
            author=dict(
                type='str'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.lab_name = None
        self.name = None
        self.custom_image = dict()

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.to_do = Actions.NoAction

        required_if = [
            ('state', 'present', [
             'source_vm'])
        ]

        super(AzureRMDtlCustomImage, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                    supports_check_mode=True,
                                                    supports_tags=True,
                                                    required_if=required_if)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                self.custom_image[key] = kwargs[key]

        if self.state == 'present':
            windows_os_state = self.custom_image.pop('windows_os_state', False)
            linux_os_state = self.custom_image.pop('linux_os_state', False)
            source_vm_name = self.custom_image.pop('source_vm')
            temp = "/subscriptions/{0}/resourcegroups/{1}/providers/microsoft.devtestlab/labs/{2}/virtualmachines/{3}"
            self.custom_image['vm'] = {}
            self.custom_image['vm']['source_vm_id'] = temp.format(self.subscription_id, self.resource_group, self.lab_name, source_vm_name)
            if windows_os_state:
                self.custom_image['vm']['windows_os_info'] = {'windows_os_state': _snake_to_camel(windows_os_state, True)}
            elif linux_os_state:
                self.custom_image['vm']['linux_os_info'] = {'linux_os_state': _snake_to_camel(linux_os_state, True)}
            else:
                self.fail("Either 'linux_os_state' or 'linux_os_state' must be specified")

        response = None

        self.mgmt_client = self.get_mgmt_svc_client(DevTestLabsClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        old_response = self.get_customimage()

        if not old_response:
            self.log("Custom Image instance doesn't exist")
            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log("Custom Image instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                if (not default_compare(self.custom_image, old_response, '', self.results)):
                    self.to_do = Actions.Update

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the Custom Image instance")

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_customimage()

            self.results['changed'] = True
            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("Custom Image instance deleted")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_customimage()
            # This currently doesnt' work as there is a bug in SDK / Service
            if isinstance(response, LROPoller) or isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)
        else:
            self.log("Custom Image instance unchanged")
            self.results['changed'] = False
            response = old_response

        if self.state == 'present':
            self.results.update({
                'id': response.get('id', None)
            })
        return self.results

    def create_update_customimage(self):
        '''
        Creates or updates Custom Image with the specified configuration.

        :return: deserialized Custom Image instance state dictionary
        '''
        self.log("Creating / Updating the Custom Image instance {0}".format(self.name))

        try:
            response = self.mgmt_client.custom_images.create_or_update(resource_group_name=self.resource_group,
                                                                       lab_name=self.lab_name,
                                                                       name=self.name,
                                                                       custom_image=self.custom_image)
            if isinstance(response, LROPoller) or isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the Custom Image instance.')
            self.fail("Error creating the Custom Image instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_customimage(self):
        '''
        Deletes specified Custom Image instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the Custom Image instance {0}".format(self.name))
        try:
            response = self.mgmt_client.custom_images.delete(resource_group_name=self.resource_group,
                                                             lab_name=self.lab_name,
                                                             name=self.name)
        except CloudError as e:
            self.log('Error attempting to delete the Custom Image instance.')
            self.fail("Error deleting the Custom Image instance: {0}".format(str(e)))

        return True

    def get_customimage(self):
        '''
        Gets the properties of the specified Custom Image.

        :return: deserialized Custom Image instance state dictionary
        '''
        self.log("Checking if the Custom Image instance {0} is present".format(self.name))
        found = False
        try:
            response = self.mgmt_client.custom_images.get(resource_group_name=self.resource_group,
                                                          lab_name=self.lab_name,
                                                          name=self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("Custom Image instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the Custom Image instance.')
        if found is True:
            return response.as_dict()

        return False


def default_compare(new, old, path, result):
    if new is None:
        return True
    elif isinstance(new, dict):
        if not isinstance(old, dict):
            result['compare'] = 'changed [' + path + '] old dict is null'
            return False
        for k in new.keys():
            if not default_compare(new.get(k), old.get(k, None), path + '/' + k, result):
                return False
        return True
    elif isinstance(new, list):
        if not isinstance(old, list) or len(new) != len(old):
            result['compare'] = 'changed [' + path + '] length is different or null'
            return False
        if isinstance(old[0], dict):
            key = None
            if 'id' in old[0] and 'id' in new[0]:
                key = 'id'
            elif 'name' in old[0] and 'name' in new[0]:
                key = 'name'
            else:
                key = list(old[0])[0]
            new = sorted(new, key=lambda x: x.get(key, None))
            old = sorted(old, key=lambda x: x.get(key, None))
        else:
            new = sorted(new)
            old = sorted(old)
        for i in range(len(new)):
            if not default_compare(new[i], old[i], path + '/*', result):
                return False
        return True
    else:
        if path == '/location':
            new = new.replace(' ', '').lower()
            old = new.replace(' ', '').lower()
        if new == old:
            return True
        else:
            result['compare'] = 'changed [' + path + '] ' + str(new) + ' != ' + str(old)
            return False


def dict_camelize(d, path, camelize_first):
    if isinstance(d, list):
        for i in range(len(d)):
            dict_camelize(d[i], path, camelize_first)
    elif isinstance(d, dict):
        if len(path) == 1:
            old_value = d.get(path[0], None)
            if old_value is not None:
                d[path[0]] = _snake_to_camel(old_value, camelize_first)
        else:
            sd = d.get(path[0], None)
            if sd is not None:
                dict_camelize(sd, path[1:], camelize_first)


def main():
    """Main execution"""
    AzureRMDtlCustomImage()


if __name__ == '__main__':
    main()
