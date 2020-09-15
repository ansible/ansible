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

DOCUMENTATION = r'''
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
    type: str
    choices: [ disabled, enabled, reloaded, reset ]
  default:
    description:
      - Change the default policy for incoming or outgoing traffic.
    type: str
    choices: [ allow, deny, reject ]
    aliases: [ policy ]
  direction:
    description:
      - Select direction for a rule or default policy command.
    type: str
    choices: [ in, incoming, out, outgoing, routed ]
  logging:
    description:
      - Toggles logging. Logged packets use the LOG_KERN syslog facility.
    type: str
    choices: [ 'on', 'off', low, medium, high, full ]
  insert:
    description:
      - Insert the corresponding rule as rule number NUM.
      - Note that ufw numbers rules starting with 1.
    type: int
  insert_relative_to:
    description:
      - Allows to interpret the index in I(insert) relative to a position.
      - C(zero) interprets the rule number as an absolute index (i.e. 1 is
        the first rule).
      - C(first-ipv4) interprets the rule number relative to the index of the
        first IPv4 rule, or relative to the position where the first IPv4 rule
        would be if there is currently none.
      - C(last-ipv4) interprets the rule number relative to the index of the
        last IPv4 rule, or relative to the position where the last IPv4 rule
        would be if there is currently none.
      - C(first-ipv6) interprets the rule number relative to the index of the
        first IPv6 rule, or relative to the position where the first IPv6 rule
        would be if there is currently none.
      - C(last-ipv6) interprets the rule number relative to the index of the
        last IPv6 rule, or relative to the position where the last IPv6 rule
        would be if there is currently none.
    type: str
    choices: [ first-ipv4, first-ipv6, last-ipv4, last-ipv6, zero ]
    default: zero
    version_added: "2.8"
  rule:
    description:
      - Add firewall rule
    type: str
    choices: [ allow, deny, limit, reject ]
  log:
    description:
      - Log new connections matched to this rule
    type: bool
  from_ip:
    description:
      - Source IP address.
    type: str
    default: any
    aliases: [ from, src ]
  from_port:
    description:
      - Source port.
    type: str
  to_ip:
    description:
      - Destination IP address.
    type: str
    default: any
    aliases: [ dest, to]
  to_port:
    description:
      - Destination port.
    type: str
    aliases: [ port ]
  proto:
    description:
      - TCP/IP protocol.
    type: str
    choices: [ any, tcp, udp, ipv6, esp, ah, gre, igmp ]
    aliases: [ protocol ]
  name:
    description:
      - Use profile located in C(/etc/ufw/applications.d).
    type: str
    aliases: [ app ]
  delete:
    description:
      - Delete rule.
    type: bool
  interface:
    description:
      - Specify interface for rule.
    type: str
    aliases: [ if ]
  route:
    description:
      - Apply the rule to routed/forwarded packets.
    type: bool
  comment:
    description:
      - Add a comment to the rule. Requires UFW version >=0.35.
    type: str
    version_added: "2.4"
'''

