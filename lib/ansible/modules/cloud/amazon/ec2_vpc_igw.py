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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'curated'}


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
  tags:
    description:
      - "A dict of tags to apply to the internet gateway. Any tags currently applied to the internet gateway and not present here will be removed."
    required: false
    default: null
    aliases: [ 'resource_tags' ]
    version_added: "2.4"
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

RETURN = '''
changed:
  description: If any changes have been made to the Internet Gateway.
  type: bool
  returned: always
  sample:
    changed: false
gateway_id:
  description: The unique identifier for the Internet Gateway.
  type: str
  returned: I(state=present)
  sample:
    gateway_id: "igw-XXXXXXXX"
tags:
  description: The tags associated the Internet Gateway.
  type: dict
  returned: I(state=present)
  sample:
    tags:
      "Ansible": "Test"
vpc_id:
  description: The VPC ID associated with the Internet Gateway.
  type: str
  returned: I(state=present)
  sample:
    vpc_id: "vpc-XXXXXXXX"
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
from ansible.module_utils.six import string_types


class AnsibleIGWException(Exception):
    pass


def get_igw_info(igw):
    return {'gateway_id': igw.id,
            'tags': igw.tags,
            'vpc_id': igw.vpc_id
            }


def get_resource_tags(vpc_conn, resource_id):
    return dict((t.name, t.value) for t in
                vpc_conn.get_all_tags(filters={'resource-id': resource_id}))


def ensure_tags(vpc_conn, resource_id, tags, add_only, check_mode):
    try:
        cur_tags = get_resource_tags(vpc_conn, resource_id)
        if cur_tags == tags:
            return {'changed': False, 'tags': cur_tags}

        if check_mode:
            latest_check_mode_tags = cur_tags

        to_delete = dict((k, cur_tags[k]) for k in cur_tags if k not in tags)
        if to_delete and not add_only:
            if check_mode:
                # just overwriting latest_check_mode_tags instead of deleting keys
                latest_check_mode_tags = dict((k, cur_tags[k]) for k in cur_tags if k not in to_delete)
            else:
                vpc_conn.delete_tags(resource_id, to_delete)

        to_add = dict((k, tags[k]) for k in tags if k not in cur_tags or cur_tags[k] != tags[k])
        if to_add:
            if check_mode:
                latest_check_mode_tags.update(to_add)
            else:
                vpc_conn.create_tags(resource_id, to_add)

        if check_mode:
            return {'changed': True, 'tags': latest_check_mode_tags}
        latest_tags = get_resource_tags(vpc_conn, resource_id)
        return {'changed': True, 'tags': latest_tags}
    except EC2ResponseError as e:
        raise AnsibleIGWException(
            'Unable to update tags for {0}, error: {1}'.format(resource_id, e))


def get_matching_igw(vpc_conn, vpc_id):
    igws = vpc_conn.get_all_internet_gateways(filters={'attachment.vpc-id': vpc_id})
    if len(igws) > 1:
        raise AnsibleIGWException(
            'EC2 returned more than one Internet Gateway for VPC {0}, aborting'
            .format(vpc_id))
    return igws[0] if igws else None


def ensure_igw_absent(vpc_conn, vpc_id, check_mode):
    igw = get_matching_igw(vpc_conn, vpc_id)
    if igw is None:
        return {'changed': False}

    if check_mode:
        return {'changed': True}

    try:
        vpc_conn.detach_internet_gateway(igw.id, vpc_id)
        vpc_conn.delete_internet_gateway(igw.id)
    except EC2ResponseError as e:
        raise AnsibleIGWException(
            'Unable to delete Internet Gateway, error: {0}'.format(e))

    return {'changed': True}


def ensure_igw_present(vpc_conn, vpc_id, tags, check_mode):
    igw = get_matching_igw(vpc_conn, vpc_id)
    changed = False
    if igw is None:
        if check_mode:
            return {'changed': True, 'gateway_id': None}

        try:
            igw = vpc_conn.create_internet_gateway()
            vpc_conn.attach_internet_gateway(igw.id, vpc_id)
            changed = True
        except EC2ResponseError as e:
            raise AnsibleIGWException(
                'Unable to create Internet Gateway, error: {0}'.format(e))

    igw.vpc_id = vpc_id

    if tags != igw.tags:
        if check_mode:
            check_mode_tags = ensure_tags(vpc_conn, igw.id, tags, False, check_mode)
            igw_info = get_igw_info(igw)
            igw_info.get('tags', {}).update(check_mode_tags.get('tags', {}))
            return {'changed': True, 'gateway': igw_info}
        ensure_tags(vpc_conn, igw.id, tags, False, check_mode)
        igw.tags = tags
        changed = True

    igw_info = get_igw_info(igw)

    return {
        'changed': changed,
        'gateway': igw_info
    }


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            vpc_id=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
            tags=dict(default=dict(), required=False, type='dict', aliases=['resource_tags'])
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
    tags = module.params.get('tags')

    nonstring_tags = [k for k, v in tags.items() if not isinstance(v, string_types)]
    if nonstring_tags:
        module.fail_json(msg='One or more tags contain non-string values: {0}'.format(nonstring_tags))

    try:
        if state == 'present':
            result = ensure_igw_present(connection, vpc_id, tags, check_mode=module.check_mode)
        elif state == 'absent':
            result = ensure_igw_absent(connection, vpc_id, check_mode=module.check_mode)
    except AnsibleIGWException as e:
        module.fail_json(msg=str(e))

    module.exit_json(changed=result['changed'], **result.get('gateway', {}))


if __name__ == '__main__':
    main()
