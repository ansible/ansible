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
module: ec2_vpc_net
short_description: Configure AWS virtual private clouds
description:
    - Create or terminate AWS virtual private clouds.  This module has a dependency on python-boto.
version_added: "2.0"
author: Jonathan Davila (@defionscode)
options:
  name:
    description:
      - The name to give your VPC. This is used in combination with the cidr_block paramater to determine if a VPC already exists.
    required: yes
  cidr_block:
    description:
      - The CIDR of the VPC
    required: yes
  tenancy:
    description:
      - Whether to be default or dedicated tenancy. This cannot be changed after the VPC has been created.
    required: false
    default: default
    choices: [ 'default', 'dedicated' ]
  dns_support:
    description:
      - Whether to enable AWS DNS support.
    required: false
    default: yes
    choices: [ 'yes', 'no' ]
  dns_hostnames:
    description:
      - Whether to enable AWS hostname support.
    required: false
    default: yes
    choices: [ 'yes', 'no' ]
  dhcp_opts_id:
    description:
      - the id of the DHCP options to use for this vpc
    default: null
    required: false
  tags:
    description:
      - The tags you want attached to the VPC. This is independent of the name value, note if you pass a 'Name' key it would override the Name of the VPC if it's different.
    default: None
    required: false
    aliases: [ 'resource_tags' ]
  state:
    description:
      - The state of the VPC. Either absent or present.
    default: present
    required: false
    choices: [ 'present', 'absent' ]
  multi_ok:
    description:
      - By default the module will not create another VPC if there is another VPC with the same name and CIDR block. Specify this as true if you want duplicate VPCs created.
    default: false
    required: false

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create a VPC with dedicate tenancy and a couple of tags

- ec2_vpc_net:
    name: Module_dev2
    cidr_block: 10.10.0.0/16
    region: us-east-1
    tags:
      module: ec2_vpc_net
      this: works
    tenancy: dedicated

