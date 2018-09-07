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
module: lxca_manage
short_description: Custom module for lxca manage config utility
description:
  - This module manages discovered devices

options:
  endpoint_ip:
    description:
      - Used with following command
      - "manage - ip of endpoint to be managed
             i.e 10.240.72.172"

  jobid:
    description:
      Id of job, to get status of it

  user:
    description:
      credential for login to device

  password:
    description:
      for login to device

  recovery_password:
    description:
      recovery password to be set in device

  force:
    description:
        Perform force operation. set to 'True'.

  storedcredential_id:
    description:
        stored credential id to be used for operation

  command_options:
    description:
      options to perform manage operation
    default: manage
    choices:
        - manage
        - manage_status

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# manage device
- name: manage device on LXCA
  lxca_manage:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    endpoint_ip: 10.243.12.44
    user: USERID1
    password: Password
    recovery_password: Password
    force: True
    command_options: manage

# get status of manage job by jobid
- name: get manage job data from LXCA
  lxca_manage:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    jobid: "12"
    command_options: manage_status

'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from pylxca import connect
from pylxca import manage
from pylxca import disconnect


SUCCESS_MSG = "Success %s result"
__changed__ = False


def _manage(module, lxca_con):
    global __changed__
    result = None

    result = manage(lxca_con, module.params['endpoint_ip'],
                    module.params['user'],
                    module.params['password'],
                    module.params['recovery_password'],
                    None,
                    module.params['force'],
                    module.params['storedcredential_id'],)
    __changed__ = True
    return result


def _manage_status(module, lxca_con):
    result = manage(lxca_con, job=module.params['jobid'])
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
    'manage': _manage,
    'manage_status': _manage_status,
}


LXCA_COMMON_ARGS = dict(
    login_user=dict(required=True),
    login_password=dict(required=True, no_log=True),
    auth_url=dict(required=True),
    noverify=dict(default=True)
)


INPUT_ARG_SPEC = dict(
    command_options=dict(default='manage', choices=list(FUNC_DICT)),
    endpoint_ip=dict(default=None),
    jobid=dict(default=None),
    user=dict(default=None, required=False),
    password=dict(default=None, required=False, no_log=True),
    force=dict(default=None),
    recovery_password=dict(default=None, no_log=True),
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
    validate_parameters(module)
    lxca_con = setup_conn(module)
    run_tasks(module, lxca_con)


if __name__ == '__main__':
    main()
