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
from ansible.module_utils.basic import AnsibleModule
try:
    from pylxca import connect
    from pylxca import disconnect
    from pylxca import configprofiles
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


def _get_configprofiles(module, lxca_con):
    global __changed__
    delete_profile = None
    unassign_profile = None
    action = module.params["lxca_action"]
    if action:
        if action.lower() in ['delete']:
            delete_profile = 'True'
            __changed__ = True
        elif action.lower() in ['unassign']:
            unassign_profile = 'True'
            __changed__ = True

    result = configprofiles(lxca_con,
                            module.params['id'],
                            module.params['config_profile_name'],
                            module.params['endpoint'],
                            module.params['restart'],
                            delete_profile,
                            unassign_profile,
                            module.params['powerdown'],
                            module.params['resetimm'],
                            module.params['force'], )
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
    'configprofiles': _get_configprofiles,
}


LXCA_COMMON_ARGS = dict(
    login_user=dict(required=True),
    login_password=dict(required=True, no_log=True),
    auth_url=dict(required=True),
    noverify=dict(default=True)
)


INPUT_ARG_SPEC = dict(
    command_options=dict(default='configprofiles', choices=list(FUNC_DICT)),
    id=dict(default=None),
    lxca_action=dict(default=None, choices=['delete', 'unassign', None]),
    endpoint=dict(default=None),
    restart=dict(default=None, choices=[None, 'immediate', 'pending']),
    config_profile_name=dict(default=None),
    powerdown=dict(default=None),
    resetimm=dict(default=None),
    force=dict(default=None),
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
