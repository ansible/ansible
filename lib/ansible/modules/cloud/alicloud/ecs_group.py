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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'curated'}

DOCUMENTATION = '''
---
module: ecs_group
version_added: "2.4"
short_description: Create, Query or Delete Security Group.
description:
  - Create, Query or Delete Security Group, and it contains security group rules management.
options:
  status:
    description: Create, delete or get information of a security group
    required: false
    default: 'present'
    aliases: ['state']
    choices: ['present', 'absent', 'getinfo']
  group_name:
    description: Name of the security group.
    required: false
    default: null
    aliases: ['name']
  description:
    description: Description of the security group.
    required: false
    default: null
  vpc_id:
    description:
      - ID of the VPC to which the security group belongs.
    required: false
    default: null
  group_tags:
    description:
      - A list of hash/dictionaries of group tags, ['{"tag_key":"value", "tag_value":"value"}'], tag_key must be not null when tag_value isn't null.
    required: false
    default: null
    aliases: [tags]
  rules:
    description:
      - List of hash/dictionaries firewall inbound rules to enforce in this group.
    required: false
    default: null
    suboptions:
        ip_protocol:
          description: IP protocol
          required: true
          choices: ["tcp", "udp", "icmp", "gre", "all"]
          aliases: ['proto']
        port_range:
          description: The range of port numbers. Tcp and udp's valid range is 1 to 65535, and other protocol's valid value is -1/-1.
          required: true
        source_group_id:
          description: The source security group id.
          required: false
          aliases: ['group_id']
        source_group_owner_id:
          description: The source security group owner id.
          required: false
          aliases: ['group_owner_id']
        source_cidr_ip:
          description: The source IP address range
          required: false
          aliases: ['cidr_ip']
        policy:
          description: Authorization policy
          required: false
          default: "accept"
          choices: ["accept", "drop"]
        priority:
          description: Authorization policy priority
          required: false
          default: 1
          choices: ["1~100"]
        nic_type:
          description: Network type
          required: false
          default: internet
          choices: ["internet", "intranet"]
  rules_egress:
    description:
      - List of hash/dictionaries firewall outbound rules to enforce in this group.
        Keys allowed are:ip_protocol, port_range, dest_group_id, dest_group_owner_id, dest_cidr_ip, policy, priority,nic_type.
        And these keys's attribution same as rules keys.
    required: false
    default: null
    suboptions:
        ip_protocol:
          description: IP protocol
          required: true
          choices: ["tcp", "udp", "icmp", "gre", "all"]
          aliases: ['proto']
        port_range:
          description: The range of port numbers. Tcp and udp's valid range is 1 to 65535, and other protocol's valid value is "-1/-1".
          required: true
        dest_group_id:
          description: The destination security group id.
          required: false
          aliases: ['group_id']
        dest_group_owner_id:
          description: The destination security group owner id.
          required: false
          aliases: ['group_owner_id']
        dest_cidr_ip:
          description: The destination IP address range
          required: false
          aliases: ['cidr_ip']
        policy:
          description: Authorization policy
          required: false
          default: "accept"
          choices: ["accept", "drop"]
        priority:
          description: Authorization policy priority
          required: false
          default: 1
          choices: ["1~100"]
        nic_type:
          description: Network type
          required: false
          default: internet
          choices: ["internet", "intranet"]
  group_id:
    description:
      - Ssecurity group ID is used to perform rules authorization.
    required: true
    default: null
author:
  - "He Guimin (@xiaozhu36)"
'''

EXAMPLES = '''
#
# Provisioning new Security Group
#

# Basic provisioning example to create security group
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
        group_name: 'AliyunSG'


# Basic provisioning example authorize security group
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
        group_id: xxxxxxxxxx
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


# Provisioning example create and authorize security group
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
        group_name: 'AliyunSG'
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
    group_ids:
     - xxxxxxxxxx
    status: absent
  tasks:
    - name: delete security grp
      ecs_group:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        group_ids: '{{ group_ids }}'
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

RETURN = '''
group_id:
    description: security group ID
    returned: when success
    type: string
    sample: "sd-safhi3gsv"
