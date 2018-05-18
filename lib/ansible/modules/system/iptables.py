#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2015, Linus Unnebäck <linus@folkdatorn.se>
# Copyright: (c) 2017, Sébastien DA ROCHA <sebastien@da-rocha.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = '''
---
module: iptables
short_description: Modify the systems iptables
version_added: "2.0"
author:
- Linus Unnebäck (@LinusU) <linus@folkdatorn.se>
- Sébastien DA ROCHA (@sebastiendarocha)
description:
  - Iptables is used to set up, maintain, and inspect the tables of IP packet
    filter rules in the Linux kernel.
  - This module does not handle the saving and/or loading of rules, but rather
    only manipulates the current rules that are present in memory. This is the
    same as the behaviour of the C(iptables) and C(ip6tables) command which
    this module uses internally.
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
    choices: [ filter, nat, mangle, raw, security ]
    default: filter
  state:
    description:
      - Whether the rule should be absent or present.
    choices: [ absent, present ]
    default: present
  action:
    description:
      - Whether the rule should be appended at the bottom or inserted at the top.
      - If the rule already exists the chain won't be modified.
    choices: [ append, insert ]
    default: append
    version_added: "2.2"
  rule_num:
    description:
      - Insert the rule as the given rule number. This works only with
        action = 'insert'.
    version_added: "2.5"
  ip_version:
    description:
      - Which version of the IP protocol this rule should apply to.
    choices: [ ipv4, ipv6 ]
    default: ipv4
  chain:
    description:
      - Chain to operate on.
      - "This option can either be the name of a user defined chain or any of
        the builtin chains: 'INPUT', 'FORWARD', 'OUTPUT', 'PREROUTING',
        'POSTROUTING', 'SECMARK', 'CONNSECMARK'."
  protocol:
    description:
      - The protocol of the rule or of the packet to check.
      - The specified protocol can be one of tcp, udp, udplite, icmp, esp,
        ah, sctp or the special keyword "all", or it can be a numeric value,
        representing one of these protocols or a different one. A protocol
        name from /etc/protocols is also allowed. A "!" argument before the
        protocol inverts the test.  The number zero is equivalent to all.
        "all" will match with all protocols and is taken as default when this
        option is omitted.
  source:
    description:
      - Source specification.
      - Address can be either a network name, a hostname, a network IP address
        (with /mask), or a plain IP address.
      - Hostnames will be resolved once only, before the rule is submitted to
        the kernel. Please note that specifying any name to be resolved with
        a remote query such as DNS is a really bad idea.
      - The mask can be either a network mask or a plain number, specifying
        the number of 1's at the left side of the network mask. Thus, a mask
        of 24 is equivalent to 255.255.255.0. A "!" argument before the
        address specification inverts the sense of the address.
  destination:
    description:
      - Destination specification.
      - Address can be either a network name, a hostname, a network IP address
        (with /mask), or a plain IP address.
      - Hostnames will be resolved once only, before the rule is submitted to
        the kernel. Please note that specifying any name to be resolved with
        a remote query such as DNS is a really bad idea.
      - The mask can be either a network mask or a plain number, specifying
        the number of 1's at the left side of the network mask. Thus, a mask
        of 24 is equivalent to 255.255.255.0. A "!" argument before the
        address specification inverts the sense of the address.
  tcp_flags:
    description:
      - TCP flags specification.
      - C(tcp_flags) expects a dict with the two keys C(flags) and C(flags_set).
    default: {}
    version_added: "2.4"
    suboptions:
        flags:
            description:
                - List of flags you want to examine.
        flags_set:
            description:
                - Flags to be set.
  match:
    description:
      - Specifies a match to use, that is, an extension module that tests for
        a specific property. The set of matches make up the condition under
        which a target is invoked. Matches are evaluated first to last if
        specified as an array and work in short-circuit fashion, i.e. if one
        extension yields false, evaluation will stop.
    default: []
  jump:
    description:
      - This specifies the target of the rule; i.e., what to do if the packet
        matches it. The target can be a user-defined chain (other than the one
        this rule is in), one of the special builtin targets which decide the
        fate of the packet immediately, or an extension (see EXTENSIONS
        below).  If this option is omitted in a rule (and the goto parameter
        is not used), then matching the rule will have no effect on the
        packet's fate, but the counters on the rule will be incremented.
  log_prefix:
    description:
      - Specifies a log text for the rule. Only make sense with a LOG jump.
    version_added: "2.5"
  goto:
    description:
      - This specifies that the processing should continue in a user specified
        chain. Unlike the jump argument return will not continue processing in
        this chain but instead in the chain that called us via jump.
  in_interface:
    description:
      - Name of an interface via which a packet was received (only for packets
        entering the INPUT, FORWARD and PREROUTING chains). When the "!"
        argument is used before the interface name, the sense is inverted. If
        the interface name ends in a "+", then any interface which begins with
        this name will match. If this option is omitted, any interface name
        will match.
  out_interface:
    description:
      - Name of an interface via which a packet is going to be sent (for
        packets entering the FORWARD, OUTPUT and POSTROUTING chains). When the
        "!" argument is used before the interface name, the sense is inverted.
        If the interface name ends in a "+", then any interface which begins
        with this name will match. If this option is omitted, any interface
        name will match.
  fragment:
    description:
      - This means that the rule only refers to second and further fragments
        of fragmented packets. Since there is no way to tell the source or
        destination ports of such a packet (or ICMP type), such a packet will
        not match any rules which specify them. When the "!" argument precedes
        fragment argument, the rule will only match head fragments, or
        unfragmented packets.
  set_counters:
    description:
      - This enables the administrator to initialize the packet and byte
        counters of a rule (during INSERT, APPEND, REPLACE operations).
  source_port:
    description:
      - Source port or port range specification. This can either be a service
        name or a port number. An inclusive range can also be specified, using
        the format first:last. If the first port is omitted, '0' is assumed;
        if the last is omitted, '65535' is assumed. If the first port is
        greater than the second one they will be swapped.
  destination_port:
    description:
      - Destination port or port range specification. This can either be
        a service name or a port number. An inclusive range can also be
        specified, using the format first:last. If the first port is omitted,
        '0' is assumed; if the last is omitted, '65535' is assumed. If the
        first port is greater than the second one they will be swapped.
  to_ports:
    description:
      - "This specifies a destination port or range of ports to use: without
        this, the destination port is never altered. This is only valid if the
        rule also specifies one of the following protocols: tcp, udp, dccp or
        sctp."
  to_destination:
    description:
      - This specifies a destination address to use with DNAT.
      - Without this, the destination address is never altered.
    version_added: "2.1"
  to_source:
    description:
      - This specifies a source address to use with SNAT.
      - Without this, the source address is never altered.
    version_added: "2.2"
  syn:
    description:
      - This allows matching packets that have the SYN bit set and the ACK
        and RST bits unset.
      - When negated, this matches all packets with the RST or the ACK bits set.
    choices: [ ignore, match, negate ]
    default: ignore
    version_added: "2.5"
  set_dscp_mark:
    description:
      - This allows specifying a DSCP mark to be added to packets.
        It takes either an integer or hex value.
      - Mutually exclusive with C(set_dscp_mark_class).
    version_added: "2.1"
  set_dscp_mark_class:
    description:
      - This allows specifying a predefined DiffServ class which will be
        translated to the corresponding DSCP mark.
      - Mutually exclusive with C(set_dscp_mark).
    version_added: "2.1"
  comment:
    description:
      - This specifies a comment that will be added to the rule.
  ctstate:
    description:
      - "C(ctstate) is a list of the connection states to match in the conntrack
        module.
        Possible states are: 'INVALID', 'NEW', 'ESTABLISHED', 'RELATED',
        'UNTRACKED', 'SNAT', 'DNAT'"
    choices: [ DNAT, ESTABLISHED, INVALID, NEW, RELATED, SNAT, UNTRACKED ]
    default: []
  limit:
    description:
      - Specifies the maximum average number of matches to allow per second.
      - The number can specify units explicitly, using `/second', `/minute',
        `/hour' or `/day', or parts of them (so `5/second' is the same as
        `5/s').
  limit_burst:
    description:
      - Specifies the maximum burst before the above limit kicks in.
    version_added: "2.1"
  uid_owner:
    description:
      - Specifies the UID or username to use in match by owner rule. From
        Ansible 2.6 when the C(!) argument is prepended then the it inverts
        the rule to apply instead to all users except that one specified.
    version_added: "2.1"
  reject_with:
    description:
      - 'Specifies the error packet type to return while rejecting. It implies
        "jump: REJECT"'
    version_added: "2.1"
  icmp_type:
    description:
      - This allows specification of the ICMP type, which can be a numeric
        ICMP type, type/code pair, or one of the ICMP type names shown by the
        command 'iptables -p icmp -h'
    version_added: "2.2"
  flush:
    description:
      - Flushes the specified table and chain of all rules.
      - If no chain is specified then the entire table is purged.
      - Ignores all other parameters.
    version_added: "2.2"
  policy:
    description:
      - Set the policy for the chain to the given target.
      - Only built-in chains can have policies.
      - This parameter requires the C(chain) parameter.
      - Ignores all other parameters.
    choices: [ ACCEPT, DROP, QUEUE, RETURN ]
    version_added: "2.2"
'''

EXAMPLES = '''
# Block specific IP
- iptables:
    chain: INPUT
    source: 8.8.8.8
    jump: DROP
  become: yes

# Forward port 80 to 8600
- iptables:
    table: nat
    chain: PREROUTING
    in_interface: eth0
    protocol: tcp
    match: tcp
    destination_port: 80
    jump: REDIRECT
    to_ports: 8600
    comment: Redirect web traffic to port 8600
  become: yes

# Allow related and established connections
- iptables:
    chain: INPUT
    ctstate: ESTABLISHED,RELATED
    jump: ACCEPT
  become: yes

# Allow new incoming SYN packets on TCP port 22 (SSH).
- iptables:
    chain: INPUT
    protocol: tcp
    destination_port: 22
    ctstate: NEW
    syn: match
    jump: ACCEPT
    comment: Accept new SSH connections.

# Tag all outbound tcp packets with DSCP mark 8
- iptables:
    chain: OUTPUT
    jump: DSCP
    table: mangle
    set_dscp_mark: 8
    protocol: tcp

# Tag all outbound tcp packets with DSCP DiffServ class CS1
- iptables:
    chain: OUTPUT
    jump: DSCP
    table: mangle
    set_dscp_mark_class: CS1
    protocol: tcp

# Insert a rule on line 5
- iptables:
    chain: INPUT
    protocol: tcp
    destination_port: 8080
    jump: ACCEPT
    rule_num: 5

# Set the policy for the INPUT chain to DROP
- iptables:
    chain: INPUT
    policy: DROP

# Reject tcp with tcp-reset
- iptables:
    chain: INPUT
    protocol: tcp
    reject_with: tcp-reset
    ip_version: ipv4

# Set tcp flags
- iptables:
    chain: OUTPUT
    jump: DROP
    protocol: tcp
    tcp_flags:
      flags: ALL
      flags_set:
        - ACK
        - RST
        - SYN
        - FIN
'''

import re

from ansible.module_utils.basic import AnsibleModule


BINS = dict(
    ipv4='iptables',
    ipv6='ip6tables',
)

ICMP_TYPE_OPTIONS = dict(
    ipv4='--icmp-type',
    ipv6='--icmpv6-type',
)


def append_param(rule, param, flag, is_list):
    if is_list:
        for item in param:
            append_param(rule, item, flag, False)
    else:
        if param is not None:
            if param[0] == '!':
                rule.extend(['!', flag, param[1:]])
            else:
                rule.extend([flag, param])


def append_tcp_flags(rule, param, flag):
    if param:
        if 'flags' in param and 'flags_set' in param:
            rule.extend([flag, ','.join(param['flags']), ','.join(param['flags_set'])])


def append_match_flag(rule, param, flag, negatable):
    if param == 'match':
        rule.extend([flag])
    elif negatable and param == 'negate':
        rule.extend(['!', flag])


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
    append_tcp_flags(rule, params['tcp_flags'], '--tcp-flags')
    append_param(rule, params['jump'], '-j', False)
    append_param(rule, params['log_prefix'], '--log-prefix', False)
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
    append_match_flag(rule, params['syn'], '--syn', True)
    append_match(rule, params['comment'], 'comment')
    append_param(rule, params['comment'], '--comment', False)
    if 'conntrack' in params['match']:
        append_csv(rule, params['ctstate'], '--ctstate')
    elif 'state' in params['match']:
        append_csv(rule, params['ctstate'], '--state')
    elif params['ctstate']:
        append_match(rule, params['ctstate'], 'conntrack')
        append_csv(rule, params['ctstate'], '--ctstate')
    append_match(rule, params['limit'] or params['limit_burst'], 'limit')
    append_param(rule, params['limit'], '--limit', False)
    append_param(rule, params['limit_burst'], '--limit-burst', False)
    append_match(rule, params['uid_owner'], 'owner')
    append_match_flag(rule, params['uid_owner'], '--uid-owner', True)
    append_param(rule, params['uid_owner'], '--uid-owner', False)
    if params['jump'] is None:
        append_jump(rule, params['reject_with'], 'REJECT')
    append_param(rule, params['reject_with'], '--reject-with', False)
    append_param(
        rule,
        params['icmp_type'],
        ICMP_TYPE_OPTIONS[params['ip_version']],
        False)
    return rule


def push_arguments(iptables_path, action, params, make_rule=True):
    cmd = [iptables_path]
    cmd.extend(['-t', params['table']])
    cmd.extend([action, params['chain']])
    if action == '-I' and params['rule_num']:
        cmd.extend([params['rule_num']])
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


def get_chain_policy(iptables_path, module, params):
    cmd = push_arguments(iptables_path, '-L', params)
    rc, out, _ = module.run_command(cmd, check_rc=True)
    chain_header = out.split("\n")[0]
    result = re.search(r'\(policy ([A-Z]+)\)', chain_header)
    if result:
        return result.group(1)
    return None


def main():
    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            table=dict(type='str', default='filter', choices=['filter', 'nat', 'mangle', 'raw', 'security']),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            action=dict(type='str', default='append', choices=['append', 'insert']),
            ip_version=dict(type='str', default='ipv4', choices=['ipv4', 'ipv6']),
            chain=dict(type='str'),
            rule_num=dict(type='str'),
            protocol=dict(type='str'),
            source=dict(type='str'),
            to_source=dict(type='str'),
            destination=dict(type='str'),
            to_destination=dict(type='str'),
            match=dict(type='list', default=[]),
            tcp_flags=dict(type='dict',
                           options=dict(
                                flags=dict(type='list'),
                                flags_set=dict(type='list'))
                           ),
            jump=dict(type='str'),
            log_prefix=dict(type='str'),
            goto=dict(type='str'),
            in_interface=dict(type='str'),
            out_interface=dict(type='str'),
            fragment=dict(type='str'),
            set_counters=dict(type='str'),
            source_port=dict(type='str'),
            destination_port=dict(type='str'),
            to_ports=dict(type='str'),
            set_dscp_mark=dict(type='str'),
            set_dscp_mark_class=dict(type='str'),
            comment=dict(type='str'),
            ctstate=dict(type='list', default=[]),
            limit=dict(type='str'),
            limit_burst=dict(type='str'),
            uid_owner=dict(type='str'),
            reject_with=dict(type='str'),
            icmp_type=dict(type='str'),
            syn=dict(type='str', default='ignore', choices=['ignore', 'match', 'negate']),
            flush=dict(type='bool', default=False),
            policy=dict(type='str', choices=['ACCEPT', 'DROP', 'QUEUE', 'RETURN']),
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
        module.fail_json(msg="Either chain or flush parameter must be specified.")

    # Flush the table
    if args['flush'] is True:
        args['changed'] = True
        if not module.check_mode:
            flush_table(iptables_path, module, module.params)

    # Set the policy
    elif module.params['policy']:
        current_policy = get_chain_policy(iptables_path, module, module.params)
        if not current_policy:
            module.fail_json(msg='Can\'t detect current policy')

        changed = current_policy != module.params['policy']
        args['changed'] = changed
        if changed and not module.check_mode:
            set_chain_policy(iptables_path, module, module.params)

    else:
        insert = (module.params['action'] == 'insert')
        rule_is_present = check_present(iptables_path, module, module.params)
        should_be_present = (args['state'] == 'present')

        # Check if target is up to date
        args['changed'] = (rule_is_present != should_be_present)
        if args['changed'] is False:
            # Target is already up to date
            module.exit_json(**args)

        # Check only; don't modify
        if not module.check_mode:
            if should_be_present:
                if insert:
                    insert_rule(iptables_path, module, module.params)
                else:
                    append_rule(iptables_path, module, module.params)
            else:
                remove_rule(iptables_path, module, module.params)

    module.exit_json(**args)


if __name__ == '__main__':
    main()
