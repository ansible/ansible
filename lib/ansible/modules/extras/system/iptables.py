#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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

BINS = dict(
    ipv4='iptables',
    ipv6='ip6tables',
)

DOCUMENTATION = '''
---
module: iptables
short_description: Modify the systems iptables
requirements: []
version_added: "2.0"
author: Linus Unnebäck (@LinusU) <linus@folkdatorn.se>
description:
  - Iptables is used to set up, maintain, and inspect the tables of IP packet
    filter rules in the Linux kernel. This module does not handle the saving
    and/or loading of rules, but rather only manipulates the current rules
    that are present in memory. This is the same as the behaviour of the
    "iptables" and "ip6tables" command which this module uses internally.
notes:
  - This module just deals with individual rules. If you need advanced
    chaining of rules the recommended way is to template the iptables restore
    file.
options:
  table:
    description:
      - This option specifies the packet matching table which the command
        should operate on. If the kernel is configured with automatic module
        loading, an attempt will be made to load the appropriate module for
        that table if it is not already there.
    required: false
    default: filter
    choices: [ "filter", "nat", "mangle", "raw", "security" ]
  state:
    description:
      - Whether the rule should be absent or present.
    required: false
    default: present
    choices: [ "present", "absent" ]
  action:
    version_added: "2.2"
    description:
      - Whether the rule should be appended at the bottom or inserted at the
        top. If the rule already exists the chain won't be modified.
    required: false
    default: append
    choices: [ "append", "insert" ]
  ip_version:
    description:
      - Which version of the IP protocol this rule should apply to.
    required: false
    default: ipv4
    choices: [ "ipv4", "ipv6" ]
  chain:
    description:
      - "Chain to operate on. This option can either be the name of a user
        defined chain or any of the builtin chains: 'INPUT', 'FORWARD',
        'OUTPUT', 'PREROUTING', 'POSTROUTING', 'SECMARK', 'CONNSECMARK'."
    required: false
  protocol:
    description:
      - The protocol of the rule or of the packet to check. The specified
        protocol can be one of tcp, udp, udplite, icmp, esp, ah, sctp or the
        special keyword "all", or it can be a numeric value, representing one
        of these protocols or a different one. A protocol name from
        /etc/protocols is also allowed. A "!" argument before the protocol
        inverts the test.  The number zero is equivalent to all. "all" will
        match with all protocols and is taken as default when this option is
        omitted.
    required: false
    default: null
  source:
    description:
      - Source specification. Address can be either a network name,
        a hostname, a network IP address (with /mask), or a plain IP address.
        Hostnames will be resolved once only, before the rule is submitted to
        the kernel. Please note that specifying any name to be resolved with
        a remote query such as DNS is a really bad idea. The mask can be
        either a network mask or a plain number, specifying the number of 1's
        at the left side of the network mask. Thus, a mask of 24 is equivalent
        to 255.255.255.0. A "!" argument before the address specification
        inverts the sense of the address.
    required: false
    default: null
  destination:
    description:
      - Destination specification. Address can be either a network name,
        a hostname, a network IP address (with /mask), or a plain IP address.
        Hostnames will be resolved once only, before the rule is submitted to
        the kernel. Please note that specifying any name to be resolved with
        a remote query such as DNS is a really bad idea. The mask can be
        either a network mask or a plain number, specifying the number of 1's
        at the left side of the network mask. Thus, a mask of 24 is equivalent
        to 255.255.255.0. A "!" argument before the address specification
        inverts the sense of the address.
    required: false
    default: null
  match:
    description:
      - Specifies a match to use, that is, an extension module that tests for
        a specific property. The set of matches make up the condition under
        which a target is invoked. Matches are evaluated first to last if
        specified as an array and work in short-circuit fashion, i.e. if one
        extension yields false, evaluation will stop.
    required: false
    default: []
  jump:
    description:
      - This specifies the target of the rule; i.e., what to do if the packet
        matches it. The target can be a user-defined chain (other than the one
        this rule is in), one of the special builtin targets which decide the
        fate of the packet immediately, or an extension (see EXTENSIONS
        below).  If this option is omitted in a rule (and the goto paramater
        is not used), then matching the rule will have no effect on the
        packet's fate, but the counters on the rule will be incremented.
    required: false
    default: null
  goto:
    description:
      - This specifies that the processing should continue in a user specified
        chain. Unlike the jump argument return will not continue processing in
        this chain but instead in the chain that called us via jump.
    required: false
    default: null
  in_interface:
    description:
      - Name of an interface via which a packet was received (only for packets
        entering the INPUT, FORWARD and PREROUTING chains). When the "!"
        argument is used before the interface name, the sense is inverted. If
        the interface name ends in a "+", then any interface which begins with
        this name will match. If this option is omitted, any interface name
        will match.
    required: false
    default: null
  out_interface:
    description:
      - Name of an interface via which a packet is going to be sent (for
        packets entering the FORWARD, OUTPUT and POSTROUTING chains). When the
        "!" argument is used before the interface name, the sense is inverted.
        If the interface name ends in a "+", then any interface which begins
        with this name will match. If this option is omitted, any interface
        name will match.
    required: false
    default: null
  fragment:
    description:
      - This means that the rule only refers to second and further fragments
        of fragmented packets. Since there is no way to tell the source or
        destination ports of such a packet (or ICMP type), such a packet will
        not match any rules which specify them. When the "!" argument precedes
        fragment argument, the rule will only match head fragments, or
        unfragmented packets.
    required: false
    default: null
  set_counters:
    description:
      - This enables the administrator to initialize the packet and byte
        counters of a rule (during INSERT, APPEND, REPLACE operations).
    required: false
    default: null
  source_port:
    description:
      - "Source port or port range specification. This can either be a service
        name or a port number. An inclusive range can also be specified, using
        the format first:last. If the first port is omitted, '0' is assumed;
        if the last is omitted, '65535' is assumed. If the first port is
        greater than the second one they will be swapped."
    required: false
    default: null
  destination_port:
    description:
      - "Destination port or port range specification. This can either be
        a service name or a port number. An inclusive range can also be
        specified, using the format first:last. If the first port is omitted,
        '0' is assumed; if the last is omitted, '65535' is assumed. If the
        first port is greater than the second one they will be swapped."
    required: false
    default: null
  to_ports:
    description:
      - "This specifies a destination port or range of ports to use: without
        this, the destination port is never altered. This is only valid if the
        rule also specifies one of the following protocols: tcp, udp, dccp or
        sctp."
    required: false
    default: null
  to_destination:
    version_added: "2.1"
    description:
      - "This specifies a destination address to use with DNAT: without
        this, the destination address is never altered."
    required: false
    default: null
  to_source:
    version_added: "2.2"
    description:
      - "This specifies a source address to use with SNAT: without
        this, the source address is never altered."
    required: false
    default: null
  set_dscp_mark:
    version_added: "2.1"
    description:
      - "This allows specifying a DSCP mark to be added to packets.
        It takes either an integer or hex value. Mutually exclusive with
        C(set_dscp_mark_class)."
    required: false
    default: null
  set_dscp_mark_class:
    version_added: "2.1"
    description:
      - "This allows specifying a predefined DiffServ class which will be
        translated to the corresponding DSCP mark. Mutually exclusive with
        C(set_dscp_mark)."
    required: false
    default: null
  comment:
    description:
      - "This specifies a comment that will be added to the rule"
    required: false
    default: null
  ctstate:
    description:
      - "ctstate is a list of the connection states to match in the conntrack
        module.
        Possible states are: 'INVALID', 'NEW', 'ESTABLISHED', 'RELATED',
        'UNTRACKED', 'SNAT', 'DNAT'"
    required: false
    default: []
  limit:
    description:
      - "Specifies the maximum average number of matches to allow per second.
        The number can specify units explicitly, using `/second', `/minute',
        `/hour' or `/day', or parts of them (so `5/second' is the same as
        `5/s')."
    required: false
    default: null
  limit_burst:
    version_added: "2.1"
    description:
      - "Specifies the maximum burst before the above limit kicks in."
    required: false
    default: null
  uid_owner:
    version_added: "2.1"
    description:
      - "Specifies the UID or username to use in match by owner rule."
    required: false
  reject_with:
    version_added: "2.1"
    description:
      - "Specifies the error packet type to return while rejecting."
    required: false
  icmp_type:
    version_added: "2.2"
    description:
      - "This allows specification of the ICMP type, which can be a numeric
        ICMP type, type/code pair, or one of the ICMP type names shown by the
        command 'iptables -p icmp -h'"
    required: false
  flush:
    version_added: "2.2"
    description:
      - "Flushes the specified table and chain of all rules. If no chain is
        specified then the entire table is purged. Ignores all other
        parameters."
    required: false
  policy:
    version_added: "2.2"
    description:
      - "Set the policy for the chain to the given target. Valid targets are
        ACCEPT, DROP, QUEUE, RETURN. Only built in chains can have policies.
        This parameter requires the chain parameter. Ignores all other
        parameters."
'''

