#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_vpc_nacl_info
short_description: Gather information about Network ACLs in an AWS VPC
description:
    - Gather information about Network ACLs in an AWS VPC
    - This module was called C(ec2_vpc_nacl_facts) before Ansible 2.9. The usage did not change.
version_added: "2.2"
author: "Brad Davidson (@brandond)"
requirements: [ boto3 ]
options:
  nacl_ids:
    description:
      - A list of Network ACL IDs to retrieve information about.
    required: false
    default: []
    aliases: [nacl_id]
    type: list
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See
        U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeNetworkAcls.html) for possible filters. Filter
        names and values are case sensitive.
    required: false
    default: {}
    type: dict
notes:
  - By default, the module will return all Network ACLs.

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all Network ACLs:
- name: Get All NACLs
  register: all_nacls
  ec2_vpc_nacl_info:
    region: us-west-2

# Retrieve default Network ACLs:
- name: Get Default NACLs
  register: default_nacls
  ec2_vpc_nacl_info:
    region: us-west-2
    filters:
      'default': 'true'
'''

RETURN = '''
nacls:
    description: Returns an array of complex objects as described below.
    returned: success
    type: complex
    contains:
        nacl_id:
            description: The ID of the Network Access Control List.
            returned: always
            type: str
        vpc_id:
            description: The ID of the VPC that the NACL is attached to.
            returned: always
            type: str
        is_default:
            description: True if the NACL is the default for its VPC.
            returned: always
            type: bool
        tags:
            description: A dict of tags associated with the NACL.
            returned: always
            type: dict
        subnets:
            description: A list of subnet IDs that are associated with the NACL.
            returned: always
            type: list
            elements: str
        ingress:
            description:
              - A list of NACL ingress rules with the following format.
              - "C([rule no, protocol, allow/deny, v4 or v6 cidr, icmp_type, icmp_code, port from, port to])"
            returned: always
            type: list
            elements: list
            sample: [[100, 'tcp', 'allow', '0.0.0.0/0', null, null, 22, 22]]
        egress:
            description:
              - A list of NACL egress rules with the following format.
              - "C([rule no, protocol, allow/deny, v4 or v6 cidr, icmp_type, icmp_code, port from, port to])"
            returned: always
            type: list
            elements: list
            sample: [[100, 'all', 'allow', '0.0.0.0/0', null, null, null, null]]
'''

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils._text import to_native
from ansible.module_utils.ec2 import (AWSRetry, ansible_dict_to_boto3_filter_list,
                                      camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict)


# VPC-supported IANA protocol numbers
# http://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml
PROTOCOL_NAMES = {'-1': 'all', '1': 'icmp', '6': 'tcp', '17': 'udp'}


def list_ec2_vpc_nacls(connection, module):

    nacl_ids = module.params.get("nacl_ids")
    filters = ansible_dict_to_boto3_filter_list(module.params.get("filters"))

    if nacl_ids is None:
        nacl_ids = []

    try:
        nacls = connection.describe_network_acls(aws_retry=True, NetworkAclIds=nacl_ids, Filters=filters)
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidNetworkAclID.NotFound':
            module.fail_json(msg='Unable to describe ACL.  NetworkAcl does not exist')
        module.fail_json_aws(e, msg="Unable to describe network ACLs {0}".format(nacl_ids))
    except BotoCoreError as e:
        module.fail_json_aws(e, msg="Unable to describe network ACLs {0}".format(nacl_ids))

    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_nacls = []
    for nacl in nacls['NetworkAcls']:
        snaked_nacls.append(camel_dict_to_snake_dict(nacl))

    # Turn the boto3 result in to ansible friendly tag dictionary
    for nacl in snaked_nacls:
        if 'tags' in nacl:
            nacl['tags'] = boto3_tag_list_to_ansible_dict(nacl['tags'], 'key', 'value')
        if 'entries' in nacl:
            nacl['egress'] = [nacl_entry_to_list(entry) for entry in nacl['entries']
                              if entry['rule_number'] < 32767 and entry['egress']]
            nacl['ingress'] = [nacl_entry_to_list(entry) for entry in nacl['entries']
                               if entry['rule_number'] < 32767 and not entry['egress']]
            del nacl['entries']
        if 'associations' in nacl:
            nacl['subnets'] = [a['subnet_id'] for a in nacl['associations']]
            del nacl['associations']
        if 'network_acl_id' in nacl:
            nacl['nacl_id'] = nacl['network_acl_id']
            del nacl['network_acl_id']

    module.exit_json(nacls=snaked_nacls)


def nacl_entry_to_list(entry):

    # entry list format
    # [ rule_num, protocol name or number, allow or deny, ipv4/6 cidr, icmp type, icmp code, port from, port to]
    elist = []

    elist.append(entry['rule_number'])

    if entry.get('protocol') in PROTOCOL_NAMES:
        elist.append(PROTOCOL_NAMES[entry['protocol']])
    else:
        elist.append(entry.get('protocol'))

    elist.append(entry['rule_action'])

    if entry.get('cidr_block'):
        elist.append(entry['cidr_block'])
    elif entry.get('ipv6_cidr_block'):
        elist.append(entry['ipv6_cidr_block'])
    else:
        elist.append(None)

    elist = elist + [None, None, None, None]

    if entry['protocol'] in ('1', '58'):
        elist[4] = entry.get('icmp_type_code', {}).get('type')
        elist[5] = entry.get('icmp_type_code', {}).get('code')

    if entry['protocol'] not in ('1', '6', '17', '58'):
        elist[6] = 0
        elist[7] = 65535
    elif 'port_range' in entry:
        elist[6] = entry['port_range']['from']
        elist[7] = entry['port_range']['to']

    return elist


def main():

    argument_spec = dict(
        nacl_ids=dict(default=[], type='list', aliases=['nacl_id']),
        filters=dict(default={}, type='dict'))

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    if module._name == 'ec2_vpc_nacl_facts':
        module.deprecate("The 'ec2_vpc_nacl_facts' module has been renamed to 'ec2_vpc_nacl_info'", version='2.13')

    connection = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())

    list_ec2_vpc_nacls(connection, module)


if __name__ == '__main__':
    main()
