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
module: lxca_unmanage
short_description: Custom module for lxca unmanage config utility
description:
  - This module unmanages managed devices

options:
  endpoint_ip:
    description:
      - "unamange - combination of ip,uuid of device and type of device
             i.e 10.240.72.172;46920C143355486F97C19A34ABC7D746;Chassis
             type have following options
                Chassis
                ThinkServer
                Storage
                Rackswitch
                Rack-Tower"

  jobid:
    description:
      Id of job, to get status of it

  force:
    description:
        Perform force operation. set to 'True'.

  command_options:
    description:
      options to perform unmanage operation
    default: unmanage
    choices:
        - unmanage
        - unmanage_status

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# unmanage device
- name: unmanage device on LXCA
  lxca_manage:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    endpoint_ip: 10.243.12.44;3C737AA5E31640CE949B10C129A8B01;Rack-Tower
    force: True
    command_options: unmanage

# get status of unmanage job by jobid
- name: get unmanage job data from LXCA
  lxca_manage:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    jobid: "12"
    command_options: unmanage_status

'''

import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import unmanage


class UnmanageModule(LXCAModuleBase):
    '''
    This class fetch information about Unmanage in lxca
    '''

    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'unmanage': self._unmanage,
            'unmanage_status': self._unmanage_status,
        }
        args_spec = dict(
            command_options=dict(default='unmanage', choices=list(self.func_dict)),
            endpoint_ip=dict(default=None),
            jobid=dict(default=None),
            force=dict(default=None),
            )
        super(UnmanageModule, self).__init__(input_args_spec=args_spec)
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

    def _unmanage(self):
        result = None

        result = unmanage(self.lxca_con, self.module.params['endpoint_ip'],
                          self.module.params['force'], None,)
        self._changed = True
        return result

    def _unmanage_status(self):
        result = unmanage(self.lxca_con, job=self.module.params['jobid'])
        return result


def main():
    UnmanageModule().run()


if __name__ == '__main__':
    main()
