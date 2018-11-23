#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Joris Weijters <joris.weijters@gmail.com>
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


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
author: "Joris Weijters (@molekuul)"
module: aix_ipsec
short_description: Manages the ipsec filter on AIX.
version_added: "2.4"
description:
  - Manages the ipsec filter rules on AIX.
notes:
  - "This module just deals with individual rules. If you need advanced
    chaining of rules the recomended way is to template the ipsec restore
    file."
options:
  state:
    description:
      - "Whether a rule should be absent or present."
    required: False
    default: started
    choices: [ "present", "absent", "started", "stopped", "flushed" ]
  ip_version:
    description:
      - "Which version of the IP protocol this rule should apply to."
    required: False
    default: 4
    choices: [ "4", "6" ]
  action:
    description:
      - "The ruleaction this can be one of the folowing: deny, permit, if,
        else, endif, shun_host, shun_port.
        All IF rules most be close with an associated ENDIF rule. These
        conditional rules can be nested, but correct nesting and scope must
        be adhered to or the rules will not load correctly.
        Required when I(state) is C(present) or C(absent)"
    required: False
    choices: [ "deny", "permit", "if", "else", "endif", "shun_host", "shun_port" ]
  protocol:
    description:
      - "The protocol of the rule or of the packet to check. The specified
        protocol can be one of: udp, icmp, icmpv6, tcp, tcp/ack, ospf, ipip,
        esp, ah or the special keyword all Value all indicates that the
        filter rule will apply to all the protocols. The protocol can also
        be specified numerically (between 1 and 252).
        Value tcp/ack implies checking for TCP packets with the ACK flag set."
    required: False
    default: all
    choices: [ "udp", "icmp", "icmpv6", "tcp", "tcp/ack", "ospf", "ipip", "esp", "ah", "all" ]
  source_address:
    description:
      - "Specifies the source address. It can be an IP address or a host name.
        If a host name is specified, the first IP address returned by the name
        server for that host will be used. This value along with the source
        subnet mask will be compared against the source address of the IP packets.
        Required when I(state) is C(present) or C(absent)"
    required: False
  source_mask:
    description:
      - "Specifies the source subnet mask. This is used in the comparison of the
        IP packet's source address with the source address of the filter rule.
        Required when I(state) is C(present) or C(absent)"
    required: False
    default: None
  source_port:
    description:
      - "Specifies the source port or ICMP type. This is the value/type that will
        be compared to the source port (or ICMP type) of the IP packet.
        Required when I(state) is C(present) or C(absent)"
    required: False
    default: None
  source_port_operation:
    description:
      - "Specifies the source port or ICMP type operation. This is the operation
        that will be used in the comparison between the source port/ICMP type
        of the packet with the source port or ICMP type specified in this
        filter rule.
        This value must be any when the protocol is ospf.
        Required when I(state) is C(present) or C(absent)"
    required: False
    choices: [ "lt", "le", "gt", "ge", "eq", "neq", "any" ]
  destination_address:
    description:
      - "Specifies the destination address. It can be an IP address or a host name.
        If a host name is specified, the first IP address returned by the name
        server for that host will be used. This value along with the source
        subnet mask will be compared against the source address of the IP packets.
        Required when I(state) is C(present) or C(absent)"
    required: False
    default: None
  destination_mask:
    description:
      - "Specifies the source destination mask. This is used in the comparison of the
        IP packet's destination address with the source address of the filter rule.
        Required when I(state) is C(present) or C(absent)"
    required: False
    default: None
  destination_port:
    description:
      - "Specifies the destination port/ICMP code. This is the value/code that
        will be compared to the destination port (or ICMP code) of the IP packet.
        Required when I(state) is C(present) or C(absent)"
    required: False
    default: None
  destination_port_operation:
    description:
      - "Specifies the destination port or ICMP code operation. This is the
        operation that will be used in the comparison between the destination
        port/ICMP code of the packet with the destination port or ICMP code.
        This value must be any when the protocol flag is ospf.
        Required when I(state) is C(present) or C(absent)"
    required: False
    choices: [ "lt", "le", "gt", "ge", "eq", "neq", "any" ]
  routing:
    description:
      - "This specifies whether the rule will apply to forwarded packets (route),
        packets destined or originated from the local host (local), or both (both).
        The default value is B."
    required: False
    default: both
    choices: [ "both", "local", "route" ]
  direction:
    description:
      - "Specifies whether the rule applys to incoming packets (incomming),
        outgoing packets (outgoing), or both.
        In use with pattern options or antivirus you can not use incomming or outgoing.
        It is valid to specify the both directions with the pattern options,
        but only the incoming packets are checked against the packets."
    required: False
    default: both
    choices: [ "both", "incomming", "outgoing" ]
  rule_id:
    description:
      - "Specifies the filter rule ID. The new rule will be added BEFORE the
        filter rule you specify. For IP version 4, the ID must be greater than 1
        because the first filter rule is a system generated rule and cannot be moved.
        If this flag is not used, the new rule will be added to the end of the filter rule table."
    required: False
    default: None
  logging:
    description:
      - "Specifies the log control. Must be specified as yes or No. If specified
        as yes, packets that match this filter rule will be included in the
        filter log."
    required: False
    default: no
    choices: [ "yes", "no" ]
  fragment_control:
    description:
      - "Specifies the fragmentation control. This flag specifies that this rule
        will apply to either all packets (Y), fragment headers and unfragmented
        packets only (H), fragments and fragment headers only (O),
        or unfragmented packets only (N)."
    required: False
    default: Y
    choices: [ "Y", "H", "O", "N" ]
  tunnel_number:
    description:
      - "Specifies the ID of the tunnel related to this filter rule. All the
        packets that match this filter rule must go through the specified tunnel.
        If this flag is not specified, this rule will only apply to non-tunnel traffic."
    required: False
    default: 0
  interface:
    description:
      - "Specifies the name of IP interface(s) to which the filter rule applies.
        The examples of the name are: all, tr0, en0, lo0, and pp0."
    required: False
    default: all
  expiration_time:
    description:
      - "Specifies the expiration time. The expiration time is the amount of
        time the rule should remain active in seconds.  The expiration_time does
        not remove the filter rule from the database. The expiration_time
        relates to the amount of time the filter rule is active while processing
        network traffic. If no expiration_time is specified, then the live time
        of the filter rule is infinite. If the expiration_time is specified in
        conjunction with a SHUN_PORT (-a S) or SHUN_HOST (-a H) filter rule,
        then this is the amount of time the remote port or remote host is denied
        or shunned once the filter rule parameters are met.
        If this expiration_time is specified independent of a shun rule, then
        this is the amount of time the filter rule will remain active once the
        filter rules are loaded into the kernel and start processing network
        traffic."
    required: False
    default: "0"
  pattern:
    description:
      - "Specifies the quoted character string or pattern. This string specified
        is interpreted as an ASCII string unless it is preceded by a 0x,
        in which case it is interpreted as a hexadecimal string.
        The pattern is compared against network traffic."
    required: False
  pattern_filename:
    description:
      - "Specifies the pattern file name. If more than one patterns are associated
        with this filter rule, then a pattern file name must be used. The pattern
        file name must be in the format of one pattern per line. A pattern is an
        unquoted character string. This file is read once when the filter rules
        are activated. For more information, see the mkfilt command."
    required: False
  description:
    description:
      - "A short description text for the filter rule. This is an optional flag
        for static filter rules, it's not applicable to dynamic filter rules."
    required: False
