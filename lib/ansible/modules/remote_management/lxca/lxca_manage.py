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
module: lxca_manage
short_description: Custom module for lxca manage config utility
description:
  - This module manages discovered devices

options:
  endpoint_ip:
    description:
      - Used with following command
      - "manage - ip of endpoint to be managed
             i.e 10.240.72.172"

  jobid:
    description:
      Id of job, to get status of it

  user:
    description:
      credential for login to device

  password:
    description:
      for login to device

  recovery_password:
    description:
      recovery password to be set in device

  force:
    description:
        Perform force operation. set to 'True'.

  storedcredential_id:
    description:
        stored credential id to be used for operation

  command_options:
    description:
      options to perform manage operation
    default: manage
    choices:
        - manage
        - manage_status

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# manage device
- name: manage device on LXCA
  lxca_manage:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    endpoint_ip: 10.243.12.44
    user: USERID1
    password: Password
    recovery_password: Password
    force: True
    command_options: manage

# get status of manage job by jobid
- name: get manage job data from LXCA
  lxca_manage:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    jobid: "12"
    command_options: manage_status

'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import manage


class ManageModule(LXCAModuleBase):
    '''
    This class fetch information about manage in lxca
    '''

    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'manage': self._manage,
            'manage_status': self._manage_status,
        }
        args_spec = dict(
            command_options=dict(default='manage', choices=list(self.func_dict)),
            endpoint_ip=dict(default=None),
            jobid=dict(default=None),
            user=dict(default=None, required=False),
            password=dict(default=None, required=False, no_log=True),
            force=dict(default=None),
            recovery_password=dict(default=None, no_log=True),
            storedcredential_id=dict(default=None),
        )
        super(ManageModule, self).__init__(input_args_spec=args_spec)
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

    def _manage(self):
        result = None

        result = manage(self.lxca_con, self.module.params['endpoint_ip'],
                        self.module.params['user'],
                        self.module.params['password'],
                        self.module.params['recovery_password'],
                        None,
                        self.module.params['force'],
                        self.module.params['storedcredential_id'],)
        self._changed = True
        return result

    def _manage_status(self):
        result = manage(self.lxca_con, job=self.module.params['jobid'])
        return result


def main():
    ManageModule().run()


if __name__ == '__main__':
    main()
