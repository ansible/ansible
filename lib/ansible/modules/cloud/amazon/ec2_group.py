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
    type: bool
  purge_rules_egress:
    version_added: "1.8"
    description:
      - Purge existing rules_egress on security group that are not found in rules_egress
    required: false
    default: 'true'
    aliases: []
    type: bool
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
  - Preview diff mode support is added in version 2.7.
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
        # this should only be needed for EC2 Classic security group rules
        # because in a VPC an ELB will use a user-account security group
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
  diff: True

- name: "Delete group by its id"
  ec2_group:
    region: eu-west-1
    group_id: sg-33b4ee5b
    state: absent
'''

RETURN = '''
group_name:
  description: Security group name
  sample: My Security Group
  type: str
  returned: on create/update
group_id:
  description: Security group id
  sample: sg-abcd1234
  type: str
  returned: on create/update
description:
  description: Description of security group
  sample: My Security Group
  type: str
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
  type: str
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
import itertools
from copy import deepcopy
from time import sleep
from collections import namedtuple
from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code
from ansible.module_utils.aws.iam import get_aws_account_id
from ansible.module_utils.aws.waiters import get_waiter
from ansible.module_utils.ec2 import AWSRetry, camel_dict_to_snake_dict, compare_aws_tags
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list, boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_tag_list
from ansible.module_utils.common.network import to_ipv6_subnet, to_subnet
from ansible.module_utils.compat.ipaddress import ip_network, IPv6Network
from ansible.module_utils._text import to_text
from ansible.module_utils.six import string_types

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # caught by AnsibleAWSModule


Rule = namedtuple('Rule', ['port_range', 'protocol', 'target', 'target_type', 'description'])
valid_targets = set(['ipv4', 'ipv6', 'group', 'ip_prefix'])
current_account_id = None


def rule_cmp(a, b):
    """Compare rules without descriptions"""
    for prop in ['port_range', 'protocol', 'target', 'target_type']:
        if prop == 'port_range' and to_text(a.protocol) == to_text(b.protocol):
            # equal protocols can interchange `(-1, -1)` and `(None, None)`
            if a.port_range in ((None, None), (-1, -1)) and b.port_range in ((None, None), (-1, -1)):
                continue
            elif getattr(a, prop) != getattr(b, prop):
                return False
        elif getattr(a, prop) != getattr(b, prop):
            return False
    return True


def rules_to_permissions(rules):
    return [to_permission(rule) for rule in rules]


def to_permission(rule):
    # take a Rule, output the serialized grant
    perm = {
        'IpProtocol': rule.protocol,
    }
    perm['FromPort'], perm['ToPort'] = rule.port_range
    if rule.target_type == 'ipv4':
        perm['IpRanges'] = [{
            'CidrIp': rule.target,
        }]
        if rule.description:
            perm['IpRanges'][0]['Description'] = rule.description
    elif rule.target_type == 'ipv6':
        perm['Ipv6Ranges'] = [{
            'CidrIpv6': rule.target,
        }]
        if rule.description:
            perm['Ipv6Ranges'][0]['Description'] = rule.description
    elif rule.target_type == 'group':
        if isinstance(rule.target, tuple):
            pair = {}
            if rule.target[0]:
                pair['UserId'] = rule.target[0]
            # group_id/group_name are mutually exclusive - give group_id more precedence as it is more specific
            if rule.target[1]:
                pair['GroupId'] = rule.target[1]
            elif rule.target[2]:
                pair['GroupName'] = rule.target[2]
            perm['UserIdGroupPairs'] = [pair]
        else:
            perm['UserIdGroupPairs'] = [{
                'GroupId': rule.target
            }]
        if rule.description:
            perm['UserIdGroupPairs'][0]['Description'] = rule.description
    elif rule.target_type == 'ip_prefix':
        perm['PrefixListIds'] = [{
            'PrefixListId': rule.target,
        }]
        if rule.description:
            perm['PrefixListIds'][0]['Description'] = rule.description
    elif rule.target_type not in valid_targets:
        raise ValueError('Invalid target type for rule {0}'.format(rule))
    return fix_port_and_protocol(perm)