'''

EXAMPLES = '''
# Make sure ipsec is started
- name: Make sure ipsec is started
  aix_ipsec:
    state: started

# Make sure ipsec is stopped
- name: Make sure ipsec is stopped
  aix_ipsec:
    state: stopped

# flush all ipsec rules
- name: Flush ipsec rules
  aix_ipsec:
    state: flushed

# Add a rule before the deny rule for interface en0
- name: Add permit rule for en0 from ip 4.3.2.1/32 port 1234 to any port at ip 1.2.3.4/32
  aix_ipsec:
    state: present
    action: 'permit'
    destination_address: '1.2.3.4'
    destination_mask: '255.255.255.255'
    destination_port_operation: 'any'
    destination_port: '0'
    source_address: '4.3.2.1'
    source_mask: '255.255.255.255'
    source_port_operation : 'eq'
    source_port: '1234'
    intf: 'en0'

# Add a rule from ip 4.3.2.1/32 that equals port 1234 to ip 1.2.3.4/24 equals port 1234 at the end of the rules.
- name: Add permit rule for port 1234
  aix_ipsec:
    state: present
    action: 'permit'
    destination_address: '1.2.3.4'
    destination_mask: '255.255.255.0'
    destination_port_operation: 'eq'
    destination_port: '1234'
    source_address: '4.3.2.1'
    source_mask: '255.255.255.255'
    source_port_operation : 'eq'
    source_port: '1234'

