#!/usr/bin/python
# -*- coding: utf-8 -*-
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = '''
---
module: ec2_group
author: "Andrew de Quincey (@adq)"
version_added: "1.3"
requirements: [ boto3 ]
short_description: maintain an ec2 VPC security group.
description:
    - maintains ec2 security groups. This module has a dependency on python-boto >= 2.5
options:
  name:
    description:
      - Name of the security group.
      - One of and only one of I(name) or I(group_id) is required.
      - Required if I(state=present).
    required: false
  group_id:
    description:
      - Id of group to delete (works only with absent).
      - One of and only one of I(name) or I(group_id) is required.
    required: false
    version_added: "2.4"
  description:
    description:
      - Description of the security group. Required when C(state) is C(present).
    required: false
  vpc_id:
    description:
      - ID of the VPC to create the group in.
    required: false
  rules:
    description:
      - List of firewall inbound rules to enforce in this group (see example). If none are supplied,
        no inbound rules will be enabled. Rules list may include its own name in `group_name`.
        This allows idempotent loopback additions (e.g. allow group to access itself).
        Rule sources list support was added in version 2.4. This allows to define multiple sources per
        source type as well as multiple source types per rule. Prior to 2.4 an individual source is allowed.
        In version 2.5 support for rule descriptions was added.
    required: false
  rules_egress:
    description:
      - List of firewall outbound rules to enforce in this group (see example). If none are supplied,
        a default all-out rule is assumed. If an empty list is supplied, no outbound rules will be enabled.
        Rule Egress sources list support was added in version 2.4. In version 2.5 support for rule descriptions
        was added.
    required: false
    version_added: "1.6"
  state:
    version_added: "1.4"
    description:
      - Create or delete a security group
    required: false
    default: 'present'
    choices: [ "present", "absent" ]
    aliases: []
  purge_rules:
    version_added: "1.8"
    description:
      - Purge existing rules on security group that are not found in rules
    required: false
    default: 'true'
    aliases: []
  purge_rules_egress:
    version_added: "1.8"
    description:
      - Purge existing rules_egress on security group that are not found in rules_egress
    required: false
    default: 'true'
    aliases: []
  tags:
    version_added: "2.4"
    description:
      - A dictionary of one or more tags to assign to the security group.
    required: false
  purge_tags:
    version_added: "2.4"
    description:
      - If yes, existing tags will be purged from the resource to match exactly what is defined by I(tags) parameter. If the I(tags) parameter is not set then
        tags will not be modified.
    required: false
    default: yes
    type: bool

extends_documentation_fragment:
    - aws
    - ec2

notes:
  - If a rule declares a group_name and that group doesn't exist, it will be
    automatically created. In that case, group_desc should be provided as well.
    The module will refuse to create a depended-on group without a description.
'''

