#!/usr/bin/python
#
# Copyright (C) 2018 Apcon.
#
# GNU General Public License v3.0+
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Module to execute apconos Commands on Apcon Switches.
# Apcon Networking

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: apconos_cert
version_added: "2.9.0"
author: "David Lee (@davidlee-ap)"
short_description: install ssl ipv4 certificate on apcon network devices
description:
  - import and install ssl ipv4 certificate with specifying remote filename
notes:
  - tested against apcon iis+ii
options:
  command:
    description:
      - currently it is not being used in apconos_cert module.
  provider:
    description:
      - please use connection:network_cli.
  ipaddress:
    description:
      - specify a remote ip address at which tftp server resides.
  filename:
    description:
      - specify a remote file name  which resides on a remote tftp server.
  wait_for:
    description:
      - list of conditions to evaluate against the output of the
        command. The task will wait for each condition to be true
        before moving forward. If the conditional is not true
        within the configured number of retries, the task fails.
        See examples.
  match:
    description:
      - The I(match) argument is used in conjunction with the
        I(wait_for) argument to specify the match policy.  Valid
        values are C(all) or C(any).  If the value is set to C(all)
        then all conditionals in the wait_for must be satisfied.  If
        the value is set to C(any) then only one of the values must be
        satisfied.
    default: all
    choices: ['any', 'all']
  retries:
    description:
      - Specifies the number of retries a command should by tried
        before it is considered failed. The command is run on the
        target device every retry and evaluated against the
        I(wait_for) conditions.
    default: 10
  interval:
    description:
      - Configures the interval in seconds to wait between retries
        of the command. If the command does not pass the specified
        conditions, the interval indicates how long to wait before
        trying the command again.
    default: 1
"""

EXAMPLES = """
- name: Install SSL Certificate
  apconos_cert:
    ipaddress: 10.0.0.100
    filename:  remoteSSLCert.pem
"""

RETURN = """
"""

import re
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.parsing import Conditional
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.apconos.apconos import load_config, run_commands
from ansible.module_utils.network.apconos.apconos import apconos_argument_spec, check_args
from ansible.module_utils.six import string_types


def to_lines(stdout):
    for item in stdout:
        if isinstance(item, string_types):
            item = str(item).split('\n')
        yield item


def construct_update_command(module):
    """construct update command
    """
    command = module.params['command']
    ipaddress = module.params['ipaddress']
    filename = module.params['filename']
    command[0] = 'tftp put ssl ipv4 ' + ipaddress[0] + ' ' + filename[0] + time.strftime("%d_%b+%H:%M:%S", time.gmtime())
    command.append('tftp get ssl ipv4 ' + ipaddress[0] + ' ' + filename[0])

    return command


def main():
    """ main entry point for module execution
    """
    spec = dict(
        wait_for=dict(type='list'),
        match=dict(default='all', choices=['all', 'any']),

        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int'),

        ipaddress=dict(type='list'),
        filename=dict(type='list'),
        command=dict(type='list'))

    spec.update(apconos_argument_spec)

    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)
    result = {'changed': False}

    wait_for = module.params['wait_for'] or list()
    conditionals = [Conditional(c) for c in wait_for]

    retries = module.params['retries']
    interval = module.params['interval']
    match = module.params['match']

    while retries > 0:
        responses = run_commands(module, construct_update_command(module))

        for item in list(conditionals):
            if item(responses):
                if match == 'any':
                    conditionals = list()
                    break
                conditionals.remove(item)

        if not conditionals:
            break

        time.sleep(interval)
        retries -= 1

    if conditionals:
        failed_conditions = [item.raw for item in conditionals]
        msg = 'One or more conditional statements have not been satisfied'
        module.fail_json(msg=msg, failed_conditions=failed_conditions)

    for item in responses:
        if len(item) == 0:
            result.update({
                'changed': True,
                'stdout': responses,
                'stdout_lines': list(to_lines(responses))
            })
        elif 'ERROR' in item:
            result.update({
                'failed': True,
                'stdout': responses,
                'stdout_lines': list(to_lines(responses))
            })
        else:
            result.update({
                'stdout': item,
                'stdout_lines': list(to_lines(responses))
            })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
