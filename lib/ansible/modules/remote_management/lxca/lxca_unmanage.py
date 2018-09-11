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
from ansible.module_utils.basic import AnsibleModule
try:
    from pylxca import connect
    from pylxca import disconnect
    from pylxca import unmanage
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


def _unmanage(module, lxca_con):
    global __changed__
    result = None

    result = unmanage(lxca_con, module.params['endpoint_ip'],
                      module.params['force'], None,)
    __changed__ = True
    return result


def _unmanage_status(module, lxca_con):
    result = unmanage(lxca_con, job=module.params['jobid'])
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
    'unmanage': _unmanage,
    'unmanage_status': _unmanage_status,
}


LXCA_COMMON_ARGS = dict(
    login_user=dict(required=True),
    login_password=dict(required=True, no_log=True),
    auth_url=dict(required=True),
    noverify=dict(default=True)
)


INPUT_ARG_SPEC = dict(
    command_options=dict(default='unmanage', choices=['unmanage', 'unmanage_status']),
    endpoint_ip=dict(default=None),
    jobid=dict(default=None),
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
