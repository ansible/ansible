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
module: lxca_users
short_description: Custom module for lxca users inventory utility
description:
  - This module returns/displays a inventory details of users

options:
  id:
    description:
      id of lxca user,

  command_options:
    description:
      options to filter users information
    default: users
    choices:
        - users

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# get all users info
- name: get users data from LXCA
  lxca_users:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"

# get specific users info by id
- name: get users data from LXCA
  lxca_users:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    id: "12"
    command_options: users

'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import users


class UsersModule(LXCAModuleBase):
    '''
    This class fetch information about users in lxca
    '''

    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'users': self._users,
        }
        args_spec = dict(
            command_options=dict(default='users', choices=list(self.func_dict)),
            id=dict(default=None),
        )
        super(UsersModule, self).__init__(input_args_spec=args_spec)
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

    def _users(self):
        return users(self.lxca_con, id=self.module.params['id'])


def main():
    UsersModule().run()


if __name__ == '__main__':
    main()
