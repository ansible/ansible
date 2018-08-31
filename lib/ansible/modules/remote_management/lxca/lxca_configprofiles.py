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
module: lxca_configprofiles
short_description: Custom module for lxca configprofiles config utility
description:
  - This module configprofiles discovered devices

options:

  lxca_action:
    description:
    - action performed on lxca, Used with following commands with option for lxca_action
    - "configprofiles
            delete - delete profile
            unassign - unassign profile"
    choices:
      - None
      - delete
      - unassign

  force:
    description:
      Perform force operation. set to 'True'.

  id:
    description:
      Id of config profile

  endpoint:
    description:
      - used with command apply_configprofiles and get_configstatus,
      - its uuid of deivce for node, rack, tower
      - endpointid for flex

  config_profile_name:
    description:
      name of config profile

  restart:
    description:
      - used with command apply_configprofiles
      - when to activate the configurations. This can be one of the following values
      - immediate - Activate all settings and restart the server immediately
      - pending - Manually activate the server profile and restart the server. this can be used
                       with apply_configprofiles only.
    choices:
      - None
      - immediate
      - pending

  powerdown:
    description:
      used with command configprofiles to power down server

  resetimm:
    description:
      used with command configprofiles to reset imm

  command_options:
    description:
      options to perform configprofiles operation
    default: configprofiles
    choices:
        - configprofiles

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = r'''
# get all configprofiles from LXCA
- name: get all configprofiles from LXCA
  lxca_configprofiles:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    command_options: configprofiles

# get particular configprofiles with id
- name: get particular configprofiles with id
  lxca_configprofiles:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    id: 63
    command_options: configprofiles

# rename configprofile name for profile with id
- name: rename configprofile name with id
  lxca_configprofiles:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    id: 63
    config_profile_name: renamed_server_profile
    command_options: configprofiles

# activate configprofile for endpoint
- name: activate configprofile on endpoint
  lxca_configprofiles:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    id: 63
    endpoint: 3C737AA5E31640CE949B10C129A8B01F
    restart: immediate
    command_options: configprofiles

# delete configprofile
- name: delete config profile with id
  lxca_configprofiles:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    id: 63
    lxca_action: delete
    command_options: configprofiles

# unassign configprofile
- name: unassign config profile with id
  lxca_configprofiles:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    id: 63
    lxca_action: unassign
    powerdown: True
    resetimm: False
    command_options: configprofiles


'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import configprofiles


class ConfigprofilesModule(LXCAModuleBase):
    '''
    This class fetch information about configprofiles in lxca
    '''

    SUCCESS_MSG = "Success %s result"
    def __init__(self):
        self.func_dict = {
            'configprofiles': self._get_configprofiles,
        }
        args_spec = dict(
            command_options=dict(default='configprofiles', choices=list(self.func_dict)),
            id=dict(default=None),
            lxca_action=dict(default=None, choices=['delete', 'unassign', None]),
            endpoint=dict(default=None),
            restart=dict(default=None, choices=[None, 'immediate', 'pending']),
            config_profile_name=dict(default=None),
            powerdown=dict(default=None),
            resetimm=dict(default=None),
            force=dict(default=None),
        )
        super(ConfigprofilesModule, self).__init__(input_args_spec=args_spec)
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

    def _get_configprofiles(self):
        delete_profile = None
        unassign_profile = None
        action = self.module.params["lxca_action"]
        if action:
            if action.lower() in ['delete']:
                delete_profile = 'True'
                self._changed = True
            elif action.lower() in ['unassign']:
                unassign_profile = 'True'
                self._changed = True

        result = configprofiles(self.lxca_con,
                                self.module.params['id'],
                                self.module.params['config_profile_name'],
                                self.module.params['endpoint'],
                                self.module.params['restart'],
                                delete_profile,
                                unassign_profile,
                                self.module.params['powerdown'],
                                self.module.params['resetimm'],
                                self.module.params['force'], )
        return result

def main():
    ConfigprofilesModule().run()


if __name__ == '__main__':
    main()