EXAMPLES = '''
- name: example using security group rule descriptions
  ec2_group:
    name: "{{ name }}"
    description: sg with rule descriptions
    vpc_id: vpc-xxxxxxxx
    profile: "{{ aws_profile }}"
    region: us-east-1
    rules:
      - proto: tcp
        ports:
        - 80
        cidr_ip: 0.0.0.0/0
        rule_desc: allow all on port 80

- name: example ec2 group
  ec2_group:
    name: example
    description: an example EC2 group
    vpc_id: 12345
    region: eu-west-1
    aws_secret_key: SECRET
    aws_access_key: ACCESS
    rules:
      - proto: tcp
        from_port: 80
        to_port: 80
        cidr_ip: 0.0.0.0/0
      - proto: tcp
        from_port: 22
        to_port: 22
        cidr_ip: 10.0.0.0/8
      - proto: tcp
        from_port: 443
        to_port: 443
        group_id: amazon-elb/sg-87654321/amazon-elb-sg
      - proto: tcp
        from_port: 3306
        to_port: 3306
        group_id: 123412341234/sg-87654321/exact-name-of-sg
      - proto: udp
        from_port: 10050
        to_port: 10050
        cidr_ip: 10.0.0.0/8
      - proto: udp
        from_port: 10051
        to_port: 10051
        group_id: sg-12345678
      - proto: icmp
        from_port: 8 # icmp type, -1 = any type
        to_port:  -1 # icmp subtype, -1 = any subtype
        cidr_ip: 10.0.0.0/8
      - proto: all
        # the containing group name may be specified here
        group_name: example
      - proto: all
        # in the 'proto' attribute, if you specify -1, all, or a protocol number other than tcp, udp, icmp, or 58 (ICMPv6),
        # traffic on all ports is allowed, regardless of any ports you specify
        from_port: 10050 # this value is ignored
        to_port: 10050 # this value is ignored
        cidr_ip: 10.0.0.0/8

    rules_egress:
      - proto: tcp
        from_port: 80
        to_port: 80
        cidr_ip: 0.0.0.0/0
        cidr_ipv6: 64:ff9b::/96
        group_name: example-other
        # description to use if example-other needs to be created
        group_desc: other example EC2 group

- name: example2 ec2 group
  ec2_group:
    name: example2
    description: an example2 EC2 group
    vpc_id: 12345
    region: eu-west-1
    rules:
      # 'ports' rule keyword was introduced in version 2.4. It accepts a single port value or a list of values including ranges (from_port-to_port).
      - proto: tcp
        ports: 22
        group_name: example-vpn
      - proto: tcp
        ports:
          - 80
          - 443
          - 8080-8099
        cidr_ip: 0.0.0.0/0
      # Rule sources list support was added in version 2.4. This allows to define multiple sources per source type as well as multiple source types per rule.
      - proto: tcp
        ports:
          - 6379
          - 26379
        group_name:
          - example-vpn
          - example-redis
      - proto: tcp
        ports: 5665
        group_name: example-vpn
        cidr_ip:
          - 172.16.1.0/24
          - 172.16.17.0/24
        cidr_ipv6:
          - 2607:F8B0::/32
          - 64:ff9b::/96
        group_id:
          - sg-edcd9784

- name: "Delete group by its id"
  ec2_group:
    group_id: sg-33b4ee5b
    state: absent
'''

RETURN = '''
group_name:
  description: Security group name
  sample: My Security Group
  type: string
  returned: on create/update
group_id:
  description: Security group id
  sample: sg-abcd1234
  type: string
  returned: on create/update
description:
  description: Description of security group
  sample: My Security Group
  type: string
  returned: on create/update
tags:
  description: Tags associated with the security group
  sample:
    Name: My Security Group
    Purpose: protecting stuff
  type: dict
  returned: on create/update
vpc_id:
  description: ID of VPC to which the security group belongs
  sample: vpc-abcd1234
  type: string
  returned: on create/update
ip_permissions:
  description: Inbound rules associated with the security group.
  sample:
    - from_port: 8182
      ip_protocol: tcp
      ip_ranges:
        - cidr_ip: "1.1.1.1/32"
      ipv6_ranges: []
      prefix_list_ids: []
      to_port: 8182
      user_id_group_pairs: []
  type: list
  returned: on create/update
ip_permissions_egress:
  description: Outbound rules associated with the security group.
  sample:
    - ip_protocol: -1
      ip_ranges:
        - cidr_ip: "0.0.0.0/0"
          ipv6_ranges: []
          prefix_list_ids: []
          user_id_group_pairs: []
  type: list
  returned: on create/update
owner_id:
  description: AWS Account ID of the security group
  sample: 123456789012
  type: int
  returned: on create/update
'''

import json
import re
from time import sleep
from collections import namedtuple
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, ec2_argument_spec, camel_dict_to_snake_dict
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_tag_list, compare_aws_tags
from ansible.module_utils.ec2 import AWSRetry
from ansible.module_utils.network.common.utils import to_ipv6_network, to_subnet

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # caught by AnsibleAWSModule


Rule = namedtuple('Rule', ['rule', 'rule_id', 'ip_permission', 'ipv4', 'ipv6'])


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_security_groups_with_backoff(connection, **kwargs):
    return connection.describe_security_groups(**kwargs)


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def sg_exists_with_backoff(connection, **kwargs):
    try:
        return connection.describe_security_groups(**kwargs)
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidGroup.NotFound':
            return {'SecurityGroups': []}
        raise


def deduplicate_rules_args(rules):
    """Returns unique rules"""
    if rules is None:
        return None
    return list(dict(zip((json.dumps(r, sort_keys=True) for r in rules), rules)).values())