EXAMPLES = r'''
- name: Allow everything and enable UFW
  ufw:
    state: enabled
    policy: allow

- name: Set logging
  ufw:
    logging: 'on'

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
    port: '53'

- name: Allow port range 60000-61000
  ufw:
    rule: allow
    port: 60000:61000
    proto: tcp

- name: Allow all access to tcp port 80
  ufw:
    rule: allow
    port: '80'
    proto: tcp

- name: Allow all access from RFC1918 networks to this host
  ufw:
    rule: allow
    src: '{{ item }}'
  loop:
    - 10.0.0.0/8
    - 172.16.0.0/12
    - 192.168.0.0/16

- name: Deny access to udp port 514 from host 1.2.3.4 and include a comment
  ufw:
    rule: deny
    proto: udp
    src: 1.2.3.4
    port: '514'
    comment: Block syslog

- name: Allow incoming access to eth0 from 1.2.3.5 port 5469 to 1.2.3.4 port 5469
  ufw:
    rule: allow
    interface: eth0
    direction: in
    proto: udp
    src: 1.2.3.5
    from_port: '5469'
    dest: 1.2.3.4
    to_port: '5469'

# Note that IPv6 must be enabled in /etc/default/ufw for IPv6 firewalling to work.
- name: Deny all traffic from the IPv6 2001:db8::/32 to tcp port 25 on this host
  ufw:
    rule: deny
    proto: tcp
    src: 2001:db8::/32
    port: '25'

- name: Deny all IPv6 traffic to tcp port 20 on this host
  # this should be the first IPv6 rule
  ufw:
    rule: deny
    proto: tcp
    port: '20'
    to_ip: "::"
    insert: 0
    insert_relative_to: first-ipv6

- name: Deny all IPv4 traffic to tcp port 20 on this host
  # This should be the third to last IPv4 rule
  # (insert: -1 addresses the second to last IPv4 rule;
  #  so the new rule will be inserted before the second
  #  to last IPv4 rule, and will be come the third to last
  #  IPv4 rule.)
  ufw:
    rule: deny
    proto: tcp
    port: '20'
    to_ip: "::"
    insert: -1
    insert_relative_to: last-ipv4

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


def compile_ipv4_regexp():
    r = r"((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}"
    r += r"(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])"
    return re.compile(r)


def compile_ipv6_regexp():
    """
    validation pattern provided by :
    https://stackoverflow.com/questions/53497/regular-expression-that-matches-
    valid-ipv6-addresses#answer-17871737
    """
    r = r"(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:"
    r += r"|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}"
    r += r"(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4})"
    r += r"{1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]"
    r += r"{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]"
    r += r"{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4})"
    r += r"{0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]"
    r += r"|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}"
    r += r"[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}"
    r += r"[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))"
    return re.compile(r)


def main():
    command_keys = ['state', 'default', 'rule', 'logging']

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', choices=['enabled', 'disabled', 'reloaded', 'reset']),
            default=dict(type='str', aliases=['policy'], choices=['allow', 'deny', 'reject']),
            logging=dict(type='str', choices=['full', 'high', 'low', 'medium', 'off', 'on']),
            direction=dict(type='str', choices=['in', 'incoming', 'out', 'outgoing', 'routed']),
            delete=dict(type='bool', default=False),
            route=dict(type='bool', default=False),
            insert=dict(type='int'),
            insert_relative_to=dict(choices=['zero', 'first-ipv4', 'last-ipv4', 'first-ipv6', 'last-ipv6'], default='zero'),
            rule=dict(type='str', choices=['allow', 'deny', 'limit', 'reject']),
            interface=dict(type='str', aliases=['if']),
            log=dict(type='bool', default=False),
            from_ip=dict(type='str', default='any', aliases=['from', 'src']),
            from_port=dict(type='str'),
            to_ip=dict(type='str', default='any', aliases=['dest', 'to']),
            to_port=dict(type='str', aliases=['port']),
            proto=dict(type='str', aliases=['protocol'], choices=['ah', 'any', 'esp', 'ipv6', 'tcp', 'udp', 'gre', 'igmp']),
            name=dict(type='str', aliases=['app']),
            comment=dict(type='str'),
        ),
        supports_check_mode=True,
        mutually_exclusive=[
            ['name', 'proto', 'logging'],
        ],
        required_one_of=([command_keys]),
        required_by=dict(
            interface=('direction', ),
        ),
    )

    cmds = []

    ipv4_regexp = compile_ipv4_regexp()
    ipv6_regexp = compile_ipv6_regexp()

    def filter_line_that_not_start_with(pattern, content):
        return ''.join([line for line in content.splitlines(True) if line.startswith(pattern)])

    def filter_line_that_contains(pattern, content):
        return [line for line in content.splitlines(True) if pattern in line]

    def filter_line_that_not_contains(pattern, content):
        return ''.join([line for line in content.splitlines(True) if not line.contains(pattern)])

    def filter_line_that_match_func(match_func, content):
        return ''.join([line for line in content.splitlines(True) if match_func(line) is not None])

    def filter_line_that_contains_ipv4(content):
        return filter_line_that_match_func(ipv4_regexp.search, content)

    def filter_line_that_contains_ipv6(content):
        return filter_line_that_match_func(ipv6_regexp.search, content)

    def is_starting_by_ipv4(ip):
        return ipv4_regexp.match(ip) is not None

    def is_starting_by_ipv6(ip):
        return ipv6_regexp.match(ip) is not None

    def execute(cmd, ignore_error=False):
        cmd = ' '.join(map(itemgetter(-1), filter(itemgetter(0), cmd)))

        cmds.append(cmd)
        (rc, out, err) = module.run_command(cmd, environ_update={"LANG": "C"})

        if rc != 0 and not ignore_error:
            module.fail_json(msg=err or out, commands=cmds)

        return out

    def get_current_rules():
        user_rules_files = ["/lib/ufw/user.rules",
                            "/lib/ufw/user6.rules",
                            "/etc/ufw/user.rules",
                            "/etc/ufw/user6.rules",
                            "/var/lib/ufw/user.rules",
                            "/var/lib/ufw/user6.rules"]

        cmd = [[grep_bin], ["-h"], ["'^### tuple'"]]

        cmd.extend([[f] for f in user_rules_files])
        return execute(cmd, ignore_error=True)

    def ufw_version():
        """
        Returns the major and minor version of ufw installed on the system.
        """
        out = execute([[ufw_bin], ["--version"]])

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

    commands = dict((key, params[key]) for key in command_keys if params[key])

    # Ensure ufw is available
    ufw_bin = module.get_bin_path('ufw', True)
    grep_bin = module.get_bin_path('grep', True)

    # Save the pre state and rules in order to recognize changes
    pre_state = execute([[ufw_bin], ['status verbose']])
    pre_rules = get_current_rules()

    changed = False

    # Execute filter
    for (command, value) in commands.items():

        cmd = [[ufw_bin], [module.check_mode, '--dry-run']]

        if command == 'state':
            states = {'enabled': 'enable', 'disabled': 'disable',
                      'reloaded': 'reload', 'reset': 'reset'}

            if value in ['reloaded', 'reset']:
                changed = True

            if module.check_mode:
                # "active" would also match "inactive", hence the space
                ufw_enabled = pre_state.find(" active") != -1
                if (value == 'disabled' and ufw_enabled) or (value == 'enabled' and not ufw_enabled):
                    changed = True
            else:
                execute(cmd + [['-f'], [states[value]]])

        elif command == 'logging':
            extract = re.search(r'Logging: (on|off)(?: \(([a-z]+)\))?', pre_state)
            if extract:
                current_level = extract.group(2)
                current_on_off_value = extract.group(1)
                if value != "off":
                    if current_on_off_value == "off":
                        changed = True
                    elif value != "on" and value != current_level:
                        changed = True
                elif current_on_off_value != "off":
                    changed = True
            else:
                changed = True

            if not module.check_mode:
                execute(cmd + [[command], [value]])

        elif command == 'default':
            if params['direction'] not in ['outgoing', 'incoming', 'routed', None]:
                module.fail_json(msg='For default, direction must be one of "outgoing", "incoming" and "routed", or direction must not be specified.')
            if module.check_mode:
                regexp = r'Default: (deny|allow|reject) \(incoming\), (deny|allow|reject) \(outgoing\), (deny|allow|reject|disabled) \(routed\)'
                extract = re.search(regexp, pre_state)
                if extract is not None:
                    current_default_values = {}
                    current_default_values["incoming"] = extract.group(1)
                    current_default_values["outgoing"] = extract.group(2)
                    current_default_values["routed"] = extract.group(3)
                    v = current_default_values[params['direction'] or 'incoming']
                    if v not in (value, 'disabled'):
                        changed = True
                else:
                    changed = True
            else:
                execute(cmd + [[command], [value], [params['direction']]])

        elif command == 'rule':
            if params['direction'] not in ['in', 'out', None]:
                module.fail_json(msg='For rules, direction must be one of "in" and "out", or direction must not be specified.')
            # Rules are constructed according to the long format
            #
            # ufw [--dry-run] [route] [delete] [insert NUM] allow|deny|reject|limit [in|out on INTERFACE] [log|log-all] \
            #     [from ADDRESS [port PORT]] [to ADDRESS [port PORT]] \
            #     [proto protocol] [app application] [comment COMMENT]
            cmd.append([module.boolean(params['route']), 'route'])
            cmd.append([module.boolean(params['delete']), 'delete'])
            if params['insert'] is not None:
                relative_to_cmd = params['insert_relative_to']
                if relative_to_cmd == 'zero':
                    insert_to = params['insert']
                else:
                    (dummy, numbered_state, dummy) = module.run_command([ufw_bin, 'status', 'numbered'])
                    numbered_line_re = re.compile(R'^\[ *([0-9]+)\] ')
                    lines = [(numbered_line_re.match(line), '(v6)' in line) for line in numbered_state.splitlines()]
                    lines = [(int(matcher.group(1)), ipv6) for (matcher, ipv6) in lines if matcher]
                    last_number = max([no for (no, ipv6) in lines]) if lines else 0
                    has_ipv4 = any([not ipv6 for (no, ipv6) in lines])
                    has_ipv6 = any([ipv6 for (no, ipv6) in lines])
                    if relative_to_cmd == 'first-ipv4':
                        relative_to = 1
                    elif relative_to_cmd == 'last-ipv4':
                        relative_to = max([no for (no, ipv6) in lines if not ipv6]) if has_ipv4 else 1
                    elif relative_to_cmd == 'first-ipv6':
                        relative_to = max([no for (no, ipv6) in lines if not ipv6]) + 1 if has_ipv4 else 1
                    elif relative_to_cmd == 'last-ipv6':
                        relative_to = last_number if has_ipv6 else last_number + 1
                    insert_to = params['insert'] + relative_to
                    if insert_to > last_number:
                        # ufw does not like it when the insert number is larger than the
                        # maximal rule number for IPv4/IPv6.
                        insert_to = None
                cmd.append([insert_to is not None, "insert %s" % insert_to])
            cmd.append([value])
            cmd.append([params['direction'], "%s" % params['direction']])
            cmd.append([params['interface'], "on %s" % params['interface']])
            cmd.append([module.boolean(params['log']), 'log'])

            for (key, template) in [('from_ip', "from %s"), ('from_port', "port %s"),
                                    ('to_ip', "to %s"), ('to_port', "port %s"),
                                    ('proto', "proto %s"), ('name', "app '%s'")]:
                value = params[key]
                cmd.append([value, template % (value)])

            ufw_major, ufw_minor, dummy = ufw_version()
            # comment is supported only in ufw version after 0.35
            if (ufw_major == 0 and ufw_minor >= 35) or ufw_major > 0:
                cmd.append([params['comment'], "comment '%s'" % params['comment']])

            rules_dry = execute(cmd)

            if module.check_mode:

                nb_skipping_line = len(filter_line_that_contains("Skipping", rules_dry))

                if not (nb_skipping_line > 0 and nb_skipping_line == len(rules_dry.splitlines(True))):

                    rules_dry = filter_line_that_not_start_with("### tuple", rules_dry)
                    # ufw dry-run doesn't send all rules so have to compare ipv4 or ipv6 rules
                    if is_starting_by_ipv4(params['from_ip']) or is_starting_by_ipv4(params['to_ip']):
                        if filter_line_that_contains_ipv4(pre_rules) != filter_line_that_contains_ipv4(rules_dry):
                            changed = True
                    elif is_starting_by_ipv6(params['from_ip']) or is_starting_by_ipv6(params['to_ip']):
                        if filter_line_that_contains_ipv6(pre_rules) != filter_line_that_contains_ipv6(rules_dry):
                            changed = True
                    elif pre_rules != rules_dry:
                        changed = True

    # Get the new state
    if module.check_mode:
        return module.exit_json(changed=changed, commands=cmds)
    else:
        post_state = execute([[ufw_bin], ['status'], ['verbose']])
        if not changed:
            post_rules = get_current_rules()
            changed = (pre_state != post_state) or (pre_rules != post_rules)
        return module.exit_json(changed=changed, commands=cmds, msg=post_state.rstrip())


if __name__ == '__main__':
    main()
