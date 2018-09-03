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
        - get_osimages


extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = r'''
# get all osimage
- name: get all osimages details from LXCA
  lxca_osimages:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"

# get globalSetting for osimages
- name: get globalSetting details from LXCA
  lxca_osimages:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    osimages_info: globalSettings
    command_options: get_osimages

# import osimage file from remote server
# osimage_dict =  {'imageType':'OS','os':'rhels','imageName':'fixed',
#                  'path':'iso/rhel73.iso','serverId':'1'}
- name: import osimage file from remote server
  lxca_osimages:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    osimages_dict: "{{ osiamges_dict }}"

# get hostplatforms detail for osimages
- name: get hostplatforms detail for osimages
  lxca_osimages:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    osimages_info: hostPlatforms
    command_options: osimages

# deploy osimage to node
# osimages_dict =  {'networkSettings':{'dns1': '10.240.0.10','dns2':'10.240.0.11','gateway':'10.240.28.1',
#                     'ipAddress':'10.240.29.226','mtu':1500,'prefixLength':64,'selectedMac':'AUTO',
#                     'subnetMask':'255.255.252.0','vlanId':521},
#                     'selectedImage':'rhels7.3|rhels7.3-x86_64-install-Minimal',
#                     'storageSettings':{'targetDevice':'localdisk'},
#               'uuid':'B918EDCA1B5F11E2803EBECB82710ADE'}
#
- name: deploy osimage to node
  lxca_osimages:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    osiamges_info: hostPlatforms
    osimages_dict: "{{ osimages_dict}}"
    command_options: osimages

# get all remoteFileServers
- name: update management server
  lxca_osimages:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    osimages_info: remoteFileServers
    command_options: osimages

# Get Specific remoteFileServers
- name: Get Specific remoteFileServers
  lxca_osimages:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    osimages_info: remoteFileServers
    osimages_dict:
      id: 1
    command_options: osimages


# Delete Specific Remote File Server
- name: Delete Specific Remote File Server
  lxca_osimages:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    osimages_info: remoteFileServers
    osimages_dict:
      deleteid: 1
    command_options: osimages


# Add Remote File Server
# osimages_dict : {'displayName':'TEST99','address': '192.168.1.10','keyPassphrase': 'Passw0rd',
#                'keyType': 'RSA-2048','port': 8080,'protocol': 'HTTPS'}
- name: Add Remote File Server
  lxca_osimages:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    osimages_info: remoteFileServers
    osimages_dict: "{{ osimages_dict }}"
    command_options: osimages

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