EXAMPLES = '''
# Block specific IP
- iptables: chain=INPUT source=8.8.8.8 jump=DROP
  become: yes

# Forward port 80 to 8600
- iptables: table=nat chain=PREROUTING in_interface=eth0 protocol=tcp match=tcp destination_port=80 jump=REDIRECT to_ports=8600 comment="Redirect web traffic to port 8600"
  become: yes

# Allow related and established connections
- iptables: chain=INPUT ctstate=ESTABLISHED,RELATED jump=ACCEPT
  become: yes

# Tag all outbound tcp packets with DSCP mark 8
- iptables: chain=OUTPUT jump=DSCP table=mangle set_dscp_mark=8 protocol=tcp

# Tag all outbound tcp packets with DSCP DiffServ class CS1
- iptables: chain=OUTPUT jump=DSCP table=mangle set_dscp_mark_class=CS1 protocol=tcp
'''


def append_param(rule, param, flag, is_list):
    if is_list:
        for item in param:
            append_param(rule, item, flag, False)
    else:
        if param is not None:
            rule.extend([flag, param])


def append_csv(rule, param, flag):
    if param:
        rule.extend([flag, ','.join(param)])


def append_match(rule, param, match):
    if param:
        rule.extend(['-m', match])


def append_jump(rule, param, jump):
    if param:
        rule.extend(['-j', jump])


