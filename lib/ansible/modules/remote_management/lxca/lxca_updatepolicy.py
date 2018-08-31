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
module: lxca_updatepolicy
short_description: Custom module for lxca update policy config utility
description:
  - This module update policy on LXCA

options:

  uuid:
    description:
      uuid of device, this is string with length greater than 16.

  jobid:
    description:
      Id of job, to get status of it

  policy_info:
    description:
      - used with command updatepolicy following values are possible
      - "FIRMWARE - Get List of Applicable Frimware policies"
      - "RESULTS - List  the persisted compare result for servers to which a policy is assigned"
      - "COMPARE_RESULTS -Check compliant with the assigned compliance policy using the job or task ID
                         that was returned when the compliance policy was assigned."
      - "NAMELIST -  Returns the available compliance policies"

    choices:
      - None
      - FIRMWARE
      - RESULTS
      - COMPARE_RESULTS
      - NAMELIST

  policy_name:
    description:
        used with command updatepolicy, name of policy to be applied

  policy_type:
    description:
      - used with command updatepolicy, policy applied to value specified it can have following value
      - CMM - Chassis Management Module
      - IOSwitch - Flex switch
      - RACKSWITCH - RackSwitch switch
      - STORAGE - Lenovo Storage system
      - SERVER - Compute node or rack server
    choices:
      - CMM
      - IOSwitch
      - RACKSWITCH
      - STORAGE
      - SERVER
      - None

  command_options:
    description:
      options to perform updatepolicy operation
    default: updatepolicy
    choices:
        - updatepolicy

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = r'''
# Get all update policies from LXCA
- name: get all update policies from LXCA
  lxca_updatepolicy:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    command_options: updatepolicy

# Get firmware update policies
- name: reload repository file
  lxca_updatepolicy:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    policy_info: FIRMWARE
    command_options: updatepolicy

# List  the persisted compare result for servers to which a policy is assigned
- name: Compare policy result
  lxca_updatepolicy:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    policy_info: RESULTS
    command_options: updatepolicy

# Check compliant with the assigned compliance policy using the job or task ID that was returned
# when the compliance policy was assigned
- name: Check complaince
  lxca_updatepolicy:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    policy_info: RESULTS
    uuid: EF362CF0FB4511E397AB40F2E9AF01D0
    jobid: 2
    command_options: updatepolicy

# Assign policy to endpoint
- name: assign policy to endpoint
  lxca_updatepolicy:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    policy_name: x220_imm2
    policy_type: SERVER
    uuid: 7C5E041E3CCA11E18B715CF3FC112D8A
    command_options: updatepolicy

# Status of assign policy to endpoint
- name: status of assign policy job
  lxca_updatepolicy:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    jobid: 3
    command_options: updatepolicy

'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import updatepolicy


class UpdatepolicyModule(LXCAModuleBase):
    '''
    This class fetch information about updatepolicy in lxca
    '''

    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'updatepolicy': self._get_updatepolicy,
        }
        args_spec = dict(
            command_options=dict(default='updatepolicy', choices=list(self.func_dict)),
            policy_info=dict(default=None,
                             choices=[None, 'FIRMWARE', 'RESULTS', 'COMPARE_RESULTS',
                                      'NAMELIST']),
            policy_name=dict(default=None),
            policy_type=dict(default=None,
                             choices=['CMM', 'IOSwitch', 'RACKSWITCH', 'STORAGE', 'SERVER', None]),
            uuid=dict(default=None),
            jobid=dict(default=None),
        )
        super(UpdatepolicyModule, self).__init__(input_args_spec=args_spec)
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

    def _get_updatepolicy(self):
        result = updatepolicy(self.lxca_con,
                              self.module.params['policy_info'],
                              self.module.params['jobid'],
                              self.module.params['uuid'],
                              self.module.params['policy_name'],
                              self.module.params['policy_type'],)
        if self.module.params['uuid'] and not self.module.params['jobid']:
            self._changed = True
        return result


def main():
    UpdatepolicyModule().run()


if __name__ == '__main__':
    main()
