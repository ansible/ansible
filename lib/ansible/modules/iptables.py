# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Linus Unnebäck <linus@folkdatorn.se>
# Copyright: (c) 2017, Sébastien DA ROCHA <sebastien@da-rocha.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = r"""
---
module: iptables
short_description: Modify iptables rules
version_added: "2.0"
author:
- Linus Unnebäck (@LinusU) <linus@folkdatorn.se>
- Sébastien DA ROCHA (@sebastiendarocha)
description:
  - M(ansible.builtin.iptables) is used to set up, maintain, and inspect the tables of IP packet
    filter rules in the Linux kernel.
  - This module does not handle the saving and/or loading of rules, but rather
    only manipulates the current rules that are present in memory. This is the
    same as the behaviour of the C(iptables) and C(ip6tables) command which
    this module uses internally.
extends_documentation_fragment: action_common_attributes
attributes:
    check_mode:
        support: full
    diff_mode:
        support: none
    platform:
        platforms: linux
notes:
  - This module just deals with individual rules. If you need advanced
    chaining of rules the recommended way is to template the iptables restore
    file.
options:
  table:
    description:
      - This option specifies the packet matching table on which the command should operate.
      - If the kernel is configured with automatic module loading, an attempt will be made
        to load the appropriate module for that table if it is not already there.
    type: str
    choices: [ filter, nat, mangle, raw, security ]
    default: filter
  state:
    description:
      - Whether the rule should be absent or present.
    type: str
    choices: [ absent, present ]
    default: present
  action:
    description:
      - Whether the rule should be appended at the bottom or inserted at the top.
      - If the rule already exists the chain will not be modified.
    type: str
    choices: [ append, insert ]
    default: append
    version_added: "2.2"
  rule_num:
    description:
      - Insert the rule as the given rule number.
      - This works only with O(action=insert).
    type: str
    version_added: "2.5"
  ip_version:
    description:
      - Which version of the IP protocol this rule should apply to.
    type: str
    choices: [ ipv4, ipv6, both ]
    default: ipv4
  chain:
    description:
      - Specify the iptables chain to modify.
      - This could be a user-defined chain or one of the standard iptables chains, like
        V(INPUT), V(FORWARD), V(OUTPUT), V(PREROUTING), V(POSTROUTING), V(SECMARK) or V(CONNSECMARK).
    type: str
  protocol:
    description:
      - The protocol of the rule or of the packet to check.
      - The specified protocol can be one of V(tcp), V(udp), V(udplite), V(icmp), V(ipv6-icmp) or V(icmpv6),
        V(esp), V(ah), V(sctp) or the special keyword V(all), or it can be a numeric value,
        representing one of these protocols or a different one.
      - A protocol name from C(/etc/protocols) is also allowed.
      - A V(!) argument before the protocol inverts the test.
      - The number zero is equivalent to all.
      - V(all) will match with all protocols and is taken as default when this option is omitted.
    type: str
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
        of 24 is equivalent to 255.255.255.0. A V(!) argument before the
        address specification inverts the sense of the address.
    type: str
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
        of 24 is equivalent to 255.255.255.0. A V(!) argument before the
        address specification inverts the sense of the address.
    type: str
  tcp_flags:
    description:
      - TCP flags specification.
      - O(tcp_flags) expects a dict with the two keys C(flags) and C(flags_set).
    type: dict
    version_added: "2.4"
    suboptions:
        flags:
            description:
                - List of flags you want to examine.
            type: list
            elements: str
        flags_set:
            description:
                - Flags to be set.
            type: list
            elements: str
  match:
    description:
      - Specifies a match to use, that is, an extension module that tests for
        a specific property.
      - The set of matches makes up the condition under which a target is invoked.
      - Matches are evaluated first to last if specified as an array and work in short-circuit
        fashion, in other words if one extension yields false, the evaluation will stop.
    type: list
    elements: str
    default: []
  jump:
    description:
      - This specifies the target of the rule; i.e., what to do if the packet matches it.
      - The target can be a user-defined chain (other than the one
        this rule is in), one of the special builtin targets that decide the
        fate of the packet immediately, or an extension (see EXTENSIONS
        below).
      - If this option is omitted in a rule (and the goto parameter
        is not used), then matching the rule will have no effect on the
        packet's fate, but the counters on the rule will be incremented.
    type: str
  gateway:
    description:
      - This specifies the IP address of the host to send the cloned packets.
      - This option is only valid when O(jump=TEE).
    type: str
    version_added: "2.8"
  log_prefix:
    description:
      - Specifies a log text for the rule. Only makes sense with a LOG jump.
    type: str
    version_added: "2.5"
  log_level:
    description:
      - Logging level according to the syslogd-defined priorities.
      - The value can be strings or numbers from 1-8.
      - This parameter is only applicable if O(jump=LOG).
    type: str
    version_added: "2.8"
    choices: [ '0', '1', '2', '3', '4', '5', '6', '7', 'emerg', 'alert', 'crit', 'error', 'warning', 'notice', 'info', 'debug' ]
  goto:
    description:
      - This specifies that the processing should continue in a user-specified chain.
      - Unlike the jump argument return will not continue processing in
        this chain but instead in the chain that called us via jump.
    type: str
  in_interface:
    description:
      - Name of an interface via which a packet was received (only for packets
        entering the V(INPUT), V(FORWARD) and V(PREROUTING) chains).
      - When the V(!) argument is used before the interface name, the sense is inverted.
      - If the interface name ends in a V(+), then any interface which begins with
        this name will match.
      - If this option is omitted, any interface name will match.
    type: str
  out_interface:
    description:
      - Name of an interface via which a packet is going to be sent (for
        packets entering the V(FORWARD), V(OUTPUT) and V(POSTROUTING) chains).
      - When the V(!) argument is used before the interface name, the sense is inverted.
      - If the interface name ends in a V(+), then any interface which begins
        with this name will match.
      - If this option is omitted, any interface name will match.
    type: str
  fragment:
    description:
      - This means that the rule only refers to second and further fragments
        of fragmented packets.
      - Since there is no way to tell the source or destination ports of such
        a packet (or ICMP type), such a packet will not match any rules which specify them.
      - When the "!" argument precedes the fragment argument, the rule will only match head fragments,
        or unfragmented packets.
    type: str
  set_counters:
    description:
      - This enables the administrator to initialize the packet and byte
        counters of a rule (during V(INSERT), V(APPEND), V(REPLACE) operations).
    type: str
  source_port:
    description:
      - Source port or port range specification.
      - This can either be a service name or a port number.
      - An inclusive range can also be specified, using the format C(first:last).
      - If the first port is omitted, V(0) is assumed; if the last is omitted, V(65535) is assumed.
      - If the first port is greater than the second one they will be swapped.
    type: str
  destination_port:
    description:
      - "Destination port or port range specification. This can either be
        a service name or a port number. An inclusive range can also be
        specified, using the format first:last. If the first port is omitted,
        '0' is assumed; if the last is omitted, '65535' is assumed. If the
        first port is greater than the second one they will be swapped.
        This is only valid if the rule also specifies one of the following
        protocols: tcp, udp, dccp or sctp."
    type: str
  destination_ports:
    description:
      - This specifies multiple destination port numbers or port ranges to match in the multiport module.
      - It can only be used in conjunction with the protocols tcp, udp, udplite, dccp and sctp.
    type: list
    elements: str
    default: []
    version_added: "2.11"
  to_ports:
    description:
      - This specifies a destination port or range of ports to use, without
        this, the destination port is never altered.
      - This is only valid if the rule also specifies one of the protocol
        V(tcp), V(udp), V(dccp) or V(sctp).
    type: str
  to_destination:
    description:
      - This specifies a destination address to use with O(ctstate=DNAT).
      - Without this, the destination address is never altered.
    type: str
    version_added: "2.1"
  to_source:
    description:
      - This specifies a source address to use with O(ctstate=SNAT).
      - Without this, the source address is never altered.
    type: str
    version_added: "2.2"
  syn:
    description:
      - This allows matching packets that have the SYN bit set and the ACK
        and RST bits unset.
      - When negated, this matches all packets with the RST or the ACK bits set.
    type: str
    choices: [ ignore, match, negate ]
    default: ignore
    version_added: "2.5"
  set_dscp_mark:
    description:
      - This allows specifying a DSCP mark to be added to packets.
        It takes either an integer or hex value.
      - If the parameter is set, O(jump) is set to V(DSCP).
      - Mutually exclusive with O(set_dscp_mark_class).
    type: str
    version_added: "2.1"
  set_dscp_mark_class:
    description:
      - This allows specifying a predefined DiffServ class which will be
        translated to the corresponding DSCP mark.
      - If the parameter is set, O(jump) is set to V(DSCP).
      - Mutually exclusive with O(set_dscp_mark).
    type: str
    version_added: "2.1"
  comment:
    description:
      - This specifies a comment that will be added to the rule.
    type: str
  ctstate:
    description:
      - A list of the connection states to match in the conntrack module.
      - Possible values are V(INVALID), V(NEW), V(ESTABLISHED), V(RELATED), V(UNTRACKED), V(SNAT), V(DNAT).
    type: list
    elements: str
    default: []
  src_range:
    description:
      - Specifies the source IP range to match the iprange module.
    type: str
    version_added: "2.8"
  dst_range:
    description:
      - Specifies the destination IP range to match in the iprange module.
    type: str
    version_added: "2.8"
  match_set:
    description:
      - Specifies a set name that can be defined by ipset.
      - Must be used together with the O(match_set_flags) parameter.
      - When the V(!) argument is prepended then it inverts the rule.
      - Uses the iptables set extension.
    type: str
    version_added: "2.11"
  match_set_flags:
    description:
      - Specifies the necessary flags for the match_set parameter.
      - Must be used together with the O(match_set) parameter.
      - Uses the iptables set extension.
      - Choices V(dst,dst) and V(src,src) added in version 2.17.
    type: str
    choices: [ "src", "dst", "src,dst", "dst,src", "dst,dst", "src,src" ]
    version_added: "2.11"
  limit:
    description:
      - Specifies the maximum average number of matches to allow per second.
      - The number can specify units explicitly, using C(/second), C(/minute),
        C(/hour) or C(/day), or parts of them (so V(5/second) is the same as
        V(5/s)).
    type: str
  limit_burst:
    description:
      - Specifies the maximum burst before the above limit kicks in.
    type: str
    version_added: "2.1"
  uid_owner:
    description:
      - Specifies the UID or username to use in the match by owner rule.
      - From Ansible 2.6 when the C(!) argument is prepended then the it inverts
        the rule to apply instead to all users except that one specified.
    type: str
    version_added: "2.1"
  gid_owner:
    description:
      - Specifies the GID or group to use in the match by owner rule.
    type: str
    version_added: "2.9"
  reject_with:
    description:
      - 'Specifies the error packet type to return while rejecting. It implies
        C(jump=REJECT).'
    type: str
    version_added: "2.1"
  icmp_type:
    description:
      - This allows specification of the ICMP type, which can be a numeric
        ICMP type, type/code pair, or one of the ICMP type names shown by the
        command C(iptables -p icmp -h).
    type: str
    version_added: "2.2"
  flush:
    description:
      - Flushes the specified table and chain of all rules.
      - If no chain is specified then the entire table is purged.
      - Ignores all other parameters.
    type: bool
    default: false
    version_added: "2.2"
  policy:
    description:
      - Set the policy for the chain to the given target.
      - Only built-in chains can have policies.
      - This parameter requires the O(chain) parameter.
      - If you specify this parameter, all other parameters will be ignored.
      - This parameter is used to set the default policy for the given O(chain).
        Do not confuse this with O(jump) parameter.
    type: str
    choices: [ ACCEPT, DROP, QUEUE, RETURN ]
    version_added: "2.2"
  wait:
    description:
      - Wait N seconds for the xtables lock to prevent multiple instances of
        the program from running concurrently.
    type: str
    version_added: "2.10"
  chain_management:
    description:
      - If V(true) and O(state) is V(present), the chain will be created if needed.
      - If V(true) and O(state) is V(absent), the chain will be deleted if the only
        other parameter passed are O(chain) and optionally O(table).
    type: bool
    default: false
    version_added: "2.13"
  numeric:
    description:
      - This parameter controls the running of the list -action of iptables, which is used internally by the module.
      - Does not affect the actual functionality. Use this if iptables hang when creating a chain or altering policy.
      - If V(true), then iptables skips the DNS-lookup of the IP addresses in a chain when it uses the list -action.
      - Listing is used internally for example when setting a policy or creating a chain.
    type: bool
    default: false
    version_added: "2.15"
