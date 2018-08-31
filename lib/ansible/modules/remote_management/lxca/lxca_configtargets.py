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
module: lxca_configtargets
short_description: Custom module for lxca configtargets config utility
description:
  - This module gets information about configtargets

options:

  id:
    description:
      Id of config profile
    required: True

  command_options:
    description:
      options to perform configtargets operation
    default: configtargets
    choices:
        - configtargets

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = r'''
# get particular configtargets with id
- name: get particular configtargets with id
  lxca_configtargets:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    id: 63
    command_options: configtargets


'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import configtargets


class ConfigtargetsModule(LXCAModuleBase):
    '''
    This class fetch information about configtargets in lxca
    '''

    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'configtargets': self._get_configtargets,
        }
        args_spec = dict(
            command_options=dict(default='configtargets', choices=list(self.func_dict)),
            id=dict(default=None),)
        super(ConfigtargetsModule, self).__init__(input_args_spec=args_spec)
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

    def _get_configtargets(self):
        result = configtargets(self.lxca_con, self.module.params['id'])
        return result


def main():
    ConfigtargetsModule().run()


if __name__ == '__main__':
    main()
