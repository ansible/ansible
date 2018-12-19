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
version_added: "2.8"
author:
  - Naval Patel (@navalkp)
  - Prashant Bhosale (@prabhosa)
module: lxca_scalablesystem
short_description: Custom module for lxca scalablesystem inventory utility
description:
  - This module returns/displays a inventory details of scalablesystem

options:
  uuid:
    description:
      uuid of scalable complex, this is string with length greater than 16.

  command_options:
    description:
      options to filter scalablesystem information
    default: scalablesystem
    choices:
        - scalablesystem

  device_type:
    description:
      scalable complex device type
    default: null
    choices:
      - None
      - flex
      - rackserver

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# get all scalablesystem info
- name: get scalablesystem data from LXCA
  lxca_scalablesystem:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"

# get specific scalablesystem info by uuid
- name: get scalablesystem data from LXCA
  lxca_scalablesystem:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    uuid: "3C737AA5E31640CE949B10C129A8B01F"
    command_options: scalablesystem

# get specific scalablesystem info by device_type
- name: get scalablesystem data from LXCA
  lxca_scalablesystem:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    device_type: "flex"
    command_options: scalablesystem

# get specific scalablesystem info by device_type and uuid
- name: get scalablesystem data from LXCA
  lxca_scalablesystem:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    uuid: "3C737AA5E31640CE949B10C129A8B01F"
    device_type: "flex"
    command_options: scalablesystem

'''

RETURN = r'''
result:
    description: scalablesystem detail from lxca
    returned: success
    type: dict
    sample:
      ComplexList:
        - complexID: "7E7FA27D"
          nodeCount: 2
          partitionCount: 1
          uuid: '118D2C88C8FD11E4947B6EAE8B4BDCDF'
          # bunch of properties
        - complexID: "7E7FB277"
          nodeCount: 3
          partitionCount: 1
          uuid: '328D2DD8C8FD11E4947B6EAE8B4BDCFF'
          # bunch of properties
        # Multiple scalablesystem details
'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.lxca.common import LXCA_COMMON_ARGS, has_pylxca, connection_object
try:
    from pylxca import scalablesystem
except ImportError:
    pass

SUCCESS_MSG = "Success %s result"


def _scalablesystem(module, lxca_con):
    return scalablesystem(lxca_con,
                          id=module.params['uuid'],
                          type=module.params['device_type'])


def setup_module_object():
    """
    this function merge argument spec and create ansible module object
    :return:
    """
    args_spec = dict(LXCA_COMMON_ARGS)
    args_spec.update(INPUT_ARG_SPEC)
    module = AnsibleModule(argument_spec=args_spec, supports_check_mode=False)

    return module


FUNC_DICT = {
    'scalablesystem': _scalablesystem,
}


INPUT_ARG_SPEC = dict(
    command_options=dict(default='scalablesystem', choices=list(FUNC_DICT)),
    uuid=dict(default=None),
    device_type=dict(default=None, choices=[None, 'flex', 'rackserver'])
)


def execute_module(module):
    """
    This function invoke commands
    :param module: Ansible module object
    """
    try:
        with connection_object(module) as lxca_con:
            result = FUNC_DICT[module.params['command_options']](module, lxca_con)
            module.exit_json(changed=False,
                             msg=SUCCESS_MSG % module.params['command_options'],
                             result=result)
    except Exception as exception:
        error_msg = '; '.join((e) for e in exception.args)
        module.fail_json(msg=error_msg, exception=traceback.format_exc())


def main():
    module = setup_module_object()
    has_pylxca(module)
    execute_module(module)


if __name__ == '__main__':
    main()
