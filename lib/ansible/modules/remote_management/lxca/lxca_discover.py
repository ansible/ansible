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
module: lxca_discover
short_description: Custom module for lxca discover inventory utility
description:
  - This module returns/displays a inventory details of discover

options:
  discover_ip:
    description:
      discover for this ip,

  jobid:
    description:
      discover status for jobid,

  command_options:
    description:
      options to filter discover information
    default: discover
    choices:
        - discover

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# get all discover info
- name: get discover data from LXCA
  lxca_discover:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"

# get specific discover info by ip
- name: get discover data from LXCA
  lxca_discover:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    ip: "10.243.12.244"
    command_options: discover

# get status of discover job by jobid
- name: get discover data from LXCA
  lxca_discover:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    jobid: "23"
    command_options: discover

'''

RETURN = r'''
# discover all device
result:
  description: discover all detail from lxca
  returned: success
  type: dict
  sample:
    chassisList: {}
    storageList: {}
    nodeList: {}
    rackswitchList: {}
    contains:
      jobid:
        description: discover ip from  lxca
        returned: success
        type: string
        sample: "293"

'''


import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.lxca.common import LXCA_COMMON_ARGS, has_pylxca, connection_object
try:
    from pylxca import discover
except ImportError:
    pass


SUCCESS_MSG = "Success %s result"


def _discover(module, lxca_con):
    result = None
    if module.params.get('discover_ip', None):
        result = {'jobid': discover(lxca_con, ip=module.params['discover_ip'])}
    elif module.params.get('jobid', None):
        result = discover(lxca_con, job=module.params['jobid'])
    else:
        result = discover(lxca_con)
    return result


def setup_module_object():
    """
    this function merge argument spec and create ansible module object
    :return:
    """
    args_spec = dict(LXCA_COMMON_ARGS)
    args_spec.update(INPUT_ARG_SPEC)
    module = AnsibleModule(argument_spec=args_spec,
                           mutually_exclusive=[['discover_ip', 'jobid']],
                           supports_check_mode=False)

    return module


FUNC_DICT = {
    'discover': _discover,
}


INPUT_ARG_SPEC = dict(
    command_options=dict(default='discover', choices=list(FUNC_DICT)),
    discover_ip=dict(default=None),
    jobid=dict(default=None),
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
