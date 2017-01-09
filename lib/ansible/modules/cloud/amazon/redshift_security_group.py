#!/usr/bin/python

# (c) 2015, Jens Carl, Hothead Games Inc.
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
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
module: redshift_security_group
author: '"Jens Carl (@j-carl), Hothead Games Inc."'
short_description: Redshift security group management
description:
  - allows you to create, delete, and modify Redshift security groups
version_added: "2.2"
options:
  state:
    description:
      - Create or delete the security group.
    default: 'present'
    choices: ['present', 'absent']
  group_name:
    description:
      - Name of the security group.
    required: false
    default: 'Default'
    aliases: ['name']
  description:
    description:
      - Describe the security group.
    required: true
  rules:
    description:
      - List of rules to add to security group.
    required: true

extends_documentation_fragment:
    - aws
requirements: [ 'boto' ]
'''

EXAMPLES = '''
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.

# Create a security group with CIDR rule.
    redshift_security_group:
        state: present
        group_name: test_with_cidr
        description: Security group with CIDR
        rules:
            - cidr: 0.0.0.0/0

# Create a security group with EC2 security group
    redshift_security_group:
        state: present
        group_name: test_with_ec2_sec_group
        description: Security group with EC2 security group
        rules:
            - sg_name: ec2_sg_test
              sg_owner: <AWS account id>

# Add a CIDR rule to an existing EC2 rule.
    redshift_security_group:
        state: present
        group_name: test_with_ec2_sec_group
        description: Security group with EC2 security group and CIDR
        rules:
            - sg_name: ec2_sg_test
              sg_owner: <AWS account id>
            - cidr: 0.0.0.0/0

# Delete a security group.
    redshift_security_group:
        state: absent
        group_name: test_with_ec2_sec_group
'''

RETURN = '''
changed:
    description: A flag indicating if any change was made or not
    returned: success
    type: boolean
    sample: True
'''
# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import connect_to_aws, ec2_argument_spec, get_aws_connection_info

try:
    import boto
    import boto.redshift
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


def _clear_rules(module, redshift, group):

    try:
        # Revoke IP ranges.
        for rule in group['IPRanges']:
            group_kwargs = {'cidrip': rule['CIDRIP']}
            redshift.revoke_cluster_security_group_ingress(group['ClusterSecurityGroupName'], **group_kwargs)

        # Revoke EC2 security groups.
        for rule in group['EC2SecurityGroups']:
            group_kwargs = {
                'ec2_security_group_name': rule['EC2SecurityGroupName'],
                'ec2_security_group_owner_id': rule['EC2SecurityGroupOwnerId']
            }
            redshift.revoke_cluster_security_group_ingress(group['ClusterSecurityGroupName'], **group_kwargs)

    except boto.exception.JSONResponseError as e:
        module.fail_json(msg=str(e))


def delete_group(module, redshift):

    group_name = module.params.get('group_name')

    try:
        redshift.delete_cluster_security_group(group_name)
    except boto.exception.JSONResponseError as e:
        module.fail_json(msg=str(e))

    return True


def create_group(module, redshift):

    group_name = module.params.get('group_name')
    description = module.params.get('description')
    rules = module.params.get('rules')

    try:
        group = []

        sec_groups = redshift.describe_cluster_security_groups(group_name)
        for sec_group in sec_groups['DescribeClusterSecurityGroupsResponse']['DescribeClusterSecurityGroupsResult']['ClusterSecurityGroups']:
            if sec_group['ClusterSecurityGroupName'] == group_name:
                group = sec_group
                break

        _clear_rules(module, redshift, group)
    except boto.redshift.exceptions.ClusterSecurityGroupNotFound:

        try:
            redshift.create_cluster_security_group(group_name, description)
        except boto.exception.JSONResponseError as e:
            module.fail_json(msg=str(e))

    # Process all rule properties.
    if rules is not None:
        if not isinstance(rules, list):
            module.fail_json(msg='Rules needs to be a list of CIDR or EC2 security groups')

    try:
        for rule in rules:
            group_kwargs = {}
            if 'cidr' in rule:
                group_kwargs['cidrip'] = rule['cidr']
            elif 'sg_name' in rule:
                group_kwargs['ec2_security_group_name'] = rule['sg_name']
                if 'sg_owner' in rule:
                    group_kwargs['ec2_security_group_owner_id'] = rule['sg_owner']

            redshift.authorize_cluster_security_group_ingress(group_name, **group_kwargs)

    except boto.exception.JSONResponseError as e:
        module.fail_json(msg=str(e))

    return True


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            state       = dict(choices=['present', 'absent'], required=True),
            group_name  = dict(aliases=['name'], default='Default'),
            description = dict(),
            rules       = dict(type='list')
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    state = module.params.get('state')

    region, url, aws_connect_params = get_aws_connection_info(module)

    if not region:
        module.fail_json(msg=str("Region not specified and unable to determinate region from EC2_REGION."))

    # Connect to the Redshift endpoint.
    try:
        conn = connect_to_aws(boto.redshift, region, **aws_connect_params)
    except boto.exception.JSONResponseError as e:
        module.fail_json(msg=str(e))

    if state == 'absent':
        changed = delete_group(module, conn)
    elif state == 'present':
        changed = create_group(module, conn)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
