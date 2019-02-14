#!/usr/bin/python

# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: apconos_update
version_added: ""
author: ""
short_description: update firmware on apcon network devices
description:
  - Sends update commands to APCON Network devices. Commands check
    current versions and statues on the devices to decide if update 
    should be executed.
options:
  device:
    description:
      - specify a device. Valid values are [all], [blade]. 
        Choosing [all] will sequentially update software on 
        both controllers, all blades and the backplane from a tftp server.
        Choosing [blade] will download the software from the controller
        and update the software for any APCON blades. If an tftp server
        address is provided, [blade] option will downloads the software from
        a TFTP server for a special blade.
        default: all
        choices: ['all', 'blade']
  blade_letter:
    description:
      - specify a blade letter.
  ipaddress:
    description:
      - specify an ip address of tftp server.
  filename:
    description:
      - specify a file name of firmware.
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
- name: Update APCON Devices
    update_update:
      device: all
      ipaddress: 10.0.0.100
      filename:  firmware_6.01_1550.pem
"""

RETURN = """
"""

import re
import time

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.apconos.apconos import load_config, run_commands 
from ansible.module_utils.network.apconos.apconos import apconos_argument_spec, check_args
from ansible.module_utils.six import string_types
from ansible.utils.display import Display

display = Display()

def to_lines(stdout):
    for item in stdout:
        if isinstance(item, string_types):
            item = str(item).split('\n')
        yield item

def check_version(module):
    """check if current version is higher.
    """
    version = module.params['version']
    responses = run_commands(module, ['show version'])
    cur_version = list(to_lines(responses))[0][1][-5:-1]

    if version is None:
        return cur_version, True
    else:
        return cur_version, (version[0]) > (cur_version)

def construct_update_command(module):
    """construct update command
    """
    command = ['update']
    device = module.params['device']
    blade_letter = module.params['blade_letter']
    ipaddress = module.params['ipaddress']
    filename = module.params['filename']
    if device[0] == 'all':
        command[0] = command[0] + ' ' + device[0] + ' ' \
                     + ipaddress[0] + ' ' + filename[0] + ' false'
    #elif device[0] == 'backplane':
    #    command[0] = command[0] + ' device backplane'
    elif device[0] == 'blade':
        #if ipaddress == None:
        #    command[0] = command[0] + ' ' + ' device blade ' + blade_letter[0] + ' false'
        #else:
        if ipaddress and blade_letter and filename:
            command[0] = command[0] + ' ' + ' device blade standalone ' + blade_letter[0] \
                     + ' ' +  ipaddress[0] + ' ' + filename[0] + ' false'
    #elif device[0] == 'controller':
    #    command[0] = command[0] + ' standby controller'

    return command 

def main():
    """ main entry point for module execution
    """
    spec = dict(
        wait_for=dict(type='list'),
        match=dict(default='all', choices=['all', 'any']),

        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int'),

        device=dict(type='list'),
        blade_letter=dict(default='A', type='list'),
        ipaddress=dict(type='list'),
        filename=dict(type='list'),
        version=dict(type='list'),
        )

    spec.update(apconos_argument_spec)

    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)
    result = {'changed': False}

    wait_for = module.params['wait_for'] or list()
    conditionals = [Conditional(c) for c in wait_for]

    retries = module.params['retries']
    interval = module.params['interval']
    match = module.params['match']

    responses = None
    cur_version, cond = check_version(module)
    while cond and retries > 0:
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

    if responses is not None:
        for item in responses:
            if len(item) == 0:
                result.update({
                    'changed': True,
                    'stdout': responses,
                    'current version': cur_version,
                    'stdout_lines': list(to_lines(responses))
                })
            elif 'ERROR' in item:
                result.update({
                    'failed': True,
                    'stdout': responses,
                    'current version': cur_version,
                    'stdout_lines': list(to_lines(responses))
                })
            else:
                result.update({
                    'stdout': item,
                    'current version': cur_version,
                    'stdout_lines': list(to_lines(responses))
                })
    else:
        msg = 'The current version is newer'
        module.fail_json(msg=msg)
        result.update({
            'current version': cur_version,
        })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
