#!/usr/bin/python
# Copyright (c) 2017 Alibaba Group Holding Limited. He Guimin <heguimin36@163.com.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see http://www.gnu.org/licenses/.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ali_security_group
version_added: "2.8"
short_description: Manage Alibaba Cloud Security Group and its rules.
description:
  - Create and Delete Security Group, Modify its description and add/remove rules.
options:
  state:
    description:
      - Create, delete a security group
    default: 'present'
    choices: ['present', 'absent']
  name:
    description:
      - Name of the security group, which is a string of 2 to 128 Chinese or English characters. It must begin with an
        uppercase/lowercase letter or a Chinese character and can contain numerals, "_", "." or "-".
        It cannot begin with http:// or https://.
        This is used in combination with C(vpc_id) to determine if a Securty Group already exists.
    required: True
    aliases: ['group_name']
  description:
    description:
      - Description of the security group, which is a string of 2 to 256 characters.
      - It cannot begin with http:// or https://.
  vpc_id:
    description:
      - ID of the VPC to create the group in. This is used in conjunction with the C(name) to ensure idempotence.
  rules:
    description:
      - List of hash/dictionaries firewall inbound rules to enforce in this group (see example). If none are supplied,
        no inbound rules will be enabled. Each rule has several keys and refer to
        https://www.alibabacloud.com/help/doc-detail/25554.htm. Each key should be format as under_score.
        At present, the valid keys including "ip_protocol", "port_range", "source_port_range", "nic_type", "policy",
        "dest_cidr_ip", "source_cidr_ip", "source_group_id", "source_group_owner_account", "source_group_owner_id",
        "priority" and "description".
  rules_egress:
    description:
      - List of hash/dictionaries firewall outbound rules to enforce in this group (see example). If none are supplied,
        no outbound rules will be enabled. Each rule has several keys and refer to
        https://www.alibabacloud.com/help/doc-detail/25560.htm. Each key should be format as under_score.
        At present, the valid keys including "ip_protocol", "port_range", "source_port_range", "nic_type", "policy",
        "dest_cidr_ip", "source_cidr_ip", "dest_group_id", "dest_group_owner_account", "dest_group_owner_id",
        "priority" and "description".
  purge_rules:
    description:
      - Purge existing rules on security group that are not found in rules
    default: True
    type: bool
  purge_rules_egress:
    description:
      - Purge existing rules_egress on security group that are not found in rules_egress
    default: True
    type: bool
  tags:
    description:
      - A hash/dictionaries of security group tags. C({"key":"value"})
    aliases: ["group_tags"]
  multi_ok:
    description:
      - By default the module will not create another Security Group if there is another Security Group
        with the same I(name) or I(vpc_id). Specify this as true if you want duplicate Security Groups created.
        There will be conflict when I(multi_ok=True) and I(recent=True).
    default: False
    type: bool
  recent:
    description:
      - By default the module will not choose the recent one if there is another Security Group with
        the same I(name) or I(vpc_id). Specify this as true if you want to target the recent Security Group.
        There will be conflict when I(multi_ok=True) and I(recent=True).
    default: False
    type: bool
requirements:
    - "python >= 2.6"
    - "footmark >= 1.7.0"
extends_documentation_fragment:
    - alicloud
author:
  - "He Guimin (@xiaozhu36)"
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the Alibaba Cloud Guide for details.
- name: create a new security group
  ali_security_group:
    name: 'AliyunSG'
    vpc_id: 'vpc-123csecd'

- name: authorize security group
  ali_security_group:
    name: 'AliyunSG'
    vpc_id: 'vpc-123csecd'
    rules:
      - ip_protocol: tcp
        port_range: 1/122
        source_cidr_ip: '10.159.6.18/12'
    rules_egress:
      - ip_protocol: icmp
        port_range: -1/-1
        source_cidr_ip: 10.0.0.0/10
        dest_group_id: 'sg-ce33rdsfe'
        priority: 1

- name: delete security grp
  ali_security_group:
    name: 'AliyunSG'
    vpc_id: 'vpc-123csecd'
    state: absent

