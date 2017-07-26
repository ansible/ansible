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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'curated'}

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
    required: false
  rules_egress:
    description:
      - List of firewall outbound rules to enforce in this group (see example). If none are supplied,
        a default all-out rule is assumed. If an empty list is supplied, no outbound rules will be enabled.
        Rule Egress sources list support was added in version 2.4.
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

extends_documentation_fragment:
    - aws
    - ec2

notes:
  - If a rule declares a group_name and that group doesn't exist, it will be
    automatically created. In that case, group_desc should be provided as well.
    The module will refuse to create a depended-on group without a description.
'''

EXAMPLES = '''
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
import time
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn
from ansible.module_utils.ec2 import get_aws_connection_info
from ansible.module_utils.ec2 import ec2_argument_spec
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.ec2 import HAS_BOTO3
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible.module_utils.ec2 import AWSRetry
import traceback

try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_security_groups_with_backoff(connection, **kwargs):
    return connection.describe_security_groups(**kwargs)


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


def add_rules_to_lookup(ipPermissions, group_id, prefix, dict):
    for rule in ipPermissions:
        for groupGrant in rule.get('UserIdGroupPairs'):
            dict[make_rule_key(prefix, rule, group_id, groupGrant.get('GroupId'))] = (rule, groupGrant)
        for ipv4Grants in rule.get('IpRanges'):
            dict[make_rule_key(prefix, rule, group_id, ipv4Grants.get('CidrIp'))] = (rule, ipv4Grants)
        for ipv6Grants in rule.get('Ipv6Ranges'):
            dict[make_rule_key(prefix, rule, group_id, ipv6Grants.get('CidrIpv6'))] = (rule, ipv6Grants)


def validate_rule(module, rule):
    VALID_PARAMS = ('cidr_ip', 'cidr_ipv6',
                    'group_id', 'group_name', 'group_desc',
                    'proto', 'from_port', 'to_port')
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

    FOREIGN_SECURITY_GROUP_REGEX = '^(\S+)/(sg-\S+)/(\S+)'
    group_id = None
    group_name = None
    ip = None
    ipv6 = None
    target_group_created = False

    if 'group_id' in rule and 'cidr_ip' in rule:
        module.fail_json(msg="Specify group_id OR cidr_ip, not both")
    elif 'group_name' in rule and 'cidr_ip' in rule:
        module.fail_json(msg="Specify group_name OR cidr_ip, not both")
    elif 'group_id' in rule and 'cidr_ipv6' in rule:
        module.fail_json(msg="Specify group_id OR cidr_ipv6, not both")
    elif 'group_name' in rule and 'cidr_ipv6' in rule:
        module.fail_json(msg="Specify group_name OR cidr_ipv6, not both")
    elif 'group_id' in rule and 'group_name' in rule:
        module.fail_json(msg="Specify group_id OR group_name, not both")
    elif 'cidr_ip' in rule and 'cidr_ipv6' in rule:
        module.fail_json(msg="Specify cidr_ip OR cidr_ipv6, not both")
    elif rule.get('group_id') and re.match(FOREIGN_SECURITY_GROUP_REGEX, rule['group_id']):
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
        elif group_name in groups and (vpc_id is None or groups[group_name]['VpcId'] == vpc_id):
            group_id = groups[group_name]['GroupId']
        else:
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


