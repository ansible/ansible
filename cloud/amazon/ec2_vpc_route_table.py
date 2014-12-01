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
module: ec2_vpc_route_table
short_description: Configure route tables for AWS virtual private clouds
description:
    - Create or removes route tables from AWS virtual private clouds.'''
'''This module has a dependency on python-boto.
version_added: "1.8"
options:
  vpc_id:
    description:
      - "The VPC in which to create the route table."
    required: true
  route_table_id:
    description:
      - "The ID of the route table to update or delete."
    required: false
    default: null
  resource_tags:
    description:
      - 'A dictionary array of resource tags of the form: { tag1: value1,'''
''' tag2: value2 }. Tags in this list are used to uniquely identify route'''
''' tables within a VPC when the route_table_id is not supplied.
    required: false
    default: null
    aliases: []
    version_added: "1.6"
  routes:
    description:
      - List of routes in the route table. Routes are specified'''
''' as dicts containing the keys 'dest' and one of 'gateway_id','''
''' 'instance_id', 'interface_id', or 'vpc_peering_connection'.
    required: true
    aliases: []
  subnets:
    description:
      - An array of subnets to add to this route table. Subnets may either'''
''' be specified by subnet ID or by a CIDR such as '10.0.0.0/24'.
    required: true
    aliases: []
  wait:
    description:
      - wait for the VPC to be in state 'available' before returning
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    aliases: []
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 300
    aliases: []
  state:
    description:
      - Create or terminate the VPC
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

# Basic creation example:
- name: Set up public subnet route table
  local_action:
    module: ec2_vpc_route_table
    vpc_id: vpc-1245678
    region: us-west-1
    resource_tags:
      Name: Public
    subnets:
      - '{{jumpbox_subnet.subnet_id}}'
      - '{{frontend_subnet.subnet_id}}'
      - '{{vpn_subnet.subnet_id}}'
    routes:
      - dest: 0.0.0.0/0
        gateway_id: '{{igw.gateway_id}}'
  register: public_route_table

- name: Set up NAT-protected route table
  local_action:
    module: ec2_vpc_route_table
    vpc_id: vpc-1245678
    region: us-west-1
    resource_tags:
      - Name: Internal
    subnets:
      - '{{application_subnet.subnet_id}}'
      - '{{database_subnet.subnet_id}}'
      - '{{splunk_subnet.subnet_id}}'
    routes:
      - dest: 0.0.0.0/0
        instance_id: '{{nat.instance_id}}'
  register: nat_route_table
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


class AnsibleRouteTableException(Exception):
    pass


class AnsibleTagCreationException(AnsibleRouteTableException):
    pass


def get_resource_tags(vpc_conn, resource_id):
    return {t.name: t.value for t in
            vpc_conn.get_all_tags(filters={'resource-id': resource_id})}


def ensure_tags(vpc_conn, resource_id, tags, add_only, check_mode):
    try:
        cur_tags = get_resource_tags(vpc_conn, resource_id)
        if tags == cur_tags:
            return {'changed': False, 'tags': cur_tags}

        to_delete = {k: cur_tags[k] for k in cur_tags if k not in tags}
        if to_delete and not add_only:
            vpc_conn.delete_tags(resource_id, to_delete, dry_run=check_mode)

        to_add = {k: tags[k] for k in tags if k not in cur_tags}
        if to_add:
            vpc_conn.create_tags(resource_id, to_add, dry_run=check_mode)

        latest_tags = get_resource_tags(vpc_conn, resource_id)
        return {'changed': True, 'tags': latest_tags}
    except EC2ResponseError as e:
        raise AnsibleTagCreationException(
            'Unable to update tags for {0}, error: {1}'.format(resource_id, e))


def get_route_table_by_id(vpc_conn, vpc_id, route_table_id):
    route_tables = vpc_conn.get_all_route_tables(
        route_table_ids=[route_table_id], filters={'vpc_id': vpc_id})
    return route_tables[0] if route_tables else None


def get_route_table_by_tags(vpc_conn, vpc_id, tags):
    filters = {'vpc_id': vpc_id}
    filters.update(dict((('tag:{0}'.format(t), v)
                         for t, v in tags.iteritems())))
    route_tables = vpc_conn.get_all_route_tables(filters=filters)

    if not route_tables:
        return None
    elif len(route_tables) == 1:
        return route_tables[0]

    raise RouteTableException(
        'Found more than one route table based on the supplied tags, aborting')


def route_spec_matches_route(route_spec, route):
    key_attr_map = {
        'destination_cidr_block': 'destination_cidr_block',
        'gateway_id': 'gateway_id',
        'instance_id': 'instance_id',
        'interface_id': 'interface_id',
        'vpc_peering_connection_id': 'vpc_peering_connection_id',
    }
    for k in key_attr_map.iterkeys():
        if k in route_spec:
            if route_spec[k] != getattr(route, k):
                return False
    return True


def rename_key(d, old_key, new_key):
    d[new_key] = d[old_key]
    del d[old_key]


def index_of_matching_route(route_spec, routes_to_match):
    for i, route in enumerate(routes_to_match):
        if route_spec_matches_route(route_spec, route):
            return i


def ensure_routes(vpc_conn, route_table, route_specs, check_mode):
    routes_to_match = list(route_table.routes)
    route_specs_to_create = []
    for route_spec in route_specs:
        i = index_of_matching_route(route_spec, routes_to_match)
        if i is None:
            route_specs_to_create.append(route_spec)
        else:
            del routes_to_match[i]
    routes_to_delete = [r for r in routes_to_match
                        if r.gateway_id != 'local']

    changed = routes_to_delete or route_specs_to_create
    if changed:
        for route_spec in route_specs_to_create:
            vpc_conn.create_route(route_table.id,
                                  dry_run=check_mode,
                                  **route_spec)

        for route in routes_to_delete:
            vpc_conn.delete_route(route_table.id,
                                  route.destination_cidr_block,
                                  dry_run=check_mode)
    return {'changed': changed}


def get_subnet_by_cidr(vpc_conn, vpc_id, cidr):
    subnets = vpc_conn.get_all_subnets(
        filters={'cidr': cidr, 'vpc_id': vpc_id})
    if len(subnets) != 1:
        raise AnsibleRouteTableException(
            'Subnet with CIDR {0} has {1} matches'.format(cidr, len(subnets))
        )
    return subnets[0]


def get_subnet_by_id(vpc_conn, vpc_id, subnet_id):
    subnets = vpc_conn.get_all_subnets(filters={'subnet-id': subnet_id})
    if len(subnets) != 1:
        raise AnsibleRouteTableException(
            'Subnet with ID {0} has {1} matches'.format(
                subnet_id, len(subnets))
        )
    return subnets[0]


def ensure_subnet_association(vpc_conn, vpc_id, route_table_id, subnet_id,
                              check_mode):
    route_tables = vpc_conn.get_all_route_tables(
        filters={'association.subnet_id': subnet_id, 'vpc_id': vpc_id}
    )
    for route_table in route_tables:
        if route_table.id is None:
            continue
        for a in route_table.associations:
            if a.subnet_id == subnet_id:
                if route_table.id == route_table_id:
                    return {'changed': False, 'association_id': a.id}
                else:
                    if check_mode:
                        return {'changed': True}
                    vpc_conn.disassociate_route_table(a.id)

    association_id = vpc_conn.associate_route_table(route_table_id, subnet_id)
    return {'changed': True, 'association_id': association_id}


def ensure_subnet_associations(vpc_conn, vpc_id, route_table, subnets,
                               check_mode):
    current_association_ids = [a.id for a in route_table.associations]
    new_association_ids = []
    changed = False
    for subnet in subnets:
        result = ensure_subnet_association(
            vpc_conn, vpc_id, route_table.id, subnet.id, check_mode)
        changed = changed or result['changed']
        if changed and check_mode:
            return {'changed': True}
        new_association_ids.append(result['association_id'])

    to_delete = [a_id for a_id in current_association_ids
                 if a_id not in new_association_ids]

    for a_id in to_delete:
        changed = True
        vpc_conn.disassociate_route_table(a_id, dry_run=check_mode)

    return {'changed': changed}


def ensure_route_table_absent(vpc_conn, vpc_id, route_table_id, resource_tags,
                              check_mode):
    if route_table_id:
        route_table = get_route_table_by_id(vpc_conn, vpc_id, route_table_id)
    elif resource_tags:
        route_table = get_route_table_by_tags(vpc_conn, vpc_id, resource_tags)
    else:
        raise AnsibleRouteTableException(
            'must provide route_table_id or resource_tags')

    if route_table is None:
        return {'changed': False}

    vpc_conn.delete_route_table(route_table.id, dry_run=check_mode)
    return {'changed': True}


def ensure_route_table_present(vpc_conn, vpc_id, route_table_id, resource_tags,
                               routes, subnets, check_mode):
    changed = False
    tags_valid = False
    if route_table_id:
        route_table = get_route_table_by_id(vpc_conn, vpc_id, route_table_id)
    elif resource_tags:
        route_table = get_route_table_by_tags(vpc_conn, vpc_id, resource_tags)
        tags_valid = route_table is not None
    else:
        raise AnsibleRouteTableException(
            'must provide route_table_id or resource_tags')

    if check_mode and route_table is None:
        return {'changed': True}

    if route_table is None:
        try:
            route_table = vpc_conn.create_route_table(vpc_id)
        except EC2ResponseError as e:
            raise AnsibleRouteTableException(
                'Unable to create route table {0}, error: {1}'
                .format(route_table_id or resource_tags, e)
            )

    if not tags_valid and resource_tags is not None:
        result = ensure_tags(vpc_conn, route_table.id, resource_tags,
                             add_only=True, check_mode=check_mode)
        changed = changed or result['changed']

    if routes is not None:
        try:
            result = ensure_routes(vpc_conn, route_table, routes, check_mode)
            changed = changed or result['changed']
        except EC2ResponseError as e:
            raise AnsibleRouteTableException(
                'Unable to ensure routes for route table {0}, error: {1}'
                .format(route_table, e)
            )

    if subnets:
        associated_subnets = []
        try:
            for subnet_name in subnets:
                if ('.' in subnet_name) and ('/' in subnet_name):
                    subnet = get_subnet_by_cidr(vpc_conn, vpc_id, subnet_name)
                else:
                    subnet = get_subnet_by_id(vpc_conn, vpc_id, subnet_name)
                associated_subnets.append(subnet)
        except EC2ResponseError as e:
            raise AnsibleRouteTableException(
                'Unable to find subnets for route table {0}, error: {1}'
                .format(route_table, e)
            )

        try:
            result = ensure_subnet_associations(
                vpc_conn, vpc_id, route_table, associated_subnets, check_mode)
            changed = changed or result['changed']
        except EC2ResponseError as e:
            raise AnsibleRouteTableException(
                'Unable to associate subnets for route table {0}, error: {1}'
                .format(route_table, e)
            )

    return {
        'changed': changed,
        'route_table_id': route_table.id,
    }


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update({
        'vpc_id': {'required': True},
        'route_table_id': {'required': False},
        'resource_tags': {'type': 'dict', 'required': False},
        'routes': {'type': 'list', 'required': False},
        'subnets': {'type': 'list', 'required': False},
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
    route_table_id = module.params.get('route_table_id')
    resource_tags = module.params.get('resource_tags')

    routes = module.params.get('routes')
    for route_spec in routes:
        rename_key(route_spec, 'dest', 'destination_cidr_block')

    subnets = module.params.get('subnets')
    state = module.params.get('state', 'present')

    try:
        if state == 'present':
            result = ensure_route_table_present(
                vpc_conn, vpc_id, route_table_id, resource_tags,
                routes, subnets, module.check_mode
            )
        elif state == 'absent':
            result = ensure_route_table_absent(
                vpc_conn, vpc_id, route_table_id, resource_tags,
                module.check_mode
            )
    except AnsibleRouteTableException as e:
        module.fail_json(msg=str(e))

    module.exit_json(**result)

from ansible.module_utils.basic import *  # noqa
from ansible.module_utils.ec2 import *  # noqa

if __name__ == '__main__':
    main()
