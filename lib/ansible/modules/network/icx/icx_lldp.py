ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: icx_lldp
version_added: "1.0"
author: "Ruckus: https://support.ruckuswireless.com/contact-us"
short_description: Manage LLDP configuration on Ruckus ICX 7000 series switches
description:
  - This module provides declarative management of LLDP service on ICX network devices.
options:
  interfaces:
    description:
      - specify interfaces
    suboptions:
      name:
        description:
          - List of ethernet ports to enable lldp.  To add a range of ports use 'to' keyword. See the example.
      state:
        description:
          - State of lldp configuration for interfaces
        choices: ['present', 'absent']

  state:
    description:
      - Enables the receipt and transmission of Link Layer Discovery Protocol (LLDP) globally.
    choices: ['present', 'absent']
  check_running_config:
    description:
      - Check running configuration. This can be set as environment variable. Module will use environment variable value(default:True), unless it is overriden, by specifying it as module parameter.
    type: bool
    default: As set in environment variable   
"""

EXAMPLES = """
- name: Disable LLDP
  icx_lldp:
    state: absent

- name: Enable LLDP
  icx_lldp:
    state: present

- name: Disable LLDP on ports 1/1/1 - 1/1/10, 1/1/20
  icx_lldp:
    interfaces:
     - name:
        - ethernet 1/1/1 to 1/1/10
        - ethernet 1/1/20
       state: absent
    state: present

- name: Enable LLDP on ports 1/1/5 - 1/1/10
  icx_lldp:
    interfaces:
      - name:
        - ethernet 1/1/1 to 1/1/10
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - lldp run
    - no lldp run
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.icx.icx import load_config, run_commands,get_env_diff


def has_lldp(module):
    run_commands(module,['skip'])
    output = run_commands(module, ['show lldp'])
    is_lldp_enable = False
    if len(output) > 0 and "LLDP is not running" not in output[0]:
        is_lldp_enable = True

    return is_lldp_enable

def map_obj_to_commands(module,commands):
    interfaces=module.params.get('interfaces')
    for item in interfaces:
        state=item.get('state')
        if state == 'present':
            for port in item.get('name'):
              if 'all' in port:
                module.fail_json(msg='cannot enable on all the ports')
              else:
                commands.append('lldp enable ports {0}'.format(str(port)))
        elif state == 'absent':
            for port in item.get('name'):
              if 'all' in port:
                module.fail_json(msg='cannot enable on all the ports')
              else:
                commands.append('no lldp enable ports {0}'.format(str(port)))

def main():
    """ main entry point for module execution
    """
    interfaces_spec=dict(
        name=dict(type='list'),
        state=dict(choices=['present', 'absent',
                            'enabled', 'disabled'])
    )

    argument_spec = dict(
        interfaces=dict(type='list',elements='dict',options=interfaces_spec),
        state=dict(choices=['present', 'absent',
                            'enabled', 'disabled']),
        check_running_config=dict(type='bool')
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()

    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    if get_env_diff(module,module.params['check_running_config']) is False:
      HAS_LLDP=None
    else:
      HAS_LLDP = has_lldp(module)

    commands = []
    state=module.params['state']
    if state is None:
        if HAS_LLDP:
            map_obj_to_commands(module,commands)
        else:
            module.fail_json(msg='LLDP is not running')
    else:
        if state == 'absent' and HAS_LLDP is None:
          commands.append('no lldp run')

        if state == 'absent' and HAS_LLDP:
          commands.append('no lldp run')

        elif state == 'present':
            if not HAS_LLDP:
                commands.append('lldp run')
            if module.params.get('interfaces'):
                map_obj_to_commands(module,commands)

    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)

        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
