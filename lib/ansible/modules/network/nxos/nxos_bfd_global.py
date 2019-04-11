#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

import datetime
def logit(msg):
    with open('/tmp/alog.txt', 'a') as of:
        d = datetime.datetime.now().replace(microsecond=0).isoformat()
        of.write("---- %s ----\n%s\n" % (d,msg))

DOCUMENTATION = '''
---
module: nxos_bfd_global
extends_documentation_fragment: nxos
version_added: "2.9"
short_description: Bidirectional Forwarding Detection (BFD) global-level configuration
description:
  - Manages Bidirectional Forwarding Detection (BFD) global-level configuration.

author: Chris Van Heuveln (@chrisvanheuveln)
notes:
options:                 # **** To Be updated after initial review *****
  echo_interface:
    description:
      - does a thing
    required: false
  echo_rx_interval:
    description:
      - does a thing
    required: false
  interval:
    # <state> bfd interval <interval> min_rx <min_rx> multiplier <multiplier>
    description:
      - does a thing
    required: false
  slow_timer:
    description:
      - does a thing
    required: false
  startup_timer:
    description:
      - does a thing
    required: false
  afi specific commands (not available for 5k/6k)
    ipv4_echo_rx_interval:
    ipv6_echo_rx_interval:
    description:
      - does a thing
    required: false
    ipv4_interval:
    ipv6_interval:
    description:
      - does a thing
    required: false
    ipv4_slow_timer:
    ipv6_slow_timer:
    description:
      - does a thing
    required: false
  fabricpath-specific commands (only available for 5k/6k/7k)
    fabricpath_interval:
    description:
      - does a thing
    required: false
    fabricpath_slow_timer:
    description:
      - does a thing
    required: false
    fabricpath_vlan:
    description:
      - does a thing
    required: false
'''
EXAMPLES = '''
- nxos_bfd_global:
    echo_interface: Ethernet1/2
    echo_interval: [50, 50, 3]
    state: present
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["router bgp 65535", "vrf test", "router-id 192.0.2.1"]   # ***** TBD ****
'''


import re, yaml

from ansible.module_utils.network.nxos.nxos import get_config, load_config   # CVH CHECK WHICH OF THESE ARE NEEDED
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.network.nxos.nxos import run_commands
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import CustomNetworkConfig
from ansible.module_utils.connection import ConnectionError

BFD_CMD_REF = '''
# BFD does not support json format yet; use cli config strings instead.
---
echo_interface:
  type: str
  getval: (no )*bfd echo-interface *(\S+)*$
  setval: '{0}bfd echo-interface {1}'
  default: ''

echo_rx_interval:
  type: int
  getval: bfd echo-rx-interval (\d+)$
  setval: bfd echo-rx-interval {0}
  default: 50
  N3K: 250

interval:
  type: int_list
  getval: bfd interval (\d+) min_rx (\d+) multiplier (\d+)
  setval: bfd interval {0} min_rx {1} multiplier {2}
  default: [50,50,3]
  N3K: [250,250,3]

slow_timer:
  type: int
  getval: bfd slow-timer (\d+)$
  setval: bfd slow-timer {0}
  default: 2000
'''
BFD_SHOW_CMD = "show run bfd all | incl '^(no )*bfd'"


def init_cmd_ref(module):
    '''Ensure BFD feature is enabled. Create cmd_ref dict.
    '''
    output = execute_show_command(module, 'show run bfd', 'text')
    if output and 'CLI command error' in output:
        if module.check_mode:
            msg = "** 'feature bfd' is disabled. BFD will auto-enable when not in check_mode **"
            module.warn(msg)
        else:
            load_config(module, 'feature bfd')

    cmd_ref = yaml.load(BFD_CMD_REF)
    cmd_ref = get_platform_defaults(module, cmd_ref)
    return cmd_ref

