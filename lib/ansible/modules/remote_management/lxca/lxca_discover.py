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
module: lxca_discover
short_description: Custom module for lxca discover inventory utility
description:
  - This module returns/displays a inventory details of discover

options:
  ip:
    description:
      discover for this ip,

  jobid:
    description:
      discover status for jobid,

  command_options:
    description:
      options to filter discover information
    default: discover
    choices:
        - discover

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# get all discover info
- name: get discover data from LXCA
  lxca_discover:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"

# get specific discover info by ip
- name: get discover data from LXCA
  lxca_discover:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    ip: "10.243.12.244"
    command_options: discover

# get status of discover job by jobid
- name: get discover data from LXCA
  lxca_discover:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    jobid: "23"
    command_options: discover

'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import discover


class DiscoverModule(LXCAModuleBase):
    '''
    This class fetch information about discover in lxca
    '''

    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'discover': self._discover,
        }
        args_spec = dict(
            command_options=dict(default='discover', choices=list(self.func_dict)),
            id=dict(default=None),
        )
        super(DiscoverModule, self).__init__(input_args_spec=args_spec)
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

    def _discover(self):
        return discover(self.lxca_con, ip=self.module.params['ip'],
                        job=self.module.params['jobid'])


def main():
    DiscoverModule().run()


if __name__ == '__main__':
    main()
