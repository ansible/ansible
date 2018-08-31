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
module: lxca_scalablesystem
short_description: Custom module for lxca scalablesystem inventory utility
description:
  - This module returns/displays a inventory details of scalablesystem

options:
  id:
    description:
      id of scalable complex,

  command_options:
    description:
      options to filter scalablesystem information
    default: scalablesystem
    choices:
        - scalablesystem

  device_type:
    description:
      scalable complex device type
    default: None
    choices:
      - None
      - flex
      - rackserver

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# get all scalablesystem info
- name: get scalablesystem data from LXCA
  lxca_scalablesystem:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"

# get specific scalablesystem info by id
- name: get scalablesystem data from LXCA
  lxca_scalablesystem:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    id: "12"
    command_options: scalablesystem

# get specific scalablesystem info by device_type
- name: get scalablesystem data from LXCA
  lxca_scalablesystem:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    device_type: "flex"
    chassis: "3C737AA5E31640CE949B10C129A8B01F"
    command_options: scalablesystem

# get specific scalablesystem info by device_type and id
- name: get scalablesystem data from LXCA
  lxca_scalablesystem:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    id: "12"
    device_type: "flex"
    chassis: "3C737AA5E31640CE949B10C129A8B01F"
    command_options: scalablesystem

'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import scalablesystem


class ScalablesystemModule(LXCAModuleBase):
    '''
    This class fetch information about scalablesystem in lxca
    '''

    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'scalablesystem': self._scalablesystem,
        }
        args_spec = dict(
            command_options=dict(default='scalablesystem', choices=list(self.func_dict)),
            id=dict(default=None),
            device_type=dict(default=None, choices=[None, 'flex', 'rackserver'])
        )
        super(ScalablesystemModule, self).__init__(input_args_spec=args_spec)
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

    def _scalablesystem(self):
        return scalablesystem(self.lxca_con,
                              id=self.module.params['id'],
                              type=self.module.params['device_type'])


def main():
    ScalablesystemModule().run()


if __name__ == '__main__':
    main()