def make_rule_key(prefix, rule, group_id, cidr_ip):
    if 'proto' in rule:
        proto, from_port, to_port = [rule.get(x, None) for x in ('proto', 'from_port', 'to_port')]
    elif 'IpProtocol' in rule:
        proto, from_port, to_port = [rule.get(x, None) for x in ('IpProtocol', 'FromPort', 'ToPort')]
    if proto not in ['icmp', 'tcp', 'udp'] and from_port == -1 and to_port == -1:
        from_port = 'none'
        to_port = 'none'
    key = "%s-%s-%s-%s-%s-%s" % (prefix, proto, from_port, to_port, group_id, cidr_ip)
    return key.lower().replace('-none', '-None')


def add_rules_to_lookup(ip_permissions, group_id, prefix, my_dict):
    for rule in ip_permissions:
        for groupGrant in rule.get('UserIdGroupPairs', []):
            my_dict[make_rule_key(prefix, rule, group_id, groupGrant.get('GroupId'))] = (rule, groupGrant)
        for ipv4Grants in rule.get('IpRanges', []):
            my_dict[make_rule_key(prefix, rule, group_id, ipv4Grants.get('CidrIp'))] = (rule, ipv4Grants)
        for ipv6Grants in rule.get('Ipv6Ranges', []):
            my_dict[make_rule_key(prefix, rule, group_id, ipv6Grants.get('CidrIpv6'))] = (rule, ipv6Grants)
    return my_dict


def validate_rule(module, rule):
    VALID_PARAMS = ('cidr_ip', 'cidr_ipv6',
                    'group_id', 'group_name', 'group_desc',
                    'proto', 'from_port', 'to_port', 'rule_desc')
    if not isinstance(rule, dict):
        module.fail_json(msg='Invalid rule parameter type [%s].' % type(rule))
    for k in rule:
        if k not in VALID_PARAMS:
            module.fail_json(msg='Invalid rule parameter \'{}\''.format(k))

    if 'group_id' in rule and 'cidr_ip' in rule:
        module.fail_json(msg='Specify group_id OR cidr_ip, not both')
    elif 'group_name' in rule and 'cidr_ip' in rule:
        module.fail_json(msg='Specify group_name OR cidr_ip, not both')
    elif 'group_id' in rule and 'cidr_ipv6' in rule:
        module.fail_json(msg="Specify group_id OR cidr_ipv6, not both")
    elif 'group_name' in rule and 'cidr_ipv6' in rule:
        module.fail_json(msg="Specify group_name OR cidr_ipv6, not both")
    elif 'cidr_ip' in rule and 'cidr_ipv6' in rule:
        module.fail_json(msg="Specify cidr_ip OR cidr_ipv6, not both")
    elif 'group_id' in rule and 'group_name' in rule:
        module.fail_json(msg='Specify group_id OR group_name, not both')


def get_target_from_rule(module, client, rule, name, group, groups, vpc_id):
    """
    Returns tuple of (group_id, ip) after validating rule params.

    rule: Dict describing a rule.
    name: Name of the security group being managed.
    groups: Dict of all available security groups.

    AWS accepts an ip range or a security group as target of a rule. This
    function validate the rule specification and return either a non-None
    group_id or a non-None ip range.
    """

    FOREIGN_SECURITY_GROUP_REGEX = r'^(\S+)/(sg-\S+)/(\S+)'
    group_id = None
    group_name = None
    ip = None
    ipv6 = None
    target_group_created = False

    validate_rule(module, rule)
    if rule.get('group_id') and re.match(FOREIGN_SECURITY_GROUP_REGEX, rule['group_id']):
        # this is a foreign Security Group. Since you can't fetch it you must create an instance of it
        owner_id, group_id, group_name = re.match(FOREIGN_SECURITY_GROUP_REGEX, rule['group_id']).groups()
        group_instance = dict(GroupId=group_id, GroupName=group_name)
        groups[group_id] = group_instance
        groups[group_name] = group_instance
    elif 'group_id' in rule:
        group_id = rule['group_id']
    elif 'group_name' in rule:
        group_name = rule['group_name']
        if group_name == name:
            group_id = group['GroupId']
            groups[group_id] = group
            groups[group_name] = group
        elif group_name in groups and group.get('VpcId') and groups[group_name].get('VpcId'):
            # both are VPC groups, this is ok
            group_id = groups[group_name]['GroupId']
        elif group_name in groups and not (group.get('VpcId') or groups[group_name].get('VpcId')):
            # both are EC2 classic, this is ok
            group_id = groups[group_name]['GroupId']
        else:
            # if we got here, either the target group does not exist, or there
            # is a mix of EC2 classic + VPC groups. Mixing of EC2 classic + VPC
            # is bad, so we have to create a new SG because no compatible group
            # exists
            if not rule.get('group_desc', '').strip():
                module.fail_json(msg="group %s will be automatically created by rule %s and "
                                     "no description was provided" % (group_name, rule))
            if not module.check_mode:
                params = dict(GroupName=group_name, Description=rule['group_desc'])
                if vpc_id:
                    params['VpcId'] = vpc_id
                auto_group = client.create_security_group(**params)
                group_id = auto_group['GroupId']
                groups[group_id] = auto_group
                groups[group_name] = auto_group
            target_group_created = True
    elif 'cidr_ip' in rule:
        ip = rule['cidr_ip']
    elif 'cidr_ipv6' in rule:
        ipv6 = rule['cidr_ipv6']

    return group_id, ip, ipv6, target_group_created