def construct_rule(params):
    rule = []
    append_param(rule, params['protocol'], '-p', False)
    append_param(rule, params['source'], '-s', False)
    append_param(rule, params['destination'], '-d', False)
    append_param(rule, params['match'], '-m', True)
    append_param(rule, params['jump'], '-j', False)
    append_param(rule, params['to_destination'], '--to-destination', False)
    append_param(rule, params['to_source'], '--to-source', False)
    append_param(rule, params['goto'], '-g', False)
    append_param(rule, params['in_interface'], '-i', False)
    append_param(rule, params['out_interface'], '-o', False)
    append_param(rule, params['fragment'], '-f', False)
    append_param(rule, params['set_counters'], '-c', False)
    append_param(rule, params['source_port'], '--source-port', False)
    append_param(rule, params['destination_port'], '--destination-port', False)
    append_param(rule, params['to_ports'], '--to-ports', False)
    append_param(rule, params['set_dscp_mark'], '--set-dscp', False)
    append_param(
        rule,
        params['set_dscp_mark_class'],
        '--set-dscp-class',
        False)
    append_match(rule, params['comment'], 'comment')
    append_param(rule, params['comment'], '--comment', False)
    append_match(rule, params['ctstate'], 'state')
    append_csv(rule, params['ctstate'], '--state')
    append_match(rule, params['limit'] or params['limit_burst'], 'limit')
    append_param(rule, params['limit'], '--limit', False)
    append_param(rule, params['limit_burst'], '--limit-burst', False)
    append_match(rule, params['uid_owner'], 'owner')
    append_param(rule, params['uid_owner'], '--uid-owner', False)
    append_jump(rule, params['reject_with'], 'REJECT')
    append_param(rule, params['reject_with'], '--reject-with', False)
    append_param(rule, params['icmp_type'], '--icmp-type', False)
    return rule


def push_arguments(iptables_path, action, params, make_rule=True):
    cmd = [iptables_path]
    cmd.extend(['-t', params['table']])
    cmd.extend([action, params['chain']])
    if make_rule:
        cmd.extend(construct_rule(params))
    return cmd


def check_present(iptables_path, module, params):
    cmd = push_arguments(iptables_path, '-C', params)
    rc, _, __ = module.run_command(cmd, check_rc=False)
    return (rc == 0)


def append_rule(iptables_path, module, params):
    cmd = push_arguments(iptables_path, '-A', params)
    module.run_command(cmd, check_rc=True)