'''

RETURN = '''
group:
    description: Dictionary of security group values
    returned: always
    type: complex
    contains:
        description:
            description: The Security Group description.
            returned: always
            type: string
            sample: "my ansible group"
        group_name:
            description: Security group name
            sample: "my-ansible-group"
            type: string
            returned: always
        group_id:
            description: Security group id
            sample: sg-abcd1234
            type: string
            returned: always
        id:
            description: Alias of "group_id".
            sample: sg-abcd1234
            type: string
            returned: always
        inner_access_policy:
            description: Whether can access each other in one security group.
            sample: True
            type: bool
            returned: always
        tags:
            description: Tags associated with the security group
            sample:
            Name: My Security Group
            From: Ansible
            type: dict
            returned: always
        vpc_id:
            description: ID of VPC to which the security group belongs
            sample: vpc-abcd1234
            type: string
            returned: always
        permissions:
            description: Inbound rules associated with the security group.
            sample:
                - create_time: "2018-06-28T08:45:58Z"
                  description: "None"
                  dest_cidr_ip: "None"
                  dest_group_id: "None"
                  dest_group_name: "None"
                  dest_group_owner_account: "None"
                  direction: "ingress"
                  ip_protocol: "TCP"
                  nic_type: "intranet"
                  policy: "Accept"
                  port_range: "22/22"
                  priority: 1
                  source_cidr_ip: "0.0.0.0/0"
                  source_group_id: "None"
                  source_group_name: "None"
                  source_group_owner_account: "None"
            type: list
            returned: always
        permissions_egress:
            description: Outbound rules associated with the security group.
            sample:
                - create_time: "2018-06-28T08:45:59Z"
                  description: "NOne"
                  dest_cidr_ip: "192.168.0.54/32"
                  dest_group_id: "None"
                  dest_group_name: "None"
                  dest_group_owner_account: "None"
                  direction: "egress"
                  ip_protocol: "TCP"
                  nic_type: "intranet"
                  policy: "Accept"
                  port_range: "80/80"
                  priority: 1
                  source_cidr_ip: "None"
                  source_group_id: "None"
                  source_group_name: "None"
                  source_group_owner_account: "None"
            type: list
            returned: always