"""

EXAMPLES = r"""
- name: Block specific IP
  ansible.builtin.iptables:
    chain: INPUT
    source: 8.8.8.8
    jump: DROP
  become: yes

- name: Forward port 80 to 8600
  ansible.builtin.iptables:
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

- name: Allow related and established connections
  ansible.builtin.iptables:
    chain: INPUT
    ctstate: ESTABLISHED,RELATED
    jump: ACCEPT
  become: yes

- name: Allow new incoming SYN packets on TCP port 22 (SSH)
  ansible.builtin.iptables:
    chain: INPUT
    protocol: tcp
    destination_port: 22
    ctstate: NEW
    syn: match
    jump: ACCEPT
    comment: Accept new SSH connections.

- name: Match on IP ranges
  ansible.builtin.iptables:
    chain: FORWARD
    src_range: 192.168.1.100-192.168.1.199
    dst_range: 10.0.0.1-10.0.0.50
    jump: ACCEPT

- name: Allow source IPs defined in ipset "admin_hosts" on port 22
  ansible.builtin.iptables:
    chain: INPUT
    match_set: admin_hosts
    match_set_flags: src
    destination_port: 22
    jump: ALLOW

- name: Tag all outbound tcp packets with DSCP mark 8
  ansible.builtin.iptables:
    chain: OUTPUT
    jump: DSCP
    table: mangle
    set_dscp_mark: 8
    protocol: tcp

