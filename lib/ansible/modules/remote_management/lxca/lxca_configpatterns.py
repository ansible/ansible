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
module: lxca_configpatterns
short_description: Custom module for lxca configpatterns config utility
description:
  - This module list/assign/delete configpatterns and apply configpattern to managed devices

options:
  status:
    description:
      config status of device. Set to True

  id:
    description:
      Id of config pattern

  endpoint:
    description:
      - used with command apply_configpatterns and get_configstatus,
      - its uuid of deivce for node, rack, tower
      - endpointid for flex

  restart:
    description:
      - used with command apply_configpatterns
      - when to activate the configurations. This can be one of the following values
      - defer - Activate IMM settings but do not restart the server.
      - immediate - Activate all settings and restart the server immediately
      - pending - Manually activate the server profile and restart the server. this can be used
                       with apply_configpatterns only.
    choices:
      - None
      - defer
      - immediate
      - pending

  type:
    description:
      - used with apply_configpatterns valid values are
    choices:
      - None
      - node
      - rack
      - tower
      - flex

  pattern_update_dict:
    description:
      used with command import_configpatterns to import pattern specified in this variable as dict.

  includeSettings:
    description:
      used with command get_configpatterns to get detailed settings of configpattern set this to 'True'

  config_pattern_name:
    description:
      name of config pattern

  command_options:
    description:
      options to perform configpatterns operation
    default: get_configpatterns
    choices:
        - get_configpatterns
        - get_particular_configpattern
        - import_configpatterns
        - apply_configpatterns
        - get_configstatus

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = r'''
# get all configpatterns from LXCA
- name: get all configpatterns from LXCA
  lxca_configpatterns:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    command_options: get_configpatterns

# get config status of endpoint
- name: get configpatterns job data from LXCA
  lxca_configpatterns:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    endpoint: "3C737AA5E31640CE949B10C129A8B01F"
    status: True
    command_options: get_configstatus

# get particular configpatterns from LXCA
- name: get particular configpatterns from LXCA
  lxca_configpatterns:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    id: 63
    includeSettings: True
    command_options: get_particular_configpattern

# apply configpattern to device
- name: apply configpattern to device
  lxca_configpatterns:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    id: 63
    endpoint: "3C737AA5E31640CE949B10C129A8B01F"
    restart: immediate
    type: node
    command_options: apply_configpatterns

# import configpattern to LXCA
- name: import configpattern to LXCA
  lxca_configpatterns:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    pattern_update_dict: "{{ pattern_dict}}"
    command_options: import_configpatterns

'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import configpatterns


class ConfigpatternsModule(LXCAModuleBase):
    '''
    This class fetch information about configpatterns in lxca
    '''

    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'get_configpatterns': self._get_configpatterns,
            'get_particular_configpattern': self._get_particular_configpattern,
            'import_configpatterns': self._import_configpatterns,
            'apply_configpatterns': self._apply_configpatterns,
            'get_configstatus': self._get_configstatus,
        }
        args_spec = dict(
            command_options=dict(default='get_configpatterns', choices=list(self.func_dict)),
            id=dict(default=None),
            status=dict(default=None),
            endpoint=dict(default=None),
            restart=dict(default=None, choices=[None, 'defer', 'immediate', 'pending']),
            type=dict(default=None, choices=[None, 'node', 'rack', 'tower', 'flex']),
            config_pattern_name=dict(default=None),
            pattern_update_dict=dict(default=None, type=('dict')),
            includeSettings=dict(default=None),
        )
        super(ConfigpatternsModule, self).__init__(input_args_spec=args_spec)
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

    def _get_configpatterns(self):
        result = configpatterns(self.lxca_con)
        return result

    def _get_particular_configpattern(self):
        pattern_dict = {}
        pattern_dict['id'] = self.module.params['id']
        pattern_dict['includeSettings'] = self.module.params['includeSettings']
        result = configpatterns(self.lxca_con, **pattern_dict)
        return result

    def _import_configpatterns(self):
        pattern_dict = {}
        pattern_dict['pattern_update_dict'] = self.module.params['pattern_update_dict']
        result = configpatterns(self.lxca_con, **pattern_dict)
        self._changed = True

        return result

    def _apply_configpatterns(self):
        pattern_dict = {}
        pattern_dict['id'] = self.module.params['id']
        pattern_dict['name'] = self.module.params['config_pattern_name']
        pattern_dict['endpoint'] = self.module.params['endpoint']
        pattern_dict['restart'] = self.module.params['restart']
        pattern_dict['type'] = self.module.params['type']
        result = configpatterns(self.lxca_con, **pattern_dict)
        self._changed = True
        return result

    def _get_configstatus(self):
        pattern_dict = {}
        pattern_dict['endpoint'] = self.module.params['endpoint']
        pattern_dict['status'] = self.module.params['status']
        result = configpatterns(self.lxca_con, **pattern_dict)
        if 'items' in result and len(result['items']) and result['items'][0]:
            result = result['items'][0]
        return result


def main():
    ConfigpatternsModule().run()


if __name__ == '__main__':
    main()
