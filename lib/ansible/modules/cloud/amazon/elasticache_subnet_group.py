#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: elasticache_subnet_group
version_added: "2.0"
short_description: manage Elasticache subnet groups
description:
     - Creates, modifies, and deletes Elasticache subnet groups. This module has a dependency on python-boto >= 2.5.
options:
  state:
    description:
      - Specifies whether the subnet should be present or absent.
    required: true
    default: present
    choices: [ 'present' , 'absent' ]
  name:
    description:
      - Database subnet group identifier.
    required: true
  description:
    description:
      - Elasticache subnet group description. Only set when a new group is added.
    required: false
    default: null
  subnets:
    description:
      - List of subnet IDs that make up the Elasticache subnet group.
    required: false
    default: null
author: "Tim Mahoney (@timmahoney)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Add or change a subnet group
- elasticache_subnet_group:
    state: present
    name: norwegian-blue
    description: My Fancy Ex Parrot Subnet Group
    subnets:
      - subnet-aaaaaaaa
      - subnet-bbbbbbbb

# Remove a subnet group
- elasticache_subnet_group:
    state: absent
    name: norwegian-blue
'''

try:
    import boto
    from boto.elasticache import connect_to_region
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import HAS_BOTO, ec2_argument_spec, get_aws_connection_info


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent']),
        name=dict(required=True),
        description=dict(required=False),
        subnets=dict(required=False, type='list'),
    )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    state = module.params.get('state')
    group_name = module.params.get('name').lower()
    group_description = module.params.get('description')
    group_subnets = module.params.get('subnets') or {}

    if state == 'present':
        for required in ['name', 'description', 'subnets']:
            if not module.params.get(required):
                module.fail_json(msg=str("Parameter %s required for state='present'" % required))
    else:
        for not_allowed in ['description', 'subnets']:
            if module.params.get(not_allowed):
                module.fail_json(msg=str("Parameter %s not allowed for state='absent'" % not_allowed))

    # Retrieve any AWS settings from the environment.
    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)

    if not region:
        module.fail_json(msg=str("Either region or AWS_REGION or EC2_REGION environment variable or boto config aws_region or ec2_region must be set."))

    """Get an elasticache connection"""
    try:
        conn = connect_to_region(region_name=region, **aws_connect_kwargs)
    except boto.exception.NoAuthHandlerFound as e:
        module.fail_json(msg=e.message)

    try:
        changed = False
        exists = False

        try:
            matching_groups = conn.describe_cache_subnet_groups(group_name, max_records=100)
            exists = len(matching_groups) > 0
        except BotoServerError as e:
            if e.error_code != 'CacheSubnetGroupNotFoundFault':
                module.fail_json(msg=e.error_message)

        if state == 'absent':
            if exists:
                conn.delete_cache_subnet_group(group_name)
                changed = True
        else:
            if not exists:
                new_group = conn.create_cache_subnet_group(group_name, cache_subnet_group_description=group_description, subnet_ids=group_subnets)
                changed = True
            else:
                changed_group = conn.modify_cache_subnet_group(group_name, cache_subnet_group_description=group_description, subnet_ids=group_subnets)
                changed = True

    except BotoServerError as e:
        if e.error_message != 'No modifications were requested.':
            module.fail_json(msg=e.error_message)
        else:
            changed = False

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