def get_platform_defaults(module, cmd_ref):
    '''Get platform type and update ref with platform specific defaults
    '''
    data = execute_show_command(module, 'show inventory', 'json')
    if data:
        pid = data['TABLE_inv']['ROW_inv'][0]['productid']
        plat = None
        if re.search(r'N3K', pid):
            plat = 'N3K'
        plat = 'N3K'
        if plat:
            for k in cmd_ref:
                if plat in cmd_ref[k]:
                    cmd_ref[k]['default'] = cmd_ref[k][plat]

    return cmd_ref


def execute_show_command(module, command, format):
    cmds = [{
        'command': command,
        'output': format,
    }]
    output = None
    try:
        output = run_commands(module, cmds)[0]
    except ConnectionError as exc:
        if 'CLI command error' in repr(exc):
            output = repr(exc)
        else:
            raise
    return output


def get_existing(module, cmd_ref, show_cmd):
    '''
    Get a list of existing command states from device; then update cmd_ref
    with any 'existing' values that differ from default states
    '''
    output = execute_show_command(module, show_cmd, 'text') or []
    if not output:
        return {}

    # Walk each cmd in cmd_ref, use cmd pattern to discover existing cmds
    output = output.split('\n')
    for k in cmd_ref:
        pattern = cmd_ref[k]['getval']
        match = [m.groups() for m in (re.search(pattern, line) for line in output) if m]
        if not match:
            continue
        match = list(match[0]) # tuple to list
        # handle 'no' keyword
        if None is match[0]:
            match.pop(0)
        elif 'no' in match[0]:
            cmd_ref[k]['no_cmd'] = True
            match.pop(0)
            if not match:
                continue
        type = cmd_ref[k]['type']
        if 'int' == type:
            cmd_ref[k]['existing'] = int(match[0])
        if 'int_list' == type:
            cmd_ref[k]['existing'] = [int(i) for i in match]
        if 'str' == type:
            cmd_ref[k]['existing'] = match[0]

    logit(cmd_ref)
    return cmd_ref


def get_playvals(module, cmd_ref):
    '''Update cmd_ref with playbook values
    '''
    for k in cmd_ref.keys():
        if k in module.params and module.params[k] is not None:
            playval = module.params[k]
            if 'int' is cmd_ref[k]['type']:
                playval = int(playval)
            elif 'int_list' is cmd_ref[k]['type']:
                playval = [int(i) for i in playval]
            cmd_ref[k]['playval'] = playval

    return cmd_ref


def get_proposed(cmd_ref):
    '''
    Compare playbook values against existing states and create a list
    of cli commands to play on the device.
    '''
    proposed = []
    # Create a list of playbook values
    playvals = [k for k,v in cmd_ref.items() if 'playval' in v]
    # Compare against current state
    for k in playvals:
        playval = cmd_ref[k]['playval']
        existing = cmd_ref[k].get('existing', cmd_ref[k]['default'])
        logit('pv: %s ex: %s' %(playval,existing))
        if playval == existing:
            continue
        cmd = None
        type = cmd_ref[k]['type']
        if 'int' == type:
            cmd = cmd_ref[k]['setval'].format(playval)
        elif 'int_list' == type:
            cmd = cmd_ref[k]['setval'].format(*(playval))
        elif 'str' == type:
            if playval:
                cmd = cmd_ref[k]['setval'].format('', playval)
            elif existing:
                cmd = cmd_ref[k]['setval'].format('no ', existing)
        if cmd:
            proposed.append(cmd)

    return proposed


def main():
    argument_spec = dict(
        echo_interface=dict(required=False, type='str'),
        echo_rx_interval=dict(required=False, type='int'),
        interval=dict(required=False, type='list'),
        slow_timer=dict(required=False, type='int'),
    )
    argument_spec.update(nxos_argument_spec)
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    warnings = list()
    check_args(module, warnings)

    cmd_ref = init_cmd_ref(module)
    cmd_ref = get_existing(module, cmd_ref, BFD_SHOW_CMD)
    cmd_ref = get_playvals(module, cmd_ref)
    cmds = get_proposed(cmd_ref)

    result = {'changed': False, 'commands': cmds, 'warnings': warnings,
              'check_mode': module.check_mode}
    if cmds:
        result['changed'] = True
        if not module.check_mode:
            load_config(module, cmds)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