'''

import time
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.alicloud_ecs import ecs_argument_spec, ecs_connect


try:
    from footmark.exception import ECSResponseError

    HAS_FOOTMARK = True
except ImportError:
    HAS_FOOTMARK = False


VALID_INGRESS_PARAMS = ["ip_protocol", "port_range", "source_port_range", "nic_type", "policy",
                        "dest_cidr_ip", "source_cidr_ip", "priority", "description",
                        "source_group_id", "source_group_owner_account", "source_group_owner_id"]
VALID_EGRESS_PARAMS = ["ip_protocol", "port_range", "source_port_range", "nic_type", "policy",
                       "dest_cidr_ip", "source_cidr_ip", "priority", "description",
                       "dest_group_id", "dest_group_owner_account", "dest_group_owner_id"]


def validate_group_rule_keys(module, rule, direction):

    if not isinstance(rule, dict):
        module.fail_json(msg='Invalid rule parameter type [{0}].'.format(type(rule)))

    VALID_PARAMS = VALID_INGRESS_PARAMS
    if direction == "egress":
        VALID_PARAMS = VALID_EGRESS_PARAMS

    for k in rule:
        if k not in VALID_PARAMS:
            module.fail_json(msg="Invalid rule parameter '{0}' for rule: {1}. Supported parametes include: {2}".format(k, rule, VALID_PARAMS))

    if 'ip_protocol' not in rule:
        module.fail_json(msg='ip_protocol is required.')
    if 'port_range' not in rule:
        module.fail_json(msg='port_range is required.')
    # The system response will return upper protocol
    rule['ip_protocol'] = str(rule['ip_protocol']).upper()


def purge_rules(module, group, existing_rule, rules, direction):

    if not isinstance(existing_rule, dict):
        module.fail_json(msg='Invalid existing rule type [{0}].'.format(type(existing_rule)))

    if not isinstance(rules, list):
        module.fail_json(msg='Invalid rules type [{0}]. The specified rules should be a list.'.format(type(rules)))

    VALID_PARAMS = VALID_INGRESS_PARAMS
    if direction == "egress":
        VALID_PARAMS = VALID_EGRESS_PARAMS

    # Find the rules which is not in the specified rules
    find = False
    for rule in rules:
        for key in VALID_PARAMS:
            if not rule.get(key):
                continue
            if existing_rule.get(key) != rule.get(key):
                find = False
                break
            find = True
        if find:
            break
    # If it is not found, there will not purge anythind
    if not find:
        return group.revoke(existing_rule, direction)
    return False


def group_exists(conn, module, vpc_id, name, multi, recent):
    """Returns None or a security group object depending on the existence of a security group.
    When supplied with a vpc_id and Name, it will check them to determine if it is a match
    otherwise it will assume the Security Group does not exist and thus return None.
    """
    if multi:
        return None
    matching_groups = []
    filters = {}
    if vpc_id:
        filters['vpc_id'] = vpc_id
    try:
        for g in conn.describe_security_groups(**filters):
            if g.security_group_name == name:
                matching_groups.append(g)
    except Exception as e:
        module.fail_json(msg="Failed to describe Security Groups: {0}".format(e))

    if len(matching_groups) == 1:
        return matching_groups[0]
    elif len(matching_groups) > 1:
        if recent:
            return matching_groups[-1]
        module.fail_json(msg='Currently there are {0} Security Groups that have the same name and '
                             'vpc id you specified. If you would like to create anyway '
                             'please pass True to the multi_ok param. Or, please pass True to the recent '
                             'param to choose the recent one.'.format(len(matching_groups)))
    return None


def main():
    argument_spec = ecs_argument_spec()
    argument_spec.update(dict(
        state=dict(default='present', type='str', choices=['present', 'absent']),
        name=dict(type='str', required=True, aliases=['group_name']),
        description=dict(type='str'),
        vpc_id=dict(type='str'),
        tags=dict(type='dict', aliases=['group_tags']),
        rules=dict(type='list'),
        rules_egress=dict(type='list'),
        purge_rules=dict(type='bool', default=True),
        purge_rules_egress=dict(type='bool', default=True),
        multi_ok=dict(type='bool', default=False),
        recent=dict(type='bool', default=False),
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    if HAS_FOOTMARK is False:
        module.fail_json(msg='footmark is required for the module ali_security_group.')

    ecs = ecs_connect(module)

    state = module.params['state']
    group_name = module.params['name']
    if str(group_name).startswith('http://') or str(group_name).startswith('https://'):
        module.fail_json(msg='Name can not start with http:// or https://')
    description = module.params['description']
    if str(description).startswith('http://') or str(description).startswith('https://'):
        module.fail_json(msg='description can not start with http:// or https://')
    multi = module.params['multi_ok']
    recent = module.params['recent']

    if multi and recent:
        module.fail_json(msg='multi_ok and recent can not be True at the same time.')

    changed = False

    group = group_exists(ecs, module, module.params['vpc_id'], group_name, multi, recent)

    if state == 'absent':
        if not group:
            module.exit_json(changed=changed, group={})
        try:
            module.exit_json(changed=group.delete(), group={})
        except ECSResponseError as e:
            module.fail_json(msg="Deleting security group {0} is failed. Error: {1}".format(group.id, e))

    if not group:
        try:
            params = module.params
            params['security_group_name'] = group_name
            params['client_token'] = "Ansible-Alicloud-%s-%s" % (hash(str(module.params)), str(time.time()))
            group = ecs.create_security_group(**params)
            changed = True
        except ECSResponseError as e:
            module.fail_json(changed=changed, msg='Creating a security group is failed. Error: {0}'.format(e))

    if not description:
        description = group.description
    if group.modify(name=group_name, description=description):
        changed = True

    # validating rules if provided
    ingress_rules = module.params['rules']
    if ingress_rules:
        direction = 'ingress'
        for rule in ingress_rules:
            validate_group_rule_keys(module, rule, direction)
        if module.params['purge_rules']:
            for existing in group.permissions:
                if existing['direction'] != direction:
                    continue
                if purge_rules(module, group, existing, ingress_rules, direction):
                    changed = True
        for rule in ingress_rules:
            if group.authorize(rule, direction):
                changed = True

    egress_rules = module.params['rules_egress']
    if egress_rules:
        direction = 'egress'
        for rule in egress_rules:
            validate_group_rule_keys(module, rule, direction)
        if module.params['purge_rules_egress']:
            for existing in group.permissions:
                if existing['direction'] != direction:
                    continue
                if purge_rules(module, group, existing, egress_rules, direction):
                    changed = True
        for rule in egress_rules:
            if group.authorize(rule, direction):
                changed = True

    module.exit_json(changed=changed, group=group.get().read())


if __name__ == '__main__':
    main()
