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
module: lxca_storedcredentials
short_description: Custom module for lxca storedcredentials utility
description:
  - This module perform CRUD operations for stored credentials in  LXCA

options:

  storedcredential_id:
    description:
        stored credential id to be used for operation

  user:
    description:
      credential for login to device

  password:
    description:
      for login to device

  description:
    description:
      detail about storedcredential.

  command_options:
    description:
      options to stored credential information
    default: storedcredentials
    choices:
        - get_storedcredentials
        - create_storedcredentials
        - update_storedcredentials
        - delete_storedcredentials

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = r'''
# Get all storedcredentials from LXCA
- name: get all stored credentials
  lxca_storedcredentials:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    command_options: get_storedcredentials

# Get specific storedcredentials from LXCA
- name: get all stored credentials
  lxca_storedcredentials:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    storecredential_id: 123
    command_options: get_storedcredentials

# Create new storedcredentials from LXCA
- name: create new stored credentials
  lxca_storedcredentials:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    user: Tes12
    password: Test1212
    description: new user for test
    command_options: create_storedcredentials

# update storedcredentials on LXCA
- name: update stored credentials
  lxca_storedcredentials:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    storecredential_id: 123
    user: Test123
    password: Test123
    description: Updated password user for test123
    command_options: update_storedcredentials

# delete storedcredentials on LXCA
- name: delete stored credentials
  lxca_storedcredentials:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    storecredential_id: 123
    command_options: delete_storedcredentials

'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import storedcredentials
from pylxca import updatepolicy


class StoredcredentialsModule(LXCAModuleBase):
    '''
    This class fetch information about storedcredentials in lxca
    '''

    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'storedcredentials': self._get_storedcredentials,
            'get_storedcredentials': self._get_storedcredentials,
            'create_storedcredentials': self._create_storedcredentials,
            'update_storedcredentials': self._update_storedcredentials,
            'delete_storedcredentials': self._delete_storedcredentials
        }
        args_spec = dict(
            command_options=dict(default='storedcredentials', choices=list(self.func_dict)),
            user=dict(default=None),
            password=dict(default=None, no_log=True),
            description=dict(default=None),
            storecredential_id=dict(default=None),
        )
        super(StoredcredentialsModule, self).__init__(input_args_spec=args_spec)
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

    def _get_storedcredentials(self):
        result = storedcredentials(self.lxca_con,
                                   id=self.module.params.get('storedcredential_id'))
        return result

    def _create_storedcredentials(self):
        result = storedcredentials(self.lxca_con,
                                   user_name=self.module.params.get('user'),
                                   password=self.module.params.get('password'),
                                   description=self.module.params.get('description'))
        self._changed = True
        return result

    def _update_storedcredentials(self):
        result = storedcredentials(self.lxca_con,
                                   id=self.module.params.get('storedcredential_id'),
                                   user_name=self.module.params.get('user'),
                                   password=self.module.params.get('password'),
                                   description=self.module.params.get('description'))
        self._changed = True
        return result

    def _delete_storedcredentials(self):
        result = storedcredentials(self.lxca_con,
                                   id=self.module.params.get('storedcredential_id'))
        self._changed = True
        return result


def main():
    StoredcredentialsModule().run()


if __name__ == '__main__':
    main()