group:
    description: Details about the security group that was created
    returned: except on delete
    type: dict
    sample: {
        "description": "travis-ansible-instance",
        "id": "sg-2ze1hhyn7tac4p85gh13",
        "name": "travis-ansible-instance",
        "region_id": "cn-beijing",
        "rules": {
            "permission": [
                {
                    "create_time": "2017-06-19T02:43:29Z",
                    "description": "",
                    "dest_cidr_ip": "",
                    "dest_group_id": "",
                    "dest_group_name": "",
                    "dest_group_owner_account": "",
                    "direction": "ingress",
                    "ip_protocol": "TCP",
                    "nic_type": "internet",
                    "policy": "Accept",
                    "port_range": "80/86",
                    "priority": 1,
                    "source_cidr_ip": "192.168.0.54/32",
                    "source_group_id": "",
                    "source_group_name": "",
                    "source_group_owner_account": ""
                },
                {
                    "create_time": "2017-06-19T02:43:29Z",
                    "description": "",
                    "dest_cidr_ip": "",
                    "dest_group_id": "",
                    "dest_group_name": "",
                    "dest_group_owner_account": "",
                    "direction": "ingress",
                    "ip_protocol": "TCP",
                    "nic_type": "internet",
                    "policy": "Accept",
                    "port_range": "8080/8088",
                    "priority": 1,
                    "source_cidr_ip": "47.89.23.33/32",
                    "source_group_id": "",
                    "source_group_name": "",
                    "source_group_owner_account": ""
                },
                {
                    "create_time": "2017-06-19T02:43:30Z",
                    "description": "",
                    "dest_cidr_ip": "47.89.23.33/32",
                    "dest_group_id": "",
                    "dest_group_name": "",
                    "dest_group_owner_account": "",
                    "direction": "egress",
                    "ip_protocol": "TCP",
                    "nic_type": "internet",
                    "policy": "Accept",
                    "port_range": "8080/8085",
                    "priority": 1,
                    "source_cidr_ip": "",
                    "source_group_id": "",
                    "source_group_name": "",
                    "source_group_owner_account": ""
                },
                {
                    "create_time": "2017-06-19T02:43:29Z",
                    "description": "",
                    "dest_cidr_ip": "192.168.0.54/32",
                    "dest_group_id": "",
                    "dest_group_name": "",
                    "dest_group_owner_account": "",
                    "direction": "egress",
                    "ip_protocol": "TCP",
                    "nic_type": "internet",
                    "policy": "Accept",
                    "port_range": "80/80",
                    "priority": 1,
                    "source_cidr_ip": "",
                    "source_group_id": "",
                    "source_group_name": "",
                    "source_group_owner_account": ""
                }
            ]
        },
        "tags": {},
        "vpc_id": ""
    }
group_rules:
    description: Details about the security group rules that were created
    returned: except on delete
    type: dict
    sample: {
        "permission": [
            {
                "create_time": "2017-06-19T02:43:29Z",
                "description": "",
                "dest_cidr_ip": "",
                "dest_group_id": "",
                "dest_group_name": "",
                "dest_group_owner_account": "",
                "direction": "ingress",
                "ip_protocol": "TCP",
                "nic_type": "internet",
                "policy": "Accept",
                "port_range": "80/86",
                "priority": 1,
                "source_cidr_ip": "192.168.0.54/32",
                "source_group_id": "",
                "source_group_name": "",
                "source_group_owner_account": ""
            },
            {
                "create_time": "2017-06-19T02:43:30Z",
                "description": "",
                "dest_cidr_ip": "47.89.23.33/32",
                "dest_group_id": "",
                "dest_group_name": "",
                "dest_group_owner_account": "",
                "direction": "egress",
                "ip_protocol": "UDP",
                "nic_type": "internet",
                "policy": "Accept",
                "port_range": "10989/10997",
                "priority": 2,
                "source_cidr_ip": "",
                "source_group_id": "",
                "source_group_name": "",
                "source_group_owner_account": ""
            }
        ]
    }
