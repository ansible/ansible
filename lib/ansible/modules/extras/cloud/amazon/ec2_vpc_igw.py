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
module: ec2_vpc_igw
short_description: configure AWS virtual private clouds
description:
    - Create or terminates AWS internat gateway in a virtual private cloud. '''
'''This module has a dependency on python-boto.
version_added: "1.8"
options:
  vpc_id:
    description:
      - "The VPC ID for which to create or remove the Internet Gateway."
    required: true
  state:
    description:
      - Create or terminate the IGW
    required: true
    default: present
    aliases: []
  region:
    description:
      - region in which the resource exists.
    required: false
    default: null
    aliases: ['aws_region', 'ec2_region']
  aws_secret_key:
    description:
      - AWS secret key. If not set then the value of the AWS_SECRET_KEY'''
''' environment variable is used.
    required: false
    default: None
    aliases: ['ec2_secret_key', 'secret_key' ]
  aws_access_key:
    description:
      - AWS access key. If not set then the value of the AWS_ACCESS_KEY'''
''' environment variable is used.
    required: false
    default: None
    aliases: ['ec2_access_key', 'access_key' ]
  validate_certs:
    description:
      - When set to "no", SSL certificates will not be validated for boto'''
''' versions >= 2.6.0.
    required: false
    default: "yes"
    choices: ["yes", "no"]
    aliases: []
    version_added: "1.5"

requirements: [ "boto" ]
author: Robert Estelle
'''

EXAMPLES = '''
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.

# Ensure that the VPC has an Internet Gateway.
# The Internet Gateway ID is can be accessed via {{igw.gateway_id}} for use
# in setting up NATs etc.
      local_action:
        module: ec2_vpc_igw
        vpc_id: {{vpc.vpc_id}}
        region: {{vpc.vpc.region}}
        state: present
      register: igw
'''


import sys  # noqa

try:
    import boto.ec2
    import boto.vpc
    from boto.exception import EC2ResponseError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False
    if __name__ != '__main__':
        raise


class AnsibleIGWException(Exception):
    pass


def ensure_igw_absent(vpc_conn, vpc_id, check_mode):
    igws = vpc_conn.get_all_internet_gateways(
        filters={'attachment.vpc-id': vpc_id})

    if not igws:
        return {'changed': False}

    if check_mode:
        return {'changed': True}

    for igw in igws:
        try:
            vpc_conn.detach_internet_gateway(igw.id, vpc_id)
            vpc_conn.delete_internet_gateway(igw.id)
        except EC2ResponseError as e:
            raise AnsibleIGWException(
                'Unable to delete Internet Gateway, error: {0}'.format(e))

    return {'changed': True}


def ensure_igw_present(vpc_conn, vpc_id, check_mode):
    igws = vpc_conn.get_all_internet_gateways(
        filters={'attachment.vpc-id': vpc_id})

    if len(igws) > 1:
        raise AnsibleIGWException(
            'EC2 returned more than one Internet Gateway for VPC {0}, aborting'
            .format(vpc_id))

    if igws:
        return {'changed': False, 'gateway_id': igws[0].id}
    else:
        if check_mode:
            return {'changed': True, 'gateway_id': None}

        try:
            igw = vpc_conn.create_internet_gateway()
            vpc_conn.attach_internet_gateway(igw.id, vpc_id)
            return {'changed': True, 'gateway_id': igw.id}
        except EC2ResponseError as e:
            raise AnsibleIGWException(
                'Unable to create Internet Gateway, error: {0}'.format(e))


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update({
        'vpc_id': {'required': True},
        'state': {'choices': ['present', 'absent'], 'default': 'present'},
    })
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    if not HAS_BOTO:
        module.fail_json(msg='boto is required for this module')

    ec2_url, aws_access_key, aws_secret_key, region = get_ec2_creds(module)
    if not region:
        module.fail_json(msg='Region must be specified')

    try:
        vpc_conn = boto.vpc.connect_to_region(
            region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
    except boto.exception.NoAuthHandlerFound as e:
        module.fail_json(msg=str(e))

    vpc_id = module.params.get('vpc_id')
    state = module.params.get('state', 'present')

    try:
        if state == 'present':
            result = ensure_igw_present(vpc_conn, vpc_id,
                                        check_mode=module.check_mode)
        elif state == 'absent':
            result = ensure_igw_absent(vpc_conn, vpc_id,
                                       check_mode=module.check_mode)
    except AnsibleIGWException as e:
        module.fail_json(msg=str(e))

    module.exit_json(**result)

from ansible.module_utils.basic import *  # noqa
from ansible.module_utils.ec2 import *  # noqa

if __name__ == '__main__':
    main()
