#!/usr/bin/python
#
# Copyright 2017 Alibaba Group Holding Limited.
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

from __builtin__ import isinstance

ANSIBLE_METADATA = {'status': ['stableinterface'],
                    'supported_by': 'core',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: ecs_group
version_added: "1.0"
short_description: Create, Query or Delete Security Group
description:
    - Create, Query or Delete Security Group

common options:
  alicloud_access_key:
    description:
      - Aliyun Cloud access key. If not set then the value of the `ALICLOUD_ACCESS_KEY`, `ACS_ACCESS_KEY_ID`, 
        `ACS_ACCESS_KEY` or `ECS_ACCESS_KEY` environment variable is used.
    required: false
    default: null
    aliases: ['acs_access_key', 'ecs_access_key','access_key']
  alicloud_secret_key:
    description:
      - Aliyun Cloud secret key. If not set then the value of the `ALICLOUD_SECRET_KEY`, `ACS_SECRET_ACCESS_KEY`,
        `ACS_SECRET_KEY`, or `ECS_SECRET_KEY` environment variable is used.
    required: false
    default: null
    aliases: ['acs_secret_access_key', 'ecs_secret_key','secret_key']
  alicloud_region:
    description:
      - The Aliyun Cloud region to use. If not specified then the value of the `ALICLOUD_REGION`, `ACS_REGION`, 
        `ACS_DEFAULT_REGION` or `ECS_REGION` environment variable, if any, is used.
    required: false
    default: null
    aliases: ['acs_region', 'ecs_region', 'region']
  status:
    description: Create or delete or get information of a security group
    required: false
    default: 'present'
    aliases: ['state']
    choices: ['present', 'absent', 'getinfo']

function create security group:  
  security_group_name:
    description:
      - The security group name.
    required: true
    default: null
    aliases: ['name']
    choices: []
  description:
    description:
      - The description of the security group.
    required: false
    default: null
    aliases: []
    choices: []
  vpc_id:
    description:
      - The ID of the VPC to which the security group belongs. If this parameter is not passed, the security group will be created using classic network type.
    required: false
    default: null
    aliases: []
    choices: []
  group_tags:
    description:
      - A list of hash/dictionaries of group tags, ['{"tag_key":"value", "tag_value":"value"}'], tag_key must be not null when tag_value isn't null
    required: false
    default: null
    aliases: []
    choices: []
  rules:
    description:
      - List of firewall inbound rules to enforce in this group.
      - keys allowed are
            - ip_protocol (required=true; choices=["tcp", "udp", "icmp", "gre", "all"]; aliases=['proto']; description=IP protocol)
            - port_range(required=true; description=The range of port numbers)
            - source_group_id(required=false; aliases=['group_id']; description=The source security group id)
            - source_group_owner_id(required=false; aliases=['group_owner_id']; description=The source security group owner id)
            - source_cidr_ip(required=false; aliases=['cidr_ip']; description=The source IP address range)
            - policy(required=false; choices=["accept", "drop"]; description=Authorizatio policy)
            - priority(required=false; choices=["1-100"]; default=1; description=Authorization policy priority)
            - nic_type(required=false; choices=["internet", "intranet"]; default=internet; description=Network type)
    required: false
    default: null
    aliases: []
    choices: []
  rules_egress:
    description:
      - List of firewall outbound rules to enforce in this group.
      - keys allowed are
            - ip_protocol (required=true; choices=["tcp", "udp", "icmp", "gre", "all"]; aliases=['proto']; description=IP protocol)
            - port_range(required=true; description=The range of port numbers)
            - dest_group_id(required=false; aliases=['group_id']; description=The destination security group id)
            - dest_group_owner_id(required=false; aliases=['group_owner_id']; description=The destination security group owner id)
            - dest_cidr_ip(required=false; aliases=['cidr_ip']; description=The destination IP address range)
            - policy(required=false; choices=["accept", "drop"]; description=Authorizatio policy)
            - priority(required=false; choices=["1-100"]; default=1; description=Authorization policy priority)
            - nic_type(required=false; choices=["internet", "intranet"]; default=internet; description=Network type)
    required: false
    default: null
    aliases: []
    choices: []

function authorize a security group:
  group_id:
    description:
      - Provide the security group id to perform rules authorization. This parameter is not required for creating new security group.
    required: true
    default: null
    aliases: ['security_group_id', 'group_ids', 'security_group_ids']
    choices: []
  rules:
    description:
      - List of firewall inbound rules to enforce in this group.
      - keys allowed are
            - ip_protocol (required=true; choices=["tcp", "udp", "icmp", "gre", "all"]; aliases=['proto']; description=IP protocol)
            - port_range(required=true; description=The range of port numbers)
            - source_group_id(required=false; aliases=['group_id']; description=The source security group id)
            - source_group_owner_id(required=false; aliases=['group_owner_id']; description=The source security group owner id)
            - source_cidr_ip(required=false; aliases=['cidr_ip']; description=The source IP address range)
            - policy(required=false; choices=["accept", "drop"]; description=Authorizatio policy)
            - priority(required=false; choices=["1-100"]; default=1; description=Authorization policy priority)
            - nic_type(required=false; choices=["internet", "intranet"]; default=internet; description=Network type)
    required: false
    default: null
    aliases: []
    choices: []
  rules_egress:
    description:
      - List of firewall outbound rules to enforce in this group.
      - keys allowed are
            - ip_protocol (required=true; choices=["tcp", "udp", "icmp", "gre", "all"]; aliases=['proto']; description=IP protocol)
            - port_range(required=true; description=The range of port numbers)
            - dest_group_id(required=false; aliases=['group_id']; description=The destination security group id)
            - dest_group_owner_id(required=false; aliases=['group_owner_id']; description=The destination security group owner id)
            - dest_cidr_ip(required=false; aliases=['cidr_ip']; description=The destination IP address range)
            - policy(required=false; choices=["accept", "drop"]; description=Authorizatio policy)
            - priority(required=false; choices=["1-100"]; default=1; description=Authorization policy priority)
            - nic_type(required=false; choices=["internet", "intranet"]; default=internet; description=Network type)
    required: false
    default: null
    aliases: []
    choices: []

function delete a security group:
  group_id:
    description:
      - A list of security groups ids.
    required: true
    default: null
    aliases: ['security_group_id', 'group_ids', 'security_group_ids']
    choices: []

function get security groups:
  group_id:
    description:
      - List of the security group ids
    required: true
    default: null
    aliases: ['security_group_id', 'group_ids', 'security_group_ids']
    choices: []
  vpc_id:
    description:
      - The ID of the VPC to which the security group belongs.
    required: false
    default: null
    aliases: []
    choices: []
'''

EXAMPLES = '''
#
# Provisioning new Security Group
#

Basic provisioning example to create security group
- name: create security group
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-shenzhen
  tasks:
    - name: create security grp
      ecs_group:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        security_group_name: 'AliyunSG'


Basic provisioning example authorize security group
- name: authorize security grp
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-shenzhen
  tasks:
    - name: authorize security group
      ecs_group:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        security_group_id: xxxxxxxxxx
        alicloud_region: '{{ alicloud_region }}'
        rules:
          - ip_protocol: tcp
            port_range: 1/122
            source_cidr_ip: '10.159.6.18/12'
        rules_egress:
          - proto: all
            port_range: -1/-1
            dest_group_id: xxxxxxxxxx
            nic_type: intranet


Provisioning example create and authorize security group
- name: create and authorize security group
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-shenzhen
  tasks:
    - name: create and authorize security grp
      ecs_group:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        security_group_name: 'AliyunSG'
        description: 'an example ECS group'
        alicloud_region: '{{ alicloud_region }}'
        rules:
          - ip_protocol: tcp
            port_range: 1/122
            source_cidr_ip: '10.159.6.18/12'
            priority: 10
            policy: drop
            nic_type: intranet
        rules_egress:
          - proto: all
            port_range: -1/-1
            dest_group_id: xxxxxxxxxx
            group_owner_id: xxxxxxxxxx
            priority: 10
            policy: accept
            nic_type: intranet


# Provisioning example to delete security group
- name: delete security grp
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: us-west-1
    security_group_ids:
     - xxxxxxxxxx
    status: absent
  tasks:
    - name: delete security grp
      ecs_group:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        security_group_ids: '{{ security_group_ids }}'
        status: '{{ status }}'


# Provisioning example to querying security group list
- name: querying security group list
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-beijing
    status: getinfo
  tasks:
    - name: Querying Security group list
      ecs_group:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        status: '{{ status }}'
'''

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.alicloud_ecs import *

import sys

try:
    from footmark.exception import ECSResponseError

    HAS_FOOTMARK = True
except ImportError:
    HAS_FOOTMARK = False


def create_security_group(module, ecs, group_name, group_description, vpc_id, group_tags):
    """
    create security group in ecs
    :param module: Ansible module object
    :param ecs: authenticated ecs connection object
    :param group_name: Name of the security group create
    :param group_description: Description of the security group
    :param vpc_id: ID of a vpc to which the security group belongs.
    :param group_tags:  A list of hash/dictionaries of group
            tags, '[{tag_key:"value", tag_value:"value"}]', tag_key
            must be not null when tag_value isn't null
    :return: Returns changed state, newly created security group id and custom message.
    """

    try:
        changed = False
        changed, security_group_id, result = ecs.create_security_group(group_name=group_name,
                                                                       group_description=group_description,
                                                                       vpc_id=vpc_id,
                                                                       group_tags=group_tags)

        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, security_group_id=security_group_id, msg=result)

    except ECSResponseError as e:
        module.fail_json(msg='Unable to create and authorize security group, error: {0}'.format(e))

    return changed, security_group_id, result


def authorize_security_group(module, ecs, security_group_id=None, inbound_rules=None, outbound_rules=None,
                             add_to_fail_result=""):
    """
    authorize security group in ecs
    :param module: Ansible module object
    :param ecs: authenticated ecs connection object
    :param security_group_id: Security Group Id for authorization
    :param inbound_rules: Inbound rules for authorization
    :param outbound_rules: Outbound rules for authorization
    :param add_to_fail_result: message to add to failed message at the beginning, if two tasks are performed
    :return: Returns changed state, security group id and custom message.
    """
    inbound_failed_rules = None
    outbound_failed_rules = None
    try:
        changed = False

        changed, inbound_failed_rules, outbound_failed_rules, result = ecs.authorize_security_group(
            security_group_id=security_group_id, inbound_rules=inbound_rules,
            outbound_rules=outbound_rules)

        if 'error' in (''.join(str(result))).lower():
            result.insert(0, add_to_fail_result)
            module.fail_json(changed=changed, group_id=security_group_id, msg=result,
                             inbound_failed_rules=inbound_failed_rules, outbound_failed_rules=outbound_failed_rules)

    except ECSResponseError as e:
        module.fail_json(msg='Unable to authorize security group, error: {0}'.format(e))

    return changed, security_group_id, result


def validate_format_sg_rules(module, inbound_rules=None, outbound_rules=None):
    """
    Validate and format security group for inbound and outbound rules
    :param module: Ansible module object
    :param inbound_rules: Inbound rules for authorization to validate and format
    :param outbound_rules: Outbound rules for authorization to validate and format
    :return:
    """
    # aliases for rule
    ip_protocol_aliases = ('ip_protocol', 'proto')
    inbound_cidr_ip_aliases = ('source_cidr_ip', 'cidr_ip')
    outbound_cidr_ip_aliases = ('dest_cidr_ip', 'cidr_ip')
    inbound_group_id_aliases = ('source_group_id', 'group_id')
    outbound_group_id_aliases = ('dest_group_id', 'group_id')
    inbound_group_owner_aliases = ('source_group_owner_id', 'group_owner_id')
    outbound_group_owner_aliases = ('dest_group_owner_id', 'group_owner_id')

    cidr_ip_aliases = {
        "inbound": inbound_cidr_ip_aliases,
        "outbound": outbound_cidr_ip_aliases,
    }

    group_id_aliases = {
        "inbound": inbound_group_id_aliases,
        "outbound": outbound_group_id_aliases,
    }

    group_owner_aliases = {
        "inbound": inbound_group_owner_aliases,
        "outbound": outbound_group_owner_aliases,
    }

    COMMON_VALID_PARAMS = ('proto', 'ip_protocol', 'cidr_ip', 'group_id', 'group_owner_id',
                           'nic_type', 'policy', 'priority', 'port_range')
    INBOUND_VALID_PARAMS = ('source_cidr_ip', 'source_group_id', 'source_group_owner_id')
    OUTBOUND_VALID_PARAMS = ('dest_cidr_ip', 'dest_group_id', 'dest_group_owner_id')

    # tcp_proto_start_port = 1
    # tcp_proto_end_port = 65535

    rule_types = []

    rule_choice = {
        "inbound": inbound_rules,
        "outbound": outbound_rules,
    }
    valid_params = {
        "inbound": INBOUND_VALID_PARAMS,
        "outbound": OUTBOUND_VALID_PARAMS,
    }

    if inbound_rules:
        rule_types.append('inbound')

    if outbound_rules:
        rule_types.append('outbound')

    for rule_type in rule_types:

        rules = rule_choice.get(rule_type)
        total_rules = 0
        if rules:
            total_rules = len(rules)

        if total_rules != 0:

            for rule in rules:

                if not isinstance(rule, dict):
                    module.fail_json(msg='Invalid rule parameter type [%s].' % type(rule))

                for k in rule:
                    if k not in COMMON_VALID_PARAMS and k not in valid_params.get(rule_type):
                        module.fail_json(msg='Invalid rule parameter \'{}\''.format(k))

                ip_protocol = get_alias_value(rule, ip_protocol_aliases)
                if ip_protocol is None:
                    module.fail_json(msg="Ip Protocol required for rule authorization")

                port_range = get_alias_value(rule, ['port_range'])
                if port_range is None:
                    module.fail_json(msg="Port range is required for rule authorization")

                # verifying whether group_id is provided and cidr_ip is not, so nic_type should be set to intranet
                cidr_ip = get_alias_value(rule, cidr_ip_aliases.get(rule_type))
                if cidr_ip is None:
                    if get_alias_value(rule, group_id_aliases.get(rule_type)) is not None:
                        if 'nic_type' in rule:
                            if not rule['nic_type'] == "intranet":
                                module.fail_json(msg="In mutual security group authorization (namely, "
                                                     "GroupId is specified, while CidrIp is not specified), "
                                                     "you must specify the nic_type as intranet")
                        else:
                            module.fail_json(msg="In mutual security group authorization (namely, "
                                                 "GroupId is specified, while CidrIp is not specified), "
                                                 "you must specify the nic_type as intranet")

                #format rules to return for authorization
                formatted_rule = {}

                formatted_rule['ip_protocol'] = ip_protocol
                formatted_rule['port_range'] = port_range

                if cidr_ip:
                    formatted_rule['cidr_ip'] = cidr_ip

                group_id  = get_alias_value(rule, group_id_aliases.get(rule_type))
                if group_id:
                    formatted_rule['group_id'] = group_id

                group_owner_id = get_alias_value(rule, group_owner_aliases.get(rule_type))
                if group_owner_id:
                    formatted_rule['group_owner_id'] = group_owner_id

                if 'nic_type' in rule:
                    if rule['nic_type']:
                        formatted_rule['nic_type'] = rule['nic_type']

                if 'policy' in rule:
                    if rule['policy']:
                        formatted_rule['policy'] = rule['policy']

                if 'priority' in rule:
                    if rule['priority']:
                        formatted_rule['priority'] = rule['priority']

                rule.clear()
                rule.update(formatted_rule)


def get_alias_value(dictionary, aliases):
    """
    Get alias or key value from a dictionary
    :param dictionary: a dictionary to check in for keys/aliases
    :param aliases: list of aliases to find in dictionary to retrieve value
    :return: returns value of found alias else None
    """

    if (dictionary and aliases) is not None:
        for alias in aliases:
            if alias in dictionary:
                return dictionary[alias]
        return None
    else:
        return None


def get_security_status(module, ecs, vpc_id=None, group_ids=None):
    """
    Querying Security Group List returns the basic information about all user-defined security groups.
    :param module: Ansible module object
    :param ecs: authenticated ecs connection object
    :param vpc_id: ID of a vpc to which an security group belongs. If it is
            null, a vpc is selected by the system
    :param group_ids: Provides a list of security groups ids.
    :return: A list of the total number of security groups,
                 the ID of the VPC to which the security group belongs
    """

    try:
        changed = False
        changed, result = ecs.get_security_status(vpc_id=vpc_id, group_ids=group_ids)

        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg=result)
    except ECSResponseError as e:
        module.fail_json(msg='Unable to get status of SecurityGroup(s), error: {0}'.format(e))
    return changed, result


def del_security_group(module, ecs, security_group_ids):
    """
    Delete Security Group , delete security group inside particular region.
    :param module: Ansible module object
    :param ecs: authenticated ecs connection object
    :param security_group_ids: The Security Group ID
    :return: result of after successfully deletion of security group
    """
    changed = False
    
    if not security_group_ids:
            module.fail_json(msg='Security Group Id  is required to Delete from security group')
    else:
        for id in security_group_ids:
            if not id:
                module.fail_json(msg='Security Group Id  is required to Delete from security group')

    try:
        changed, result = ecs.delete_security_group(group_ids=security_group_ids)
        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg=result)

    except ECSResponseError as e:
        module.fail_json(msg='Unable to create instance due to following error :{0}'.format(e))
    return changed, result


def main():
    if HAS_FOOTMARK is False:
        print("Footmark required for this module")
        sys.exit(1)

    argument_spec = ecs_argument_spec()
    argument_spec.update(dict(
        status=dict(default='present', aliases=['state'], choices=['present', 'absent', 'getinfo'], type='str'),
        security_group_name=dict(type='str', aliases=['name']),
        description=dict(type='str'),
        vpc_id=dict(type='str'),
        group_tags=dict(type='list'),
        rules=dict(type='list'),
        rules_egress=dict(type='list'),
        group_ids=dict(type='list', aliases=['security_group_ids', 'group_id', 'security_group_id'])
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    ecs = ecs_connect(module)

    region, acs_connect_kwargs = get_acs_connection_info(module)

    tagged_instances = []

    state = module.params['status']

    if state == 'present':

        group_name = module.params['security_group_name']
        group_description = module.params['description']
        vpc_id = module.params['vpc_id']
        group_tags = module.params['group_tags']
        group_ids = module.params['group_ids']

        # validating group_id and name
        if group_ids and group_name:
            module.fail_json(msg='provide either security group id or name, not both')
        elif group_ids:
            if len(group_ids) != 1:
                module.fail_json(msg='provide single security group id for rule authorization')
        elif group_name is None:
            module.fail_json(msg='provide either security group id or name')

        # validating rules if provided
        total_rules_count = 0
        inbound_rules = module.params['rules']
        if inbound_rules:
            total_rules_count = len(inbound_rules)

        outbound_rules = module.params['rules_egress']
        if outbound_rules:
            total_rules_count += len(outbound_rules)

        validate_format_sg_rules(module, inbound_rules, outbound_rules)

        if total_rules_count > 100:
            module.fail_json(msg='more than 100 rules for authorization are not allowed')

        # Verifying if rules are provided for group_id to authorize security group
        if group_ids:
            if total_rules_count == 0:
                module.fail_json(msg='provide rules for authorization')

            changed, security_group_id, result = authorize_security_group(module, ecs, security_group_id=group_ids[0],
                                                                          inbound_rules=inbound_rules,
                                                                          outbound_rules=outbound_rules)
        # if security group creation is required
        else:

            changed, security_group_id, result = create_security_group(module, ecs, group_name=group_name,
                                                                       group_description=group_description,
                                                                       vpc_id=vpc_id,
                                                                       group_tags=group_tags)

            # if rule authorization is required after group creation
            if security_group_id and (inbound_rules or outbound_rules):
                c, s, result_details = authorize_security_group(module, ecs, security_group_id, inbound_rules,
                                                                outbound_rules,
                                                                add_to_fail_result=result[0])
                result.extend(result_details)

        module.exit_json(changed=changed, group_id=security_group_id, msg=result)

    elif state == 'getinfo':
        vpc_id = module.params['vpc_id']
        group_ids = module.params['group_ids']

        (changed, result) = get_security_status(module, ecs, vpc_id, group_ids)
        module.exit_json(changed=changed, result=result)

    elif state == 'absent':

        security_group_ids = module.params['group_ids']        

        (changed, result) = del_security_group(module, ecs, security_group_ids)
        module.exit_json(changed=changed, result=result)


# import ECSConnection
main()