- name: Tag all outbound tcp packets with DSCP DiffServ class CS1
  ansible.builtin.iptables:
    chain: OUTPUT
    jump: DSCP
    table: mangle
    set_dscp_mark_class: CS1
    protocol: tcp

# Create the user-defined chain ALLOWLIST
- iptables:
    chain: ALLOWLIST
    chain_management: true

# Delete the user-defined chain ALLOWLIST
- iptables:
    chain: ALLOWLIST
    chain_management: true
    state: absent

- name: Insert a rule on line 5
  ansible.builtin.iptables:
    chain: INPUT
    protocol: tcp
    destination_port: 8080
    jump: ACCEPT
    action: insert
    rule_num: 5

# Think twice before running following task as this may lock target system
- name: Set the policy for the INPUT chain to DROP
  ansible.builtin.iptables:
    chain: INPUT
    policy: DROP

- name: Reject tcp with tcp-reset
  ansible.builtin.iptables:
    chain: INPUT
    protocol: tcp
    reject_with: tcp-reset
    ip_version: ipv4

- name: Set tcp flags
  ansible.builtin.iptables:
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

- name: Iptables flush filter
  ansible.builtin.iptables:
    chain: "{{ item }}"
    flush: yes
  with_items:  [ 'INPUT', 'FORWARD', 'OUTPUT' ]

