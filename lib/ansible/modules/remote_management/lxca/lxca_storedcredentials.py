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
module: lxca_storedcredentials
short_description: Custom module for lxca storedcredentials utility
description:
  - This module perform CRUD operations for stored credentials in  LXCA

options:

  storedcredential_id:
    description:
        stored credential id to be used for operation

  user:
    description:
      credential for login to device

  password:
    description:
      for login to device

  description:
    description:
      detail about storedcredential.

  command_options:
    description:
      options to stored credential information
    default: storedcredentials
    choices:
        - get_storedcredentials
        - create_storedcredentials
        - update_storedcredentials
        - delete_storedcredentials

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = r'''
# Get all storedcredentials from LXCA
- name: get all stored credentials
  lxca_storedcredentials:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    command_options: get_storedcredentials

# Get specific storedcredentials from LXCA
- name: get all stored credentials
  lxca_storedcredentials:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    storecredential_id: 123
    command_options: get_storedcredentials

# Create new storedcredentials from LXCA
- name: create new stored credentials
  lxca_storedcredentials:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    user: Tes12
    password: Test1212
    description: new user for test
    command_options: create_storedcredentials

# update storedcredentials on LXCA
- name: update stored credentials
  lxca_storedcredentials:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    storecredential_id: 123
    user: Test123
    password: Test123
    description: Updated password user for test123
    command_options: update_storedcredentials

# delete storedcredentials on LXCA
- name: delete stored credentials
  lxca_storedcredentials:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    storecredential_id: 123
    command_options: delete_storedcredentials

'''

import traceback
from ansible.module_utils.basic import AnsibleModule
try:
    from pylxca import connect
    from pylxca import disconnect
    from pylxca import storedcredentials
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


def _get_storedcredentials(module, lxca_con):
    result = storedcredentials(lxca_con,
                               id=module.params.get('storedcredential_id'))
    return result


def _create_storedcredentials(module, lxca_con):
    global __changed__
    result = storedcredentials(lxca_con,
                               user_name=module.params.get('user'),
                               password=module.params.get('password'),
                               description=module.params.get('description'))
    __changed__ = True
    return result


def _update_storedcredentials(module, lxca_con):
    global __changed__
    result = storedcredentials(lxca_con,
                               id=module.params.get('storedcredential_id'),
                               user_name=module.params.get('user'),
                               password=module.params.get('password'),
                               description=module.params.get('description'))
    __changed__ = True
    return result


def _delete_storedcredentials(module, lxca_con):
    global __changed__
    result = storedcredentials(lxca_con,
                               id=module.params.get('storedcredential_id'))
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
    'storedcredentials': _get_storedcredentials,
    'get_storedcredentials': _get_storedcredentials,
    'create_storedcredentials': _create_storedcredentials,
    'update_storedcredentials': _update_storedcredentials,
    'delete_storedcredentials': _delete_storedcredentials
}


LXCA_COMMON_ARGS = dict(
    login_user=dict(required=True),
    login_password=dict(required=True, no_log=True),
    auth_url=dict(required=True),
    noverify=dict(default=True)
)


INPUT_ARG_SPEC = dict(
    command_options=dict(default='storedcredentials',
                         choices=['get_storedcredentials',
                                  'create_storedcredentials',
                                  'update_storedcredentials',
                                  'delete_storedcredentials']),
    user=dict(default=None),
    password=dict(default=None, no_log=True),
    description=dict(default=None),
    storedcredential_id=dict(default=None),
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
