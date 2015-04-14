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
short_description: configure AWS virtual private clouds
description:
    - Create or terminates AWS virtual private clouds.  This module has a dependency on python-boto.
version_added: "2.0"
options:
  name:
    description:
      - The name to give your VPC. This is used in combination with the cidr_block paramater to determine if a VPC already exists.
    required: yes
  cidr_block:
    description:
      - The CIDR of the VPC
    required: yes
    aliases: []
  tenancy:
    description:
      - Whether to be default or dedicated tenancy. This cannot be changed after the VPC has been created.
    required: false
    default: default
  dns_support:
    description:
      - Whether to enable AWS DNS support.
    required: false
    default: true
  dns_hostnames:
    description:
      - Whether to enable AWS hostname support.
    required: false
    default: true
  dhcp_id:
    description:
      - the id of the DHCP options to use for this vpc
    default: null
    required: false
  tags:
    description:
      - The tags you want attached to the VPC. This is independent of the name value, note if you pass a 'Name' key it would override the Name of the VPC if it's different.
    default: None
    required: false
  state:
    description:
      - The state of the VPC. Either absent or present.
    default: present
    required: false
  multi_ok:
    description:
      - By default the module will not create another VPC if there is another VPC with the same name and CIDR block. Specify this as true if you want duplicate VPCs created.
    default: false
    required: false
author: Jonathan Davila
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Create a VPC with dedicate tenancy and a couple of tags

- ec2_vpc:
    name: Module_dev2
    cidr_block: 170.10.0.0/16
    region: us-east-1
    tags:
      new_vpc: ec2_vpc_module
      this: works22
    tenancy: dedicated

