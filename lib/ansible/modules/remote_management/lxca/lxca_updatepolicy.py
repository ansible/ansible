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
module: lxca_updatepolicy
short_description: Custom module for lxca update policy config utility
description:
  - This module update policy on LXCA

options:

  uuid:
    description:
      uuid of device, this is string with length greater than 16.

  jobid:
    description:
      Id of job, to get status of it

  policy_info:
    description:
      - used with command updatepolicy following values are possible
      - "FIRMWARE - Get List of Applicable Frimware policies"
      - "RESULTS - List  the persisted compare result for servers to which a policy is assigned"
      - "COMPARE_RESULTS -Check compliant with the assigned compliance policy using the job or task ID
                         that was returned when the compliance policy was assigned."
      - "NAMELIST -  Returns the available compliance policies"

    choices:
      - None
      - FIRMWARE
      - RESULTS
      - COMPARE_RESULTS
      - NAMELIST

  policy_name:
    description:
        used with command updatepolicy, name of policy to be applied

  policy_type:
    description:
      - used with command updatepolicy, policy applied to value specified it can have following value
      - CMM - Chassis Management Module
      - IOSwitch - Flex switch
      - RACKSWITCH - RackSwitch switch
      - STORAGE - Lenovo Storage system
      - SERVER - Compute node or rack server
    choices:
      - CMM
      - IOSwitch
      - RACKSWITCH
      - STORAGE
      - SERVER
      - None

  command_options:
    description:
      options to perform updatepolicy operation
    default: updatepolicy
    choices:
        - updatepolicy

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = r'''
# Get all update policies from LXCA
- name: get all update policies from LXCA
  lxca_updatepolicy:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    command_options: updatepolicy

# Get firmware update policies
- name: reload repository file
  lxca_updatepolicy:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    policy_info: FIRMWARE
    command_options: updatepolicy

# List  the persisted compare result for servers to which a policy is assigned
- name: Compare policy result
  lxca_updatepolicy:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    policy_info: RESULTS
    command_options: updatepolicy

# Check compliant with the assigned compliance policy using the job or task ID that was returned
# when the compliance policy was assigned
- name: Check complaince
  lxca_updatepolicy:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    policy_info: RESULTS
    uuid: EF362CF0FB4511E397AB40F2E9AF01D0
    jobid: 2
    command_options: updatepolicy

# Assign policy to endpoint
- name: assign policy to endpoint
  lxca_updatepolicy:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    policy_name: x220_imm2
    policy_type: SERVER
    uuid: 7C5E041E3CCA11E18B715CF3FC112D8A
    command_options: updatepolicy

# Status of assign policy to endpoint
- name: status of assign policy job
  lxca_updatepolicy:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    jobid: 3
    command_options: updatepolicy

'''

import traceback
from ansible.module_utils.basic import AnsibleModule
try:
    from pylxca import connect
    from pylxca import disconnect
    from pylxca import updatepolicy
    HAS_PYLXCA = True
except Exception:
    HAS_PYLXCA = False


SUCCESS_MSG = "Success %s result"
__changed__ = False
PYLXCA_REQUIRED = 'Lenovo xClarity Administrator Python Client pylxca is required for this module.'


def has_pylxca(module):
    """
    Check pylxca is installed
    :param module:
    """
    if not HAS_PYLXCA:
        module.fail_json(msg=PYLXCA_REQUIRED)


def _get_updatepolicy(module, lxca_con):
    global __changed__
    result = updatepolicy(lxca_con,
                          module.params['policy_info'],
                          module.params['jobid'],
                          module.params['uuid'],
                          module.params['policy_name'],
                          module.params['policy_type'],)
    if module.params['uuid'] and not module.params['jobid']:
        __changed__ = True
    return result


def setup_module_object():
    """
    this function merge argument spec and create ansible module object
    :return:
    """
    args_spec = dict(LXCA_COMMON_ARGS)
    args_spec.update(INPUT_ARG_SPEC)
    module = AnsibleModule(argument_spec=args_spec, supports_check_mode=False)

    return module


def setup_conn(module):
    """
    this function create connection to LXCA
    :param module:
    :return:  lxca connection
    """
    lxca_con = None
    try:
        lxca_con = connect(module.params['auth_url'],
                           module.params['login_user'],
                           module.params['login_password'],
                           module.params['noverify'], )
    except Exception as exception:
        error_msg = '; '.join((e) for e in exception.args)
        module.fail_json(msg=error_msg, exception=traceback.format_exc())
    return lxca_con


def validate_parameters(module):
    """
    validate parameters mostly it will be place holder
    :param module:
    """
    pass


FUNC_DICT = {
    'updatepolicy': _get_updatepolicy,
}


LXCA_COMMON_ARGS = dict(
    login_user=dict(required=True),
    login_password=dict(required=True, no_log=True),
    auth_url=dict(required=True),
    noverify=dict(default=True)
)


INPUT_ARG_SPEC = dict(
    command_options=dict(default='updatepolicy', choices=list(FUNC_DICT)),
    policy_info=dict(default=None,
                     choices=[None, 'FIRMWARE', 'RESULTS', 'COMPARE_RESULTS',
                              'NAMELIST']),
    policy_name=dict(default=None),
    policy_type=dict(default=None,
                     choices=['CMM', 'IOSwitch', 'RACKSWITCH', 'STORAGE', 'SERVER', None]),
    uuid=dict(default=None),
    jobid=dict(default=None),
)


def execute_module(module, lxca_con):
    """
    This function invoke commands
    :param module: Ansible module object
    :param lxca_con:  lxca connection object
    """
    try:
        result = FUNC_DICT[module.params['command_options']](module, lxca_con)
        disconnect(lxca_con)
        module.exit_json(changed=__changed__,
                         msg=SUCCESS_MSG % module.params['command_options'],
                         result=result)
    except Exception as exception:
        error_msg = '; '.join((e) for e in exception.args)
        disconnect(lxca_con)
        module.fail_json(msg=error_msg, exception=traceback.format_exc())


def run_tasks(module, lxca_con):
    """

    :param module: Ansible module object
    :param lxca_con:  lxca connection object
    """
    execute_module(module, lxca_con)


def main():
    module = setup_module_object()
    has_pylxca(module)
    validate_parameters(module)
    lxca_con = setup_conn(module)
    run_tasks(module, lxca_con)


if __name__ == '__main__':
    main()
