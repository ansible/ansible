#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'curated'}


DOCUMENTATION = '''
---
module: ec2_vpc_subnet
short_description: Manage subnets in AWS virtual private clouds
description:
    - Manage subnets in AWS virtual private clouds
version_added: "2.0"
author: Robert Estelle (@erydo), Brad Davidson (@brandond)
requirements: [ boto3 ]
options:
  az:
    description:
      - "The availability zone for the subnet. Only required when state=present."
    required: false
    default: null
  cidr:
    description:
      - "The CIDR block for the subnet. E.g. 192.0.2.0/24. Only required when state=present."
    required: false
    default: null
  tags:
    description:
      - "A dict of tags to apply to the subnet. Any tags currently applied to the subnet and not present here will be removed."
    required: false
    default: null
    aliases: [ 'resource_tags' ]
  state:
    description:
      - "Create or remove the subnet"
    required: false
    default: present
    choices: [ 'present', 'absent' ]
  vpc_id:
    description:
      - "VPC ID of the VPC in which to create the subnet."
    required: false
    default: null
  map_public:
    description:
     - "Specify true to indicate that instances launched into the subnet should be assigned public IP address by default."
    required: false
    default: false
    version_added: "2.4"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create subnet for database servers
  ec2_vpc_subnet:
    state: present
    vpc_id: vpc-123456
    cidr: 10.0.1.16/28
    resource_tags:
      Name: Database Subnet
  register: database_subnet

- name: Remove subnet for database servers
  ec2_vpc_subnet:
    state: absent
    vpc_id: vpc-123456
    cidr: 10.0.1.16/28

'''

import time
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list, ansible_dict_to_boto3_tag_list, ec2_argument_spec
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, get_aws_connection_info
from ansible.module_utils.ec2 import boto3_conn, boto3_tag_list_to_ansible_dict, HAS_BOTO3

try:
    import botocore
except ImportError:
    pass  # caught by imported boto3


def get_subnet_info(subnet):
    if 'Subnets' in subnet:
        return [get_subnet_info(s) for s in subnet['Subnets']]
    elif 'Subnet' in subnet:
        subnet = camel_dict_to_snake_dict(subnet['Subnet'])
    else:
        subnet = camel_dict_to_snake_dict(subnet)

    if 'tags' in subnet:
        subnet['tags'] = boto3_tag_list_to_ansible_dict(subnet['tags'])
    else:
        subnet['tags'] = dict()

    if 'subnet_id' in subnet:
        subnet['id'] = subnet['subnet_id']
        del subnet['subnet_id']

    return subnet


def subnet_exists(conn, subnet_id):
    filters = ansible_dict_to_boto3_filter_list({'subnet-id': subnet_id})
    subnets = get_subnet_info(conn.describe_subnets(Filters=filters))
    if len(subnets) > 0 and 'state' in subnets[0] and subnets[0]['state'] == "available":
        return subnets[0]
    else:
        return False


def create_subnet(conn, module, vpc_id, cidr, az, check_mode):
    try:
        new_subnet = get_subnet_info(conn.create_subnet(VpcId=vpc_id, CidrBlock=cidr, AvailabilityZone=az))
        # Sometimes AWS takes its time to create a subnet and so using
        # new subnets's id to do things like create tags results in
        # exception.  boto doesn't seem to refresh 'state' of the newly
        # created subnet, i.e.: it's always 'pending'.
        subnet = False
        while subnet is False:
            subnet = subnet_exists(conn, new_subnet['id'])
            time.sleep(0.1)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "DryRunOperation":
            subnet = None
        else:
            module.fail_json(msg=e.message, exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))

    return subnet


def ensure_tags(conn, module, subnet, tags, add_only, check_mode):
    try:
        cur_tags = subnet['tags']

        to_delete = dict((k, cur_tags[k]) for k in cur_tags if k not in tags)
        if to_delete and not add_only and not check_mode:
            conn.delete_tags(Resources=[subnet['id']], Tags=ansible_dict_to_boto3_tag_list(to_delete))

        to_add = dict((k, tags[k]) for k in tags if k not in cur_tags or cur_tags[k] != tags[k])
        if to_add and not check_mode:
            conn.create_tags(Resources=[subnet['id']], Tags=ansible_dict_to_boto3_tag_list(to_add))

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != "DryRunOperation":
            module.fail_json(msg=e.message, exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))


def ensure_map_public(conn, module, subnet, map_public, check_mode):
    if check_mode:
        return

    try:
        conn.modify_subnet_attribute(SubnetId=subnet['id'], MapPublicIpOnLaunch={'Value': map_public})
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))


def get_matching_subnet(conn, vpc_id, cidr):
    filters = ansible_dict_to_boto3_filter_list({'vpc-id': vpc_id, 'cidr-block': cidr})
    subnets = get_subnet_info(conn.describe_subnets(Filters=filters))
    if len(subnets) > 0:
        return subnets[0]
    else:
        return None


def ensure_subnet_present(conn, module, vpc_id, cidr, az, tags, map_public, check_mode):
    subnet = get_matching_subnet(conn, vpc_id, cidr)
    changed = False
    if subnet is None:
        if not check_mode:
            subnet = create_subnet(conn, module, vpc_id, cidr, az, check_mode)
        changed = True
        # Subnet will be None when check_mode is true
        if subnet is None:
            return {
                'changed': changed,
                'subnet': {}
            }
    if map_public != subnet['map_public_ip_on_launch']:
        ensure_map_public(conn, module, subnet, map_public, check_mode)
        subnet['map_public_ip_on_launch'] = map_public
        changed = True

    if tags != subnet['tags']:
        ensure_tags(conn, module, subnet, tags, False, check_mode)
        subnet['tags'] = tags
        changed = True

    return {
        'changed': changed,
        'subnet': subnet
    }


def ensure_subnet_absent(conn, module, vpc_id, cidr, check_mode):
    subnet = get_matching_subnet(conn, vpc_id, cidr)
    if subnet is None:
        return {'changed': False}

    try:
        if not check_mode:
            conn.delete_subnet(SubnetId=subnet['id'], DryRun=check_mode)
        return {'changed': True}
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            az=dict(default=None, required=False),
            cidr=dict(default=None, required=True),
            state=dict(default='present', choices=['present', 'absent']),
            tags=dict(default={}, required=False, type='dict', aliases=['resource_tags']),
            vpc_id=dict(default=None, required=True),
            map_public=dict(default=False, required=False, type='bool')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 and botocore are required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)
    else:
        module.fail_json(msg="region must be specified")

    vpc_id = module.params.get('vpc_id')
    tags = module.params.get('tags')
    cidr = module.params.get('cidr')
    az = module.params.get('az')
    state = module.params.get('state')
    map_public = module.params.get('map_public')

    try:
        if state == 'present':
            result = ensure_subnet_present(connection, module, vpc_id, cidr, az, tags, map_public,
                                           check_mode=module.check_mode)
        elif state == 'absent':
            result = ensure_subnet_absent(connection, module, vpc_id, cidr,
                                          check_mode=module.check_mode)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