def rule_from_group_permission(perm):
    def ports_from_permission(p):
        if 'FromPort' not in p and 'ToPort' not in p:
            return (None, None)
        return (int(perm['FromPort']), int(perm['ToPort']))

    # outputs a rule tuple
    for target_key, target_subkey, target_type in [
        ('IpRanges', 'CidrIp', 'ipv4'),
        ('Ipv6Ranges', 'CidrIpv6', 'ipv6'),
        ('PrefixListIds', 'PrefixListId', 'ip_prefix'),
    ]:
        if target_key not in perm:
            continue
        for r in perm[target_key]:
            # there may be several IP ranges here, which is ok
            yield Rule(
                ports_from_permission(perm),
                to_text(perm['IpProtocol']),
                r[target_subkey],
                target_type,
                r.get('Description')
            )
    if 'UserIdGroupPairs' in perm and perm['UserIdGroupPairs']:
        for pair in perm['UserIdGroupPairs']:
            target = pair['GroupId']
            if pair.get('UserId', '').startswith('amazon-'):
                # amazon-elb and amazon-prefix rules don't need
                # group-id specified, so remove it when querying
                # from permission
                target = (
                    target[0],
                    None,
                    target[2],
                )
            elif 'VpcPeeringConnectionId' in pair or pair['UserId'] != current_account_id:
                target = (
                    pair.get('UserId', None),
                    pair.get('GroupId', None),
                    pair.get('GroupName', None),
                )

            yield Rule(
                ports_from_permission(perm),
                to_text(perm['IpProtocol']),
                target,
                'group',
                pair.get('Description')
            )


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_security_groups_with_backoff(connection, **kwargs):
    return connection.describe_security_groups(**kwargs)


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def sg_exists_with_backoff(connection, **kwargs):
    try:
        return connection.describe_security_groups(**kwargs)
    except is_boto3_error_code('InvalidGroup.NotFound'):
        return {'SecurityGroups': []}


def deduplicate_rules_args(rules):
    """Returns unique rules"""
    if rules is None:
        return None
    return list(dict(zip((json.dumps(r, sort_keys=True) for r in rules), rules)).values())


