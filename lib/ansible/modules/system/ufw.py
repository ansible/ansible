#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Ahti Kitsik <ak@ahtik.com>
# Copyright: (c) 2014, Jarno Keskikangas <jarno.keskikangas@gmail.com>
# Copyright: (c) 2013, Aleksey Ovcharenko <aleksey.ovcharenko@gmail.com>
# Copyright: (c) 2013, James Martin <jmartin@basho.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ufw
short_description: Manage firewall with UFW
description:
    - Manage firewall with UFW.
version_added: 1.6
author:
    - Aleksey Ovcharenko (@ovcharenko)
    - Jarno Keskikangas (@pyykkis)
    - Ahti Kitsik (@ahtik)
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
    choices: [ disabled, enabled, reloaded, reset ]
  policy:
    description:
      - Change the default policy for incoming or outgoing traffic.
    aliases: [ default ]
    choices: [ allow, deny, reject ]
  direction:
    description:
      - Select direction for a rule or default policy command.
    choices: [ in, incoming, out, outgoing, routed ]
  logging:
    description:
      - Toggles logging. Logged packets use the LOG_KERN syslog facility.
    choices: [ on, off, low, medium, high, full ]
  insert:
    description:
      - Insert the corresponding rule as rule number NUM
  rule:
    description:
      - Add firewall rule
    choices: ['allow', 'deny', 'limit', 'reject']
  log:
    description:
      - Log new connections matched to this rule
    type: bool
  from_ip:
    description:
      - Source IP address.
    aliases: [ from, src ]
    default: any
  from_port:
    description:
      - Source port.
  to_ip:
    description:
      - Destination IP address.
    aliases: [ dest, to]
    default: any
  to_port:
    description:
      - Destination port.
    aliases: [ port ]
  proto:
    description:
      - TCP/IP protocol.
    choices: [ any, tcp, udp, ipv6, esp, ah ]
  name:
    description:
      - Use profile located in C(/etc/ufw/applications.d).
    aliases: [ app ]
  delete:
    description:
      - Delete rule.
    type: bool
  interface:
    description:
      - Specify interface for rule.
    aliases: [ if ]
  route:
    description:
      - Apply the rule to routed/forwarded packets.
    type: bool
  comment:
    description:
      - Add a comment to the rule. Requires UFW version >=0.35.
    version_added: "2.4"
'''

EXAMPLES = '''
- name: Allow everything and enable UFW
  ufw:
    state: enabled
    policy: allow

- name: Set logging
  ufw:
    logging: on

# Sometimes it is desirable to let the sender know when traffic is
# being denied, rather than simply ignoring it. In these cases, use
# reject instead of deny. In addition, log rejected connections:
- ufw:
    rule: reject
    port: auth
    log: yes

# ufw supports connection rate limiting, which is useful for protecting
# against brute-force login attacks. ufw will deny connections if an IP
# address has attempted to initiate 6 or more connections in the last
# 30 seconds. See  http://www.debian-administration.org/articles/187
# for details. Typical usage is:
- ufw:
    rule: limit
    port: ssh
    proto: tcp

# Allow OpenSSH. (Note that as ufw manages its own state, simply removing
# a rule=allow task can leave those ports exposed. Either use delete=yes
# or a separate state=reset task)
- ufw:
    rule: allow
    name: OpenSSH

- name: Delete OpenSSH rule
  ufw:
    rule: allow
    name: OpenSSH
    delete: yes

- name: Deny all access to port 53
  ufw:
    rule: deny
    port: 53

- name: Allow port range 60000-61000
  ufw:
    rule: allow
    port: 60000:61000

- name: Allow all access to tcp port 80
  ufw:
    rule: allow
    port: 80
    proto: tcp

- name: Allow all access from RFC1918 networks to this host
  ufw:
    rule: allow
    src: '{{ item }}'
  with_items:
    - 10.0.0.0/8
    - 172.16.0.0/12
    - 192.168.0.0/16

- name: Deny access to udp port 514 from host 1.2.3.4 and include a comment
  ufw:
    rule: deny
    proto: udp
    src: 1.2.3.4
    port: 514
    comment: Block syslog

- name: Allow incoming access to eth0 from 1.2.3.5 port 5469 to 1.2.3.4 port 5469
  ufw:
    rule: allow
    interface: eth0
    direction: in
    proto: udp
    src: 1.2.3.5
    from_port: 5469
    dest: 1.2.3.4
    to_port: 5469

# Note that IPv6 must be enabled in /etc/default/ufw for IPv6 firewalling to work.
- name: Deny all traffic from the IPv6 2001:db8::/32 to tcp port 25 on this host
  ufw:
    rule: deny
    proto: tcp
    src: 2001:db8::/32
    port: 25

# Can be used to further restrict a global FORWARD policy set to allow
- name: Deny forwarded/routed traffic from subnet 1.2.3.0/24 to subnet 4.5.6.0/24
  ufw:
    rule: deny
    route: yes
    src: 1.2.3.0/24
    dest: 4.5.6.0/24
