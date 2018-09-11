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
module: lxca_configpatterns
short_description: Custom module for lxca configpatterns config utility
description:
  - This module list/assign/delete configpatterns and apply configpattern to managed devices

options:
  status:
    description:
      config status of device. Set to True

  id:
    description:
      Id of config pattern

  endpoint:
    description:
      - used with command apply_configpatterns and get_configstatus,
      - its uuid of deivce for node, rack, tower
      - endpointid for flex

  restart:
    description:
      - used with command apply_configpatterns
      - when to activate the configurations. This can be one of the following values
      - defer - Activate IMM settings but do not restart the server.
      - immediate - Activate all settings and restart the server immediately
      - pending - Manually activate the server profile and restart the server. this can be used
                       with apply_configpatterns only.
    choices:
      - None
      - defer
      - immediate
      - pending

  type:
    description:
      - used with apply_configpatterns valid values are
    choices:
      - None
      - node
      - rack
      - tower
      - flex

  pattern_update_dict:
    description:
      used with command import_configpatterns to import pattern specified in this variable as dict.

  includeSettings:
    description:
      used with command get_configpatterns to get detailed settings of configpattern set this to 'True'

  config_pattern_name:
    description:
      name of config pattern

  command_options:
    description:
      options to perform configpatterns operation
    default: configpatterns
    choices:
        - get_configpatterns
        - get_particular_configpattern
        - import_configpatterns
        - apply_configpatterns
        - get_configstatus

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = r'''
# get all configpatterns from LXCA
- name: get all configpatterns from LXCA
  lxca_configpatterns:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    command_options: get_configpatterns

# get config status of endpoint
- name: get configpatterns job data from LXCA
  lxca_configpatterns:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    endpoint: "3C737AA5E31640CE949B10C129A8B01F"
    status: True
    command_options: get_configstatus

# get particular configpatterns from LXCA
- name: get particular configpatterns from LXCA
  lxca_configpatterns:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    id: 63
    includeSettings: True
    command_options: get_particular_configpattern

# apply configpattern to device
- name: apply configpattern to device
  lxca_configpatterns:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    id: 63
    endpoint: "3C737AA5E31640CE949B10C129A8B01F"
    restart: immediate
    type: node
    command_options: apply_configpatterns

# import configpattern to LXCA
- name: import configpattern to LXCA
  lxca_configpatterns:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    pattern_update_dict: "{{ pattern_dict}}"
    command_options: import_configpatterns

'''

import traceback
from ansible.module_utils.basic import AnsibleModule
try:
    from pylxca import connect
    from pylxca import disconnect
    from pylxca import configpatterns
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


def _get_configpatterns(module, lxca_con):
    result = configpatterns(lxca_con)
    return result


def _get_particular_configpattern(module, lxca_con):
    pattern_dict = {}
    pattern_dict['id'] = module.params['id']
    pattern_dict['includeSettings'] = module.params['includeSettings']
    result = configpatterns(lxca_con, **pattern_dict)
    return result


def _import_configpatterns(module, lxca_con):
    global __changed__
    pattern_dict = {}
    pattern_dict['pattern_update_dict'] = module.params['pattern_update_dict']
    result = configpatterns(lxca_con, **pattern_dict)
    __changed__ = True

    return result


def _apply_configpatterns(module, lxca_con):
    global __changed__
    pattern_dict = {}
    pattern_dict['id'] = module.params['id']
    pattern_dict['name'] = module.params['config_pattern_name']
    pattern_dict['endpoint'] = module.params['endpoint']
    pattern_dict['restart'] = module.params['restart']
    pattern_dict['type'] = module.params['type']
    result = configpatterns(lxca_con, **pattern_dict)
    __changed__ = True
    return result


def _get_configstatus(module, lxca_con):
    pattern_dict = {}
    pattern_dict['endpoint'] = module.params['endpoint']
    pattern_dict['status'] = module.params['status']
    result = configpatterns(lxca_con, **pattern_dict)
    if 'items' in result and len(result['items']) and result['items'][0]:
        result = result['items'][0]
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
    'configpatterns': _get_configpatterns,
    'get_configpatterns': _get_configpatterns,
    'get_particular_configpattern': _get_particular_configpattern,
    'import_configpatterns': _import_configpatterns,
    'apply_configpatterns': _apply_configpatterns,
    'get_configstatus': _get_configstatus,
}


LXCA_COMMON_ARGS = dict(
    login_user=dict(required=True),
    login_password=dict(required=True, no_log=True),
    auth_url=dict(required=True),
    noverify=dict(default=True)
)

INPUT_ARG_SPEC = dict(
    command_options=dict(default='configpatterns', choices=['get_configpatterns',
                                                            'get_particular_configpattern',
                                                            'import_configpatterns',
                                                            'apply_configpatterns',
                                                            'get_configstatus']),
    id=dict(default=None),
    status=dict(default=None),
    endpoint=dict(default=None),
    restart=dict(default=None, choices=[None, 'defer', 'immediate', 'pending']),
    type=dict(default=None, choices=[None, 'node', 'rack', 'tower', 'flex']),
    config_pattern_name=dict(default=None),
    pattern_update_dict=dict(default=None, type=('dict')),
    includeSettings=dict(default=None),
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
