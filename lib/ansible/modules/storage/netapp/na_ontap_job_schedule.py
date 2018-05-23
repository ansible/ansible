#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: na_ontap_job_schedule
short_description: Manage NetApp Ontap Job Schedule
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author:
- Archana Ganesan (garchana@netapp.com), Suhas Bangalore Shekar (bsuhas@netapp.com)
description:
- Create/Delete/Modify_minute job-schedules on ONTAP
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
      -1 represents all minutes and
       only supported for cron schedule create and modify.
      Range is [-1..59]
'''

EXAMPLES = """
    - name: Create Job
      na_ontap_job_schedule:
        state: present
        name: jobName
        job_minutes: jobMinutes
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
    - name: Delete Job
      na_ontap_job_schedule:
        state: present
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

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPJob(object):
    '''Class with job schedule cron methods'''

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, type='str', choices=[
                       'present', 'absent'], default='present'),
            name=dict(required=True, type='str'),
            job_minutes=dict(required=False, type='int'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['name', 'job_minutes'])
            ],
            supports_check_mode=True
        )

        parameters = self.module.params

        # set up state variables
        self.state = parameters['state']
        self.name = parameters['name']
        self.job_minutes = parameters['job_minutes']

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
        job_get_iter = netapp_utils.zapi.NaElement(
            'job-schedule-cron-get-iter')
        job_schedule_info = netapp_utils.zapi.NaElement(
            'job-schedule-cron-info')
        job_schedule_info.add_new_child('job-schedule-name', self.name)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(job_schedule_info)
        job_get_iter.add_child_elem(query)
        result = self.server.invoke_successfully(job_get_iter, True)
        return_value = None
        # check if job exists
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) >= 1:
            job_exists_info = result.get_child_by_name('attributes-list').\
                get_child_by_name('job-schedule-cron-info')
            return_value = {
                'name': job_exists_info.get_child_content('job-schedule-name'),
                'job_minutes': job_exists_info.get_child_by_name(
                    'job-schedule-cron-minute')
                .get_child_content('cron-minute')
            }
        return return_value

    def create_job_schedule(self):
        """
        Creates a job schedule
        """
        job_schedule_create = netapp_utils.zapi\
            .NaElement.create_node_with_children(
                'job-schedule-cron-create',
                **{'job-schedule-name': self.name})
        job_schedule_create.add_node_with_children(
            'job-schedule-cron-minute',
            **{'cron-minute': str(self.job_minutes)})
        try:
            self.server.invoke_successfully(job_schedule_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating job schedule %s: %s'
                                  % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def delete_job_schedule(self):
        """
        Delete a job schedule
        """
        job_schedule_delete = netapp_utils.zapi\
            .NaElement.create_node_with_children(
                'job-schedule-cron-destroy',
                **{'job-schedule-name': self.name})
        try:
            self.server.invoke_successfully(job_schedule_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting job schedule %s: %s'
                                  % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def modify_minute_job_schedule(self):
        """
        modify a job schedule
        """
        job_schedule_modify_minute = netapp_utils.zapi\
            .NaElement.create_node_with_children(
                'job-schedule-cron-modify',
                **{'job-schedule-name': self.name})
        job_schedule_modify_minute.add_node_with_children(
            'job-schedule-cron-minute',
            **{'cron-minute': str(self.job_minutes)})
        try:
            self.server.invoke_successfully(job_schedule_modify_minute,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying job schedule %s: %s'
                                  % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Apply action to job-schedule
        """
        changed = False
        job_schedule_exists = False
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_ontap_zapi(
            module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_job_schedule", cserver)
        job_details = self.get_job_schedule()
        if job_details:
            job_schedule_exists = True
            if self.state == 'absent':  # delete
                changed = True
            elif self.state == 'present':  # modify
                if job_details['job_minutes'] != str(self.job_minutes):
                    changed = True
        else:
            if self.state == 'present':  # create
                changed = True
        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':  # execute create
                    if not job_schedule_exists:
                        self.create_job_schedule()
                    else:  # execute modify minute
                        self.modify_minute_job_schedule()
                elif self.state == 'absent':  # execute delete
                    self.delete_job_schedule()
        self.module.exit_json(changed=changed)


def main():
    '''Execute action'''
    job_obj = NetAppONTAPJob()
    job_obj.apply()


if __name__ == '__main__':
    main()
