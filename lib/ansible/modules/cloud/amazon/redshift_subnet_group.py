#!/usr/bin/python

# Copyright 2014 Jens Carl, Hothead Games Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
author:
  - "Jens Carl (@j-carl), Hothead Games Inc."
module: redshift_subnet_group
version_added: "2.2"
short_description: manage Redshift cluster subnet groups
description:
  - Create, modifies, and deletes Redshift cluster subnet groups.
options:
  state:
    description:
      - Specifies whether the subnet should be present or absent.
    default: 'present'
    choices: ['present', 'absent' ]
  group_name:
    description:
      - Cluster subnet group name.
    required: true
    aliases: ['name']
  group_description:
    description:
      - Database subnet group description.
    aliases: ['description']
  group_subnets:
    description:
      - List of subnet IDs that make up the cluster subnet group.
    aliases: ['subnets']
requirements: [ 'boto' ]
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# Create a Redshift subnet group
- local_action:
    module: redshift_subnet_group
    state: present
    group_name: redshift-subnet
    group_description: Redshift subnet
    group_subnets:
        - 'subnet-aaaaa'
        - 'subnet-bbbbb'

# Remove subnet group
- redshift_subnet_group:
    state: absent
    group_name: redshift-subnet
'''

RETURN = '''
group:
    description: dictionary containing all Redshift subnet group information
    returned: success
    type: complex
    contains:
        name:
            description: name of the Redshift subnet group
            returned: success
            type: str
            sample: "redshift_subnet_group_name"
        vpc_id:
            description: Id of the VPC where the subnet is located
            returned: success
            type: str
            sample: "vpc-aabb1122"
'''

try:
    import boto
    import boto.redshift
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import HAS_BOTO, connect_to_aws, ec2_argument_spec, get_aws_connection_info


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent']),
        group_name=dict(required=True, aliases=['name']),
        group_description=dict(required=False, aliases=['description']),
        group_subnets=dict(required=False, aliases=['subnets'], type='list'),
    ))
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto v2.9.0+ required for this module')

    state = module.params.get('state')
    group_name = module.params.get('group_name')
    group_description = module.params.get('group_description')
    group_subnets = module.params.get('group_subnets')

    if state == 'present':
        for required in ('group_name', 'group_description', 'group_subnets'):
            if not module.params.get(required):
                module.fail_json(msg=str("parameter %s required for state='present'" % required))
    else:
        for not_allowed in ('group_description', 'group_subnets'):
            if module.params.get(not_allowed):
                module.fail_json(msg=str("parameter %s not allowed for state='absent'" % not_allowed))

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    if not region:
        module.fail_json(msg=str("Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file"))

    # Connect to the Redshift endpoint.
    try:
        conn = connect_to_aws(boto.redshift, region, **aws_connect_params)
    except boto.exception.JSONResponseError as e:
        module.fail_json(msg=str(e))

    try:
        changed = False
        exists = False
        group = None

        try:
            matching_groups = conn.describe_cluster_subnet_groups(group_name, max_records=100)
            exists = len(matching_groups) > 0
        except boto.exception.JSONResponseError as e:
            if e.body['Error']['Code'] != 'ClusterSubnetGroupNotFoundFault':
                # if e.code != 'ClusterSubnetGroupNotFoundFault':
                module.fail_json(msg=str(e))

        if state == 'absent':
            if exists:
                conn.delete_cluster_subnet_group(group_name)
                changed = True

        else:
            if not exists:
                new_group = conn.create_cluster_subnet_group(group_name, group_description, group_subnets)
                group = {
                    'name': new_group['CreateClusterSubnetGroupResponse']['CreateClusterSubnetGroupResult']
                    ['ClusterSubnetGroup']['ClusterSubnetGroupName'],
                    'vpc_id': new_group['CreateClusterSubnetGroupResponse']['CreateClusterSubnetGroupResult']
                    ['ClusterSubnetGroup']['VpcId'],
                }
            else:
                changed_group = conn.modify_cluster_subnet_group(group_name, group_subnets, description=group_description)
                group = {
                    'name': changed_group['ModifyClusterSubnetGroupResponse']['ModifyClusterSubnetGroupResult']
                    ['ClusterSubnetGroup']['ClusterSubnetGroupName'],
                    'vpc_id': changed_group['ModifyClusterSubnetGroupResponse']['ModifyClusterSubnetGroupResult']
                    ['ClusterSubnetGroup']['VpcId'],
                }

            changed = True

    except boto.exception.JSONResponseError as e:
        module.fail_json(msg=str(e))

    module.exit_json(changed=changed, group=group)


if __name__ == '__main__':
    main()
