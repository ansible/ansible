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
cmds:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["bfd echo-interface loopback1", "bfd slow-timer 2000"]
'''


import re, yaml

from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.network.nxos.nxos import load_config, run_commands, get_capabilities
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import CustomNetworkConfig
from ansible.module_utils.connection import ConnectionError

BFD_CMD_REF = """
# The cmd_ref is a yaml formatted list of module commands.
# A leading underscore denotes a non-command variable; e.g. _template.
# BFD does not have convenient json data so this cmd_ref uses raw cli configs.
---
# _template holds common settings for all commands
_template:
  # Enable feature bfd if disabled
  feature: bfd
  # Common get syntax for BFD commands
  get_command: show run bfd all | incl '^(no )*bfd'

echo_interface:
  kind: str
  getval: (no )*bfd echo-interface *(\S+)*$
  setval: '{0}bfd echo-interface {1}'
  default: ''

echo_rx_interval:
  kind: int
  getval: bfd echo-rx-interval (\d+)$
  setval: bfd echo-rx-interval {0}
  default: 50
  N3K:
    default: 250

interval:
  kind: list
  getval: bfd interval (\d+) min_rx (\d+) multiplier (\d+)
  setval: bfd interval {0} min_rx {1} multiplier {2}
  default: [50,50,3]
  N3K:
    default: [250,250,3]

slow_timer:
  kind: int
  getval: bfd slow-timer (\d+)$
  setval: bfd slow-timer {0}
  default: 2000
"""


def init_cmd_ref(module, cmd_ref_str):
    """Initialize cmd_ref from yaml data.
    Return cmd_ref dict.
    """
    cmd_ref = yaml.load(cmd_ref_str)
    cmd_ref['_proposed'] = []
    cmd_ref = feature_enable(module, cmd_ref)

    # Create a list of supported commands based on cmd_ref keys
    cmd_ref['commands'] = [k for k in cmd_ref if not k.startswith('_')]
    cmd_ref = get_platform_defaults(module, cmd_ref)
    return cmd_ref


def feature_enable(module, cmd_ref):
    """Enable the feature if specified in cmd_ref.
    Return updated cmd_ref.
    """
    feature = cmd_ref['_template'].get('feature')
    if feature:
        show_cmd = "show run | incl 'feature {0}'".format(feature)
        output = execute_show_command(module, show_cmd, 'text')
        if not output or 'CLI command error' in output:
            msg = "** 'feature {0}' is not enabled. Module will auto-enable ** ".format(feature)
            module.warn(msg)
            cmd_ref['_proposed'].append('feature {0}'.format(feature))
    return cmd_ref


def get_platform_defaults(module, cmd_ref):
    """Query device for platform type; update cmd_ref with platform specific defaults.
    Return updated cmd_ref.
    """
    info = get_capabilities(module).get('device_info')
    os_platform = info.get('network_os_platform')
    plat = None
    if 'N3K' in os_platform:
        plat = 'N3K'

    # Update platform-specific settings for each item in cmd_ref
    if plat:
        plat_spec_cmds = [k for k in cmd_ref['commands'] if plat in cmd_ref[k]]
        for k in plat_spec_cmds:
            for plat_key in cmd_ref[k][plat]:
                cmd_ref[k][plat_key] = cmd_ref[k][plat][plat_key]

    return cmd_ref


def execute_show_command(module, command, format):
    """Generic show command helper.
    'CLI command error' exceptions are caught and must be handled by caller.
    Return device output as a newline-separated string or None.
    """
    cmds = [{
        'command': command,
        'output': format,
    }]
    output = None
    try:
        output = run_commands(module, cmds)
        if output:
            output = output[0]
    except ConnectionError as exc:
        if 'CLI command error' in repr(exc):
            # CLI may be feature disabled
            output = repr(exc)
        else:
            raise
    return output


def get_existing(module, cmd_ref):
    """Update cmd_ref with existing command states from the device.
    Store these states in each command's 'existing' key.
    Return updated cmd_ref.
    """
    show_cmd = cmd_ref['_template']['get_command']
    output = execute_show_command(module, show_cmd, 'text') or []
    if not output:
        return cmd_ref

    # Walk each cmd in cmd_ref, use cmd pattern to discover existing cmds
    output = output.split('\n')
    for k in cmd_ref['commands']:
        pattern = cmd_ref[k]['getval']
        match = [m.groups() for m in (re.search(pattern, line) for line in output) if m]
        if not match:
            continue
        if len(match) > 1:
            raise "get_existing: multiple match instances are not currently supported"
        match = list(match[0]) # tuple to list
        # Example match results for patterns that nvgen with the 'no' prefix:
        # When pattern: '(no )*foo *(\S+)*$' And:
        #  When output: 'no foo'  -> match: ['no ', None]
        #  When output: 'foo 50'  -> match: [None, '50']
        if None is match[0]:
            match.pop(0)
        elif 'no' in match[0]:
            cmd_ref[k]['no_cmd'] = True
            match.pop(0)
            if not match:
                continue
        kind = cmd_ref[k]['kind']
        if 'int' == kind:
            cmd_ref[k]['existing'] = int(match[0])
        elif 'list' == kind:
            cmd_ref[k]['existing'] = [str(i) for i in match]
        elif 'str' == kind:
            cmd_ref[k]['existing'] = match[0]
        else:
            raise "get_existing: unknown 'kind' value specified for key '{0}'".format(k)

    return cmd_ref


def get_playvals(module, cmd_ref):
    """Update cmd_ref with values from the playbook.
    Store these values in each command's 'playval' key.
    Return updated cmd_ref.
    """
    for k in cmd_ref.keys():
        if k in module.params and module.params[k] is not None:
            playval = module.params[k]
            if 'int' == cmd_ref[k]['kind']:
                playval = int(playval)
            elif 'list' == cmd_ref[k]['kind']:
                playval = [str(i) for i in playval]
            cmd_ref[k]['playval'] = playval

    return cmd_ref


def get_proposed(cmd_ref):
    """Compare playbook values against existing states and create a list of proposed commands.
    Return a list of raw cli command strings.
    """
    # '_proposed' may be empty list or contain initializations; e.g. ['feature foo']
    proposed = cmd_ref['_proposed']
    # Create a list of commands that have playbook values
    play_keys = [k for k in cmd_ref['commands'] if 'playval' in cmd_ref[k]]
    # Compare against current state
    for k in play_keys:
        playval = cmd_ref[k]['playval']
        existing = cmd_ref[k].get('existing', cmd_ref[k]['default'])
        if playval == existing:
            continue
        cmd = None
        kind = cmd_ref[k]['kind']
        if 'int' == kind:
            cmd = cmd_ref[k]['setval'].format(playval)
        elif 'list' == kind:
            cmd = cmd_ref[k]['setval'].format(*(playval))
        elif 'str' == kind:
            if playval:
                cmd = cmd_ref[k]['setval'].format('', playval)
            elif existing:
                cmd = cmd_ref[k]['setval'].format('no ', existing)
        else:
            raise "get_proposed: unknown 'kind' value specified for key '{0}'".format(k)
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

    cmd_ref = init_cmd_ref(module, BFD_CMD_REF)
    cmd_ref = get_existing(module, cmd_ref)
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
