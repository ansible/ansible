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
module: lxca_log
short_description: Custom module for lxca event log inventory utility
description:
  - This module returns/displays a inventory details of lxca events

options:
  filter:
    description:
      filter events log,

  command_options:
    description:
      options to filter lxcalog information
    default: lxcalog
    choices:
        - lxcalog

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# get all lxcalog info
- name: get lxcalog data from LXCA
  lxca_log:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"

# get specific lxcalog info by id
- name: get lxcalog data from LXCA
  lxca_log:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    filter: "12"
    command_options: lxcalog

'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from pylxca import lxcalog
from pylxca import connect
from pylxca import disconnect


SUCCESS_MSG = "Success %s result"


def _lxcalog(module, lxca_con):
    return lxcalog(lxca_con, id=module.params['filter'])


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
    'lxcalog': _lxcalog,
}


LXCA_COMMON_ARGS = dict(
    login_user=dict(required=True),
    login_password=dict(required=True, no_log=True),
    auth_url=dict(required=True),
    noverify=dict(default=True)
)

INPUT_ARG_SPEC = dict(
    command_options=dict(default='lxcalog', choices=list(FUNC_DICT)),
    filter=dict(default=None),
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
        module.exit_json(changed=False,
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
    validate_parameters(module)
    lxca_con = setup_conn(module)
    run_tasks(module, lxca_con)


if __name__ == '__main__':
    main()
