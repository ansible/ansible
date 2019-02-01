#!/usr/bin/python

# (c) 2018, NetApp, Inc
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
  job_hour:
    version_added: '2.8'
    description:
    - The hour(s) of the day when the job should be run.
      Job Manager cron scheduling hour.
      -1 represents all hours and is
      only supported for cron schedule create and modify.
      Range is [-1..23]
  job_month:
    version_added: '2.8'
    description:
    - The month(s) when the job should be run.
      Job Manager cron scheduling month.
      -1 represents all months and is
      only supported for cron schedule create and modify.
      Range is [-1..11]
  job_day_of_month:
    version_added: '2.8'
    description:
    - The day(s) of the month when the job should be run.
      Job Manager cron scheduling day of month.
      -1 represents all days of a month from 1 to 31, and is
      only supported for cron schedule create and modify.
      Range is [-1..31]
  job_day_of_week:
    version_added: '2.8'
    description:
    - The day(s) in the week when the job should be run.
      Job Manager cron scheduling day of week.
      Zero represents Sunday. -1 represents all days of a week and is
      only supported for cron schedule create and modify.
      Range is [-1..6]
'''

EXAMPLES = """
    - name: Create Job for 11.30PM at 10th of every month
      na_ontap_job_schedule:
        state: present
        name: jobName
        job_minutes: 30
        job_hour: 23
        job_day_of_month: 10
        job_month: -1
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
            job_minutes=dict(required=False, type='int'),
            job_month=dict(required=False, type='int'),
            job_hour=dict(required=False, type='int'),
            job_day_of_month=dict(required=False, type='int'),
            job_day_of_week=dict(required=False, type='int')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

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
            job_exists_info = result['attributes-list']['job-schedule-cron-info']
            job_details = {
                'name': job_exists_info.get_child_content('job-schedule-name'),
                'job_minutes': int(job_exists_info['job-schedule-cron-minute']['cron-minute']),
                # set default values to other job attributes (by default, cron runs on all months if months is empty)
                'job_hour': 0,
                'job_month': -1,
                'job_day_of_month': 0,
                'job_day_of_week': 0
            }
            if job_exists_info.get_child_by_name('job-schedule-cron-hour'):
                job_details['job_hour'] = int(job_exists_info['job-schedule-cron-hour']['cron-hour'])
            if job_exists_info.get_child_by_name('job-schedule-cron-month'):
                job_details['job_month'] = int(job_exists_info['job-schedule-cron-month']['cron-month'])
            if job_exists_info.get_child_by_name('job-schedule-cron-day'):
                job_details['job_day_of_month'] = int(job_exists_info['job-schedule-cron-day']['cron-day-of-month'])
            if job_exists_info.get_child_by_name('job-schedule-cron-day-of-week'):
                job_details['job_day_of_week'] = int(job_exists_info['job-schedule-cron-day-of-week']
                                                     ['cron-day-of-week'])
        return job_details

    def add_job_details(self, na_element_object, values):
        """
        Add children node for create or modify NaElement object
        :param na_element_object: modif or create NaElement object
        :param values: dictionary of cron values to be added
        :return: None
        """
        if values.get('job_minutes'):
            na_element_object.add_node_with_children(
                'job-schedule-cron-minute', **{'cron-minute': str(values['job_minutes'])})
        if values.get('job_hour'):
            na_element_object.add_node_with_children(
                'job-schedule-cron-hour', **{'cron-hour': str(values['job_hour'])})
        if values.get('job_month'):
            na_element_object.add_node_with_children(
                'job-schedule-cron-month', **{'cron-month': str(values['job_month'])})
        if values.get('job_day_of_month'):
            na_element_object.add_node_with_children(
                'job-schedule-cron-day', **{'cron-day-of-month': str(values['job_day_of_month'])})
        if values.get('job_day_of_week'):
            na_element_object.add_node_with_children(
                'job-schedule-cron-day-of-week', **{'cron-day-of-week': str(values['job_day_of_week'])})

    def create_job_schedule(self):
        """
        Creates a job schedule
        """
        # job_minutes is mandatory for create
        if self.parameters.get('job_minutes') is None:
            self.module.fail_json(msg='Error: missing required parameter job_minutes for create')

        job_schedule_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'job-schedule-cron-create', **{'job-schedule-name': self.parameters['name']})
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
        job_schedule_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'job-schedule-cron-destroy', **{'job-schedule-name': self.parameters['name']})
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
        cserver = netapp_utils.setup_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_job_schedule", cserver)

    def apply(self):
        """
        Apply action to job-schedule
        """
        self.autosupport_log()
        current = self.get_job_schedule()
        action = self.na_helper.get_cd_action(current, self.parameters)
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