def insert_rule(iptables_path, module, params):
    cmd = push_arguments(iptables_path, '-I', params)
    module.run_command(cmd, check_rc=True)


def remove_rule(iptables_path, module, params):
    cmd = push_arguments(iptables_path, '-D', params)
    module.run_command(cmd, check_rc=True)


def flush_table(iptables_path, module, params):
    cmd = push_arguments(iptables_path, '-F', params, make_rule=False)
    module.run_command(cmd, check_rc=True)


def set_chain_policy(iptables_path, module, params):
    cmd = push_arguments(iptables_path, '-P', params, make_rule=False)
    cmd.append(params['policy'])
    module.run_command(cmd, check_rc=True)


def main():
    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            table=dict(
                required=False,
                default='filter',
                choices=['filter', 'nat', 'mangle', 'raw', 'security']),
            state=dict(
                required=False,
                default='present',
                choices=['present', 'absent']),
            action=dict(
                required=False,
                default='append',
                type='str',
                choices=['append', 'insert']),
            ip_version=dict(
                required=False,
                default='ipv4',
                choices=['ipv4', 'ipv6']),
            chain=dict(required=False, default=None, type='str'),
            protocol=dict(required=False, default=None, type='str'),
            source=dict(required=False, default=None, type='str'),
            to_source=dict(required=False, default=None, type='str'),
            destination=dict(required=False, default=None, type='str'),
            to_destination=dict(required=False, default=None, type='str'),
            match=dict(required=False, default=[], type='list'),
            jump=dict(required=False, default=None, type='str'),
            goto=dict(required=False, default=None, type='str'),
            in_interface=dict(required=False, default=None, type='str'),
            out_interface=dict(required=False, default=None, type='str'),
            fragment=dict(required=False, default=None, type='str'),
            set_counters=dict(required=False, default=None, type='str'),
            source_port=dict(required=False, default=None, type='str'),
            destination_port=dict(required=False, default=None, type='str'),
            to_ports=dict(required=False, default=None, type='str'),
            set_dscp_mark=dict(required=False, default=None, type='str'),
            set_dscp_mark_class=dict(required=False, default=None, type='str'),
            comment=dict(required=False, default=None, type='str'),
            ctstate=dict(required=False, default=[], type='list'),
            limit=dict(required=False, default=None, type='str'),
            limit_burst=dict(required=False, default=None, type='str'),
            uid_owner=dict(required=False, default=None, type='str'),
            reject_with=dict(required=False, default=None, type='str'),
            icmp_type=dict(required=False, default=None, type='str'),
            flush=dict(required=False, default=False, type='bool'),
            policy=dict(
                required=False,
                default=None,
                type='str',
                choices=['ACCEPT', 'DROP', 'QUEUE', 'RETURN']),
        ),
        mutually_exclusive=(
            ['set_dscp_mark', 'set_dscp_mark_class'],
            ['flush', 'policy'],
        ),
    )
    args = dict(
        changed=False,
        failed=False,
        ip_version=module.params['ip_version'],
        table=module.params['table'],
        chain=module.params['chain'],
        flush=module.params['flush'],
        rule=' '.join(construct_rule(module.params)),
        state=module.params['state'],
    )

    ip_version = module.params['ip_version']
    iptables_path = module.get_bin_path(BINS[ip_version], True)

    # Check if chain option is required
    if args['flush'] is False and args['chain'] is None:
        module.fail_json(
            msg="Either chain or flush parameter must be specified.")

    # Flush the table
    if args['flush'] is True:
        flush_table(iptables_path, module, module.params)
        module.exit_json(**args)

    # Set the policy
    if module.params['policy']:
        set_chain_policy(iptables_path, module, module.params)
        module.exit_json(**args)

    insert = (module.params['action'] == 'insert')
    rule_is_present = check_present(iptables_path, module, module.params)
    should_be_present = (args['state'] == 'present')

    # Check if target is up to date
    args['changed'] = (rule_is_present != should_be_present)

    # Check only; don't modify
    if module.check_mode:
        module.exit_json(changed=args['changed'])

    # Target is already up to date
    if args['changed'] is False:
        module.exit_json(**args)

    if should_be_present:
        if insert:
            insert_rule(iptables_path, module, module.params)
        else:
            append_rule(iptables_path, module, module.params)
    else:
        remove_rule(iptables_path, module, module.params)

    module.exit_json(**args)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
