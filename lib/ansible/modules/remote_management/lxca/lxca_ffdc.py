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
module: lxca_ffdc
short_description: Custom module for lxca ffdc inventory utility
description:
  - This module returns/displays a inventory details of ffdc

options:
  uuid:
    description:
      uuid of lxca ffdc,
    required: True

  command_options:
    description:
      options to filter ffdc information
    default: ffdc
    choices:
        - ffdc

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# get all ffdc info
- name: get ffdc data from LXCA
  lxca_ffdc:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"

# get specific ffdc info by id
- name: get ffdc data from LXCA
  lxca_ffdc:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    id: "12"
    command_options: ffdc

'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import ffdc


class FfdcModule(LXCAModuleBase):
    '''
    This class fetch information about ffdc in lxca
    '''
    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'ffdc': self._ffdc,
        }
        args_spec = dict(
            command_options=dict(default='ffdc', choices=list(self.func_dict)),
            uuid=dict(default=None, required=True),
        )
        super(FfdcModule, self).__init__(input_args_spec=args_spec)
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

    def _ffdc(self):
        return ffdc(self.lxca_con, id=self.module.params['uuid'])


def main():
    FfdcModule().run()


if __name__ == '__main__':
    main()
