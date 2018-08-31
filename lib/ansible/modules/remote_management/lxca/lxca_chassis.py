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
module: lxca_chassis
short_description: Custom module for lxca chassis inventory utility
description:
  - This module returns/displays a inventory details of chassis

options:
  uuid:
    description:
      uuid of device, this is string with length greater than 16.

  command_options:
    description:
      options to filter nodes information
    default: nodes
    choices:
        - chassis
        - chassis_by_uuid
        - chassis_status_managed
        - chassis_status_unmanaged

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# get all chassis info
- name: get chassis data from LXCA
  lxca_chassis:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"

# get specific chassis info by uuid
- name: get chassis data from LXCA
  lxca_chassis:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    uuid: "3C737AA5E31640CE949B10C129A8B01F"
    command_options: chassis_by_uuid

# get managed chassis
- name: get chassis data from LXCA
  lxca_chassis:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    command_options: chassis_status_managed

# get unmanaged chassis
- name: get chassis data from LXCA
  lxca_chassis:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    command_options: chassis_status_managed

'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import chassis


class ChassisModule(LXCAModuleBase):
    '''
    This class fetch information about nodes in lxca
    '''

    UUID_REQUIRED = 'UUID of device is required for chassis_by_uuid command.'
    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'chassis': self._chassis,
            'chassis_by_uuid': self._chassis_by_uuid,
            'chassis_status_managed': self._chassis_status_managed,
            'chassis_status_unmanaged': self._chassis_status_unmanaged

        }
        args_spec = dict(
            command_options=dict(default='chassis', choices=list(self.func_dict)),
            uuid=dict(default=None), chassis=dict(default=None)
        )
        super(ChassisModule, self).__init__(input_args_spec=args_spec)
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

    def _chassis(self):
        return chassis(self.lxca_con)

    def _chassis_by_uuid(self):
        if not self.module.params['uuid']:
            self.module.fail_json(msg=self.UUID_REQUIRED)
        return chassis(self.lxca_con, self.module.params['uuid'])

    def _chassis_status_managed(self):
        return chassis(self.lxca_con, status='managed')

    def _chassis_status_unmanaged(self):
        return chassis(self.lxca_con, status='unmanaged')


def main():
    ChassisModule().run()


if __name__ == '__main__':
    main()
