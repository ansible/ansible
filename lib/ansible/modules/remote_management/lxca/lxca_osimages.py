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
module: lxca_osimages
short_description: Custom module for lxca osimages and deployment config utility
description:
  - This module perform osimagess and deployment operation on LXCA

options:

  osimages_info:
    description:
      - Used with osimages it can have following values
      - globalSettings - Setting global values used in os deployment
      - hostPlatforms - Used for deploying os images
      - remoteFileServers - Used for remote ftp, http server operations
    choices:
      - globalSettings
      - hostPlatforms
      - remoteFileServers
      - None

  osimages_dict:
    type:
      dict
    description:
      Used with osimages it is used for setting osimages and os deployment parameters.

  command_options:
    description:
      options to perform osimages operation
    default: osimages
    choices:
        - osimages
        - get_osimages_pkg


extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = r'''
# Query osimages
- name: get osimages details from LXCA
  lxca_osimages:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    update_key: filetypes
    type: changeHistory
    fixids: lnvgy_sw_lxca-fw-repository-pack_1-1.0.1_anyos_noarch
    command_options: get_osimages_pkg

# update osimages
- name: update management server
  lxca_osimages:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: refresh
    command_options: update_osimages_pkg

# update osimages download fixids
- name: update management server
  lxca_osimages:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: acquire
    fixids: ibm_fw_imm2_1aoo78j-6.20_anyos_noarch
    command_options: update_osimages_pkg

# update osimages delete fixids
- name: update management server
  lxca_osimages:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: delete
    fixids: ibm_fw_imm2_1aoo78j-6.20_anyos_noarch
    command_options: update_osimages_pkg

# import files to osimages
- name: import management server
  lxca_osimages:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: import
    files: /home/naval/updates/updates/lnvgy_sw_lxca_thinksystemrepo1-1.3.2_anyos_noarch.xml
    command_options: import_osimages_pkg

'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import osimages


class OsimagesModule(LXCAModuleBase):
    '''
    This class fetch information about osimages in lxca
    '''

    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'osimages': self._get_osimages,
            'get_osimages': self._get_osimages,
        }
        args_spec = dict(
            command_options=dict(default='osimages', choices=list(self.func_dict)),
            osimages_info=dict(default=None,
                               choices=[None, 'globalSettings', 'hostPlatforms',
                                        'remoteFileServers']),
            osimages_dict=dict(default=None, type=('dict')),
        )
        super(OsimagesModule, self).__init__(input_args_spec=args_spec)
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

    def _get_osimages(self):
        osimages_info = self.module.params.get('osimages_info')
        osimages_dict = self.module.params.get('osimages_dict')
        if osimages_info and osimages_dict:
            result = osimages(self.lxca_con,
                              osimages_info,
                              **osimages_dict)
            self._changed = True
        elif osimages_dict:
            result = osimages(self.lxca_con,
                              **osimages_dict)
            self._changed = True
        elif osimages_info:
            result = osimages(self.lxca_con,
                              osimages_info)
        else:
            result = osimages(self.lxca_con)
        return result



def main():
    OsimagesModule().run()


if __name__ == '__main__':
    main()
