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
module: lxca_cmms
short_description: Custom module for lxca cmms inventory utility
description:
  - This module returns/displays a inventory details of cmms

options:
  uuid:
    description:
      uuid of device, this is string with length greater than 16.

  command_options:
    description:
      options to filter nodes information
    default: cmms
    choices:
        - cmms
        - cmms_by_uuid
        - cmms_by_chassis_uuid

  chassis:
    description:
      uuid of chassis, this is string with length greater than 16.

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# get all cmms info
- name: get nodes data from LXCA
  lxca_cmms:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"

# get specific cmms info by uuid
- name: get nodes data from LXCA
  lxca_cmms:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    uuid: "3C737AA5E31640CE949B10C129A8B01F"
    command_options: cmms_by_uuid

# get specific cmms info by chassis uuid
- name: get nodes data from LXCA
  lxca_cmms:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    chassis: "3C737AA5E31640CE949B10C129A8B01F"
    command_options: cmms_by_chassis_uuid

'''

RETURN = r'''
result:
    description: cmms detail from lxca
    returned: success
    type: dict
    sample:
      cmmList:
        - machineType: ''
          model: ''
          type: 'CMM'
          uuid: '118D2C88C8FD11E4947B6EAE8B4BDCDF'
          # bunch of properties
        - machineType: ''
          model: ''
          type: 'CMM'
          uuid: '223D2C88C8FD11E4947B6EAE8B4BDCDF'
          # bunch of properties
        # Multiple cmms details
'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.lxca.common import LXCA_COMMON_ARGS, has_pylxca, connection_object
try:
    from pylxca import cmms
except ImportError:
    pass


UUID_REQUIRED = 'UUID of device is required for cmms_by_uuid command.'
CHASSIS_UUID_REQUIRED = 'UUID of chassis is required for cmms_by_chassis_uuid command.'
SUCCESS_MSG = "Success %s result"


def _cmms(module, lxca_con):
    return cmms(lxca_con)


def _cmms_by_uuid(module, lxca_con):
    if not module.params['uuid']:
        module.fail_json(msg=UUID_REQUIRED)
    return cmms(lxca_con, module.params['uuid'])


def _cmms_by_chassis_uuid(module, lxca_con):
    if not module.params['chassis']:
        module.fail_json(msg=CHASSIS_UUID_REQUIRED)
    return cmms(lxca_con, chassis=module.params['chassis'])


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
    'cmms': _cmms,
    'cmms_by_uuid': _cmms_by_uuid,
    'cmms_by_chassis_uuid': _cmms_by_chassis_uuid,
}


INPUT_ARG_SPEC = dict(
    command_options=dict(default='cmms', choices=['cmms', 'cmms_by_uuid',
                                                  'cmms_by_chassis_uuid']),
    uuid=dict(default=None),
    chassis=dict(default=None)
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
