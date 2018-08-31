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
module: lxca_switches
short_description: Custom module for lxca switches inventory utility
description:
  - This module returns/displays a inventory details of switches and enable/disable ports

options:
  uuid:
    description:
      uuid of device, this is string with length greater than 16.

  command_options:
    description:
      options to filter switches information
    default: switches
    choices:
      - switches
      - switches_by_uuid
      - switches_by_chassis_uuid
      - switches_list_ports
      - switches_change_status_of_ports

  chassis:
    description:
      uuid of chassis, this is string with length greater than 16.

  ports:
    description:
      ports of switch to operate on its comma separated string.

  ports_action:
    description:
      enable or disable ports of switch.
    choices:
      - None
      - enable
      - disable

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# get all switches info
- name: get switches data from LXCA
  lxca_switches:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"

# get specific switches info by uuid
- name: get switches data from LXCA
  lxca_switches:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    uuid: "3C737AA5E31640CE949B10C129A8B01F"
    command_options: switches_by_uuid

# get specific switches info by chassis uuid
- name: get switches data from LXCA
  lxca_switches:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    chassis: "3C737AA5E31640CE949B10C129A8B01F"
    command_options: switches_by_chassis_uuid

# get switches ports
- name: get all switches port data from LXCA
  lxca_switches:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    command_options: switches_list_ports

# get particular switch ports
- name: get particular switch ports detailed data from LXCA
  lxca_switches:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    uuid: "3C737AA5E31640CE949B10C129A8B01F"
    command_options: switches_list_ports

# Update switch ports
- name: Update switch ports from LXCA
  lxca_switches:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    uuid: "3C737AA5E31640CE949B10C129A8B01F"
    ports_action = enabled
    ports = [1,3]
    command_options: switches_change_status_of_ports

'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import switches


class SwitchesModule(LXCAModuleBase):
    '''
    This class fetch information about switches in lxca
    '''

    UUID_REQUIRED = 'UUID of device is required for switches_by_uuid command.'
    UUID_REQUIRED_FOR_PORTS_ACTION = 'UUID of device is required for switches_change_status_of_ports command.'

    CHASSIS_UUID_REQUIRED = 'UUID of chassis is required for switches_by_chassis_uuid command.'
    PORTS_ACTION_REQUIRED = 'ports_action is required for switches_change_status_of_ports command.'
    PORTS_REQUIRED = 'ports is required for switches_change_status_of_ports command.'
    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'switches': self._switches,
            'switches_by_uuid': self._switches_by_uuid,
            'switches_by_chassis_uuid': self._switches_by_chassis_uuid,
            'switches_list_ports': self.switches_list_ports,
            'switches_change_status_of_ports': self.switches_change_status_of_ports,
        }
        args_spec = dict(
            command_options=dict(default='switches', choices=list(self.func_dict)),
            uuid=dict(default=None),
            chassis=dict(default=None),
            ports=dict(default=None),
            ports_action=dict(default=None, choices=[None, 'enable', 'disable'])
        )
        super(SwitchesModule, self).__init__(input_args_spec=args_spec)
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

    def _switches(self):
        return switches(self.lxca_con)

    def _switches_by_uuid(self):
        if not self.module.params['uuid']:
            self.module.fail_json(msg=self.UUID_REQUIRED)
        return switches(self.lxca_con, uuid=self.module.params['uuid'])

    def _switches_by_chassis_uuid(self):
        if not self.module.params['chassis']:
            self.module.fail_json(msg=self.CHASSIS_UUID_REQUIRED)
        return switches(self.lxca_con, chassis=self.module.params['chassis'])

    def switches_list_ports(self):
        return switches(self.lxca_con, uuid=self.module.params['uuid'], ports="")

    def switches_change_status_of_ports(self):
        if not self.module.params['uuid']:
            self.module.fail_json(msg=self.UUID_REQUIRED_FOR_PORTS_ACTION)
        if not self.module.params['ports_action']:
            self.module.fail_json(msg=self.PORTS_ACTION_REQUIRED)
        if not self.module.params['ports']:
            self.module.fail_json(msg=self.PORTS_REQUIRED)

        self._changed = True
        return switches(self.lxca_con, uuid=self.module.params['uuid'],
                        ports=self.module.params['ports'],
                        action=self.module.params['ports_action'])


def main():
    SwitchesModule().run()


if __name__ == '__main__':
    main()
