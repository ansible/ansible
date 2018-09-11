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
    default: null
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
from ansible.module_utils.basic import AnsibleModule
try:
    from pylxca import connect
    from pylxca import disconnect
    from pylxca import jobs
    HAS_PYLXCA = True
except Exception:
    HAS_PYLXCA = False


SUCCESS_MSG = "Success %s result"
__changed__ = False
PYLXCA_REQUIRED = 'Lenovo xClarity Administrator Python Client pylxca is required for this module.'


def has_pylxca(module):
    """
    Check pylxca is installed
    :param module:
    """
    if not HAS_PYLXCA:
        module.fail_json(msg=PYLXCA_REQUIRED)


def _jobs(module, lxca_con):
    return jobs(lxca_con, id=module.params['id'],
                state=module.params['job_state'])


def _jobs_by_uuid(module, lxca_con):
    return jobs(lxca_con, id=module.params['uuid'])


def _jobs_delete(module, lxca_con):
    global __changed__
    __changed__ = True
    return jobs(lxca_con, id=module.params['jobs_delete'])


def _jobs_cancel(module, lxca_con):
    global __changed__
    __changed__ = True
    return jobs(lxca_con, id=module.params['jobs_cancel'])


def setup_module_object():
    """
    this function merge argument spec and create ansible module object
    :return:
    """
    args_spec = dict(LXCA_COMMON_ARGS)
    args_spec.update(INPUT_ARG_SPEC)
    module = AnsibleModule(argument_spec=args_spec, supports_check_mode=False)

    return module


def setup_conn(module):
    """
    this function create connection to LXCA
    :param module:
    :return:  lxca connection
    """
    lxca_con = None
    try:
        lxca_con = connect(module.params['auth_url'],
                           module.params['login_user'],
                           module.params['login_password'],
                           module.params['noverify'], )
    except Exception as exception:
        error_msg = '; '.join((e) for e in exception.args)
        module.fail_json(msg=error_msg, exception=traceback.format_exc())
    return lxca_con


def validate_parameters(module):
    """
    validate parameters mostly it will be place holder
    :param module:
    """
    pass


FUNC_DICT = {
    'jobs': _jobs,
    'jobs_by_uuid': _jobs_by_uuid,
    'jobs_delete': _jobs_delete,
    'Jobs_cancel': _jobs_cancel,
}


LXCA_COMMON_ARGS = dict(
    login_user=dict(required=True),
    login_password=dict(required=True, no_log=True),
    auth_url=dict(required=True),
    noverify=dict(default=True)
)

INPUT_ARG_SPEC = dict(
    command_options=dict(default='jobs', choices=list(FUNC_DICT)),
    id=dict(default=None),
    uuid=dict(default=None),
    job_state=dict(default=None, choices=[None, 'Pending', 'Running', 'Complete',
                                          'Cancelled', 'Running_With_Errors',
                                          'Cancelled_With_Errors',
                                          'Stopped_With_Error', 'Interrupted']),
    delete=dict(default=None),
    cancel=dict(default=None))


def execute_module(module, lxca_con):
    """
    This function invoke commands
    :param module: Ansible module object
    :param lxca_con:  lxca connection object
    """
    try:
        result = FUNC_DICT[module.params['command_options']](module, lxca_con)
        disconnect(lxca_con)
        module.exit_json(changed=__changed__,
                         msg=SUCCESS_MSG % module.params['command_options'],
                         result=result)
    except Exception as exception:
        error_msg = '; '.join((e) for e in exception.args)

        module.fail_json(msg=error_msg, exception=traceback.format_exc())


def run_tasks(module, lxca_con):
    """

    :param module: Ansible module object
    :param lxca_con:  lxca connection object
    """
    execute_module(module, lxca_con)


def main():
    module = setup_module_object()
    has_pylxca(module)
    validate_parameters(module)
    lxca_con = setup_conn(module)
    run_tasks(module, lxca_con)


if __name__ == '__main__':
    main()
