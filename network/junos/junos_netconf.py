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

DOCUMENTATION = """
---
module: junos_netconf
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Configures the Junos Netconf system service
description:
  - This module provides an abstraction that enables and configures
    the netconf system service running on Junos devices.  This module
    can be used to easily enable the Netconf API. Netconf provides
    a programmatic interface for working with configuration and state
    resources as defined in RFC 6242.
extends_documentation_fragment: junos
options:
  listens_on:
    description:
      - This argument specifies the port the netconf service should
        listen on for SSH connections.  The default port as defined
        in RFC 6242 is 830.
    required: true
    default: 830
  state:
    description:
      - Specifies the state of the M(junos_netconf) resource on
        the remote device.  If the O(state) argument is set to
        I(present) the netconf service will be configured.  If the
        O(state) argument is set to I(absent) the netconf service
        will be removed from the configuration.
    required: true
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: enable netconf service on port 830
  junos_netconf:
    listens_on: 830
    state: present

- name: disable netconf service
  junos_netconf:
    state: absent
"""

RETURN = """
"""
import re

def parse_port(config):
    match = re.search(r'port (\d+)', config)
    if match:
        return int(match.group(1))

def get_instance(module):
    cmd = 'show configuration system services netconf'
    cfg = module.run_commands(cmd)[0]
    result = dict(state='absent')
    if cfg:
        result = dict(state='present')
        result['port'] = parse_port(cfg)
    return result

def main():
    """main entry point for module execution
    """

    argument_spec = dict(
        listens_on=dict(type='int', default=830),
        state=dict(default='present', choices=['present', 'absent']),
        transport=dict(default='cli', choices=['cli'])
    )

    module = get_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    state = module.params['state']
    port = module.params['listens_on']

    result = dict(changed=False)

    instance = get_instance(module)
    commands = None

    if state == 'present' and instance.get('state') == 'absent':
        commands = 'set system services netconf ssh port %s' % port
    elif state == 'absent' and instance.get('state') == 'present':
        commands = 'delete system services netconf'
    elif port != instance.get('port'):
        commands = 'set system services netconf ssh port %s' % port

    if commands:
        if not module.check_mode:
            comment = 'configuration updated by junos_netconf'
            module.connection.configure(commands, comment=comment)
        result['changed'] = True

    module.exit_json(**result)

from ansible.module_utils.basic import *
from ansible.module_utils.shell import *
from ansible.module_utils.junos import *

if __name__ == '__main__':
    main()