'''

import re
from operator import itemgetter

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', choices=['enabled', 'disabled', 'reloaded', 'reset']),
            default=dict(type='str', aliases=['policy'], choices=['allow', 'deny', 'reject']),
            logging=dict(type='str', choices=['full', 'high', 'low', 'medium', 'off', 'on']),
            direction=dict(type='str', choices=['in', 'incoming', 'out', 'outgoing', 'routed']),
            delete=dict(type='bool', default=False),
            route=dict(type='bool', default=False),
            insert=dict(type='str'),
            rule=dict(type='str', choices=['allow', 'deny', 'limit', 'reject']),
            interface=dict(type='str', aliases=['if']),
            log=dict(type='bool', default=False),
            from_ip=dict(type='str', default='any', aliases=['from', 'src']),
            from_port=dict(type='str'),
            to_ip=dict(type='str', default='any', aliases=['dest', 'to']),
            to_port=dict(type='str', aliases=['port']),
            proto=dict(type='str', aliases=['protocol'], choices=['ah', 'any', 'esp', 'ipv6', 'tcp', 'udp']),
            app=dict(type='str', aliases=['name']),
            comment=dict(type='str'),
        ),
        supports_check_mode=True,
        mutually_exclusive=[
            ['app', 'proto', 'logging']
        ],
    )

    cmds = []

    def execute(cmd):
        cmd = ' '.join(map(itemgetter(-1), filter(itemgetter(0), cmd)))

        cmds.append(cmd)
        (rc, out, err) = module.run_command(cmd)

        if rc != 0:
            module.fail_json(msg=err or out)

    def ufw_version():
        """
        Returns the major and minor version of ufw installed on the system.
        """
        rc, out, err = module.run_command("%s --version" % ufw_bin)
        if rc != 0:
            module.fail_json(
                msg="Failed to get ufw version.", rc=rc, out=out, err=err
            )

        lines = [x for x in out.split('\n') if x.strip() != '']
        if len(lines) == 0:
            module.fail_json(msg="Failed to get ufw version.", rc=0, out=out)

        matches = re.search(r'^ufw.+(\d+)\.(\d+)(?:\.(\d+))?.*$', lines[0])
        if matches is None:
            module.fail_json(msg="Failed to get ufw version.", rc=0, out=out)

        # Convert version to numbers
        major = int(matches.group(1))
        minor = int(matches.group(2))
        rev = 0
        if matches.group(3) is not None:
            rev = int(matches.group(3))

        return major, minor, rev

    params = module.params

    # Ensure at least one of the command arguments are given
    command_keys = ['state', 'default', 'rule', 'logging']
    commands = dict((key, params[key]) for key in command_keys if params[key])

    if len(commands) < 1:
        module.fail_json(msg="Not any of the command arguments %s given" % commands)

    if (params['interface'] is not None and params['direction'] is None):
        module.fail_json(msg="Direction must be specified when creating a rule on an interface")

    # Ensure ufw is available
    ufw_bin = module.get_bin_path('ufw', True)

    # Save the pre state and rules in order to recognize changes
    (_, pre_state, _) = module.run_command(ufw_bin + ' status verbose')
    (_, pre_rules, _) = module.run_command("grep '^### tuple' /lib/ufw/user.rules /lib/ufw/user6.rules /etc/ufw/user.rules /etc/ufw/user6.rules")

    # Execute commands
    for (command, value) in commands.items():
        cmd = [[ufw_bin], [module.check_mode, '--dry-run']]

        if command == 'state':
            states = {'enabled': 'enable', 'disabled': 'disable',
                      'reloaded': 'reload', 'reset': 'reset'}
            execute(cmd + [['-f'], [states[value]]])

        elif command == 'logging':
            execute(cmd + [[command], [value]])

        elif command == 'default':
            execute(cmd + [[command], [value], [params['direction']]])

        elif command == 'rule':
            # Rules are constructed according to the long format
            #
            # ufw [--dry-run] [route] [delete] [insert NUM] allow|deny|reject|limit [in|out on INTERFACE] [log|log-all] \
            #     [from ADDRESS [port PORT]] [to ADDRESS [port PORT]] \
            #     [proto protocol] [app application] [comment COMMENT]
            cmd.append([module.boolean(params['route']), 'route'])
            cmd.append([module.boolean(params['delete']), 'delete'])
            cmd.append([params['insert'], "insert %s" % params['insert']])
            cmd.append([value])
            cmd.append([params['direction'], "%s" % params['direction']])
            cmd.append([params['interface'], "on %s" % params['interface']])
            cmd.append([module.boolean(params['log']), 'log'])

            for (key, template) in [('from_ip', "from %s"), ('from_port', "port %s"),
                                    ('to_ip', "to %s"), ('to_port', "port %s"),
                                    ('proto', "proto %s"), ('app', "app '%s'")]:
                value = params[key]
                cmd.append([value, template % (value)])

            ufw_major, ufw_minor, _ = ufw_version()
            # comment is supported only in ufw version after 0.35
            if (ufw_major == 0 and ufw_minor >= 35) or ufw_major > 0:
                cmd.append([params['comment'], "comment '%s'" % params['comment']])

            execute(cmd)

    # Get the new state
    (_, post_state, _) = module.run_command(ufw_bin + ' status verbose')
    (_, post_rules, _) = module.run_command("grep '^### tuple' /lib/ufw/user.rules /lib/ufw/user6.rules /etc/ufw/user.rules /etc/ufw/user6.rules")
    changed = (pre_state != post_state) or (pre_rules != post_rules)

    return module.exit_json(changed=changed, commands=cmds, msg=post_state.rstrip())


if __name__ == '__main__':
    main()
