#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
module: na_ontap_job_schedule
short_description: NetApp ONTAP Job Schedule
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Create/Delete/Modify job-schedules on ONTAP
options:
  state:
    description:
    - Whether the specified job schedule should exist or not.
    choices: ['present', 'absent']
    default: present
  name:
    description:
    - The name of the job-schedule to manage.
    required: true
  job_minutes:
    description:
    - The minute(s) of each hour when the job should be run.
      Job Manager cron scheduling minute.
      -1 represents all minutes and is
      only supported for cron schedule create and modify.
      Range is [-1..59]
    type: list
  job_hours:
    version_added: '2.8'
    description:
    - The hour(s) of the day when the job should be run.
      Job Manager cron scheduling hour.
      -1 represents all hours and is
      only supported for cron schedule create and modify.
      Range is [-1..23]
    type: list
  job_months:
    version_added: '2.8'
    description:
    - The month(s) when the job should be run.
      Job Manager cron scheduling month.
      -1 represents all months and is
      only supported for cron schedule create and modify.
      Range is [-1..11]
    type: list
  job_days_of_month:
    version_added: '2.8'
    description:
    - The day(s) of the month when the job should be run.
      Job Manager cron scheduling day of month.
      -1 represents all days of a month from 1 to 31, and is
      only supported for cron schedule create and modify.
      Range is [-1..31]
    type: list
  job_days_of_week:
    version_added: '2.8'
    description:
    - The day(s) in the week when the job should be run.
      Job Manager cron scheduling day of week.
      Zero represents Sunday. -1 represents all days of a week and is
      only supported for cron schedule create and modify.
      Range is [-1..6]
    type: list
'''

EXAMPLES = """
    - name: Create Job for 11.30PM at 10th of every month
      na_ontap_job_schedule:
        state: present
        name: jobName
        job_minutes: 30
        job_hours: 23
        job_days_of_month: 10
        job_months: -1
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
    - name: Delete Job
      na_ontap_job_schedule:
        state: absent
        name: jobName
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
"""

RETURN = """

"""


import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPJob(object):
    '''Class with job schedule cron methods'''

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=[
                       'present', 'absent'], default='present'),
            name=dict(required=True, type='str'),
            job_minutes=dict(required=False, type='list'),
            job_months=dict(required=False, type='list'),
            job_hours=dict(required=False, type='list'),
            job_days_of_month=dict(required=False, type='list'),
            job_days_of_week=dict(required=False, type='list')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        self.set_playbook_zapi_key_map()

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def set_playbook_zapi_key_map(self):
        self.na_helper.zapi_string_keys = {
            'name': 'job-schedule-name',
        }
        self.na_helper.zapi_list_keys = {
            'job_minutes': ('job-schedule-cron-minute', 'cron-minute'),
            'job_months': ('job-schedule-cron-month', 'cron-month'),
            'job_hours': ('job-schedule-cron-hour', 'cron-hour'),
            'job_days_of_month': ('job-schedule-cron-day', 'cron-day-of-month'),
            'job_days_of_week': ('job-schedule-cron-day-of-week', 'cron-day-of-week')
        }

    def get_job_schedule(self):
        """
        Return details about the job
        :param:
            name : Job name
        :return: Details about the Job. None if not found.
        :rtype: dict
        """
        job_get_iter = netapp_utils.zapi.NaElement('job-schedule-cron-get-iter')
        job_get_iter.translate_struct({
            'query': {
                'job-schedule-cron-info': {
                    'job-schedule-name': self.parameters['name']
                }
            }
        })
        result = self.server.invoke_successfully(job_get_iter, True)
        job_details = None
        # check if job exists
        if result.get_child_by_name('num-records') and int(result['num-records']) >= 1:
            job_info = result['attributes-list']['job-schedule-cron-info']
            job_details = dict()
            for item_key, zapi_key in self.na_helper.zapi_string_keys.items():
                job_details[item_key] = job_info[zapi_key]
            for item_key, zapi_key in self.na_helper.zapi_list_keys.items():
                parent, dummy = zapi_key
                job_details[item_key] = self.na_helper.get_value_for_list(from_zapi=True,
                                                                          zapi_parent=job_info.get_child_by_name(parent)
                                                                          )
                # if any of the job_hours, job_minutes, job_months, job_days are empty:
                # it means the value is -1 for ZAPI
                if not job_details[item_key]:
                    job_details[item_key] = ['-1']
        return job_details

    def add_job_details(self, na_element_object, values):
        """
        Add children node for create or modify NaElement object
        :param na_element_object: modif or create NaElement object
        :param values: dictionary of cron values to be added
        :return: None
        """
        for item_key in values:
            if item_key in self.na_helper.zapi_string_keys:
                zapi_key = self.na_helper.zapi_string_keys.get(item_key)
                na_element_object[zapi_key] = values[item_key]
            elif item_key in self.na_helper.zapi_list_keys:
                parent_key, child_key = self.na_helper.zapi_list_keys.get(item_key)
                na_element_object.add_child_elem(self.na_helper.get_value_for_list(from_zapi=False,
                                                                                   zapi_parent=parent_key,
                                                                                   zapi_child=child_key,
                                                                                   data=values.get(item_key)))

    def create_job_schedule(self):
        """
        Creates a job schedule
        """
        # job_minutes is mandatory for create
        if self.parameters.get('job_minutes') is None:
            self.module.fail_json(msg='Error: missing required parameter job_minutes for create')

        job_schedule_create = netapp_utils.zapi.NaElement('job-schedule-cron-create')
        self.add_job_details(job_schedule_create, self.parameters)
        try:
            self.server.invoke_successfully(job_schedule_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating job schedule %s: %s'
                                  % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_job_schedule(self):
        """
        Delete a job schedule
        """
        job_schedule_delete = netapp_utils.zapi.NaElement('job-schedule-cron-destroy')
        self.add_job_details(job_schedule_delete, self.parameters)
        try:
            self.server.invoke_successfully(job_schedule_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting job schedule %s: %s'
                                  % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def modify_job_schedule(self, params):
        """
        modify a job schedule
        """
        job_schedule_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'job-schedule-cron-modify', **{'job-schedule-name': self.parameters['name']})
        self.add_job_details(job_schedule_modify, params)
        try:
            self.server.invoke_successfully(job_schedule_modify, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying job schedule %s: %s'
                                  % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def autosupport_log(self):
        """
        Autosupport log for job_schedule
        :return: None
        """
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_job_schedule", cserver)

    def apply(self):
        """
        Apply action to job-schedule
        """
        self.autosupport_log()
        current = self.get_job_schedule()
        action = self.na_helper.get_cd_action(current, self.parameters)
        if action is None and self.parameters['state'] == 'present':
            modify = self.na_helper.get_modified_attributes(current, self.parameters)

        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if action == 'create':
                    self.create_job_schedule()
                elif action == 'delete':
                    self.delete_job_schedule()
                elif modify:
                    self.modify_job_schedule(modify)
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    '''Execute action'''
    job_obj = NetAppONTAPJob()
    job_obj.apply()


if __name__ == '__main__':
    main()