def ports_expand(ports):
    # takes a list of ports and returns a list of (port_from, port_to)
    ports_expanded = []
    for port in ports:
        if not isinstance(port, str):
            ports_expanded.append((port,) * 2)
        elif '-' in port:
            ports_expanded.append(tuple(p.strip() for p in port.split('-', 1)))
        else:
            ports_expanded.append((port.strip(),) * 2)

    return ports_expanded


def rule_expand_ports(rule):
    # takes a rule dict and returns a list of expanded rule dicts
    if 'ports' not in rule:
        return [rule]

    ports = rule['ports'] if isinstance(rule['ports'], list) else [rule['ports']]

    rule_expanded = []
    for from_to in ports_expand(ports):
        temp_rule = rule.copy()
        del temp_rule['ports']
        temp_rule['from_port'], temp_rule['to_port'] = from_to
        rule_expanded.append(temp_rule)

    return rule_expanded


def rules_expand_ports(rules):
    # takes a list of rules and expands it based on 'ports'
    if not rules:
        return rules

    return [rule for rule_complex in rules
            for rule in rule_expand_ports(rule_complex)]


def rule_expand_source(rule, source_type):
    # takes a rule dict and returns a list of expanded rule dicts for specified source_type
    sources = rule[source_type] if isinstance(rule[source_type], list) else [rule[source_type]]
    source_types_all = ('cidr_ip', 'cidr_ipv6', 'group_id', 'group_name')

    rule_expanded = []
    for source in sources:
        temp_rule = rule.copy()
        for s in source_types_all:
            temp_rule.pop(s, None)
        temp_rule[source_type] = source
        rule_expanded.append(temp_rule)

    return rule_expanded


def rule_expand_sources(rule):
    # takes a rule dict and returns a list of expanded rule discts
    source_types = (stype for stype in ('cidr_ip', 'cidr_ipv6', 'group_id', 'group_name') if stype in rule)

    return [r for stype in source_types
            for r in rule_expand_source(rule, stype)]


def rules_expand_sources(rules):
    # takes a list of rules and expands it based on 'cidr_ip', 'group_id', 'group_name'
    if not rules:
        return rules

    return [rule for rule_complex in rules
            for rule in rule_expand_sources(rule_complex)]


def update_rules_description(module, client, rule_type, group_id, ip_permissions):
    if module.check_mode:
        return
    try:
        if rule_type == "in":
            client.update_security_group_rule_descriptions_ingress(GroupId=group_id, IpPermissions=[ip_permissions])
        if rule_type == "out":
            client.update_security_group_rule_descriptions_egress(GroupId=group_id, IpPermissions=[ip_permissions])
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to update rule description for group %s" % group_id)


def serialize_group_grant(group_id, rule):
    permission = {'IpProtocol': rule['proto'],
                  'FromPort': rule['from_port'],
                  'ToPort': rule['to_port'],
                  'UserIdGroupPairs': [{'GroupId': group_id}]}

    if 'rule_desc' in rule:
        permission['UserIdGroupPairs'][0]['Description'] = rule.get('rule_desc') or ''

    return fix_port_and_protocol(permission)


