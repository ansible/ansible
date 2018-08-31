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
module: lxca_log
short_description: Custom module for lxca event log inventory utility
description:
  - This module returns/displays a inventory details of lxca events

options:
  filter:
    description:
      filter events log,

  command_options:
    description:
      options to filter lxcalog information
    default: lxcalog
    choices:
        - lxcalog

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# get all lxcalog info
- name: get lxcalog data from LXCA
  lxca_log:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"

# get specific lxcalog info by id
- name: get lxcalog data from LXCA
  lxca_log:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    filter: "12"
    command_options: lxcalog

'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import lxcalog


class LxcalogModule(LXCAModuleBase):
    '''
    This class fetch information about lxcalog in lxca
    '''

    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'lxcalog': self._lxcalog,
        }
        args_spec = dict(
            command_options=dict(default='lxcalog', choices=list(self.func_dict)),
            filter=dict(default=None),
        )
        super(LxcalogModule, self).__init__(input_args_spec=args_spec)
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

    def _lxcalog(self):
        return lxcalog(self.lxca_con, id=self.module.params['filter'])


def main():
    LxcalogModule().run()


if __name__ == '__main__':
    main()
