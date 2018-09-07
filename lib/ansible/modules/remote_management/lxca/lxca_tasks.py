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
module: lxca_tasks
short_description: Custom module for lxca tasks inventory utility
description:
  - This module returns/displays a inventory details of tasks

options:
  id:
    description:
      id of lxca task jobUID,

  lxca_action:
    description:
      - action performed on lxca tasks
    choices:
      - None
      - cancel
      - update
      - delete

  update_list:
    description:
      - used with command task to update task status this is used with action=update
      - example
        [{'jobUID':'9','percentage':50},{'jobUID':'8','percentage':50}]"


  command_options:
    description:
      options to filter tasks information
    default: tasks
    choices:
        - tasks

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# get all tasks info
- name: get tasks data from LXCA
  lxca_tasks:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"

# get specific tasks info by id
- name: get tasks data from LXCA
  lxca_tasks:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    id: "12"
    command_options: tasks

# delete tasks
- name: delete tasks data from LXCA
  lxca_tasks:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    id: "12"
    lxca_action: delete
    command_options: tasks

# cancel tasks
- name: cancel tasks data from LXCA
  lxca_tasks:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    cancel: "12"
    lxca_action: cancel
    command_options: tasks

'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from pylxca import tasks
from pylxca import connect
from pylxca import disconnect


SUCCESS_MSG = "Success %s result"
__changed__ = False


def _tasks(module, lxca_con):
    result = None
    tasks_dict = {}
    job_uid = module.params["id"]
    action = module.params["lxca_action"]
    if action in ['cancel', 'delete']:
        tasks_dict['jobUID'] = job_uid
        tasks_dict['action'] = action
        _changed = True
    elif action in ['update']:
        tasks_dict['action'] = action
        update_list = module.params["update_list"]
        tasks_dict['updateList'] = update_list
        _changed__ = True
    else:
        tasks_dict['jobUID'] = job_uid

    result = tasks(lxca_con, **tasks_dict)
    return result


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
    'tasks': _tasks,
}


LXCA_COMMON_ARGS = dict(
    login_user=dict(required=True),
    login_password=dict(required=True, no_log=True),
    auth_url=dict(required=True),
    noverify=dict(default=True)
)

INPUT_ARG_SPEC = dict(
    command_options=dict(default='tasks', choices=list(FUNC_DICT)),
    id=dict(default=None),
    lxca_action=dict(default=None, choices=[None, 'cancel', 'delete', 'update']),
    update_list=dict(default=None, type=('list')),
)


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
        disconnect(lxca_con)
        module.fail_json(msg=error_msg, exception=traceback.format_exc())


def run_tasks(module, lxca_con):
    """

    :param module: Ansible module object
    :param lxca_con:  lxca connection object
    """
    execute_module(module, lxca_con)


def main():
    module = setup_module_object()
    validate_parameters(module)
    lxca_con = setup_conn(module)
    run_tasks(module, lxca_con)


if __name__ == '__main__':
    main()