def serialize_revoke(grant, rule):
    permission = {'IpProtocol': rule['IpProtocol'],
                  'FromPort': rule.get('FromPort'),
                  'ToPort': rule.get('ToPort')}
    if 'GroupId' in grant:
        permission['UserIdGroupPairs'] = [{'GroupId': grant['GroupId']}]
    elif 'CidrIp' in grant:
        permission['IpRanges'] = [grant]
    elif 'CidrIpv6' in grant:
        permission['Ipv6Ranges'] = [grant]
    return fix_port_and_protocol(permission)


def serialize_ip_grant(rule, thisip, ethertype):
    permission = {'IpProtocol': rule['proto'],
                  'FromPort': rule['from_port'],
                  'ToPort': rule['to_port']}
    if ethertype == "ipv4":
        permission['IpRanges'] = [{'CidrIp': thisip}]
        if 'rule_desc' in rule:
            permission['IpRanges'][0]['Description'] = rule.get('rule_desc') or ''
    elif ethertype == "ipv6":
        permission['Ipv6Ranges'] = [{'CidrIpv6': thisip}]
        if 'rule_desc' in rule:
            permission['Ipv6Ranges'][0]['Description'] = rule.get('rule_desc') or ''

    return fix_port_and_protocol(permission)


def fix_port_and_protocol(permission):
    for key in ['FromPort', 'ToPort']:
        if key in permission:
            if permission[key] is None:
                del permission[key]
            else:
                permission[key] = int(permission[key])

    permission['IpProtocol'] = str(permission['IpProtocol'])

    return permission


def assemble_permissions_to_revoke(purge_ingress_rule_ids, purge_egress_rule_ids, current_ingress, current_egress):
    revoke_ingress = []
    revoke_egress = []
    for rules_to_purge, revoke_list, current_rules in [(purge_ingress_rule_ids, revoke_ingress, current_ingress),
                                                       (purge_egress_rule_ids, revoke_egress, current_egress)]:
        for rule_id in rules_to_purge:
            rule, grant = current_rules[rule_id]
            ip_permission = serialize_revoke(grant, rule)
            revoke_list.append(ip_permission)
    return revoke_ingress, revoke_egress


def remove_old_permissions(client, module, revoke_ingress, revoke_egress, group_id, changed):
    changed |= bool(revoke_ingress or revoke_egress)
    if revoke_ingress:
        revoke(client, module, revoke_ingress, group_id, 'in')
    if revoke_egress:
        revoke(client, module, revoke_egress, group_id, 'out')
    return changed


def revoke(client, module, ip_permissions, group_id, rule_type):
    if not module.check_mode:
        try:
            if rule_type == 'in':
                client.revoke_security_group_ingress(GroupId=group_id, IpPermissions=ip_permissions)
            elif rule_type == 'out':
                client.revoke_security_group_egress(GroupId=group_id, IpPermissions=ip_permissions)
        except (BotoCoreError, ClientError) as e:
            rules = 'ingress rules' if rule_type == 'in' else 'egress rules'
            module.fail_json_aws(e, "Unable to revoke {0}: {1}".format(rules, ip_permissions))


def add_new_permissions(client, module, new_ingress, new_egress, group_id, changed):
    changed |= bool(new_ingress or new_egress)
    if new_ingress:
        authorize(client, module, new_ingress, group_id, 'in')
    if new_egress:
        authorize(client, module, new_egress, group_id, 'out')
    return changed


def authorize(client, module, ip_permissions, group_id, rule_type):
    if not module.check_mode:
        try:
            if rule_type == 'in':
                client.authorize_security_group_ingress(GroupId=group_id, IpPermissions=ip_permissions)
            elif rule_type == 'out':
                client.authorize_security_group_egress(GroupId=group_id, IpPermissions=ip_permissions)
        except (BotoCoreError, ClientError) as e:
            rules = 'ingress rules' if rule_type == 'in' else 'egress rules'
            module.fail_json_aws(e, "Unable to authorize {0}: {1}".format(rules, ip_permissions))