def validate_rule(module, rule):
    VALID_PARAMS = ('cidr_ip', 'cidr_ipv6', 'ip_prefix',
                    'group_id', 'group_name', 'group_desc',
                    'proto', 'from_port', 'to_port', 'rule_desc')
    if not isinstance(rule, dict):
        module.fail_json(msg='Invalid rule parameter type [%s].' % type(rule))
    for k in rule:
        if k not in VALID_PARAMS:
            module.fail_json(msg='Invalid rule parameter \'{0}\' for rule: {1}'.format(k, rule))

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
    Returns tuple of (target_type, target, group_created) after validating rule params.

    rule: Dict describing a rule.
    name: Name of the security group being managed.
    groups: Dict of all available security groups.

    AWS accepts an ip range or a security group as target of a rule. This
    function validate the rule specification and return either a non-None
    group_id or a non-None ip range.
    """
    FOREIGN_SECURITY_GROUP_REGEX = r'^([^/]+)/?(sg-\S+)?/(\S+)'
    group_id = None
    group_name = None
    target_group_created = False

    validate_rule(module, rule)
    if rule.get('group_id') and re.match(FOREIGN_SECURITY_GROUP_REGEX, rule['group_id']):
        # this is a foreign Security Group. Since you can't fetch it you must create an instance of it
        owner_id, group_id, group_name = re.match(FOREIGN_SECURITY_GROUP_REGEX, rule['group_id']).groups()
        group_instance = dict(UserId=owner_id, GroupId=group_id, GroupName=group_name)
        groups[group_id] = group_instance
        groups[group_name] = group_instance
        # group_id/group_name are mutually exclusive - give group_id more precedence as it is more specific
        if group_id and group_name:
            group_name = None
        return 'group', (owner_id, group_id, group_name), False
    elif 'group_id' in rule:
        return 'group', rule['group_id'], False
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
            auto_group = None
            filters = {'group-name': group_name}
            if vpc_id:
                filters['vpc-id'] = vpc_id
            # if we got here, either the target group does not exist, or there
            # is a mix of EC2 classic + VPC groups. Mixing of EC2 classic + VPC
            # is bad, so we have to create a new SG because no compatible group
            # exists
            if not rule.get('group_desc', '').strip():
                # retry describing the group once
                try:
                    auto_group = get_security_groups_with_backoff(client, Filters=ansible_dict_to_boto3_filter_list(filters)).get('SecurityGroups', [])[0]
                except (is_boto3_error_code('InvalidGroup.NotFound'), IndexError):
                    module.fail_json(msg="group %s will be automatically created by rule %s but "
                                         "no description was provided" % (group_name, rule))
                except ClientError as e:  # pylint: disable=duplicate-except
                    module.fail_json_aws(e)
            elif not module.check_mode:
                params = dict(GroupName=group_name, Description=rule['group_desc'])
                if vpc_id:
                    params['VpcId'] = vpc_id
                try:
                    auto_group = client.create_security_group(**params)
                    get_waiter(
                        client, 'security_group_exists',
                    ).wait(
                        GroupIds=[auto_group['GroupId']],
                    )
                except is_boto3_error_code('InvalidGroup.Duplicate'):
                    # The group exists, but didn't show up in any of our describe-security-groups calls
                    # Try searching on a filter for the name, and allow a retry window for AWS to update
                    # the model on their end.
                    try:
                        auto_group = get_security_groups_with_backoff(client, Filters=ansible_dict_to_boto3_filter_list(filters)).get('SecurityGroups', [])[0]
                    except IndexError as e:
                        module.fail_json(msg="Could not create or use existing group '{0}' in rule. Make sure the group exists".format(group_name))
                    except ClientError as e:
                        module.fail_json_aws(
                            e,
                            msg="Could not create or use existing group '{0}' in rule. Make sure the group exists".format(group_name))
            if auto_group is not None:
                group_id = auto_group['GroupId']
                groups[group_id] = auto_group
                groups[group_name] = auto_group
            target_group_created = True
        return 'group', group_id, target_group_created
    elif 'cidr_ip' in rule:
        return 'ipv4', validate_ip(module, rule['cidr_ip']), False
    elif 'cidr_ipv6' in rule:
        return 'ipv6', validate_ip(module, rule['cidr_ipv6']), False
    elif 'ip_prefix' in rule:
        return 'ip_prefix', rule['ip_prefix'], False

    module.fail_json(msg="Could not match target for rule {0}".format(rule), failed_rule=rule)


def ports_expand(ports):
    # takes a list of ports and returns a list of (port_from, port_to)
    ports_expanded = []
    for port in ports:
        if not isinstance(port, string_types):
            ports_expanded.append((port,) * 2)
        elif '-' in port:
            ports_expanded.append(tuple(int(p.strip()) for p in port.split('-', 1)))
        else:
            ports_expanded.append((int(port.strip()),) * 2)

    return ports_expanded


def rule_expand_ports(rule):
    # takes a rule dict and returns a list of expanded rule dicts
    if 'ports' not in rule:
        if isinstance(rule.get('from_port'), string_types):
            rule['from_port'] = int(rule.get('from_port'))
        if isinstance(rule.get('to_port'), string_types):
            rule['to_port'] = int(rule.get('to_port'))
        return [rule]

    ports = rule['ports'] if isinstance(rule['ports'], list) else [rule['ports']]

    rule_expanded = []
    for from_to in ports_expand(ports):
        temp_rule = rule.copy()
        del temp_rule['ports']
        temp_rule['from_port'], temp_rule['to_port'] = sorted(from_to)
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
    source_types_all = ('cidr_ip', 'cidr_ipv6', 'group_id', 'group_name', 'ip_prefix')

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
    source_types = (stype for stype in ('cidr_ip', 'cidr_ipv6', 'group_id', 'group_name', 'ip_prefix') if stype in rule)

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
            client.update_security_group_rule_descriptions_ingress(GroupId=group_id, IpPermissions=ip_permissions)
        if rule_type == "out":
            client.update_security_group_rule_descriptions_egress(GroupId=group_id, IpPermissions=ip_permissions)
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to update rule description for group %s" % group_id)


def fix_port_and_protocol(permission):
    for key in ('FromPort', 'ToPort'):
        if key in permission:
            if permission[key] is None:
                del permission[key]
            else:
                permission[key] = int(permission[key])

    permission['IpProtocol'] = to_text(permission['IpProtocol'])

    return permission


def remove_old_permissions(client, module, revoke_ingress, revoke_egress, group_id):
    if revoke_ingress:
        revoke(client, module, revoke_ingress, group_id, 'in')
    if revoke_egress:
        revoke(client, module, revoke_egress, group_id, 'out')
    return bool(revoke_ingress or revoke_egress)


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


def add_new_permissions(client, module, new_ingress, new_egress, group_id):
    if new_ingress:
        authorize(client, module, new_ingress, group_id, 'in')
    if new_egress:
        authorize(client, module, new_egress, group_id, 'out')
    return bool(new_ingress or new_egress)


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


def validate_ip(module, cidr_ip):
    split_addr = cidr_ip.split('/')
    if len(split_addr) == 2:
        # this_ip is a IPv4 or IPv6 CIDR that may or may not have host bits set
        # Get the network bits if IPv4, and validate if IPv6.
        try:
            ip = to_subnet(split_addr[0], split_addr[1])
            if ip != cidr_ip:
                module.warn("One of your CIDR addresses ({0}) has host bits set. To get rid of this warning, "
                            "check the network mask and make sure that only network bits are set: {1}.".format(
                                cidr_ip, ip))
        except ValueError:
            # to_subnet throws a ValueError on IPv6 networks, so we should be working with v6 if we get here
            try:
                isinstance(ip_network(to_text(cidr_ip)), IPv6Network)
                ip = cidr_ip
            except ValueError:
                # If a host bit is set on something other than a /128, IPv6Network will throw a ValueError
                # The ipv6_cidr in this case probably looks like "2001:DB8:A0B:12F0::1/64" and we just want the network bits
                ip6 = to_ipv6_subnet(split_addr[0]) + "/" + split_addr[1]
                if ip6 != cidr_ip:
                    module.warn("One of your IPv6 CIDR addresses ({0}) has host bits set. To get rid of this warning, "
                                "check the network mask and make sure that only network bits are set: {1}.".format(cidr_ip, ip6))
                return ip6
        return ip
    return cidr_ip


def update_tags(client, module, group_id, current_tags, tags, purge_tags):
    tags_need_modify, tags_to_delete = compare_aws_tags(current_tags, tags, purge_tags)

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

    return bool(tags_need_modify or tags_to_delete)


def update_rule_descriptions(module, group_id, present_ingress, named_tuple_ingress_list, present_egress, named_tuple_egress_list):
    changed = False
    client = module.client('ec2')
    ingress_needs_desc_update = []
    egress_needs_desc_update = []

    for present_rule in present_egress:
        needs_update = [r for r in named_tuple_egress_list if rule_cmp(r, present_rule) and r.description != present_rule.description]
        for r in needs_update:
            named_tuple_egress_list.remove(r)
        egress_needs_desc_update.extend(needs_update)
    for present_rule in present_ingress:
        needs_update = [r for r in named_tuple_ingress_list if rule_cmp(r, present_rule) and r.description != present_rule.description]
        for r in needs_update:
            named_tuple_ingress_list.remove(r)
        ingress_needs_desc_update.extend(needs_update)

    if ingress_needs_desc_update:
        update_rules_description(module, client, 'in', group_id, rules_to_permissions(ingress_needs_desc_update))
        changed |= True
    if egress_needs_desc_update:
        update_rules_description(module, client, 'out', group_id, rules_to_permissions(egress_needs_desc_update))
        changed |= True
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


def wait_for_rule_propagation(module, group, desired_ingress, desired_egress, purge_ingress, purge_egress):
    group_id = group['GroupId']
    tries = 6

    def await_rules(group, desired_rules, purge, rule_key):
        for i in range(tries):
            current_rules = set(sum([list(rule_from_group_permission(p)) for p in group[rule_key]], []))
            if purge and len(current_rules ^ set(desired_rules)) == 0:
                return group
            elif purge:
                conflicts = current_rules ^ set(desired_rules)
                # For cases where set comparison is equivalent, but invalid port/proto exist
                for a, b in itertools.combinations(conflicts, 2):
                    if rule_cmp(a, b):
                        conflicts.discard(a)
                        conflicts.discard(b)
                if not len(conflicts):
                    return group
            elif current_rules.issuperset(desired_rules) and not purge:
                return group
            sleep(10)
            group = get_security_groups_with_backoff(module.client('ec2'), GroupIds=[group_id])['SecurityGroups'][0]
        module.warn("Ran out of time waiting for {0} {1}. Current: {2}, Desired: {3}".format(group_id, rule_key, current_rules, desired_rules))
        return group

    group = get_security_groups_with_backoff(module.client('ec2'), GroupIds=[group_id])['SecurityGroups'][0]
    if 'VpcId' in group and module.params.get('rules_egress') is not None:
        group = await_rules(group, desired_egress, purge_egress, 'IpPermissionsEgress')
    return await_rules(group, desired_ingress, purge_ingress, 'IpPermissions')


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
    except (BotoCoreError, ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Error in describe_security_groups")

    if security_groups:
        groups = dict((group['GroupId'], group) for group in all_groups)
        groups.update(dict((group['GroupName'], group) for group in all_groups))
        if vpc_id:
            vpc_wins = dict((group['GroupName'], group) for group in all_groups if group.get('VpcId') and group['VpcId'] == vpc_id)
            groups.update(vpc_wins)
        # maintain backwards compatibility by using the last matching group
        return security_groups[-1], groups
    return None, {}


def verify_rules_with_descriptions_permitted(client, module, rules, rules_egress):
    if not hasattr(client, "update_security_group_rule_descriptions_egress"):
        all_rules = rules if rules else [] + rules_egress if rules_egress else []
        if any('rule_desc' in rule for rule in all_rules):
            module.fail_json(msg="Using rule descriptions requires botocore version >= 1.7.2.")


def get_diff_final_resource(client, module, security_group):
    def get_account_id(security_group, module):
        try:
            owner_id = security_group.get('owner_id', module.client('sts').get_caller_identity()['Account'])
        except (BotoCoreError, ClientError) as e:
            owner_id = "Unable to determine owner_id: {0}".format(to_text(e))
        return owner_id

    def get_final_tags(security_group_tags, specified_tags, purge_tags):
        if specified_tags is None:
            return security_group_tags
        tags_need_modify, tags_to_delete = compare_aws_tags(security_group_tags, specified_tags, purge_tags)
        end_result_tags = dict((k, v) for k, v in specified_tags.items() if k not in tags_to_delete)
        end_result_tags.update(dict((k, v) for k, v in security_group_tags.items() if k not in tags_to_delete))
        end_result_tags.update(tags_need_modify)
        return end_result_tags

    def get_final_rules(client, module, security_group_rules, specified_rules, purge_rules):
        if specified_rules is None:
            return security_group_rules
        if purge_rules:
            final_rules = []
        else:
            final_rules = list(security_group_rules)
        specified_rules = flatten_nested_targets(module, deepcopy(specified_rules))
        for rule in specified_rules:
            format_rule = {
                'from_port': None, 'to_port': None, 'ip_protocol': rule.get('proto', 'tcp'),
                'ip_ranges': [], 'ipv6_ranges': [], 'prefix_list_ids': [], 'user_id_group_pairs': []
            }
            if rule.get('proto', 'tcp') in ('all', '-1', -1):
                format_rule['ip_protocol'] = '-1'
                format_rule.pop('from_port')
                format_rule.pop('to_port')
            elif rule.get('ports'):
                if rule.get('ports') and (isinstance(rule['ports'], string_types) or isinstance(rule['ports'], int)):
                    rule['ports'] = [rule['ports']]
                for port in rule.get('ports'):
                    if isinstance(port, string_types) and '-' in port:
                        format_rule['from_port'], format_rule['to_port'] = port.split('-')
                    else:
                        format_rule['from_port'] = format_rule['to_port'] = port
            elif rule.get('from_port') or rule.get('to_port'):
                format_rule['from_port'] = rule.get('from_port', rule.get('to_port'))
                format_rule['to_port'] = rule.get('to_port', rule.get('from_port'))
            for source_type in ('cidr_ip', 'cidr_ipv6', 'prefix_list_id'):
                if rule.get(source_type):
                    rule_key = {'cidr_ip': 'ip_ranges', 'cidr_ipv6': 'ipv6_ranges', 'prefix_list_id': 'prefix_list_ids'}.get(source_type)
                    if rule.get('rule_desc'):
                        format_rule[rule_key] = [{source_type: rule[source_type], 'description': rule['rule_desc']}]
                    else:
                        if not isinstance(rule[source_type], list):
                            rule[source_type] = [rule[source_type]]
                        format_rule[rule_key] = [{source_type: target} for target in rule[source_type]]
            if rule.get('group_id') or rule.get('group_name'):
                rule_sg = camel_dict_to_snake_dict(group_exists(client, module, module.params['vpc_id'], rule.get('group_id'), rule.get('group_name'))[0])
                format_rule['user_id_group_pairs'] = [{
                    'description': rule_sg.get('description', rule_sg.get('group_desc')),
                    'group_id': rule_sg.get('group_id', rule.get('group_id')),
                    'group_name': rule_sg.get('group_name', rule.get('group_name')),
                    'peering_status': rule_sg.get('peering_status'),
                    'user_id': rule_sg.get('user_id', get_account_id(security_group, module)),
                    'vpc_id': rule_sg.get('vpc_id', module.params['vpc_id']),
                    'vpc_peering_connection_id': rule_sg.get('vpc_peering_connection_id')
                }]
                for k, v in format_rule['user_id_group_pairs'][0].items():
                    if v is None:
                        format_rule['user_id_group_pairs'][0].pop(k)
            final_rules.append(format_rule)
            # Order final rules consistently
            final_rules.sort(key=lambda x: x.get('cidr_ip', x.get('ip_ranges', x.get('ipv6_ranges', x.get('prefix_list_ids', x.get('user_id_group_pairs'))))))
        return final_rules
    security_group_ingress = security_group.get('ip_permissions', [])
    specified_ingress = module.params['rules']
    purge_ingress = module.params['purge_rules']
    security_group_egress = security_group.get('ip_permissions_egress', [])
    specified_egress = module.params['rules_egress']
    purge_egress = module.params['purge_rules_egress']
    return {
        'description': module.params['description'],
        'group_id': security_group.get('group_id', 'sg-xxxxxxxx'),
        'group_name': security_group.get('group_name', module.params['name']),
        'ip_permissions': get_final_rules(client, module, security_group_ingress, specified_ingress, purge_ingress),
        'ip_permissions_egress': get_final_rules(client, module, security_group_egress, specified_egress, purge_egress),
        'owner_id': get_account_id(security_group, module),
        'tags': get_final_tags(security_group.get('tags', {}), module.params['tags'], module.params['purge_tags']),
        'vpc_id': security_group.get('vpc_id', module.params['vpc_id'])}


def flatten_nested_targets(module, rules):
    def _flatten(targets):
        for target in targets:
            if isinstance(target, list):
                for t in _flatten(target):
                    yield t
            elif isinstance(target, string_types):
                yield target

    if rules is not None:
        for rule in rules:
            target_list_type = None
            if isinstance(rule.get('cidr_ip'), list):
                target_list_type = 'cidr_ip'
            elif isinstance(rule.get('cidr_ipv6'), list):
                target_list_type = 'cidr_ipv6'
            if target_list_type is not None:
                rule[target_list_type] = list(_flatten(rule[target_list_type]))
    return rules


def main():
    argument_spec = dict(
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
    rules = flatten_nested_targets(module, deepcopy(module.params['rules']))
    rules_egress = flatten_nested_targets(module, deepcopy(module.params['rules_egress']))
    rules = deduplicate_rules_args(rules_expand_sources(rules_expand_ports(rules)))
    rules_egress = deduplicate_rules_args(rules_expand_sources(rules_expand_ports(rules_egress)))
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
    group_created_new = not bool(group)

    global current_account_id
    current_account_id = get_aws_account_id(module)

    before = {}
    after = {}

    # Ensure requested group is absent
    if state == 'absent':
        if group:
            # found a match, delete it
            before = camel_dict_to_snake_dict(group, ignore_list=['Tags'])
            before['tags'] = boto3_tag_list_to_ansible_dict(before.get('tags', []))
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
            before = camel_dict_to_snake_dict(group, ignore_list=['Tags'])
            before['tags'] = boto3_tag_list_to_ansible_dict(before.get('tags', []))
            if group['Description'] != description:
                module.warn("Group description does not match existing group. Descriptions cannot be changed without deleting "
                            "and re-creating the security group. Try using state=absent to delete, then rerunning this task.")
        else:
            # no match found, create it
            group = create_security_group(client, module, name, description, vpc_id)
            changed = True

        if tags is not None and group is not None:
            current_tags = boto3_tag_list_to_ansible_dict(group.get('Tags', []))
            changed |= update_tags(client, module, group['GroupId'], current_tags, tags, purge_tags)

    if group:
        named_tuple_ingress_list = []
        named_tuple_egress_list = []
        current_ingress = sum([list(rule_from_group_permission(p)) for p in group['IpPermissions']], [])
        current_egress = sum([list(rule_from_group_permission(p)) for p in group['IpPermissionsEgress']], [])

        for new_rules, rule_type, named_tuple_rule_list in [(rules, 'in', named_tuple_ingress_list),
                                                            (rules_egress, 'out', named_tuple_egress_list)]:
            if new_rules is None:
                continue
            for rule in new_rules:
                target_type, target, target_group_created = get_target_from_rule(
                    module, client, rule, name, group, groups, vpc_id)
                changed |= target_group_created

                if rule.get('proto', 'tcp') in ('all', '-1', -1):
                    rule['proto'] = '-1'
                    rule['from_port'] = None
                    rule['to_port'] = None
                try:
                    int(rule.get('proto', 'tcp'))
                    rule['proto'] = to_text(rule.get('proto', 'tcp'))
                    rule['from_port'] = None
                    rule['to_port'] = None
                except ValueError:
                    # rule does not use numeric protocol spec
                    pass

                named_tuple_rule_list.append(
                    Rule(
                        port_range=(rule['from_port'], rule['to_port']),
                        protocol=to_text(rule.get('proto', 'tcp')),
                        target=target, target_type=target_type,
                        description=rule.get('rule_desc'),
                    )
                )

        # List comprehensions for rules to add, rules to modify, and rule ids to determine purging
        new_ingress_permissions = [to_permission(r) for r in (set(named_tuple_ingress_list) - set(current_ingress))]
        new_egress_permissions = [to_permission(r) for r in (set(named_tuple_egress_list) - set(current_egress))]

        if module.params.get('rules_egress') is None and 'VpcId' in group:
            # when no egress rules are specified and we're in a VPC,
            # we add in a default allow all out rule, which was the
            # default behavior before egress rules were added
            rule = Rule((None, None), '-1', '0.0.0.0/0', 'ipv4', None)
            if rule in current_egress:
                named_tuple_egress_list.append(rule)
            if rule not in current_egress:
                current_egress.append(rule)

        # List comprehensions for rules to add, rules to modify, and rule ids to determine purging
        present_ingress = list(set(named_tuple_ingress_list).union(set(current_ingress)))
        present_egress = list(set(named_tuple_egress_list).union(set(current_egress)))

        if purge_rules:
            revoke_ingress = []
            for p in present_ingress:
                if not any([rule_cmp(p, b) for b in named_tuple_ingress_list]):
                    revoke_ingress.append(to_permission(p))
        else:
            revoke_ingress = []
        if purge_rules_egress and module.params.get('rules_egress') is not None:
            if module.params.get('rules_egress') is []:
                revoke_egress = [
                    to_permission(r) for r in set(present_egress) - set(named_tuple_egress_list)
                    if r != Rule((None, None), '-1', '0.0.0.0/0', 'ipv4', None)
                ]
            else:
                revoke_egress = []
                for p in present_egress:
                    if not any([rule_cmp(p, b) for b in named_tuple_egress_list]):
                        revoke_egress.append(to_permission(p))
        else:
            revoke_egress = []

        # named_tuple_ingress_list and named_tuple_egress_list got updated by
        # method update_rule_descriptions, deep copy these two lists to new
        # variables for the record of the 'desired' ingress and egress sg permissions
        desired_ingress = deepcopy(named_tuple_ingress_list)
        desired_egress = deepcopy(named_tuple_egress_list)

        changed |= update_rule_descriptions(module, group['GroupId'], present_ingress, named_tuple_ingress_list, present_egress, named_tuple_egress_list)

        # Revoke old rules
        changed |= remove_old_permissions(client, module, revoke_ingress, revoke_egress, group['GroupId'])
        rule_msg = 'Revoking {0}, and egress {1}'.format(revoke_ingress, revoke_egress)

        new_ingress_permissions = [to_permission(r) for r in (set(named_tuple_ingress_list) - set(current_ingress))]
        new_ingress_permissions = rules_to_permissions(set(named_tuple_ingress_list) - set(current_ingress))
        new_egress_permissions = rules_to_permissions(set(named_tuple_egress_list) - set(current_egress))
        # Authorize new rules
        changed |= add_new_permissions(client, module, new_ingress_permissions, new_egress_permissions, group['GroupId'])

        if group_created_new and module.params.get('rules') is None and module.params.get('rules_egress') is None:
            # A new group with no rules provided is already being awaited.
            # When it is created we wait for the default egress rule to be added by AWS
            security_group = get_security_groups_with_backoff(client, GroupIds=[group['GroupId']])['SecurityGroups'][0]
        elif changed and not module.check_mode:
            # keep pulling until current security group rules match the desired ingress and egress rules
            security_group = wait_for_rule_propagation(module, group, desired_ingress, desired_egress, purge_rules, purge_rules_egress)
        else:
            security_group = get_security_groups_with_backoff(client, GroupIds=[group['GroupId']])['SecurityGroups'][0]
        security_group = camel_dict_to_snake_dict(security_group, ignore_list=['Tags'])
        security_group['tags'] = boto3_tag_list_to_ansible_dict(security_group.get('tags', []))

    else:
        security_group = {'group_id': None}

    if module._diff:
        if module.params['state'] == 'present':
            after = get_diff_final_resource(client, module, security_group)

        security_group['diff'] = [{'before': before, 'after': after}]

    module.exit_json(changed=changed, **security_group)


if __name__ == '__main__':
    main()
