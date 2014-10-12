#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Ahti Kitsik <ak@ahtik.com>
# (c) 2014, Jarno Keskikangas <jarno.keskikangas@gmail.com>
# (c) 2013, Aleksey Ovcharenko <aleksey.ovcharenko@gmail.com>
# (c) 2013, James Martin <jmartin@basho.com>
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

DOCUMENTATION = '''
---
module: ufw
short_description: Manage firewall with UFW
description:
    - Manage firewall with UFW.
version_added: 1.6
author: Aleksey Ovcharenko, Jarno Keskikangas, Ahti Kitsik
notes:
    - See C(man ufw) for more examples.
requirements:
    - C(ufw) package
options:
  state:
    description:
      - C(enabled) reloads firewall and enables firewall on boot.
      - C(disabled) unloads firewall and disables firewall on boot.
      - C(reloaded) reloads firewall.
      - C(reset) disables and resets firewall to installation defaults.
    required: false
    choices: ['enabled', 'disabled', 'reloaded', 'reset']
  policy:
    description:
      - Change the default policy for incoming or outgoing traffic.
    required: false
    alias: default
    choices: ['allow', 'deny', 'reject']
  direction:
    description:
      - Select direction for a rule or default policy command.
    required: false
    choices: ['in', 'out', 'incoming', 'outgoing', 'routed']
  logging:
    description:
      - Toggles logging. Logged packets use the LOG_KERN syslog facility.
    choices: ['on', 'off', 'low', 'medium', 'high', 'full']
    required: false
  insert:
    description:
      - Insert the corresponding rule as rule number NUM
    required: false
  rule:
    description:
      - Add firewall rule
    required: false
    choices: ['allow', 'deny', 'reject', 'limit']
  log:
    description:
      - Log new connections matched to this rule
    required: false
    choices: ['yes', 'no']
  from_ip:
    description:
      - Source IP address.
    required: false
    aliases: ['from', 'src']
    default: 'any'
  from_port:
    description:
      - Source port.
    required: false
  to_ip:
    description:
      - Destination IP address.
    required: false
    aliases: ['to', 'dest']
    default: 'any'
  to_port:
    description:
      - Destination port.
    required: false
    aliases: ['port']
  proto:
    description:
      - TCP/IP protocol.
    choices: ['any', 'tcp', 'udp', 'ipv6', 'esp', 'ah']
    required: false
  name:
    description:
      - Use profile located in C(/etc/ufw/applications.d)
    required: false
    aliases: ['app']
  delete:
    description:
      - Delete rule.
    required: false
    choices: ['yes', 'no']
  interface:
    description:
      - Specify interface for rule.
    required: false
    aliases: ['if']
'''

EXAMPLES = '''
# Allow everything and enable UFW
ufw: state=enabled policy=allow

# Set logging
ufw: logging=on

# Sometimes it is desirable to let the sender know when traffic is
# being denied, rather than simply ignoring it. In these cases, use
# reject instead of deny. In addition, log rejected connections:
ufw: rule=reject port=auth log=yes

# ufw supports connection rate limiting, which is useful for protecting
# against brute-force login attacks. ufw will deny connections if an IP
# address has attempted to initiate 6 or more connections in the last
# 30 seconds. See  http://www.debian-administration.org/articles/187
# for details. Typical usage is:
ufw: rule=limit port=ssh proto=tcp

# Allow OpenSSH
ufw: rule=allow name=OpenSSH

# Delete OpenSSH rule
ufw: rule=allow name=OpenSSH delete=yes

# Deny all access to port 53:
ufw: rule=deny port=53

# Allow all access to tcp port 80:
ufw: rule=allow port=80 proto=tcp

# Allow all access from RFC1918 networks to this host:
ufw: rule=allow src={{ item }}
with_items:
- 10.0.0.0/8
- 172.16.0.0/12
- 192.168.0.0/16

# Deny access to udp port 514 from host 1.2.3.4:
ufw: rule=deny proto=udp src=1.2.3.4 port=514

# Allow incoming access to eth0 from 1.2.3.5 port 5469 to 1.2.3.4 port 5469
ufw: rule=allow interface=eth0 direction=in proto=udp src=1.2.3.5 from_port=5469 dest=1.2.3.4 to_port=5469

# Deny all traffic from the IPv6 2001:db8::/32 to tcp port 25 on this host.
# Note that IPv6 must be enabled in /etc/default/ufw for IPv6 firewalling to work.
ufw: rule=deny proto=tcp src=2001:db8::/32 port=25
'''

