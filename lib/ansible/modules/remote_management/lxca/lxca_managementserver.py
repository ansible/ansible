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
module: lxca_managementserver
short_description: Custom module for lxca managementserver config utility
description:
  - This module update management server repository on LXCA

options:

  update_key:
    description:
      - Used with managementserver commands following are valid options
        Returns the specified type of update. This can be one of the following values.
      - C(all) - Returns all information. This is the default value.
      - C(currentVersion) - Returns the current version of Lenovo XClarity Administrator.
      - C(history)  Returns the history of management-server updates.
      - C(importDir) Returns the directory for the management-server updates repository.
      - C(size) - Returns the repository size (in bytes).
      - C(updates) - Returns information about all updates packages.
      - C(updatedDate) - Returns the date when the last update was performed.

    choices:
      - None
      - all
      - currentVersion
      - history
      - importDir
      - size
      - updates
      - updatedDate

  files:
    description:
      - Used with managementserver commands to import files to LXCA file can be specified as comma separated string
      - example
      - '/home/naval/updates/updates/lnvgy_sw_lxca_thinksystemrepo1-1.3.2_anyos_noarch.txt,
         /home/naval/updates/updates/lnvgy_sw_lxca_thinksystemrepo1-1.3.2_anyos_noarch.chg,
         /home/naval/updates/updates/lnvgy_sw_lxca_thinksystemrepo1-1.3.2_anyos_noarch.xml'


  lxca_action:
    description:
    - action performed on lxca, Used with following commands with option for lxca_action
    - "update_managementserver_pkg
            apply   - install a management-server update.
            refresh - Retrieves information (metadata) about the latest available
                   management-server updates from the Lenovo XClarity Support website.
            acquire - Downloads the specified management-server update packages from the
                      Lenovo XClarity Support website.
            delete  - Use the DELETE method to delete update packages.
            import  - import fixids files"
    choices:
      - None
      - apply
      - refresh
      - acquire
      - delete
      - import

  fixids:
    description:
      - its string with value like 'lnvgy_sw_lxca-fw-repository-pack_1-1.0.1_anyos_noarch'

  type:
    description:
      - changeHistory. Returns the change-history file for the specified management-server update
      - readme. Returns the readme file for the specified management-server update
    choices:
      - None
      - changeHistory
      - readme

  jobid:
    description:
      Id of job, to get status of it


  command_options:
    description:
      options to perform managementserver operation
    default: managementserver
    choices:
        - managementserver
        - get_managementserver_pkg
        - update_managementserver_pkg
        - import_managementserver_pkg

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = r'''
# Query managementserver
- name: get managementserver details from LXCA
  lxca_managementserver:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    update_key: filetypes
    type: changeHistory
    fixids: lnvgy_sw_lxca-fw-repository-pack_1-1.0.1_anyos_noarch
    command_options: get_managementserver_pkg

# update managementserver
- name: update management server
  lxca_managementserver:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: refresh
    command_options: update_managementserver_pkg

# update managementserver download fixids
- name: update management server
  lxca_managementserver:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: acquire
    fixids: ibm_fw_imm2_1aoo78j-6.20_anyos_noarch
    command_options: update_managementserver_pkg

# update managementserver delete fixids
- name: update management server
  lxca_managementserver:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: delete
    fixids: ibm_fw_imm2_1aoo78j-6.20_anyos_noarch
    command_options: update_managementserver_pkg

# import files to managementserver
- name: import management server
  lxca_managementserver:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: import
    files: /home/naval/updates/updates/lnvgy_sw_lxca_thinksystemrepo1-1.3.2_anyos_noarch.xml
    command_options: import_managementserver_pkg

'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import managementserver


class ManagementserverModule(LXCAModuleBase):
    '''
    This class fetch information about managementserver in lxca
    '''

    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'managementserver': self._get_managementserver_pkg,
            'get_managementserver_pkg': self._get_managementserver_pkg,
            'update_managementserver_pkg': self._update_managementserver_pkg,
            'import_managementserver_pkg': self._import_managementserver_pkg,
        }
        args_spec = dict(
            command_options=dict(default='managementserver', choices=list(self.func_dict)),
            update_key=dict(default=None,
                            choices=['all', 'currentVersion', 'history', 'importDir',
                                     'size', 'updates', 'updatedDate', None]),
            files=dict(default=None),
            lxca_action=dict(default=None, choices=['apply', 'refresh', 'acquire',
                                                    'delete', 'import', None]),
            type=dict(default=None, choices=['changeHistory', 'readme', None]),
            fixids=dict(default=None),
            jobid=dict(default=None),
        )
        super(ManagementserverModule, self).__init__(input_args_spec=args_spec)
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

    def _get_managementserver_pkg(self):
        result = managementserver(self.lxca_con,
                                  self.module.params['update_key'],
                                  self.module.params['fixids'],
                                  self.module.params['type'])
        return result

    def _update_managementserver_pkg(self):
        result = managementserver(self.lxca_con,
                                  self.module.params['update_key'],
                                  self.module.params['fixids'],
                                  self.module.params['type'],
                                  self.module.params['lxca_action'],)
        self._changed = True
        return result

    def _import_managementserver_pkg(self):
        result = managementserver(self.lxca_con,
                                  self.module.params['update_key'],
                                  self.module.params['fixids'],
                                  self.module.params['type'],
                                  self.module.params['lxca_action'],
                                  self.module.params['files'],
                                  self.module.params['jobid'],)
        self._changed = True
        return result


def main():
    ManagementserverModule().run()


if __name__ == '__main__':
    main()
