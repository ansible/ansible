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
module: azure_rm_devtestlabschedule
version_added: "2.8"
short_description: Manage Azure DevTest Lab Schedule instance.
description:
    - Create, update and delete instance of Azure DecTest Lab Schedule.

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
            - The name of the schedule.
        required: True
        choices:
            - lab_vms_startup
            - lab_vms_shutdown
    time:
        description:
            - The time of day the schedule will occur.
    time_zone_id:
        description:
            - The time zone ID.
    state:
      description:
        - Assert the state of the Schedule.
        - Use C(present) to create or update an Schedule and C(absent) to delete it.
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
  - name: Create (or update) DevTest Lab Schedule
    azure_rm_devtestlabschedule:
      resource_group: myResourceGroup
      lab_name: myLab
      name: lab_vms_shutdown
      time: "1030"
      time_zone_id: "UTC+12"
'''

RETURN = '''
id:
    description:
        - The identifier of the resource.
    returned: always
    type: str
    sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourcegroups/myResourceGroup/providers/microsoft.devtestlab/labs/myLab/schedules/l
             abVmsShutdown"
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


class AzureRMSchedule(AzureRMModuleBase):
    """Configuration class for an Azure RM Schedule resource"""

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
                required=True,
                choices=['lab_vms_startup', 'lab_vms_shutdown']
            ),
            time=dict(
                type='str'
            ),
            time_zone_id=dict(
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
        self.schedule = dict()

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.to_do = Actions.NoAction

        required_if = [
            ('state', 'present', ['time', 'time_zone_id'])
        ]

        super(AzureRMSchedule, self).__init__(derived_arg_spec=self.module_arg_spec,
                                              supports_check_mode=True,
                                              supports_tags=True,
                                              required_if=required_if)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                self.schedule[key] = kwargs[key]

        self.schedule['status'] = "Enabled"

        if self.name == 'lab_vms_startup':
            self.name = 'LabVmsStartup'
            self.schedule['task_type'] = 'LabVmsStartupTask'
        elif self.name == 'lab_vms_shutdown':
            self.name = 'LabVmsShutdown'
            self.schedule['task_type'] = 'LabVmsShutdownTask'

        if self.state == 'present':
            self.schedule['daily_recurrence'] = {'time': self.schedule.pop('time')}
            self.schedule['time_zone_id'] = self.schedule['time_zone_id'].upper()

        response = None

        self.mgmt_client = self.get_mgmt_svc_client(DevTestLabsClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        resource_group = self.get_resource_group(self.resource_group)

        old_response = self.get_schedule()

        if not old_response:
            self.log("Schedule instance doesn't exist")
            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log("Schedule instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                if (not default_compare(self.schedule, old_response, '', self.results)):
                    self.to_do = Actions.Update

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the Schedule instance")

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_schedule()

            self.results['changed'] = True
            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("Schedule instance deleted")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_schedule()
            # This currently doesn't work as there is a bug in SDK / Service
            if isinstance(response, LROPoller) or isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)
        else:
            self.log("Schedule instance unchanged")
            self.results['changed'] = False
            response = old_response

        if self.state == 'present':
            self.results.update({
                'id': response.get('id', None)
            })
        return self.results

    def create_update_schedule(self):
        '''
        Creates or updates Schedule with the specified configuration.

        :return: deserialized Schedule instance state dictionary
        '''
        self.log("Creating / Updating the Schedule instance {0}".format(self.name))

        try:
            response = self.mgmt_client.schedules.create_or_update(resource_group_name=self.resource_group,
                                                                   lab_name=self.lab_name,
                                                                   name=self.name,
                                                                   schedule=self.schedule)
            if isinstance(response, LROPoller) or isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the Schedule instance.')
            self.fail("Error creating the Schedule instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_schedule(self):
        '''
        Deletes specified Schedule instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the Schedule instance {0}".format(self.name))
        try:
            response = self.mgmt_client.schedules.delete(resource_group_name=self.resource_group,
                                                         lab_name=self.lab_name,
                                                         name=self.name)
        except CloudError as e:
            self.log('Error attempting to delete the Schedule instance.')
            self.fail("Error deleting the Schedule instance: {0}".format(str(e)))

        return True

    def get_schedule(self):
        '''
        Gets the properties of the specified Schedule.

        :return: deserialized Schedule instance state dictionary
        '''
        self.log("Checking if the Schedule instance {0} is present".format(self.name))
        found = False
        try:
            response = self.mgmt_client.schedules.get(resource_group_name=self.resource_group,
                                                      lab_name=self.lab_name,
                                                      name=self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("Schedule instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the Schedule instance.')
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


def main():
    """Main execution"""
    AzureRMSchedule()


if __name__ == '__main__':
    main()