# remove a rule
- name: Remove Rule
  aix_ipsec:
    state: absent
    action: 'permit'
    destination_address: '1.2.3.4'
    destination_mask: '255.255.255.255'
    destination_port_operation: 'any'
    destination_port: '0'
    source_address: '4.3.2.1'
    source_mask: '255.255.255.255'
    source_port_operation : 'eq'
    source_port: '1234'
    intf: 'en0'
'''

RETURN = '''
changed:
    description: whether the rules are changed
    returned: always
    type: boolean
    sample: True
msg:
    description: return message from the added or removed rule or status of the ipsec
    returned: changed
    type: string
    sample: "Rule -n 8 -v 4 -a P -s 1.2.3.4 -m 255.255.255.255 -p 1234 -o eq -O any -d 4.3.2.1 -M 255.255.255.255 -P 0 -i en0 added"
results:
    description: detailed results from the current rules, the new rule, rule_id, etc.
    returned: always
    type: dictionary
    sample:
        "results": {
            "changed": False,
            "current_rules": [
                {
                    "action": "permit",
                    "apply": "no",
                    "desc": "Default Rule",
                    "dest": "0.0.0.0",
                    "dir": "both",
                    "dmask": "0.0.0.0",
                    "doper": "eq",
                    "dtype": "4001",
                    "expt": "0",
                    "fid": "1",
                    "frag": "all packets",
                    "intf": "all",
                    "log": "no",
                    "patp": "",
                    "patt": "",
                    "proto": "udp",
                    "routing": "both",
                    "smask": "0.0.0.0",
                    "soper": "eq",
                    "source": "0.0.0.0",
                    "stype": "4001",
                    "tunnel": "0"
                },
                {
                    "action": "*** Dynamic filter placement rule for IKE tunnels ***",
                    "fid": "2",
                    "source": "no"
                }],
            "new_rule": {
                "action": "permit",
                "desc": "",
                "dest": "1.2.3.4",
                "dir": "both",
                "dmask": "255.255.255.255",
                "doper": "any",
                "dtype": "0",
                "expt": "0",
                "frag": "all packets",
                "intf": "en0",
                "log": "no",
                "patp": "",
                "patt": "",
                "proto": "all",
                "routing": "both",
                "smask": "255.255.255.255",
                "soper": "eq",
                "source": "4.3.2.1",
                "stype": "1234",
                "tunnel": "0"
            }
        }

