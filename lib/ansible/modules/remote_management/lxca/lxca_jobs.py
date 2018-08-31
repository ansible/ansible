#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'supported_by': 'community',
    'status': ['preview']
}


DOCUMENTATION = '''
---
version_added: "1.1"
author:
  - Naval Patel (@navalkp)
  - Prashant Bhosale (@prabhosa)
module: lxca_jobs
short_description: Custom module for lxca jobs inventory utility
description:
  - This module returns/displays a inventory details of jobs

options:
  id:
    description:
      id of lxca job,

  uuid:
    description:
      uuid of device, Jobs for this uuid, uuid amd job_state are mutually exclusive

  delete:
    description:
      id of job to delete

  cancel:
    description:
      id of job to cancel

  job_state:
    description:
      state of job
    default: None
    choices:
      - None
      - Pending
      - Running
      - Complete
      - Cancelled
      - Running_With_Errors
      - Cancelled_With_Errors
      - Stopped_With_Error
      - Interrupted

  command_options:
    description:
      options to filter jobs information
    default: jobs
    choices:
        - jobs
        - jobs_by_uuid
        - jobs_delete
        - Jobs_cancel

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# get all jobs info
- name: get jobs data from LXCA
  lxca_jobs:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"

# get specific jobs info by id
- name: get jobs data from LXCA
  lxca_jobs:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    id: "12"
    command_options: jobs

# get jobs info by state
- name: get jobs data from LXCA
  lxca_jobs:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    job_state: "Complete"
    command_options: jobs

# get jobs info by id and state
- name: get jobs data from LXCA
  lxca_jobs:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    job_state: "Complete"
    id: "12"
    command_options: jobs

# get jobs info by uuid
- name: get jobs data from LXCA
  lxca_jobs:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    uuid: "3C737AA5E31640CE949B10C129A8B01F"
    command_options: jobs

# delete jobs
- name: delete jobs data from LXCA
  lxca_jobs:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    delete: "12"
    command_options: jobs_delete

# cancel jobs
- name: cancel jobs data from LXCA
  lxca_jobs:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    cancel: "12"
    command_options: jobs_cancel

'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import jobs


class JobsModule(LXCAModuleBase):
    '''
    This class fetch information about jobs in lxca
    '''
    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'jobs': self._jobs,
            'jobs_delete':self._jobs_delete,
            'Jobs_cancel':self._jobs_cancel,
        }
        args_spec = dict(
            command_options=dict(default='jobs', choices=list(self.func_dict)),
            id=dict(default=None),
            uuid=dict(default=None),
            job_state=dict(default=None, choices=[None, 'Pending', 'Running', 'Complete',
                                                  'Cancelled', 'Running_With_Errors', 'Cancelled_With_Errors',
                                                  'Stopped_With_Error', 'Interrupted']),
            delete = dict(default=None),
            cancel = dict(default=None),
        )
        super(JobsModule, self).__init__(input_args_spec=args_spec)
        self._changed = False

    def execute_module(self):
        try:
            result = self.func_dict[self.module.params['command_options']]()
            return dict(changed=self._changed,
                        msg=self.SUCCESS_MSG % self.module.params['command_options'],
                        result=result)
        except Exception as exception:
            error_msg = '; '.join((e) for e in exception.args)
            self.module.fail_json(msg=error_msg, exception=traceback.format_exc())

    def _jobs(self):
        return jobs(self.lxca_con, id=self.module.params['id'],
                    state = self.module.params['job_state'])

    def _jobs_by_uuid(self):
        return jobs(self.lxca_con, id=self.module.params['uuid'])

    def _jobs_delete(self):
        self._changed = True
        return jobs(self.lxca_con, id=self.module.params['jobs_delete'])

    def _jobs_cancel(self):
        self._changed = True
        return jobs(self.lxca_con, id=self.module.params['jobs_cancel'])

def main():
    JobsModule().run()


if __name__ == '__main__':
    main()
