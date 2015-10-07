#!/usr/bin/python
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

DOCUMENTATION = '''
---
module: rds_subnet_group
version_added: "1.5"
short_description: manage RDS database subnet groups
description:
     - Creates, modifies, and deletes RDS database subnet groups. This module has a dependency on python-boto >= 2.5.
options:
  state:
    description:
      - Specifies whether the subnet should be present or absent.
    required: true
    default: present
    aliases: []
    choices: [ 'present' , 'absent' ]
  name:
    description:
      - Database subnet group identifier.
    required: true
    default: null
    aliases: []
  description:
    description:
      - Database subnet group description. Only set when a new group is added.
    required: false
    default: null
    aliases: []
  subnets:
    description:
      - List of subnet IDs that make up the database subnet group.
    required: false
    default: null
    aliases: []
author: "Scott Anderson (@tastychutney)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Add or change a subnet group
- rds_subnet_group
    state: present
    name: norwegian-blue
    description: My Fancy Ex Parrot Subnet Group
    subnets:
      - subnet-aaaaaaaa
      - subnet-bbbbbbbb

# Remove a subnet group
- rds_subnet_group:
    state: absent
    name: norwegian-blue
'''

try:
    import boto.rds
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            state             = dict(required=True,  choices=['present', 'absent']),
            name              = dict(required=True),
            description       = dict(required=False),
            subnets           = dict(required=False, type='list'),
        )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    state                   = module.params.get('state')
    group_name              = module.params.get('name').lower()
    group_description       = module.params.get('description')
    group_subnets           = module.params.get('subnets') or {}

    if state == 'present':
        for required in ['name', 'description', 'subnets']:
            if not module.params.get(required):
                module.fail_json(msg = str("Parameter %s required for state='present'" % required))
    else:
        for not_allowed in ['description', 'subnets']:
            if module.params.get(not_allowed):
                module.fail_json(msg = str("Parameter %s not allowed for state='absent'" % not_allowed))

    # Retrieve any AWS settings from the environment.
    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)

    if not region:
        module.fail_json(msg = str("Either region or AWS_REGION or EC2_REGION environment variable or boto config aws_region or ec2_region must be set."))

    try:
        conn = boto.rds.connect_to_region(region, **aws_connect_kwargs)
    except boto.exception.BotoServerError, e:
        module.fail_json(msg = e.error_message)

    try:
        changed = False
        exists = False

        try:
            matching_groups = conn.get_all_db_subnet_groups(group_name, max_records=100)
            exists = len(matching_groups) > 0
        except BotoServerError, e:
            if e.error_code != 'DBSubnetGroupNotFoundFault':
                module.fail_json(msg = e.error_message)
        
        if state == 'absent':
            if exists:
                conn.delete_db_subnet_group(group_name)
                changed = True
        else:
            if not exists:
                new_group = conn.create_db_subnet_group(group_name, desc=group_description, subnet_ids=group_subnets)
                changed = True
            else:
                # Sort the subnet groups before we compare them
                matching_groups[0].subnet_ids.sort()
                group_subnets.sort()
                if ( (matching_groups[0].name != group_name) or (matching_groups[0].description != group_description) or (matching_groups[0].subnet_ids != group_subnets) ):
                    changed_group = conn.modify_db_subnet_group(group_name, description=group_description, subnet_ids=group_subnets)
                    changed = True
    except BotoServerError, e:
        module.fail_json(msg = e.error_message)

    module.exit_json(changed=changed)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
