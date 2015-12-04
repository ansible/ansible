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

DOCUMENTATION = '''
---
module: ec2_vpc_subnet
short_description: Manage subnets in AWS virtual private clouds
description:
    - Manage subnets in AWS virtual private clouds
version_added: "2.0"
author: Robert Estelle (@erydo)
options:
  az:
    description:
      - "The availability zone for the subnet. Only required when state=present."
    required: false
    default: null
  cidr:
    description:
      - "The CIDR block for the subnet. E.g. 10.0.0.0/16. Only required when state=present."
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

import sys  # noqa
import time

try:
    import boto.ec2
    import boto.vpc
    from boto.exception import EC2ResponseError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False
    if __name__ != '__main__':
        raise


class AnsibleVPCSubnetException(Exception):
    pass


class AnsibleVPCSubnetCreationException(AnsibleVPCSubnetException):
    pass


class AnsibleVPCSubnetDeletionException(AnsibleVPCSubnetException):
    pass


class AnsibleTagCreationException(AnsibleVPCSubnetException):
    pass


def get_subnet_info(subnet):

    subnet_info = { 'id': subnet.id,
                    'availability_zone': subnet.availability_zone,
                    'available_ip_address_count': subnet.available_ip_address_count,
                    'cidr_block': subnet.cidr_block,
                    'default_for_az': subnet.defaultForAz,
                    'map_public_ip_on_launch': subnet.mapPublicIpOnLaunch,
                    'state': subnet.state,
                    'tags': subnet.tags,
                    'vpc_id': subnet.vpc_id
                  }

    return subnet_info

def subnet_exists(vpc_conn, subnet_id):
    filters = {'subnet-id': subnet_id}
    subnet = vpc_conn.get_all_subnets(filters=filters)
    if subnet[0].state == "available":
        return subnet[0]
    else:
        return False


def create_subnet(vpc_conn, vpc_id, cidr, az, check_mode):
    try:
        new_subnet = vpc_conn.create_subnet(vpc_id, cidr, az, dry_run=check_mode)
        # Sometimes AWS takes its time to create a subnet and so using
        # new subnets's id to do things like create tags results in
        # exception.  boto doesn't seem to refresh 'state' of the newly
        # created subnet, i.e.: it's always 'pending'.
        subnet = False
        while subnet is False:
            subnet = subnet_exists(vpc_conn, new_subnet.id)
            time.sleep(0.1)
    except EC2ResponseError as e:
        if e.error_code == "DryRunOperation":
            subnet = None
        else:
            raise AnsibleVPCSubnetCreationException(
              'Unable to create subnet {0}, error: {1}'.format(cidr, e))

    return subnet


def get_resource_tags(vpc_conn, resource_id):
    return dict((t.name, t.value) for t in
                vpc_conn.get_all_tags(filters={'resource-id': resource_id}))


def ensure_tags(vpc_conn, resource_id, tags, add_only, check_mode):
    try:
        cur_tags = get_resource_tags(vpc_conn, resource_id)
        if cur_tags == tags:
            return {'changed': False, 'tags': cur_tags}

        to_delete = dict((k, cur_tags[k]) for k in cur_tags if k not in tags)
        if to_delete and not add_only:
            vpc_conn.delete_tags(resource_id, to_delete, dry_run=check_mode)

        to_add = dict((k, tags[k]) for k in tags if k not in cur_tags or cur_tags[k] != tags[k])
        if to_add:
            vpc_conn.create_tags(resource_id, to_add, dry_run=check_mode)

        latest_tags = get_resource_tags(vpc_conn, resource_id)
        return {'changed': True, 'tags': latest_tags}
    except EC2ResponseError as e:
        raise AnsibleTagCreationException(
            'Unable to update tags for {0}, error: {1}'.format(resource_id, e))


def get_matching_subnet(vpc_conn, vpc_id, cidr):
    subnets = vpc_conn.get_all_subnets(filters={'vpc_id': vpc_id})
    return next((s for s in subnets if s.cidr_block == cidr), None)


def ensure_subnet_present(vpc_conn, vpc_id, cidr, az, tags, check_mode):
    subnet = get_matching_subnet(vpc_conn, vpc_id, cidr)
    changed = False
    if subnet is None:
        subnet = create_subnet(vpc_conn, vpc_id, cidr, az, check_mode)
        changed = True
        # Subnet will be None when check_mode is true
        if subnet is None:
            return {
                'changed': changed,
                'subnet': {}
            }

    if tags != subnet.tags:
        ensure_tags(vpc_conn, subnet.id, tags, False, check_mode)
        subnet.tags = tags
        changed = True

    subnet_info = get_subnet_info(subnet)

    return {
        'changed': changed,
        'subnet': subnet_info
    }


def ensure_subnet_absent(vpc_conn, vpc_id, cidr, check_mode):
    subnet = get_matching_subnet(vpc_conn, vpc_id, cidr)
    if subnet is None:
        return {'changed': False}

    try:
        vpc_conn.delete_subnet(subnet.id, dry_run=check_mode)
        return {'changed': True}
    except EC2ResponseError as e:
        raise AnsibleVPCSubnetDeletionException(
            'Unable to delete subnet {0}, error: {1}'
            .format(subnet.cidr_block, e))


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            az = dict(default=None, required=False),
            cidr = dict(default=None, required=True),
            state = dict(default='present', choices=['present', 'absent']),
            tags = dict(default=None, required=False, type='dict', aliases=['resource_tags']),
            vpc_id = dict(default=None, required=True)
        )
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_BOTO:
        module.fail_json(msg='boto is required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region:
        try:
            connection = connect_to_aws(boto.vpc, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError), e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

    vpc_id = module.params.get('vpc_id')
    tags = module.params.get('tags')
    cidr = module.params.get('cidr')
    az = module.params.get('az')
    state = module.params.get('state')

    try:
        if state == 'present':
            result = ensure_subnet_present(connection, vpc_id, cidr, az, tags,
                                           check_mode=module.check_mode)
        elif state == 'absent':
            result = ensure_subnet_absent(connection, vpc_id, cidr,
                                          check_mode=module.check_mode)
    except AnsibleVPCSubnetException as e:
        module.fail_json(msg=str(e))

    module.exit_json(**result)

from ansible.module_utils.basic import *  # noqa
from ansible.module_utils.ec2 import *  # noqa

if __name__ == '__main__':
    main()
