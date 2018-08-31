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
module: lxca_updaterepo
short_description: Custom module for lxca updaterepo config utility
description:
  - This module update repository on LXCA

options:

  repo_key:
    description:
      - used with updaterepo command following values are used.
      - "supportedMts - Returns a list of supported machine types"
      - "size - Returns the repository size"
      - "lastRefreshed - Returns the timestamp of the last repository refresh"
      - "importDir - Returns the import directory for the repository."
      - "publicKeys - Returns the supported signed keys"
      - "updates - Returns information about all firmware updates"
      - "updatesByMt - Returns information about firmware updates for the specified
                       machine type"
      - "updatesByMtByComp - Returns the update component names for the specified
                       machine type"
    choices:
      - None
      - supportedMts
      - size
      - lastRefreshed
      - importDir
      - publicKeys
      - updates
      - updatesByMt
      - updatesByMtByComp


  lxca_action:
    description:
    - action performed on lxca, Used with following commands with option for lxca_action
    - "updaterepo
            read - Reloads the repository files. The clears the update information in cache and
                          reads the update file again from the repository.
            refresh - Retrieves information about the latest available firmware updates from
                        the Lenovo Support website, and stores the information to
                        the firmware-updates repository.
            acquire - Downloads the specified firmware updates from Lenovo Support website,
                       and stores the updates to the firmware-updates repository.
            delete - Deletes the specified firmware updates from the firmware-updates
                      repository."
    choices:
      - None
      - read
      - refresh
      - acquire
      - delete

  machine_type:
    description:
      - used with command updaterepo
      - its string with value like '7903'

  fixids:
    description:
      - its string with value like 'lnvgy_sw_lxca-fw-repository-pack_1-1.0.1_anyos_noarch'

  scope:
    description:
      - used with command updaterepo, following are possible values
      - all - When lxca_action=refresh is specified, this parameter returns information about all versions of all
                firmware updates that are available for all supported devices.
      - latest - When lxca_action=refresh is specified, this parameter returns information about the most current
               version of all firmware updates for all supported devices.
      - payloads - When lxca_action=acquire is specified, this parameter returns information about specific
                firmware updates.
    choices:
      - all
      - latest
      - payloads
      - None

  file_type:
    description:
      - used with command updaterepo,   When lxca_action=delete is specified, this parameter
        is used. You can specify one of the following values
      - all - Deletes selected update-package files (payload, change history, readme, and metadata files)
      - payloads - Deletes only the selected payload image files
    choices:
      - None
      - all
      - payloads

  command_options:
    description:
      options to perform updaterepo operation
    default: updaterepo
    choices:
        - updaterepo

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = r'''
# Query updaterepo from LXCA
- name: get all updaterepo from LXCA
  lxca_updaterepo:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    repo_key: size
    command_options: updaterepo

# Reload repository file updaterepo
- name: reload repository file
  lxca_updaterepo:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: read
    command_options: updaterepo

# Retrieves information about the latest available firmware updates
- name: Refresh repository from lenovo site
  lxca_updaterepo:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: read
    machine_type: 7903
    command_options: updaterepo

# Downloads the specified firmware updates
- name: dwonload firmware updates from lenovo site to LXCA
  lxca_updaterepo:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: acquire
    machine_type: 7903
    scope: payloads
    fixids: ibm_fw_imm2_1aoo78j-6.20_anyos_noarch
    command_options: updaterepo

# delete repository file
- name: delete config profile with id
  lxca_updaterepo:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: delete
    machine_type: 7903
    file_type: payloads
    fixids: ibm_fw_imm2_1aoo78j-6.20_anyos_noarch
    command_options: updaterepo


'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import updaterepo


class UpdaterepoModule(LXCAModuleBase):
    '''
    This class fetch information about updaterepo in lxca
    '''

    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'updaterepo': self._get_updaterepo,
        }
        args_spec = dict(
            command_options=dict(default='updaterepo', choices=list(self.func_dict)),
            repo_key=dict(default=None,
                          choices=[None, 'supportedMts', 'size', 'lastRefreshed',
                                   'importDir', 'publicKeys', 'updates',
                                   'updatesByMt', 'updatesByMtByComp']),
            lxca_action=dict(default=None, choices=['read', 'refresh', 'acquire', 'delete', None]),
            machine_type=dict(default=None),
            fixids=dict(default=None),
            scope=dict(default=None, choices=['all', 'latest', 'payloads', None]),
            file_type=dict(default=None, choices=[None, 'all', 'payloads']),
        )
        super(UpdaterepoModule, self).__init__(input_args_spec=args_spec)
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

    def _get_updaterepo(self):
        result = updaterepo(self.lxca_con,
                            self.module.params['repo_key'],
                            self.module.params['lxca_action'],
                            self.module.params['machine_type'],
                            self.module.params['scope'],
                            self.module.params['fixids'],
                            self.module.params['file_type'],)
        if self.module.params['lxca_action']:
            self._changed = True
        return result


def main():
    UpdaterepoModule().run()


if __name__ == '__main__':
    main()