def authorize_ip(type, changed, client, group, groupRules,
                 ip, ip_permission, module, rule, ethertype):
    # If rule already exists, don't later delete it
    for thisip in ip:
        rule_id = make_rule_key(type, rule, group['GroupId'], thisip)
        if rule_id in groupRules:
            del groupRules[rule_id]
        else:
            if not module.check_mode:
                ip_permission = serialize_ip_grant(rule, thisip, ethertype)
                if ip_permission:
                    try:
                        if type == "in":
                            client.authorize_security_group_ingress(GroupId=group['GroupId'],
                                                                    IpPermissions=[ip_permission])
                        elif type == "out":
                            client.authorize_security_group_egress(GroupId=group['GroupId'],
                                                                   IpPermissions=[ip_permission])
                    except botocore.exceptions.ClientError as e:
                        module.fail_json(msg="Unable to authorize %s for ip %s security group '%s' - %s" %
                                             (type, thisip, group['GroupName'], e),
                                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
            changed = True
    return changed, ip_permission


def serialize_group_grant(group_id, rule):
    permission = {'IpProtocol': rule['proto'],
                  'FromPort': rule['from_port'],
                  'ToPort': rule['to_port'],
                  'UserIdGroupPairs': [{'GroupId': group_id}]}

    convert_ports_to_int(permission)

    return permission


def serialize_revoke(grant, rule):
    permission = dict()
    fromPort = rule['FromPort'] if 'FromPort' in rule else None
    toPort = rule['ToPort'] if 'ToPort' in rule else None
    if 'GroupId' in grant:
        permission = {'IpProtocol': rule['IpProtocol'],
                      'FromPort': fromPort,
                      'ToPort': toPort,
                      'UserIdGroupPairs': [{'GroupId': grant['GroupId'], 'UserId': grant['UserId']}]
                      }
    elif 'CidrIp' in grant:
        permission = {'IpProtocol': rule['IpProtocol'],
                      'FromPort': fromPort,
                      'ToPort': toPort,
                      'IpRanges': [grant]
                      }
    elif 'CidrIpv6' in grant:
        permission = {'IpProtocol': rule['IpProtocol'],
                      'FromPort': fromPort,
                      'ToPort': toPort,
                      'Ipv6Ranges': [grant]
                      }
    if rule['IpProtocol'] in ('all', '-1', -1):
        del permission['FromPort']
        del permission['ToPort']
    return permission


def serialize_ip_grant(rule, thisip, ethertype):
    permission = {'IpProtocol': rule['proto'],
                  'FromPort': rule['from_port'],
                  'ToPort': rule['to_port']}
    if ethertype == "ipv4":
        permission.update({'IpRanges': [{'CidrIp': thisip}]})
    elif ethertype == "ipv6":
        permission.update({'Ipv6Ranges': [{'CidrIpv6': thisip}]})

    convert_ports_to_int(permission)

    return permission


def convert_ports_to_int(permission):
    for key in ['FromPort', 'ToPort']:
        if permission[key] is not None:
            permission[key] = int(permission[key])


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
        purge_rules_egress=dict(default=True, required=False, type='bool')
    )
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[['name', 'group_id']],
        required_if=[['state', 'present', ['name']]],
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    name = module.params['name']
    group_id = module.params['group_id']
    description = module.params['description']
    vpc_id = module.params['vpc_id']
    rules = deduplicate_rules_args(rules_expand_sources(rules_expand_ports(module.params['rules'])))
    rules_egress = deduplicate_rules_args(rules_expand_sources(rules_expand_ports(module.params['rules_egress'])))
    state = module.params.get('state')
    purge_rules = module.params['purge_rules']
    purge_rules_egress = module.params['purge_rules_egress']

    if state == 'present' and not description:
        module.fail_json(msg='Must provide description when state is present.')

    changed = False
    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    if not region:
        module.fail_json(msg="The AWS region must be specified as an "
                             "environment variable or in the AWS credentials "
                             "profile.")
    client = boto3_conn(module, conn_type='client', resource='ec2', endpoint=ec2_url, region=region, **aws_connect_params)
    group = None
    groups = dict()
    security_groups = []
    # do get all security groups
    # find if the group is present
    try:
        response = get_security_groups_with_backoff(client)
        security_groups = response.get('SecurityGroups', [])
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg="Error in describe_security_groups: %s" % "Unable to locate credentials", exception=traceback.format_exc())
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Error in describe_security_groups: %s" % e, exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))

    for sg in security_groups:
        groups[sg['GroupId']] = sg
        groupName = sg['GroupName']
        if groupName in groups:
            # Prioritise groups from the current VPC
            if vpc_id is None or sg['VpcId'] == vpc_id:
                groups[groupName] = sg
        else:
            groups[groupName] = sg

        if group_id:
            if sg['GroupId'] == group_id:
                group = sg
        else:
            if groupName == name and (vpc_id is None or sg['VpcId'] == vpc_id):
                group = sg

    # Ensure requested group is absent
    if state == 'absent':
        if group:
            # found a match, delete it
            try:
                if not module.check_mode:
                    client.delete_security_group(GroupId=group['GroupId'])
            except botocore.exceptions.ClientError as e:
                module.fail_json(msg="Unable to delete security group '%s' - %s" % (group, e),
                                 exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
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
                module.fail_json(
                    msg="Group description does not match existing group. ec2_group does not support this case.")

        # if the group doesn't exist, create it now
        else:
            # no match found, create it
            if not module.check_mode:
                params = dict(GroupName=name, Description=description)
                if vpc_id:
                    params['VpcId'] = vpc_id
                group = client.create_security_group(**params)
                # When a group is created, an egress_rule ALLOW ALL
                # to 0.0.0.0/0 is added automatically but it's not
                # reflected in the object returned by the AWS API
                # call. We re-read the group for getting an updated object
                # amazon sometimes takes a couple seconds to update the security group so wait till it exists
                while True:
                    group = get_security_groups_with_backoff(client, GroupIds=[group['GroupId']])['SecurityGroups'][0]
                    if not group['IpPermissionsEgress']:
                        time.sleep(0.1)
                    else:
                        break

            changed = True
    else:
        module.fail_json(msg="Unsupported state requested: %s" % state)

    # create a lookup for all existing rules on the group
    if group:
        # Manage ingress rules
        groupRules = {}
        add_rules_to_lookup(group['IpPermissions'], group['GroupId'], 'in', groupRules)
        # Now, go through all provided rules and ensure they are there.
        if rules is not None:
            ip_permission = []
            for rule in rules:
                validate_rule(module, rule)
                group_id, ip, ipv6, target_group_created = get_target_from_rule(module, client, rule, name,
                                                                                group, groups, vpc_id)
                if target_group_created:
                    changed = True

                if rule['proto'] in ('all', '-1', -1):
                    rule['proto'] = -1
                    rule['from_port'] = None
                    rule['to_port'] = None

                if group_id:
                    rule_id = make_rule_key('in', rule, group['GroupId'], group_id)
                    if rule_id in groupRules:
                        del groupRules[rule_id]
                    else:
                        if not module.check_mode:
                            ip_permission = serialize_group_grant(group_id, rule)
                            if ip_permission:
                                ips = ip_permission
                                if vpc_id:
                                    [useridpair.update({'VpcId': vpc_id}) for useridpair in
                                     ip_permission.get('UserIdGroupPairs')]
                                try:
                                    client.authorize_security_group_ingress(GroupId=group['GroupId'], IpPermissions=[ips])
                                except botocore.exceptions.ClientError as e:
                                    module.fail_json(
                                        msg="Unable to authorize ingress for group %s security group '%s' - %s" %
                                            (group_id, group['GroupName'], e),
                                        exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
                        changed = True
                elif ip:
                    # Convert ip to list we can iterate over
                    if ip and not isinstance(ip, list):
                        ip = [ip]

                    changed, ip_permission = authorize_ip("in", changed, client, group, groupRules, ip, ip_permission,
                                                          module, rule, "ipv4")
                elif ipv6:
                    # Convert ip to list we can iterate over
                    if not isinstance(ipv6, list):
                        ipv6 = [ipv6]
                    # If rule already exists, don't later delete it
                    changed, ip_permission = authorize_ip("in", changed, client, group, groupRules, ipv6, ip_permission,
                                                          module, rule, "ipv6")
        # Finally, remove anything left in the groupRules -- these will be defunct rules
        if purge_rules:
            for (rule, grant) in groupRules.values():
                ip_permission = serialize_revoke(grant, rule)
                if not module.check_mode:
                    try:
                        client.revoke_security_group_ingress(GroupId=group['GroupId'], IpPermissions=[ip_permission])
                    except botocore.exceptions.ClientError as e:
                        module.fail_json(
                            msg="Unable to revoke ingress for security group '%s' - %s" %
                                (group['GroupName'], e),
                            exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
                changed = True

        # Manage egress rules
        groupRules = {}
        add_rules_to_lookup(group['IpPermissionsEgress'], group['GroupId'], 'out', groupRules)
        # Now, go through all provided rules and ensure they are there.
        if rules_egress is not None:
            for rule in rules_egress:
                validate_rule(module, rule)
                group_id, ip, ipv6, target_group_created = get_target_from_rule(module, client, rule, name,
                                                                                group, groups, vpc_id)
                if target_group_created:
                    changed = True

                if rule['proto'] in ('all', '-1', -1):
                    rule['proto'] = -1
                    rule['from_port'] = None
                    rule['to_port'] = None

                if group_id:
                    rule_id = make_rule_key('out', rule, group['GroupId'], group_id)
                    if rule_id in groupRules:
                        del groupRules[rule_id]
                    else:
                        if not module.check_mode:
                            ip_permission = serialize_group_grant(group_id, rule)
                            if ip_permission:
                                ips = ip_permission
                                if vpc_id:
                                    [useridpair.update({'VpcId': vpc_id}) for useridpair in
                                     ip_permission.get('UserIdGroupPairs')]
                                try:
                                    client.authorize_security_group_egress(GroupId=group['GroupId'], IpPermissions=[ips])
                                except botocore.exceptions.ClientError as e:
                                    module.fail_json(
                                        msg="Unable to authorize egress for group %s security group '%s' - %s" %
                                            (group_id, group['GroupName'], e),
                                        exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
                        changed = True
                elif ip:
                    # Convert ip to list we can iterate over
                    if not isinstance(ip, list):
                        ip = [ip]
                    changed, ip_permission = authorize_ip("out", changed, client, group, groupRules, ip,
                                                          ip_permission, module, rule, "ipv4")
                elif ipv6:
                    # Convert ip to list we can iterate over
                    if not isinstance(ipv6, list):
                        ipv6 = [ipv6]
                    # If rule already exists, don't later delete it
                    changed, ip_permission = authorize_ip("out", changed, client, group, groupRules, ipv6,
                                                          ip_permission, module, rule, "ipv6")
        else:
            # when no egress rules are specified,
            # we add in a default allow all out rule, which was the
            # default behavior before egress rules were added
            default_egress_rule = 'out--1-None-None-' + group['GroupId'] + '-0.0.0.0/0'
            if default_egress_rule not in groupRules:
                if not module.check_mode:
                    ip_permission = [{'IpProtocol': '-1',
                                      'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                                      }
                                     ]
                    try:
                        client.authorize_security_group_egress(GroupId=group['GroupId'], IpPermissions=ip_permission)
                    except botocore.exceptions.ClientError as e:
                        module.fail_json(msg="Unable to authorize egress for ip %s security group '%s' - %s" %
                                             ('0.0.0.0/0',
                                              group['GroupName'],
                                              e),
                                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
                changed = True
            else:
                # make sure the default egress rule is not removed
                del groupRules[default_egress_rule]

        # Finally, remove anything left in the groupRules -- these will be defunct rules
        if purge_rules_egress:
            for (rule, grant) in groupRules.values():
                # we shouldn't be revoking 0.0.0.0 egress
                if grant != '0.0.0.0/0':
                    ip_permission = serialize_revoke(grant, rule)
                    if not module.check_mode:
                        try:
                            client.revoke_security_group_egress(GroupId=group['GroupId'], IpPermissions=[ip_permission])
                        except botocore.exceptions.ClientError as e:
                            module.fail_json(msg="Unable to revoke egress for ip %s security group '%s' - %s" %
                                                 (grant, group['GroupName'], e),
                                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
                    changed = True

    if group:
        security_group = get_security_groups_with_backoff(client, GroupIds=[group['GroupId']])['SecurityGroups'][0]
        security_group = camel_dict_to_snake_dict(security_group)
        security_group['tags'] = boto3_tag_list_to_ansible_dict(security_group.get('tags', {}),
                                                                tag_name_key_name='key', tag_value_key_name='value')
        module.exit_json(changed=changed, **security_group)
    else:
        module.exit_json(changed=changed, group_id=None)

if __name__ == '__main__':
    main()