- name: Iptables flush nat
  ansible.builtin.iptables:
    table: nat
    chain: '{{ item }}'
    flush: yes
  with_items: [ 'INPUT', 'OUTPUT', 'PREROUTING', 'POSTROUTING' ]

- name: Log packets arriving into an user-defined chain
  ansible.builtin.iptables:
    chain: LOGGING
    action: append
    state: present
    limit: 2/second
    limit_burst: 20
    log_prefix: "IPTABLES:INFO: "
    log_level: info

- name: Allow connections on multiple ports
  ansible.builtin.iptables:
    chain: INPUT
    protocol: tcp
    destination_ports:
      - "80"
      - "443"
      - "8081:8083"
    jump: ACCEPT
"""

import re

from ansible.module_utils.compat.version import LooseVersion

from ansible.module_utils.basic import AnsibleModule


IPTABLES_WAIT_SUPPORT_ADDED = '1.4.20'

IPTABLES_WAIT_WITH_SECONDS_SUPPORT_ADDED = '1.6.0'

BINS = dict(
    ipv4='iptables',
    ipv6='ip6tables',
)

ICMP_TYPE_OPTIONS = dict(
    ipv4='--icmp-type',
    ipv6='--icmpv6-type',
    both='--icmp-type --icmpv6-type',
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


def append_wait(rule, param, flag):
    if param:
        rule.extend([flag, param])


def construct_rule(params):
    rule = []
    append_param(rule, params['protocol'], '-p', False)
    append_param(rule, params['source'], '-s', False)
    append_param(rule, params['destination'], '-d', False)
    append_param(rule, params['match'], '-m', True)
    append_tcp_flags(rule, params['tcp_flags'], '--tcp-flags')
    append_param(rule, params['jump'], '-j', False)
    if params.get('jump') and params['jump'].lower() == 'tee':
        append_param(rule, params['gateway'], '--gateway', False)
    append_param(rule, params['log_prefix'], '--log-prefix', False)
    append_param(rule, params['log_level'], '--log-level', False)
    append_param(rule, params['to_destination'], '--to-destination', False)
    append_match(rule, params['destination_ports'], 'multiport')
    append_csv(rule, params['destination_ports'], '--dports')
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
    if params.get('set_dscp_mark') and params.get('jump').lower() != 'dscp':
        append_jump(rule, params['set_dscp_mark'], 'DSCP')

    append_param(
        rule,
        params['set_dscp_mark_class'],
        '--set-dscp-class',
        False)
    if params.get('set_dscp_mark_class') and params.get('jump').lower() != 'dscp':
        append_jump(rule, params['set_dscp_mark_class'], 'DSCP')
    append_match_flag(rule, params['syn'], '--syn', True)
    if 'conntrack' in params['match']:
        append_csv(rule, params['ctstate'], '--ctstate')
    elif 'state' in params['match']:
        append_csv(rule, params['ctstate'], '--state')
    elif params['ctstate']:
        append_match(rule, params['ctstate'], 'conntrack')
        append_csv(rule, params['ctstate'], '--ctstate')
    if 'iprange' in params['match']:
        append_param(rule, params['src_range'], '--src-range', False)
        append_param(rule, params['dst_range'], '--dst-range', False)
    elif params['src_range'] or params['dst_range']:
        append_match(rule, params['src_range'] or params['dst_range'], 'iprange')
        append_param(rule, params['src_range'], '--src-range', False)
        append_param(rule, params['dst_range'], '--dst-range', False)
    if 'set' in params['match']:
        append_param(rule, params['match_set'], '--match-set', False)
        append_match_flag(rule, 'match', params['match_set_flags'], False)
    elif params['match_set']:
        append_match(rule, params['match_set'], 'set')
        append_param(rule, params['match_set'], '--match-set', False)
        append_match_flag(rule, 'match', params['match_set_flags'], False)
    append_match(rule, params['limit'] or params['limit_burst'], 'limit')
    append_param(rule, params['limit'], '--limit', False)
    append_param(rule, params['limit_burst'], '--limit-burst', False)
    append_match(rule, params['uid_owner'], 'owner')
    append_match_flag(rule, params['uid_owner'], '--uid-owner', True)
    append_param(rule, params['uid_owner'], '--uid-owner', False)
    append_match(rule, params['gid_owner'], 'owner')
    append_match_flag(rule, params['gid_owner'], '--gid-owner', True)
    append_param(rule, params['gid_owner'], '--gid-owner', False)
    if params['jump'] is None:
        append_jump(rule, params['reject_with'], 'REJECT')
        append_jump(rule, params['set_dscp_mark_class'], 'DSCP')
        append_jump(rule, params['set_dscp_mark'], 'DSCP')

    append_param(rule, params['reject_with'], '--reject-with', False)
    append_param(
        rule,
        params['icmp_type'],
        ICMP_TYPE_OPTIONS[params['ip_version']],
        False)
    append_match(rule, params['comment'], 'comment')
    append_param(rule, params['comment'], '--comment', False)
    return rule


def push_arguments(iptables_path, action, params, make_rule=True):
    cmd = [iptables_path]
    cmd.extend(['-t', params['table']])
    cmd.extend([action, params['chain']])
    if action == '-I' and params['rule_num']:
        cmd.extend([params['rule_num']])
    if params['wait']:
        cmd.extend(['-w', params['wait']])
    if make_rule:
        cmd.extend(construct_rule(params))
    return cmd


def check_rule_present(iptables_path, module, params):
    cmd = push_arguments(iptables_path, '-C', params)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
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
    cmd = push_arguments(iptables_path, '-L', params, make_rule=False)
    if module.params['numeric']:
        cmd.append('--numeric')
    rc, out, err = module.run_command(cmd, check_rc=True)
    chain_header = out.split("\n")[0]
    result = re.search(r'\(policy ([A-Z]+)\)', chain_header)
    if result:
        return result.group(1)
    return None


def get_iptables_version(iptables_path, module):
    cmd = [iptables_path, '--version']
    rc, out, err = module.run_command(cmd, check_rc=True)
    return out.split('v')[1].rstrip('\n')


def create_chain(iptables_path, module, params):
    cmd = push_arguments(iptables_path, '-N', params, make_rule=False)
    module.run_command(cmd, check_rc=True)


def check_chain_present(iptables_path, module, params):
    cmd = push_arguments(iptables_path, '-L', params, make_rule=False)
    if module.params['numeric']:
        cmd.append('--numeric')
    rc, out, err = module.run_command(cmd, check_rc=False)
    return (rc == 0)


def delete_chain(iptables_path, module, params):
    cmd = push_arguments(iptables_path, '-X', params, make_rule=False)
    module.run_command(cmd, check_rc=True)


def main():
    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            table=dict(type='str', default='filter', choices=['filter', 'nat', 'mangle', 'raw', 'security']),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            action=dict(type='str', default='append', choices=['append', 'insert']),
            ip_version=dict(type='str', default='ipv4', choices=['ipv4', 'ipv6', 'both']),
            chain=dict(type='str'),
            rule_num=dict(type='str'),
            protocol=dict(type='str'),
            wait=dict(type='str'),
            source=dict(type='str'),
            to_source=dict(type='str'),
            destination=dict(type='str'),
            to_destination=dict(type='str'),
            match=dict(type='list', elements='str', default=[]),
            tcp_flags=dict(type='dict',
                           options=dict(
                                flags=dict(type='list', elements='str'),
                                flags_set=dict(type='list', elements='str'))
                           ),
            jump=dict(type='str'),
            gateway=dict(type='str'),
            log_prefix=dict(type='str'),
            log_level=dict(type='str',
                           choices=['0', '1', '2', '3', '4', '5', '6', '7',
                                    'emerg', 'alert', 'crit', 'error',
                                    'warning', 'notice', 'info', 'debug'],
                           default=None,
                           ),
            goto=dict(type='str'),
            in_interface=dict(type='str'),
            out_interface=dict(type='str'),
            fragment=dict(type='str'),
            set_counters=dict(type='str'),
            source_port=dict(type='str'),
            destination_port=dict(type='str'),
            destination_ports=dict(type='list', elements='str', default=[]),
            to_ports=dict(type='str'),
            set_dscp_mark=dict(type='str'),
            set_dscp_mark_class=dict(type='str'),
            comment=dict(type='str'),
            ctstate=dict(type='list', elements='str', default=[]),
            src_range=dict(type='str'),
            dst_range=dict(type='str'),
            match_set=dict(type='str'),
            match_set_flags=dict(
                type='str',
                choices=['src', 'dst', 'src,dst', 'dst,src', 'src,src', 'dst,dst']
            ),
            limit=dict(type='str'),
            limit_burst=dict(type='str'),
            uid_owner=dict(type='str'),
            gid_owner=dict(type='str'),
            reject_with=dict(type='str'),
            icmp_type=dict(type='str'),
            syn=dict(type='str', default='ignore', choices=['ignore', 'match', 'negate']),
            flush=dict(type='bool', default=False),
            policy=dict(type='str', choices=['ACCEPT', 'DROP', 'QUEUE', 'RETURN']),
            chain_management=dict(type='bool', default=False),
            numeric=dict(type='bool', default=False),
        ),
        mutually_exclusive=(
            ['set_dscp_mark', 'set_dscp_mark_class'],
            ['flush', 'policy'],
        ),
        required_by=dict(
            set_dscp_mark=('jump',),
            set_dscp_mark_class=('jump',),
        ),
        required_if=[
            ['jump', 'TEE', ['gateway']],
            ['jump', 'tee', ['gateway']],
            ['flush', False, ['chain']],
        ]
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
        chain_management=module.params['chain_management'],
        wait=module.params['wait'],
    )

    ip_version = ['ipv4', 'ipv6'] if module.params['ip_version'] == 'both' else [module.params['ip_version']]
    iptables_path = [module.get_bin_path('iptables', True) if ip_version == 'ipv4' else module.get_bin_path('ip6tables', True) for ip_version in ip_version]

    both_changed = False

    for path in iptables_path:
        if module.params.get('log_prefix', None) or module.params.get('log_level', None):
            if module.params['jump'] is None:
                module.params['jump'] = 'LOG'
            elif module.params['jump'] != 'LOG':
                module.fail_json(msg="Logging options can only be used with the LOG jump target.")

        # Check if wait option is supported
        iptables_version = LooseVersion(get_iptables_version(path, module))

        if iptables_version >= LooseVersion(IPTABLES_WAIT_SUPPORT_ADDED):
            if iptables_version < LooseVersion(IPTABLES_WAIT_WITH_SECONDS_SUPPORT_ADDED):
                module.params['wait'] = ''
        else:
            module.params['wait'] = None

        # Flush the table
        if args['flush'] is True:
            args['changed'] = True
            both_changed = True
            if not module.check_mode:
                flush_table(path, module, module.params)

        # Set the policy
        elif module.params['policy']:
            current_policy = get_chain_policy(path, module, module.params)
            if not current_policy:
                module.fail_json(msg='Can\'t detect current policy')

            changed = current_policy != module.params['policy']
            args['changed'] = changed
            both_changed = both_changed or changed
            if changed and not module.check_mode:
                set_chain_policy(path, module, module.params)

        # Delete the chain if there is no rule in the arguments
        elif (args['state'] == 'absent') and not args['rule']:
            chain_is_present = check_chain_present(
                path, module, module.params
            )
            args['changed'] = chain_is_present
            both_changed = both_changed or chain_is_present

            if (chain_is_present and args['chain_management'] and not module.check_mode):
                delete_chain(path, module, module.params)

        else:
            # Create the chain if there are no rule arguments
            if (args['state'] == 'present') and not args['rule']:
                chain_is_present = check_chain_present(
                    path, module, module.params
                )
                args['changed'] = not chain_is_present
                both_changed = both_changed or not chain_is_present

                if (not chain_is_present and args['chain_management'] and not module.check_mode):
                    create_chain(path, module, module.params)

            else:
                insert = (module.params['action'] == 'insert')
                rule_is_present = check_rule_present(
                    path, module, module.params
                )

                should_be_present = (args['state'] == 'present')
                # Check if target is up to date
                args['changed'] = (rule_is_present != should_be_present)
                both_changed = both_changed or (rule_is_present != should_be_present)
                if args['changed'] is False:
                    # Target is already up to date
                    continue

                # Modify if not check_mode
                if not module.check_mode:
                    if should_be_present:
                        if insert:
                            insert_rule(path, module, module.params)
                        else:
                            append_rule(path, module, module.params)
                    else:
                        remove_rule(path, module, module.params)

    args['changed'] = both_changed

    module.exit_json(**args)


if __name__ == '__main__':
    main()