vpc_id:
    description: ID of the VPC to which the security group belongs
    returned: when success
    type: string
    sample: "vpc-snif3g3iv"
'''
# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.alicloud_ecs import get_acs_connection_info, ecs_argument_spec, ecs_connect
# from ansible.module_utils.ecs import get_acs_connection_info, ecs_argument_spec, ecs_connect


try:
    from footmark.exception import ECSResponseError

    HAS_FOOTMARK = True
except ImportError:
    HAS_FOOTMARK = False

# try:
#     from ecsutils.ecs import *
#
#     HAS_ECS = True
# except ImportError:
#     HAS_ECS = False


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
        changed, group_id, result = ecs.create_security_group(group_name=group_name, group_description=group_description,
                                                              vpc_id=vpc_id, group_tags=group_tags)

        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg='Creating SecurityGroup is failed, error: %s ; group_id: %s.'
                                                  % (str(result), group_id))

    except ECSResponseError as e:
        module.fail_json(changed=changed, msg='Unable to create SecurityGroup, error: {0}'.format(e))

    return changed, group_id, result


def authorize_security_group(module, ecs, group_id, inbound_rules, outbound_rules, add_to_fail_result=""):
    """
    authorize security group in ecs
    :param module: Ansible module object
    :param ecs: authenticated ecs connection object
    :param group_id: Security Group Id for authorization
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
            group_id, inbound_rules, outbound_rules)

        if 'error' in (''.join(str(result))).lower():
            result.insert(0, add_to_fail_result)
            module.fail_json(changed=changed, msg="Authorizing SecurityGroup is failed, error: %s ; group_id: %s ; "
                                                  "failed inbound rules: %s ; failed outbound rules: %s."
                                                  % (str(result), group_id, inbound_failed_rules, outbound_failed_rules))

    except ECSResponseError as e:
        module.fail_json(msg='Unable to authorize security group, error: {0}'.format(e))

    return changed, group_id, result


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

                # format rules to return for authorization
                formatted_rule = {}

                formatted_rule['ip_protocol'] = ip_protocol
                formatted_rule['port_range'] = port_range

                if cidr_ip:
                    formatted_rule['cidr_ip'] = cidr_ip

                group_id = get_alias_value(rule, group_id_aliases.get(rule_type))
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


def get_group_info(group):
    """
    Retrieves instance information from a security group
    returns it as a dictionary
    """
    group_info = {'id': group.id, 'name': group.name, 'description': group.description, 'region_id': group.region_id,
                  'tags': group.tags, 'vpc_id': group.vpc_id, 'rules': group.permissions}

    return group_info


def get_groups(module, ecs, vpc_id=None, group_ids=None):
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
        if not isinstance(group_ids, list) or len(group_ids) < 1:
            module.fail_json(msg='SecurityGroup Id is required to retrieval and it should be a list, aborting')

        changed, result = ecs.get_security_status(vpc_id=vpc_id, group_ids=group_ids)

        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg=result)

        groups = []
        if result and len(result) > 0:
            groups.append(get_group_info(result[0]))
    except ECSResponseError as e:
        module.fail_json(msg='Unable to get info of SecurityGroup(s), error: %s ; group_ids: %s.'
                             % (str(e), str(group_ids)))

    return changed, groups


def get_group(module, ecs, group_id=None):
    """
    Querying Security Group List returns the basic information about all user-defined security groups.
    :param module: Ansible module object
    :param ecs: authenticated ecs connection object.
    :param group_id: The ID of security group.
    :return: A dict of the security group.
    """

    try:
        changed, group, result = ecs.get_security_group_attribute(group_id=group_id)

        if 'error' in (''.join(str(result))).lower():
            # module.log()
            module.fail_json(msg="Retrieving security group {0} attribute got an error: {1}".format(group_id, result))

        if group:
            return changed, get_group_info(group)
    except ECSResponseError as e:
        module.fail_json(msg='Unable to get info of SecurityGroup {0}, error: {1}.'.format(group_id, e))


def del_security_group(module, ecs, group_ids):
    """
    Delete Security Group , delete security group inside particular region.
    :param module: Ansible module object
    :param ecs: authenticated ecs connection object
    :param group_ids: The Security Group ID
    :return: result of after successfully deletion of security group
    """
    changed = False
    if not isinstance(group_ids, list) or len(group_ids) < 1:
        module.fail_json(msg='SecurityGroup Id is required to delete and it should be a list, aborting')

    try:
        changed, result = ecs.delete_security_group(group_ids=group_ids)
        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg='Deleting SecurityGroup(s) is failed, error: %s ; group_ids: %s'
                                                  % (str(result), str(group_ids)))

    except ECSResponseError as e:
        module.fail_json(changed=changed, msg='Unable to delete SecurityGroup(s), error: %s ; group_ids: %s'
                                              % (str(e), str(group_ids)))

    return changed, result


def main():
    # if HAS_ECS is False:
    #     module.fail_json("ecsutils required for this module")
    if HAS_FOOTMARK is False:
        module.fail_json("Footmark required for this module")

    argument_spec = ecs_argument_spec()
    argument_spec.update(dict(
        status=dict(default='present', aliases=['state'], choices=['present', 'absent', 'getinfo'], type='str'),
        group_name=dict(type='str', aliases=['name']),
        description=dict(type='str'),
        vpc_id=dict(type='str'),
        group_tags=dict(type='list', aliases=['tags']),
        rules=dict(type='list'),
        rules_egress=dict(type='list'),
        group_id=dict(type='str')
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    ecs = ecs_connect(module)

    state = module.params['status']

    if state == 'present':

        group_name = module.params['group_name']
        description = module.params['description']
        vpc_id = module.params['vpc_id']
        group_tags = module.params['group_tags']
        group_id = module.params['group_id']

        # # validating group_id and name
        # if group_ids and group_name:
        #     module.fail_json(msg='provide either security group id or name, not both')
        # elif group_ids:
        #     if len(group_ids) != 1:
        #         module.fail_json(msg='provide single security group id for rule authorization')
        # elif group_name is None:
        #     module.fail_json(msg='provide either security group id or name')

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
        if not group_id:
            changed, group_id, result = create_security_group(module, ecs, group_name=group_name,
                                                              group_description=description,
                                                              vpc_id=vpc_id, group_tags=group_tags)

        if group_id and (inbound_rules or outbound_rules):
            changed, sg_id, _ = authorize_security_group(module, ecs, group_id=group_id, inbound_rules=inbound_rules,
                                                         outbound_rules=outbound_rules, add_to_fail_result=result)

            # if rule authorization is required after group creation

        # if group_ids:
        #     if total_rules_count == 0:
        #         module.fail_json(msg='provide rules for authorization')
        #
        #     changed, group_id, result = authorize_security_group(module, ecs, group_id=group_ids[0],
        #                                                                   inbound_rules=inbound_rules,
        #                                                                   outbound_rules=outbound_rules)
        # # if security group creation is required
        # else:
        #
        #     changed, group_id, result = create_security_group(module, ecs, group_name=group_name,
        #                                                                group_description=group_description,
        #                                                                vpc_id=vpc_id,
        #                                                                group_tags=group_tags)
        #
        #     # if rule authorization is required after group creation
        #     if group_id and (inbound_rules or outbound_rules):
        #         c, s, result_details = authorize_security_group(module, ecs, group_id, inbound_rules,
        #                                                         outbound_rules,
        #                                                         add_to_fail_result=result[0])
        #         result.extend(result_details)
        changed, group = get_group(module, ecs, group_id)

        module.exit_json(changed=changed, group_id=group['id'], group=group, group_rules=group['rules'], vpc_id=group['vpc_id'])

    elif state == 'getinfo':
        group_id = module.params['group_id']

        (changed, group) = get_group(module, ecs, group_id)
        module.exit_json(changed=changed, group_id=group['id'], group=group, group_rules=group['rules'], vpc_id=group['vpc_id'])

    elif state == 'absent':
        group_ids = [module.params['group_id']]

        (changed, result) = del_security_group(module, ecs, group_ids)
        module.exit_json(changed=changed, group_id=group_ids[0])


if __name__ == '__main__':
    main()