from operator import itemgetter


def main():
    module = AnsibleModule(
        argument_spec = dict(
            state     = dict(default=None,  choices=['enabled', 'disabled', 'reloaded', 'reset']),
            default   = dict(default=None,  aliases=['policy'], choices=['allow', 'deny', 'reject']),
            logging   = dict(default=None,  choices=['on', 'off', 'low', 'medium', 'high', 'full']),
            direction = dict(default=None,  choices=['in', 'incoming', 'out', 'outgoing', 'routed']),
            delete    = dict(default=False, type='bool'),
            insert    = dict(default=None),
            rule      = dict(default=None,  choices=['allow', 'deny', 'reject', 'limit']),
            interface = dict(default=None,  aliases=['if']),
            log       = dict(default=False, type='bool'),
            from_ip   = dict(default='any', aliases=['src', 'from']),
            from_port = dict(default=None),
            to_ip     = dict(default='any', aliases=['dest', 'to']),
            to_port   = dict(default=None,  aliases=['port']),
            proto     = dict(default=None,  aliases=['protocol'], choices=['any', 'tcp', 'udp', 'ipv6', 'esp', 'ah']),
            app       = dict(default=None,  aliases=['name'])
        ),
        supports_check_mode = True,
        mutually_exclusive = [['app', 'proto', 'logging']]
    )

    cmds = []

    def execute(cmd):
        cmd = ' '.join(map(itemgetter(-1), filter(itemgetter(0), cmd)))

        cmds.append(cmd)
        (rc, out, err) = module.run_command(cmd)

        if rc != 0:
            module.fail_json(msg=err or out)

    params = module.params

    # Ensure at least one of the command arguments are given
    command_keys = ['state', 'default', 'rule', 'logging']
    commands = dict((key, params[key]) for key in command_keys if params[key])

    if len(commands) < 1:
        module.fail_json(msg="Not any of the command arguments %s given" % commands)

    if('interface' in params and 'direction' not in params):
      module.fail_json(msg="Direction must be specified when creating a rule on an interface")

    # Ensure ufw is available
    ufw_bin = module.get_bin_path('ufw', True)

    # Save the pre state and rules in order to recognize changes
    (_, pre_state, _) = module.run_command(ufw_bin + ' status verbose')
    (_, pre_rules, _) = module.run_command("grep '^### tuple' /lib/ufw/user*.rules")

    # Execute commands
    for (command, value) in commands.iteritems():
        cmd = [[ufw_bin], [module.check_mode, '--dry-run']]

        if command == 'state':
            states = { 'enabled': 'enable',  'disabled': 'disable',
                       'reloaded': 'reload', 'reset': 'reset' }
            execute(cmd + [['-f'], [states[value]]])

        elif command == 'logging':
            execute(cmd + [[command], [value]])

        elif command == 'default':
            execute(cmd + [[command], [value], [params['direction']]])

        elif command == 'rule':
            # Rules are constructed according to the long format
            #
            # ufw [--dry-run] [delete] [insert NUM] allow|deny|reject|limit [in|out on INTERFACE] [log|log-all] \
            #     [from ADDRESS [port PORT]] [to ADDRESS [port PORT]] \
            #     [proto protocol] [app application]
            cmd.append([module.boolean(params['delete']), 'delete'])
            cmd.append([params['insert'], "insert %s" % params['insert']])
            cmd.append([value])
            cmd.append([module.boolean(params['log']), 'log'])

            for (key, template) in [('direction', "%s"      ), ('interface', "on %s"   ),
                                    ('from_ip',   "from %s" ), ('from_port', "port %s" ),
                                    ('to_ip',     "to %s"   ), ('to_port',   "port %s" ),
                                    ('proto',     "proto %s"), ('app',       "app '%s'")]:

                value = params[key]
                cmd.append([value, template % (value)])

            execute(cmd)

    # Get the new state
    (_, post_state, _) = module.run_command(ufw_bin + ' status verbose')
    (_, post_rules, _) = module.run_command("grep '^### tuple' /lib/ufw/user*.rules")
    changed = (pre_state != post_state) or (pre_rules != post_rules)

    return module.exit_json(changed=changed, commands=cmds, msg=post_state.rstrip())

# import module snippets
from ansible.module_utils.basic import *

main()
