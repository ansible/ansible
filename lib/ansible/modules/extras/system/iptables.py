#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Linus Unnebäck <linus@folkdatorn.se>
#
# This file is part of Ansible
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

# import module snippets
from ansible.module_utils.basic import *

DOCUMENTATION = '''
---
module: iptables
short_description: Modify the systems iptables
requirements: []
version_added: "2.0"
author: Linus Unnebäck (@LinusU) <linus@folkdatorn.se>
description: Iptables is used to set up, maintain, and inspect the tables of IPv4 packet filter rules in the Linux kernel.
options:
  table:
    description: Packet matching table to operate on.
    required: false
    default: filter
    choices: [ "filter", "nat", "mangle", "raw", "security" ]
  chain:
    description: Chain to operate on.
    required: true
    choices: [ "INPUT", "FORWARD", "OUTPUT", "PREROUTING", "POSTROUTING", "SECMARK", "CONNSECMARK" ]
  rule:
    description: The rule that should be absent or present
    required: true
  state:
    description: Wheter the rule should be absent or present
    required: false
    default: present
    choices: [ "present", "absent" ]
'''

EXAMPLES = '''
# Block specific IP
- iptables: chain=INPUT rule='-s 8.8.8.8 -j DROP'
  become: yes

# Forward port 80 to 8600
- iptables: table=nat chain=PREROUTING rule='-i eth0 -p tcp -m tcp --dport 80 -j REDIRECT --to-ports 8600'
  become: yes
'''


def push_arguments(iptables_path, action, args):
    cmd = [iptables_path]
    cmd.extend(['-t', args['table']])
    cmd.extend([action, args['chain']])
    cmd.extend(args['rule'].split(' '))
    return cmd


def check_present(iptables_path, module, args):
    cmd = push_arguments(iptables_path, '-C', args)
    rc, _, __ = module.run_command(cmd, check_rc=False)
    return (rc == 0)


def append_rule(iptables_path, module, args):
    cmd = push_arguments(iptables_path, '-A', args)
    module.run_command(cmd, check_rc=True)


def remove_rule(iptables_path, module, args):
    cmd = push_arguments(iptables_path, '-D', args)
    module.run_command(cmd, check_rc=True)


def main():
    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            table=dict(required=False, default='filter', choices=['filter', 'nat', 'mangle', 'raw', 'security']),
            chain=dict(required=True, default=None, choices=['INPUT', 'FORWARD', 'OUTPUT', 'PREROUTING', 'POSTROUTING', 'SECMARK', 'CONNSECMARK']),
            rule=dict(required=True, default=None),
            state=dict(required=False, default='present', choices=['present', 'absent']),
        ),
    )
    args = dict(
        changed=False,
        failed=False,
        table=module.params['table'],
        chain=module.params['chain'],
        rule=module.params['rule'],
        state=module.params['state'],
    )
    iptables_path = module.get_bin_path('iptables', True)
    rule_is_present = check_present(iptables_path, module, args)
    should_be_present = (args['state'] == 'present')

    # Check if target is up to date
    args['changed'] = (rule_is_present != should_be_present)

    # Check only; don't modify
    if module.check_mode:
        module.exit_json(changed=args['changed'])

    # Target is already up to date
    if args['changed'] == False:
        module.exit_json(**args)

    if should_be_present:
        append_rule(iptables_path, module, args)
    else:
        remove_rule(iptables_path, module, args)

    module.exit_json(**args)

if __name__ == '__main__':
    main()