def add_cidr_ip_list(module, cidr_ip, ip_type, rule, rule_type, group_id):
    rules_list = []
    if not isinstance(cidr_ip, list):
        cidr_ip = [cidr_ip]
    for ip in cidr_ip:
        ip = validate_ip(module, ip)
        rule_id = make_rule_key(rule_type, rule, group_id, ip)
        ip_permission = serialize_ip_grant(rule, ip, ip_type)
        if ip_type == 'ipv4':
            new_rule = Rule(rule=rule, rule_id=rule_id, ip_permission=ip_permission, ipv4=cidr_ip, ipv6=None)
        else:
            new_rule = Rule(rule=rule, rule_id=rule_id, ip_permission=ip_permission, ipv4=None, ipv6=cidr_ip)
        rules_list.append(new_rule)
    return rules_list


def validate_ip(module, cidr_ip):
    split_addr = cidr_ip.split('/')
    if len(split_addr) == 2:
        # this_ip is a IPv4 or IPv6 CIDR that may or may not have host bits set
        # Get the network bits.
        try:
            ip = to_subnet(split_addr[0], split_addr[1])
        except ValueError:
            ip = to_ipv6_network(split_addr[0]) + "/" + split_addr[1]
        if ip != cidr_ip:
            module.warn("One of your CIDR addresses ({0}) has host bits set. To get rid of this warning, "
                        "check the network mask and make sure that only network bits are set: {1}.".format(cidr_ip, ip))
    else:
        ip = cidr_ip
    return ip


def update_existing_rules(client, module, group_id, ingress, egress, changed):
    for new, old, rule_type in [ingress, egress]:
        for r in new:
            grant_type = 'ip' if bool(r.ipv4 or r.ipv6) else 'group'
            if check_rule_description_update(client, module, r.rule_id, r.rule, grant_type, old):
                changed = True
                rule_type = 'in' if r in ingress[0] else 'out'
                update_rules_description(module, client, rule_type, group_id, r.ip_permission)
    return changed


def check_rule_description_update(client, module, rule_id, rule, grant_type, current_rules):
    needs_update = False
    if 'rule_desc' in rule:
        new_rule_description = rule.get('rule_desc') or ''
        if grant_type == 'group':
            current_rule_description = current_rules[rule_id][0]['UserIdGroupPairs'][0].get('Description', '')
        else:
            current_rule_description = (
                current_rules[rule_id][0].get('IpRanges')
                or current_rules[rule_id][0].get('Ipv6Ranges')
            )[0].get('Description')
        if new_rule_description != current_rule_description:
            needs_update = True
    return needs_update


def update_tags(client, module, group_id, current_tags, tags, purge_tags, changed):
    tags_need_modify, tags_to_delete = compare_aws_tags(current_tags, tags, purge_tags)
    changed |= bool(tags_need_modify or tags_to_delete)

    if not module.check_mode:
        if tags_to_delete:
            try:
                client.delete_tags(Resources=[group_id], Tags=[{'Key': tag} for tag in tags_to_delete])
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Unable to delete tags {0}".format(tags_to_delete))

        # Add/update tags
        if tags_need_modify:
            try:
                client.create_tags(Resources=[group_id], Tags=ansible_dict_to_boto3_tag_list(tags_need_modify))
            except (BotoCoreError, ClientError) as e:
                module.fail_json(e, msg="Unable to add tags {0}".format(tags_need_modify))

    return changed


def create_security_group(client, module, name, description, vpc_id):
    if not module.check_mode:
        params = dict(GroupName=name, Description=description)
        if vpc_id:
            params['VpcId'] = vpc_id
        try:
            group = client.create_security_group(**params)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Unable to create security group")
        # When a group is created, an egress_rule ALLOW ALL
        # to 0.0.0.0/0 is added automatically but it's not
        # reflected in the object returned by the AWS API
        # call. We re-read the group for getting an updated object
        # amazon sometimes takes a couple seconds to update the security group so wait till it exists
        while True:
            sleep(3)
            group = get_security_groups_with_backoff(client, GroupIds=[group['GroupId']])['SecurityGroups'][0]
            if group.get('VpcId') and not group.get('IpPermissionsEgress'):
                pass
            else:
                break
        return group
    return None


