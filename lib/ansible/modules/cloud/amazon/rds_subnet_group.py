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
  region:
    description:
      - The AWS region to use. If not specified then the value of the EC2_REGION environment variable, if any, is used.
    required: true
    default: null
    aliases: [ 'aws_region', 'ec2_region' ]
  aws_access_key:
    description:
      - AWS access key. If not set then the value of the AWS_ACCESS_KEY environment variable is used.
    required: false
    default: null
    aliases: [ 'ec2_access_key', 'access_key' ]
  aws_secret_key:
    description:
      - AWS secret key. If not set then the value of the AWS_SECRET_KEY environment variable is used. 
    required: false
    default: null
    aliases: [ 'ec2_secret_key', 'secret_key' ]
requirements: [ "boto" ]
author: Scott Anderson
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

import sys
import time

try:
    import boto.rds
    from boto.exception import BotoServerError
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)

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
    ec2_url, aws_access_key, aws_secret_key, region = get_ec2_creds(module)

    if not region:
        module.fail_json(msg = str("region not specified and unable to determine region from EC2_REGION."))

    try:
        conn = boto.rds.connect_to_region(region, aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
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

            else:
                changed_group = conn.modify_db_subnet_group(group_name, description=group_description, subnet_ids=group_subnets)

    except BotoServerError, e:
        module.fail_json(msg = e.error_message)

    module.exit_json(changed=changed)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
