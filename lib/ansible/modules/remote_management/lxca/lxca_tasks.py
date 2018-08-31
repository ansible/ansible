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
        - tasks_update
        - tasks_delete
        - tasks_cancel

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
    command_options: tasks_delete

# cancel tasks
- name: cancel tasks data from LXCA
  lxca_tasks:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    cancel: "12"
    lxca_action: cancel
    command_options: tasks_cancel

'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import tasks


class tasksModule(LXCAModuleBase):
    '''
    This class fetch information about tasks in lxca
    '''

    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'tasks': self._tasks,
        }
        args_spec = dict(
            command_options=dict(default='tasks', choices=list(self.func_dict)),
            id=dict(default=None),
            lxca_action=dict(default=None, choices=[None, 'cancel', 'delete', 'update']),
            update_list=dict(default=None, type=('list')),
        )
        super(tasksModule, self).__init__(input_args_spec=args_spec)
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

    def _tasks(self):
        result = None
        tasks_dict = {}
        job_uid = self.module.params["id"]
        action = self.module.params["lxca_action"]
        if action in ['cancel', 'delete']:
            tasks_dict['jobUID'] = job_uid
            tasks_dict['action'] = action
            self._changed = True
        elif action in ['update']:
            tasks_dict['action'] = action
            update_list = self.module.params["update_list"]
            tasks_dict['updateList'] = update_list
            self._changed__ = True
        else:
            tasks_dict['jobUID'] = job_uid

        result = tasks(self.lxca_con, **tasks_dict)
        return result

def main():
    tasksModule().run()


if __name__ == '__main__':
    main()