def group_exists(client, module, vpc_id, group_id, name):
    params = {'Filters': []}
    if group_id:
        params['GroupIds'] = [group_id]
    if name:
        # Add name to filters rather than params['GroupNames']
        # because params['GroupNames'] only checks the default vpc if no vpc is provided
        params['Filters'].append({'Name': 'group-name', 'Values': [name]})
    if vpc_id:
        params['Filters'].append({'Name': 'vpc-id', 'Values': [vpc_id]})
    # Don't filter by description to maintain backwards compatibility

    try:
        security_groups = sg_exists_with_backoff(client, **params).get('SecurityGroups', [])
        all_groups = get_security_groups_with_backoff(client).get('SecurityGroups', [])
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Error in describe_security_groups")

    if security_groups:
        groups = dict((group['GroupId'], group) for group in all_groups)
        groups.update(dict((group['GroupName'], group) for group in all_groups))
        # maintain backwards compatibility by using the last matching group
        return security_groups[-1], groups
    return None, {}


def has_rule_description_attr(client):
    return hasattr(client, "update_security_group_rule_descriptions_egress")


def verify_rules_with_descriptions_permitted(client, module, rules, rules_egress):
    if not has_rule_description_attr(client):
        all_rules = rules if rules else [] + rules_egress if rules_egress else []
        if any('rule_desc' in rule for rule in all_rules):
            module.fail_json(msg="Using rule descriptions requires botocore version >= 1.7.2.")


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        name=dict(),
        group_id=dict(),
        description=dict(),
        vpc_id=dict(),
        rules=dict(type='list'),
        rules_egress=dict(type='list'),
        state=dict(default='present', type='str', choices=['present', 'absent']),
        purge_rules=dict(default=True, required=False, type='bool'),
        purge_rules_egress=dict(default=True, required=False, type='bool'),
        tags=dict(required=False, type='dict', aliases=['resource_tags']),
        purge_tags=dict(default=True, required=False, type='bool')
    )
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[['name', 'group_id']],
        required_if=[['state', 'present', ['name']]],
    )

    name = module.params['name']
    group_id = module.params['group_id']
    description = module.params['description']
    vpc_id = module.params['vpc_id']
    rules = deduplicate_rules_args(rules_expand_sources(rules_expand_ports(module.params['rules'])))
    rules_egress = deduplicate_rules_args(rules_expand_sources(rules_expand_ports(module.params['rules_egress'])))
    state = module.params.get('state')
    purge_rules = module.params['purge_rules']
    purge_rules_egress = module.params['purge_rules_egress']
    tags = module.params['tags']
    purge_tags = module.params['purge_tags']

    if state == 'present' and not description:
        module.fail_json(msg='Must provide description when state is present.')

    changed = False
    client = module.client('ec2')

    verify_rules_with_descriptions_permitted(client, module, rules, rules_egress)
    group, groups = group_exists(client, module, vpc_id, group_id, name)

    # Ensure requested group is absent
    if state == 'absent':
        if group:
            # found a match, delete it
            try:
                if not module.check_mode:
                    client.delete_security_group(GroupId=group['GroupId'])
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Unable to delete security group '%s'" % group)
            else:
                group = None
                changed = True
        else:
            # no match found, no changes required
            pass

    # Ensure requested group is present
    elif state == 'present':
        if group:
            # existing group
            if group['Description'] != description:
                module.warn("Group description does not match existing group. Descriptions cannot be changed without deleting "
                            "and re-creating the security group. Try using state=absent to delete, then rerunning this task.")
        else:
            # no match found, create it
            group = create_security_group(client, module, name, description, vpc_id)
            changed = True

        if tags is not None and group is not None:
            current_tags = boto3_tag_list_to_ansible_dict(group.get('Tags', []))
            changed = update_tags(client, module, group['GroupId'], current_tags, tags, purge_tags, changed)

    if group:
        named_tuple_ingress_list = []
        named_tuple_egress_list = []
        current_ingress = add_rules_to_lookup(group['IpPermissions'], group['GroupId'], 'in', {})
        current_egress = add_rules_to_lookup(group['IpPermissionsEgress'], group['GroupId'], 'out', {})

        for new_rules, rule_type, named_tuple_rule_list in [(rules, 'in', named_tuple_ingress_list),
                                                            (rules_egress, 'out', named_tuple_egress_list)]:
            if new_rules is None:
                continue
            for rule in new_rules:
                group_id, ipv4, ipv6, target_group_created = get_target_from_rule(module, client, rule, name,
                                                                                  group, groups, vpc_id)
                if target_group_created:
                    changed = True

                if rule['proto'] in ('all', '-1', -1):
                    rule['proto'] = -1
                    rule['from_port'] = None
                    rule['to_port'] = None

                if group_id:
                    rule_id = make_rule_key(rule_type, rule, group['GroupId'], group_id)
                    ip_permission = serialize_group_grant(group_id, rule)
                    if ip_permission and vpc_id:
                        [useridpair.update({'VpcId': vpc_id}) for useridpair in
                         ip_permission.get('UserIdGroupPairs', [])]
                    named_tuple_rule_list.append(Rule(rule=rule, rule_id=rule_id, ip_permission=ip_permission,
                                                      ipv4=ipv4, ipv6=ipv6))
                if ipv4:
                    named_tuple_rule_list.extend(add_cidr_ip_list(module, ipv4, "ipv4", rule, rule_type, group['GroupId']))
                if ipv6:
                    named_tuple_rule_list.extend(add_cidr_ip_list(module, ipv6, "ipv6", rule, rule_type, group['GroupId']))

        # List comprehensions for rules to add, rules to modify, and rule ids to determine purging
        new_ingress_permissions = [r.ip_permission for r in named_tuple_ingress_list if r.rule_id not in current_ingress]
        new_egress_permissions = [r.ip_permission for r in named_tuple_egress_list if r.rule_id not in current_egress]
        present_ingress = [r for r in named_tuple_ingress_list if r.rule_id in current_ingress]
        present_egress = [r for r in named_tuple_egress_list if r.rule_id in current_egress]
        user_ingress_rule_ids = [r.rule_id for r in named_tuple_ingress_list]
        user_egress_rule_ids = [r.rule_id for r in named_tuple_egress_list]

        if rules_egress is None and 'VpcId' not in group:
            # when no egress rules are specified and we're in a VPC,
            # we add in a default allow all out rule, which was the
            # default behavior before egress rules were added
            rule = {'IpProtocol': '-1', 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
            rule_id = make_rule_key('out', rule, group['GroupId'], '0.0.0.0/0')
            if rule_id not in current_egress:
                new_egress_permissions.append(rule)
            else:
                present_egress.append(Rule(rule=rule, rule_id=rule_id, ip_permission=rule, ipv4='0.0.0.0/0', ipv6=None))

        # Find rules to purge
        purge_ingress_rule_ids = []
        purge_egress_rule_ids = []
        if purge_rules:
            purge_ingress_rule_ids = [rule_id for rule_id in current_ingress if rule_id not in user_ingress_rule_ids]
        if purge_rules_egress:
            for rule_id in current_egress:
                if rule_id not in user_egress_rule_ids:
                    if rules_egress:
                        purge_egress_rule_ids.append(rule_id)
                    else:
                        if not rule_id.endswith('0.0.0.0/0'):
                            purge_egress_rule_ids.append(rule_id)

        # Assemble ip permissions to remove
        revoke_ingress, revoke_egress = assemble_permissions_to_revoke(purge_ingress_rule_ids, purge_egress_rule_ids,
                                                                       current_ingress, current_egress)

        # Revoke old rules
        changed = remove_old_permissions(client, module, revoke_ingress, revoke_egress, group['GroupId'], changed)

        # Authorize new rules
        changed = add_new_permissions(client, module, new_ingress_permissions, new_egress_permissions, group['GroupId'], changed)

        # Update existing rules
        changed = update_existing_rules(client, module, group['GroupId'], ingress=(present_ingress, current_ingress, 'in'),
                                        egress=(present_egress, current_egress, 'out'), changed=changed)

    if group:
        if changed:
            sleep(5)
        security_group = get_security_groups_with_backoff(client, GroupIds=[group['GroupId']])['SecurityGroups'][0]
        security_group = camel_dict_to_snake_dict(security_group)
        security_group['tags'] = boto3_tag_list_to_ansible_dict(security_group.get('tags', []),
                                                                tag_name_key_name='key', tag_value_key_name='value')
        module.exit_json(changed=changed, **security_group)
    else:
        module.exit_json(changed=changed, group_id=None)


if __name__ == '__main__':
    main()