'''

# import module snippets
from ansible.module_utils.basic import AnsibleModule
import itertools
import socket


def get_current_rules(module, lsfilt_path):
    # This function recieves the list of current rules
    lijst = []
    ip_ver = module.params['ip_version']
    cmd = "%s %s %s %s" % (lsfilt_path, '-v', ip_ver, '-O')
    (rc, out, err) = module.run_command(cmd)
    if rc != 0:
        module.fail_json(
            msg="Could not retrieve current ipsec rules", rc=rc, err=err)
    keys = (
        'fid',
        'action',
        'source',
        'smask',
        'dest',
        'dmask',
        'apply',
        'proto',
        'soper',
        'stype',
        'doper',
        'dtype',
        'routing',
        'dir',
        'log',
        'frag',
        'tunnel',
        'intf',
        'expt',
        'patp',
        'patt',
        'desc')
    for line in out.splitlines():
        values = line.split("|")
        adict = dict(itertools.izip(keys, values))
        lijst.append(adict)
    return lijst


def rule_from_input(module):
    # This function crates a rule from the module input simular to the information you recieve
    # with the lsfilt command.
    new_rule = dict(
        action=module.params["action"],
        desc=module.params["desc"],
        dest=module.params["dest"],
        dir=module.params["dir"],
        dmask=module.params["dmask"],
        doper=module.params["doper"],
        dtype=module.params["dtype"],
        expt=module.params["expt"],
        frag=module.params["fragrule"],
        intf=module.params["intf"],
        log=module.params["log"],
        patp=module.params["patp"],
        patt=module.params["patt"],
        proto=module.params["proto"],
        routing=module.params["routing"],
        smask=module.params["smask"],
        soper=module.params["soper"],
        source=module.params["source"],
        stype=module.params["stype"],
        tunnel=module.params["tunnel"]
    )
    return new_rule


def resolv_hostname(hostname):
    try:
        ip = socket.gethostbyname(hostname)
        return ip
    except socket.error:
        return 0


def match_rule(new_rule, current_rules):
    # This module checks if the new_rule exists in the list of current_rules
    fid = ""
    result = False
    for cur_rule in current_rules:
        # I have to copy the cur_rule because in the matching I want not to
        # match the apply and/or the fid
        cur_match_rule = cur_rule.copy()
        new_match_rule = new_rule.copy()
        # convert the source and destination to IP adresses
        new_match_rule["source"] = resolv_hostname(new_rule["source"])
        new_match_rule["dest"] = resolv_hostname(new_rule["dest"])
        if 'apply' in cur_match_rule:
            del cur_match_rule['apply']
        # save the fid and then remove it from the dict
        if 'fid' in cur_match_rule:
            rule_fid = cur_match_rule['fid']
            del cur_match_rule['fid']
        if (cur_match_rule == new_match_rule):
            fid = rule_fid
            result = True
    return result, fid


def create_rule_args(module):
    # This function creates the paramaterlist needed for genfilt to add the rule
    # first start with the default parameters
    str = "-v " + module.params['ip_version'] \
        + " -a " + module.params['action_param'] \
        + " -s " + module.params['source'] \
        + " -m " + module.params['smask'] \
        + " -p " + module.params['stype'] \
        + " -o " + module.params['soper'] \
        + " -O " + module.params['doper'] \
        + " -d " + module.params['dest'] \
        + " -M " + module.params['dmask'] \
        + " -P " + module.params['dtype']
    # now add the extra parameters if they are not default value
    # Add parameter rule_id
    if (module.params['rule_id'] !=
            module.argument_spec['rule_id']['default']):
        str = str + " -n " + module.params['rule_id']
    # Add parameter protocol
    if (module.params['proto'] != module.argument_spec['proto']['default']):
        str = str + " -c " + module.params['proto']
    # Add parameter routing
    if (module.params['routing'] !=
            module.argument_spec['routing']['default']):
        if (module.params['routing'] == "both"):
            str = str + " -r B"
        elif (module.params['routing'] == "local"):
            str = str + " -r L"
        elif (module.params['routing'] == "route"):
            str = str + " -r R"
    # Add parameter Direction
    if (module.params['dir'] != module.argument_spec['dir']['default']):
        if (module.params['dir'] == "both"):
            str = str + " -w B"
        elif (module.params['dir'] == "incomming"):
            str = str + " -w I"
        elif (module.params['dir'] == "outgoing"):
            str = str + " -w O"
    # Add parameter logging
    if (module.params['log'] != module.argument_spec['log']['default']):
        if (module.params['log'] == "yes"):
            str = str + " -l Y"
        elif (module.params['log'] == "no"):
            str = str + " -l N"
    # Add parameter fragment_control
    if (module.params['frag'] != module.argument_spec['frag']['default']):
        str = str + " -f " + module.params['frag']
    # Add parameter tunnel
    if (module.params['tunnel'] != module.argument_spec['tunnel']['default']):
        str = str + " -t " + module.params['tunnel']
    # Add parameter interface
    if (module.params['intf'] != module.argument_spec['intf']['default']):
        str = str + " -i " + module.params['intf']
    # Add parameter description
    if (module.params['desc'] != module.argument_spec['desc']['default']):
        str = str + " -D " + '"' + module.params['desc'] + '"'
    # Add parameter expiration_time
    if (module.params['expt'] != module.argument_spec['expt']['default']):
        str = str + " -e " + module.params['expt']
    # Add parameter expiration_time
    if (module.params['expt'] != module.argument_spec['expt']['default']):
        str = str + " -e " + module.params['expt']
    # Add parameter quoted_pattern
    if (module.params['patp'] != module.argument_spec['patp']['default']):
        str = str + " -x " + module.params['patp']
    # Add parameter pattern_filename
    if (module.params['patt'] != module.argument_spec['patt']['default']):
        str = str + " -X " + module.params['patt']

    # return the value
    return str


def find_deny_rules(rules):
    deny_rules = []
    for rule in rules:
        if 'action' in rule:
            if rule['action'] == 'deny':
                deny_rules.append(rule)
    return deny_rules


def add_rule(module, new_rule, genfilt_path):
    cmd = genfilt_path + " " + new_rule
    (rc, out, err) = module.run_command(cmd)
    if rc != 0:
        module.fail_json(
            msg="Could not add new ipsec rule", rc=rc, err=err)
    activate_rules(module)


def remove_rule(module, fid, rmfilt_path):
    cmd = rmfilt_path + " -v " + module.params['ip_version'] + " -n " + fid
    (rc, out, err) = module.run_command(cmd)
    if rc != 0:
        module.fail_json(
            msg="Could not remove ipsec rule" + fid, rc=rc, err=err)
    activate_rules(module)


def activate_rules(module):
    mkfilt_path = module.get_bin_path("mkfilt", True)
    cmd = mkfilt_path + " -u" + " -v " + module.params['ip_version']
    (rc, out, err) = module.run_command(cmd)

#    if rc != 0:
#        module.fail_json(msg="Could not activate ipsec rules" +
#                         " Command used: " + cmd, rc=rc, err=err)

    if rc == 255:
        create_device(module)
        (rc, out, err) = module.run_command(cmd)
        if rc != 0:
            module.fail_json(msg="Could not activate ipsec rules" +
                             " Command used: " + cmd, rc=rc, err=err)
    else:
        if rc != 0:
            module.fail_json(msg="Could not activate ipsec rules" +
                         " Command used: " + cmd, rc=rc, err=err)


def create_device(module):
    mkdev_path = module.get_bin_path("mkdev", True)
    mkdev_cmd = mkdev_path + " -c ipsec -t " + module.params['ip_version']
    (rc, out, err) = module.run_command(mkdev_cmd)
    if rc != 0:
        module.fail_json(msg="Could not define ipsec device" +
                " Command used: " + mkdev_cmd, rc=rc, err=err)



def stop_start_ipsec(module, mkfilt_path, lsfilt_path):
    # check if firewall is running, if not, msg from lsfilt -a is: IPv4 filter is currently inactive.
    changed = False
    ipsecstatus, ipsecrunning = _ipsec_running(module, lsfilt_path)
    if ipsecrunning and module.params['state'] == 'stopped':
        changed = True
        msg = 'Dectivated ipsec'
        if not module.check_mode:
            cmd = mkfilt_path + " -d" + " -v " + module.params['ip_version']
            (rc, out, err) = module.run_command(cmd)
            if rc == 255:
                create_device(module)
                (rc, out, err) = module.run_command(cmd)
            if rc != 0:
                module.fail_json(
                    msg="Could not deactivate ipsec rules", rc=rc, err=err)
    elif not ipsecrunning and module.params['state'] == 'started':
        changed = True
        msg = 'Activated ipsec'
        if not module.check_mode:
            cmd = mkfilt_path + " -u" + " -v " + module.params['ip_version']
            (rc, out, err) = module.run_command(cmd)
            if rc == 255:
                create_device(module)
                (rc, out, err) = module.run_command(cmd)
            if rc != 0:
                module.fail_json(
                    msg="Could not start ipsec rules", rc=rc, err=err)
    else:
        changed = False
        msg = 'status of IPsec = ' + ipsecstatus

    return changed, msg


def _ipsec_running(module, lsfilt_path):
    chk_cmd = lsfilt_path + " -v " + module.params['ip_version'] + " -a"
    (rc, out, err) = module.run_command(chk_cmd)
    if rc == 255:
        create_device(module)
        (rc, out, err) = module.run_command(chk_cmd)
    if rc != 0:
        module.fail_json(
            msg="Could not check ipsec status", rc=rc, err=err)
    else:
        if 'Beginning of' in out:
            running = 'Activated', True
        elif 'inactive' in out:
            running = 'Stopped', False
        else:
            module.fail_json(
                msg="Could not check ipsec status", rc=rc, err=err)
    return running


def flush_ipsec(module, rmfilt_path, mkfilt_path, lsfilt_path):
    cmd = rmfilt_path + " -v " + module.params['ip_version'] + " -n all"
    (rc, out, err) = module.run_command(cmd)
    if rc == 255:
        create_device(module)
        (rc, out, err) = module.run_command(cmd)
    if rc != 0:
        module.fail_json(
            msg="Could not flush ipsec rules", rc=rc, err=err)
    module.params['state'] = 'stopped'
    stop_start_ipsec(module, mkfilt_path, lsfilt_path)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(
                required=False,
                default='started',
                choices=['present', 'absent', 'started', 'stopped', 'flushed']),
            ip_version=dict(
                required=False,
                default='4',
                choices=['4', '6']),
            action=dict(
                required=False,
                default=None,
                choices=['deny', 'permit', 'if', 'else', 'endif', 'shun_host', 'shun_port']),
            proto=dict(
                required=False,
                default='all',
                choices=[
                        'udp',
                        'icmp',
                        'icmpv6',
                        'tcp',
                        'tcp/ack',
                        'ospf',
                        'ipip',
                        'esp',
                        'ah',
                        'all'],
                aliases=['protocol']),
            source=dict(
                required=False,
                default=None,
                type='str',
                aliases=['source_address']),
            smask=dict(
                required=False,
                default=None,
                aliases=['source_mask']),
            stype=dict(
                required=False,
                default=None,
                type='str',
                aliases=['source_port']),
            soper=dict(
                required=False,
                choices=['lt', 'le', 'gt', 'ge', 'eq', 'neq', 'any'],
                aliases=['source_port_operation']),
            dest=dict(
                required=False,
                default=None,
                type='str',
                aliases=['destination_address']),
            dmask=dict(
                required=False,
                default=None,
                type='str',
                aliases=['destination_mask']),
            dtype=dict(
                required=False,
                default=None,
                type='str',
                aliases=['destination_port']),
            doper=dict(
                required=False,
                choices=['lt', 'le', 'gt', 'ge', 'eq', 'neq', 'any'],
                aliases=['destination_port_operation']),
            routing=dict(
                required=False,
                default='both',
                choices=['both', 'local', 'route']),
            rule_id=dict(
                required=False,
                default=None,
                type='str'),
            dir=dict(
                required=False,
                default='both',
                choices=['both', 'incomming', 'outgoing'],
                aliases=['direction']),
            log=dict(
                required=False,
                default='no',
                choices=['yes', 'no'],
                aliases=['logging']),
            frag=dict(
                required=False,
                default='Y',
                choices=['Y', 'H', 'O', 'N'],
                aliases=['fragment_control']),
            tunnel=dict(
                required=False,
                default="0",
                type='str',
                aliases=['tunnel_number']),
            intf=dict(
                required=False,
                default='all',
                typr='str',
                aliases=['interface']),
            expt=dict(
                required=False,
                default="0",
                type='str',
                aliases=['expiration_time']),
            patp=dict(
                required=False,
                default="",
                type='str',
                aliases=['pattern']),
            patt=dict(
                required=False,
                default="",
                type='str',
                aliases=['pattern_filename']),
            desc=dict(
                required=False,
                default="",
                type='str',
                aliases=['description'])
        ),
        supports_check_mode=True,
        required_if=(
            ['state', 'present',
                ['action',
                    'source',
                    'smask',
                    'stype',
                    'soper',
                    'dest',
                    'dmask',
                    'dtype',
                    'doper']
             ],
            ['state', 'absent',
                ['action',
                    'source',
                    'smask',
                    'stype',
                    'soper',
                    'dest',
                    'dmask',
                    'dtype',
                    'doper']
             ]
        )
    )

    # set the fragmentation type: Y, H, O, N
    if (module.params['frag'] == 'Y'):
        module.params['fragrule'] = "all packets"
    elif (module.params['frag'] == 'H'):
        module.params[
            'fragrule'] = "fragment headers and unfragmented packets only"
    elif (module.params['frag'] == 'O'):
        module.params['fragrule'] = "fragments and fragment headers only"
    elif (module.params['frag'] == 'N'):
        module.params['fragrule'] = "unfragmented packets only"
    # set the Action parameter
    # deny', 'permit', 'if', 'else', 'endif', 'shun_host', 'shun_port'
    if (module.params['action'] == 'deny'):
        module.params['action_param'] = 'D'
    elif (module.params['action'] == 'permit'):
        module.params['action_param'] = 'P'
    elif (module.params['action'] == 'if'):
        module.params['action_param'] = 'I'
    elif (module.params['action'] == 'else'):
        module.params['action_param'] = 'L'
    elif (module.params['action'] == 'endif'):
        module.params['action_param'] = 'E'
    elif (module.params['action'] == 'shun_host'):
        module.params['action_param'] = 'H'
    elif (module.params['action'] == 'shun_port'):
        module.params['action_param'] = 'S'

    lsfilt_path = module.get_bin_path("lsfilt", True)
    genfilt_path = module.get_bin_path("genfilt", True)
    mkfilt_path = module.get_bin_path("mkfilt", True)
    rmfilt_path = module.get_bin_path("rmfilt", True)
    result = {}
    msg = ""
    result['changed'] = False
    current_rules = get_current_rules(module, lsfilt_path)
    new_rule = rule_from_input(module)

    if module.params['state'] == 'started' or module.params['state'] == 'stopped':
        (result['changed'], msg) = stop_start_ipsec(module, mkfilt_path, lsfilt_path)
        new_rule.clear()
    elif module.params['state'] == 'flushed':
        if not module.check_mode:
            flush_ipsec(module, rmfilt_path, mkfilt_path, lsfilt_path)
        result['changed'] = True
        msg = "Ipsec rules flushed"
        new_rule.clear()
    else:
        match, match_fid = match_rule(new_rule, current_rules)
        if match and (module.params['state'] == 'present'):
            # if the rule exists and it should be pressent,
            # the rule does not has to be added
            result['changed'] = False
        elif not match and (module.params['state'] == 'present'):
            cmd_args_new_rule = create_rule_args(module)
            new_rule_id = ""
            # New rule does not exist, but should be present
            # If no rulenumber is given, find-out where to put the rule???????
            # find the deny rules.
            # If a rule has an "intf = any" place this before rule 3
            # If a rule has an "intf != any" place the rule before the deny rule of that interface
            # If a deny rule does not exist, place the permitrule at the end.
            # place deny rules to the end of the list
            # calculate New rule number
            if module.params['action'] != "deny":
                if not module.params['rule_id']:
                    deny_rules = find_deny_rules(current_rules)
                    result['deny_rules'] = deny_rules
                    # if there is no deny rule, add the deny rule to the end of the
                    # list ( new_rule_id is not set )
                    if deny_rules:
                        if module.params['intf'] == "all":
                            new_rule_id = "3"
                        else:
                            # find the deny rule that compie with the interface
                            for rule in deny_rules:
                                if module.params['intf'] == rule['intf']:
                                    new_rule_id = rule['fid']
                else:
                    new_rule_id = module.params['rule_id']
            if new_rule_id:
                cmd_args_new_rule = "-n " + new_rule_id + " " + cmd_args_new_rule
                result['new_rule_id'] = new_rule_id

            result['args'] = cmd_args_new_rule
            result['changed'] = True
            msg = "Rule " + cmd_args_new_rule + " added."
            if not module.check_mode:
                add_rule(module, cmd_args_new_rule, genfilt_path)
        elif match and (module.params['state'] == 'absent'):
            # rule is present but it shoudn't be, it will be removed
            result['changed'] = True
            msg = "Rule removed from ruleid: " + match_fid
            if not module.check_mode:
                remove_rule(module, match_fid, rmfilt_path)
        elif not match and (module.params['state'] == 'absent'):
            # The rule should not exist , and it doesn't.
            result['changed'] = False

    result['current_rules'] = current_rules
    result['new_rule'] = new_rule
    module.exit_json(changed=result['changed'], rc=0, msg=msg, results=result)

if __name__ == '__main__':
    main()
