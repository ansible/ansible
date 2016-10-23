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
module: ec2_vpc_igw
short_description: Manage an AWS VPC Internet gateway
description:
    - Manage an AWS VPC Internet gateway
version_added: "2.0"
author: Robert Estelle (@erydo)
options:
  vpc_id:
    description:
      - The VPC ID for the VPC in which to manage the Internet Gateway.
    required: true
    default: null
  state:
    description:
      - Create or terminate the IGW
    required: false
    default: present
    choices: [ 'present', 'absent' ]
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Ensure that the VPC has an Internet Gateway.
# The Internet Gateway ID is can be accessed via {{igw.gateway_id}} for use in setting up NATs etc.
ec2_vpc_igw:
  vpc_id: vpc-abcdefgh
  state: present
register: igw

'''

try:
    import boto.ec2
    import boto.vpc
    from boto.exception import EC2ResponseError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False
    if __name__ != '__main__':
        raise

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import AnsibleAWSError, connect_to_aws, ec2_argument_spec, get_aws_connection_info


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
    argument_spec.update(
        dict(
            vpc_id = dict(required=True),
            state = dict(default='present', choices=['present', 'absent'])
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto is required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region:
        try:
            connection = connect_to_aws(boto.vpc, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

    vpc_id = module.params.get('vpc_id')
    state = module.params.get('state', 'present')

    try:
        if state == 'present':
            result = ensure_igw_present(connection, vpc_id, check_mode=module.check_mode)
        elif state == 'absent':
            result = ensure_igw_absent(connection, vpc_id, check_mode=module.check_mode)
    except AnsibleIGWException as e:
        module.fail_json(msg=str(e))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