'''


import time
import sys

try:
    import boto
    import boto.ec2
    import boto.vpc
    from boto.exception import EC2ResponseError

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
    """Returns True or False in regards to the existance of a VPC. When supplied
    with a CIDR, it will check for matching tags to determine if it is a match
    otherwise it will assume the VPC does not exist and thus return false.
    """
    exists=False
    matched_vpc=None

    try:
        matching_vpcs=vpc.get_all_vpcs(filters={'tag:Name' : name, 'cidr-block' : cidr_block})
    except Exception, e:
        e_msg=boto_exception(e)
        module.fail_json(msg=e_msg)

    if len(matching_vpcs) == 1 and not multi:
        exists=True
        matched_vpc=str(matching_vpcs).split(':')[1].split(']')[0]
    elif len(matching_vpcs) > 1 and not multi:
        module.fail_json(msg='Currently there are %d VPCs that have the same name and '
                             'CIDR block you specified. If you would like to create '
                             'the VPC anyways please pass True to the multi_ok param.' % len(matching_vpcs))

    return exists, matched_vpc

def vpc_needs_update(module, vpc, vpc_id, dns_support, dns_hostnames, dhcp_id, tags):
    """This returns True or False. Intended to run after vpc_exists.
    It will check all the characteristics of the parameters passed and compare them
    to the active VPC. If any discrepancy is found, it will report true, meaning that
    the VPC needs to be update in order to match the specified state in the params.
    """

    update_dhcp=False
    update_tags=False
    dhcp_match=False

    try:
        dhcp_list=vpc.get_all_dhcp_options()

        if dhcp_id is not None:
            has_default=vpc.get_all_vpcs(filters={'dhcp-options-id' : 'default', 'vpc-id' : vpc_id})
            for opts in dhcp_list:
                if (str(opts).split(':')[1] == dhcp_id) or has_default:
                    dhcp_match=True
                    break
                else:
                    pass
    except Exception, e:
        e_msg=boto_exception(e)
        module.fail_json(msg=e_msg)

        if not dhcp_match or (has_default and dhcp_id != 'default'):
            update_dhcp=True

    if dns_hostnames and dns_support == False:
        module.fail_json('In order to enable DNS Hostnames you must have DNS support enabled')
    else:

    # Note: Boto currently doesn't currently provide an interface to ec2-describe-vpc-attribute
    # which is needed in order to detect the current status of DNS options. For now we just update
    # the attribute each time and is not used as a changed-factor.
        try:
            vpc.modify_vpc_attribute(vpc_id, enable_dns_support=dns_support)
            vpc.modify_vpc_attribute(vpc_id, enable_dns_hostnames=dns_hostnames)
        except Exception, e:
            e_msg=boto_exception(e)
            module.fail_json(msg=e_msg)

    if tags:
        try:
            current_tags = dict((t.name, t.value) for t in vpc.get_all_tags(filters={'resource-id': vpc_id}))
            if not set(tags.items()).issubset(set(current_tags.items())):
                update_tags=True
        except Exception, e:
            e_msg=boto_exception(e)
            module.fail_json(msg=e_msg)

    return update_dhcp, update_tags


def update_vpc_tags(module, vpc, vpc_id, tags, name):
    tags.update({'Name': name})
    try:
        vpc.create_tags(vpc_id, tags)
        updated_tags=dict((t.name, t.value) for t in vpc.get_all_tags(filters={'resource-id': vpc_id}))
    except Exception, e:
        e_msg=boto_exception(e)
        module.fail_json(msg=e_msg)

    return updated_tags


def update_dhcp_opts(module, vpc, vpc_id, dhcp_id):
    try:
        vpc.associate_dhcp_options(dhcp_id, vpc_id)
        dhcp_list=vpc.get_all_dhcp_options()
    except Exception, e:
        e_msg=boto_exception(e)
        module.fail_json(msg=e_msg)

    for opts in dhcp_list:
        vpc_dhcp=vpc.get_all_vpcs(filters={'dhcp-options-id' : opts, 'vpc-id' : vpc_id})
        matched=False
        if opts == dhcp_id:
            matched=True
            return opts

    if matched == False:
        return dhcp_id

def main():
    argument_spec=ec2_argument_spec()
    argument_spec.update(dict(
            name=dict(type='str', default=None, required=True),
            cidr_block=dict(type='str', default=None, required=True),
            tenancy=dict(choices=['default', 'dedicated'], default='default'),
            dns_support=dict(type='bool', default=True),
            dns_hostnames=dict(type='bool', default=True),
            dhcp_opts_id=dict(type='str', default=None, required=False),
            tags=dict(type='dict', required=False, default=None),
            state=dict(choices=['present', 'absent'], default='present'),
            region=dict(type='str', required=True),
            multi_ok=dict(type='bool', default=False)
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    if not HAS_BOTO:
        module.fail_json(msg='Boto is required for this module')

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
    new_dhcp_opts=None
    new_tags=None
    update_dhcp=False
    update_tags=False

    region, ec2_url, aws_connect_kwargs=get_aws_connection_info(module)

    try:
        vpc=boto.vpc.connect_to_region(
            region,
            **aws_connect_kwargs
        )
    except boto.exception.NoAuthHandlerFound, e:
        module.fail_json(msg=str(e))

    already_exists, vpc_id=vpc_exists(module, vpc, name, cidr_block, multi)

    if already_exists:
        update_dhcp, update_tags=vpc_needs_update(module, vpc, vpc_id, dns_support, dns_hostnames, dhcp_id, tags)
        if update_dhcp or update_tags:
            changed=True

        try:
            e_tags=dict((t.name, t.value) for t in vpc.get_all_tags(filters={'resource-id': vpc_id}))
            dhcp_list=vpc.get_all_dhcp_options()
            has_default=vpc.get_all_vpcs(filters={'dhcp-options-id' : 'default', 'vpc-id' : vpc_id})
        except Exception, e:
            e_msg=boto_exception(e)
            module.fail_json(msg=e_msg)

        dhcp_opts=None

        try:
            for opts in dhcp_list:
                if vpc.get_all_vpcs(filters={'dhcp-options-id' : opts, 'vpc-id' : vpc_id}):
                    dhcp_opts=opts
                    break
                else:
                    pass
        except Exception, e:
            e_msg=boto_exception(e)
            module.fail_json(msg=e_msg)

        if not dhcp_opts and has_default:
            dhcp_opts='default'

    if state == 'present':

        if not changed and already_exists:
            module.exit_json(changed=changed, vpc_id=vpc_id)
        elif changed:
            if update_dhcp:
                dhcp_opts=update_dhcp_opts(module, vpc, vpc_id, dhcp_id)
            if update_tags:
                e_tags=update_vpc_tags(module, vpc, vpc_id, tags, name)

            module.exit_json(changed=changed, name=name, dhcp_options_id=dhcp_opts, tags=e_tags)

        if not already_exists:
            try:
                vpc_id=str(vpc.create_vpc(cidr_block, instance_tenancy=tenancy)).split(':')[1]
                vpc.create_tags(vpc_id, dict(Name=name))
            except Exception, e:
                e_msg=boto_exception(e)
                module.fail_json(msg=e_msg)

            update_dhcp, update_tags=vpc_needs_update(module, vpc, vpc_id, dns_support, dns_hostnames, dhcp_id, tags)

            if update_dhcp:
                new_dhcp_opts=update_dhcp_opts(module, vpc, vpc_id, dhcp_id)
            if update_tags:
                new_tags=update_vpc_tags(module, vpc, vpc_id, tags, name)
                module.exit_json(changed=True, name=name, vpc_id=vpc_id, dhcp_options=new_dhcp_opts, tags=new_tags)
    elif state == 'absent':
        if already_exists:
            changed=True
            try:
                vpc.delete_vpc(vpc_id)
                module.exit_json(changed=changed, vpc_id=vpc_id)
            except Exception, e:
                e_msg=boto_exception(e)
                module.fail_json(msg="%s. You may want to use the ec2_vpc_subnet, ec2_vpc_igw, "
                "and/or ec2_vpc_rt modules to ensure the other components are absent." % e_msg)
        else:
            module.exit_json(msg="VPC is absent")
# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
