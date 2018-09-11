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
module: lxca_nodes
short_description: Custom module for lxca nodes inventory utility
description:
  - This module returns/displays a inventory details of nodes

options:
  uuid:
    description:
      uuid of device, this is string with length greater than 16.

  command_options:
    description:
      options to filter nodes information
    default: nodes
    choices:
        - nodes
        - nodes_by_uuid
        - nodes_by_chassis_uuid
        - nodes_status_managed
        - nodes_status_unmanaged

  chassis:
    description:
      uuid of chassis, this is string with length greater than 16.

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# get all nodes info
- name: get nodes data from LXCA
  lxca_nodes:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"

# get specific nodes info by uuid
- name: get nodes data from LXCA
  lxca_nodes:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    uuid: "3C737AA5E31640CE949B10C129A8B01F"
    command_options: nodes_by_uuid

# get specific nodes info by chassis uuid
- name: get nodes data from LXCA
  lxca_nodes:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    chassis: "3C737AA5E31640CE949B10C129A8B01F"
    command_options: nodes_by_chassis_uuid

# get managed nodes
- name: get nodes data from LXCA
  lxca_nodes:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    command_options: nodes_status_managed

# get unmanaged nodes
- name: get nodes data from LXCA
  lxca_nodes:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    command_options: nodes_status_unmanaged

'''

import traceback
from ansible.module_utils.basic import AnsibleModule
try:
    from pylxca import connect
    from pylxca import disconnect
    from pylxca import nodes
    HAS_PYLXCA = True
except Exception:
    HAS_PYLXCA = False


UUID_REQUIRED = 'UUID of device is required for nodes_by_uuid command.'
CHASSIS_UUID_REQUIRED = 'UUID of chassis is required for nodes_by_chassis_uuid command.'
SUCCESS_MSG = "Success %s result"
PYLXCA_REQUIRED = 'Lenovo xClarity Administrator Python Client pylxca is required for this module.'


def has_pylxca(module):
    """
    Check pylxca is installed
    :param module:
    """
    if not HAS_PYLXCA:
        module.fail_json(msg=PYLXCA_REQUIRED)


def _nodes(module, lxca_con):
    return nodes(lxca_con)


def _nodes_by_uuid(module, lxca_con):
    if not module.params['uuid']:
        module.fail_json(msg=UUID_REQUIRED)
    return nodes(lxca_con, module.params['uuid'])


def _nodes_by_chassis_uuid(module, lxca_con):
    if not module.params['chassis']:
        module.fail_json(msg=CHASSIS_UUID_REQUIRED)
    return nodes(lxca_con, chassis=module.params['chassis'])


def _nodes_status_managed(module, lxca_con):
    return nodes(lxca_con, status='managed')


def _nodes_status_unmanaged(module, lxca_con):
    return nodes(lxca_con, status='unmanaged')


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
    'nodes': _nodes,
    'nodes_by_uuid': _nodes_by_uuid,
    'nodes_by_chassis_uuid': _nodes_by_chassis_uuid,
    'nodes_status_managed': _nodes_status_managed,
    'nodes_status_unmanaged': _nodes_status_unmanaged,
}


LXCA_COMMON_ARGS = dict(
    login_user=dict(required=True),
    login_password=dict(required=True, no_log=True),
    auth_url=dict(required=True),
    noverify=dict(default=True)
)
INPUT_ARG_SPEC = dict(
    command_options=dict(default='nodes', choices=['nodes', 'nodes_by_uuid',
                                                   'nodes_by_chassis_uuid',
                                                   'nodes_status_managed',
                                                   'nodes_status_unmanaged']),
    uuid=dict(default=None), chassis=dict(default=None)
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
        module.exit_json(changed=True,
                         msg=SUCCESS_MSG % module.params['command_options'],
                         result=result)
    except Exception as exception:
        error_msg = '; '.join((e) for e in exception.args)
        disconnect(lxca_con)
        module.fail_json(msg=error_msg, exception=traceback.format_exc())


def run_tasks(module, lxca_con):
    """
    This function invoke commands
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