'''

import time
import sys

try:
    import boto
    import boto.ec2
    import boto.vpc
    from boto.exception import BotoServerError
    HAS_BOTO=True
except ImportError:
    HAS_BOTO=False

def boto_exception(err):
    '''generic error message handler'''
    if hasattr(err, 'error_message'):
        error = err.error_message
    elif hasattr(err, 'message'):
        error = err.message
    else:
        error = '%s: %s' % (Exception, err)

    return error

def vpc_exists(module, vpc, name, cidr_block, multi):
    """Returns True or False in regards to the existence of a VPC. When supplied
    with a CIDR, it will check for matching tags to determine if it is a match
    otherwise it will assume the VPC does not exist and thus return false.
    """
    matched_vpc = None

    try:
        matching_vpcs=vpc.get_all_vpcs(filters={'tag:Name' : name, 'cidr-block' : cidr_block})
    except Exception, e:
        e_msg=boto_exception(e)
        module.fail_json(msg=e_msg)

    if len(matching_vpcs) == 1:
        matched_vpc = matching_vpcs[0]
    elif len(matching_vpcs) > 1:
        if multi:
            module.fail_json(msg='Currently there are %d VPCs that have the same name and '
                             'CIDR block you specified. If you would like to create '
                             'the VPC anyway please pass True to the multi_ok param.' % len(matching_vpcs))
    
    return matched_vpc


def update_vpc_tags(vpc, module, vpc_obj, tags, name):
    
    if tags is None:
        tags = dict()
        
    tags.update({'Name': name})
    try:
        current_tags = dict((t.name, t.value) for t in vpc.get_all_tags(filters={'resource-id': vpc_obj.id}))
        if cmp(tags, current_tags):
            vpc.create_tags(vpc_obj.id, tags)
            return True
        else:
            return False
    except Exception, e:
        e_msg=boto_exception(e)
        module.fail_json(msg=e_msg)
        

def update_dhcp_opts(connection, module, vpc_obj, dhcp_id):
    
    if vpc_obj.dhcp_options_id != dhcp_id:
        connection.associate_dhcp_options(dhcp_id, vpc_obj.id)
        return True
    else:
        return False

def get_vpc_values(vpc_obj):

    if vpc_obj is not None:
        vpc_values = vpc_obj.__dict__
        if "region" in vpc_values:
            vpc_values.pop("region")
        if "item" in vpc_values:
            vpc_values.pop("item")
        if "connection" in vpc_values:
            vpc_values.pop("connection")
        return vpc_values
    else:
        return None

def main():
    argument_spec=ec2_argument_spec()
    argument_spec.update(dict(
            name = dict(type='str', default=None, required=True),
            cidr_block = dict(type='str', default=None, required=True),
            tenancy = dict(choices=['default', 'dedicated'], default='default'),
            dns_support = dict(type='bool', default=True),
            dns_hostnames = dict(type='bool', default=True),
            dhcp_opts_id = dict(type='str', default=None, required=False),
            tags = dict(type='dict', required=False, default=None, aliases=['resource_tags']),
            state = dict(choices=['present', 'absent'], default='present'),
            multi_ok = dict(type='bool', default=False)
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto is required for this module')

    name=module.params.get('name')
    cidr_block=module.params.get('cidr_block')
    tenancy=module.params.get('tenancy')
    dns_support=module.params.get('dns_support')
    dns_hostnames=module.params.get('dns_hostnames')
    dhcp_id=module.params.get('dhcp_opts_id')
    tags=module.params.get('tags')
    state=module.params.get('state')
    multi=module.params.get('multi_ok')
    
    changed=False

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    
    if region:
        try:
            connection = connect_to_aws(boto.vpc, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, StandardError), e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")
        
    if dns_hostnames and not dns_support:
        module.fail_json('In order to enable DNS Hostnames you must also enable DNS support')

    if state == 'present':
        
        # Check if VPC exists
        vpc_obj = vpc_exists(module, connection, name, cidr_block, multi)
        
        if vpc_obj is None:
            try:
                vpc_obj = connection.create_vpc(cidr_block, instance_tenancy=tenancy)
                changed = True
            except BotoServerError, e:
                module.fail_json(msg=e)
        
        if dhcp_id is not None:        
            try:
                if update_dhcp_opts(connection, module, vpc_obj, dhcp_id):
                    changed = True
            except BotoServerError, e:
                module.fail_json(msg=e)
        
        if tags is not None or name is not None:            
            try:
                if update_vpc_tags(connection, module, vpc_obj, tags, name):
                    changed = True
            except BotoServerError, e:
                module.fail_json(msg=e)
                

        # Note: Boto currently doesn't currently provide an interface to ec2-describe-vpc-attribute
        # which is needed in order to detect the current status of DNS options. For now we just update
        # the attribute each time and is not used as a changed-factor.
        try:
            connection.modify_vpc_attribute(vpc_obj.id, enable_dns_support=dns_support)
            connection.modify_vpc_attribute(vpc_obj.id, enable_dns_hostnames=dns_hostnames)
        except BotoServerError, e:
            e_msg=boto_exception(e)
            module.fail_json(msg=e_msg)
            
        # get the vpc obj again in case it has changed
        try:
            vpc_obj = connection.get_all_vpcs(vpc_obj.id)[0]
        except BotoServerError, e:
            e_msg=boto_exception(e)
            module.fail_json(msg=e_msg)
        
        module.exit_json(changed=changed, vpc=get_vpc_values(vpc_obj))

    elif state == 'absent':
        
        # Check if VPC exists
        vpc_obj = vpc_exists(module, connection, name, cidr_block, multi)
        
        if vpc_obj is not None:
            try:
                connection.delete_vpc(vpc_obj.id)
                vpc_obj = None
                changed = True
            except BotoServerError, e:
                e_msg = boto_exception(e)
                module.fail_json(msg="%s. You may want to use the ec2_vpc_subnet, ec2_vpc_igw, "
                "and/or ec2_vpc_route_table modules to ensure the other components are absent." % e_msg)
            
        module.exit_json(changed=changed, vpc=get_vpc_values(vpc_obj))
            
# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
