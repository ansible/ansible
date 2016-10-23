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
module: ec2_vpc_route_table
short_description: Manage route tables for AWS virtual private clouds
description:
    - Manage route tables for AWS virtual private clouds
version_added: "2.0"
author: Robert Estelle (@erydo), Rob White (@wimnat)
options:
  lookup:
    description:
      - "Look up route table by either tags or by route table ID. Non-unique tag lookup will fail. If no tags are specifed then no lookup for an existing route table is performed and a new route table will be created. To change tags of a route table, you must look up by id."
    required: false
    default: tag
    choices: [ 'tag', 'id' ]
  propagating_vgw_ids:
    description:
      - "Enable route propagation from virtual gateways specified by ID."
    default: None
    required: false
  route_table_id:
    description:
      - "The ID of the route table to update or delete."
    required: false
    default: null
  routes:
    description:
      - "List of routes in the route table.
        Routes are specified as dicts containing the keys 'dest' and one of 'gateway_id',
        'instance_id', 'interface_id', or 'vpc_peering_connection_id'.
        If 'gateway_id' is specified, you can refer to the VPC's IGW by using the value 'igw'. Routes are required for present states."
    required: false
    default: None
  state:
    description:
      - "Create or destroy the VPC route table"
    required: false
    default: present
    choices: [ 'present', 'absent' ]
  subnets:
    description:
      - "An array of subnets to add to this route table. Subnets may be specified by either subnet ID, Name tag, or by a CIDR such as '10.0.0.0/24'."
    required: true
  tags:
    description:
      - "A dictionary of resource tags of the form: { tag1: value1, tag2: value2 }. Tags are used to uniquely identify route tables within a VPC when the route_table_id is not supplied."
    required: false
    default: null
    aliases: [ "resource_tags" ]
  vpc_id:
    description:
      - "VPC ID of the VPC in which to create the route table."
    required: true
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Basic creation example:
- name: Set up public subnet route table
  ec2_vpc_route_table:
    vpc_id: vpc-1245678
    region: us-west-1
    tags:
      Name: Public
    subnets:
      - "{{ jumpbox_subnet.subnet.id }}"
      - "{{ frontend_subnet.subnet.id }}"
      - "{{ vpn_subnet.subnet_id }}"
    routes:
      - dest: 0.0.0.0/0
        gateway_id: "{{ igw.gateway_id }}"
  register: public_route_table

- name: Set up NAT-protected route table
  ec2_vpc_route_table:
    vpc_id: vpc-1245678
    region: us-west-1
    tags:
      Name: Internal
    subnets:
      - "{{ application_subnet.subnet.id }}"
      - 'Database Subnet'
      - '10.0.0.0/8'
    routes:
      - dest: 0.0.0.0/0
        instance_id: "{{ nat.instance_id }}"
  register: nat_route_table

'''

import re

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


class AnsibleRouteTableException(Exception):
    pass


class AnsibleIgwSearchException(AnsibleRouteTableException):
    pass


class AnsibleTagCreationException(AnsibleRouteTableException):
    pass


class AnsibleSubnetSearchException(AnsibleRouteTableException):
    pass

CIDR_RE = re.compile('^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$')
SUBNET_RE = re.compile('^subnet-[A-z0-9]+$')
ROUTE_TABLE_RE = re.compile('^rtb-[A-z0-9]+$')


def find_subnets(vpc_conn, vpc_id, identified_subnets):
    """
    Finds a list of subnets, each identified either by a raw ID, a unique
    'Name' tag, or a CIDR such as 10.0.0.0/8.

    Note that this function is duplicated in other ec2 modules, and should
    potentially be moved into potentially be moved into a shared module_utils
    """
    subnet_ids = []
    subnet_names = []
    subnet_cidrs = []
    for subnet in (identified_subnets or []):
        if re.match(SUBNET_RE, subnet):
            subnet_ids.append(subnet)
        elif re.match(CIDR_RE, subnet):
            subnet_cidrs.append(subnet)
        else:
            subnet_names.append(subnet)

    subnets_by_id = []
    if subnet_ids:
        subnets_by_id = vpc_conn.get_all_subnets(
            subnet_ids, filters={'vpc_id': vpc_id})

        for subnet_id in subnet_ids:
            if not any(s.id == subnet_id for s in subnets_by_id):
                raise AnsibleSubnetSearchException(
                    'Subnet ID "{0}" does not exist'.format(subnet_id))

    subnets_by_cidr = []
    if subnet_cidrs:
        subnets_by_cidr = vpc_conn.get_all_subnets(
            filters={'vpc_id': vpc_id, 'cidr': subnet_cidrs})

        for cidr in subnet_cidrs:
            if not any(s.cidr_block == cidr for s in subnets_by_cidr):
                raise AnsibleSubnetSearchException(
                    'Subnet CIDR "{0}" does not exist'.format(cidr))

    subnets_by_name = []
    if subnet_names:
        subnets_by_name = vpc_conn.get_all_subnets(
            filters={'vpc_id': vpc_id, 'tag:Name': subnet_names})

        for name in subnet_names:
            matching_count = len([1 for s in subnets_by_name if s.tags.get('Name') == name])
            if matching_count == 0:
                raise AnsibleSubnetSearchException(
                    'Subnet named "{0}" does not exist'.format(name))
            elif matching_count > 1:
                raise AnsibleSubnetSearchException(
                    'Multiple subnets named "{0}"'.format(name))

    return subnets_by_id + subnets_by_cidr + subnets_by_name


def find_igw(vpc_conn, vpc_id):
    """
    Finds the Internet gateway for the given VPC ID.

    Raises an AnsibleIgwSearchException if either no IGW can be found, or more
    than one found for the given VPC.

    Note that this function is duplicated in other ec2 modules, and should
    potentially be moved into potentially be moved into a shared module_utils
    """
    igw = vpc_conn.get_all_internet_gateways(
        filters={'attachment.vpc-id': vpc_id})

    if not igw:
        raise AnsibleIgwSearchException('No IGW found for VPC {0}'.
                                         format(vpc_id))
    elif len(igw) == 1:
        return igw[0].id
    else:
        raise AnsibleIgwSearchException('Multiple IGWs found for VPC {0}'.
                                        format(vpc_id))


def get_resource_tags(vpc_conn, resource_id):
    return dict((t.name, t.value) for t in
                vpc_conn.get_all_tags(filters={'resource-id': resource_id}))


def tags_match(match_tags, candidate_tags):
    return all((k in candidate_tags and candidate_tags[k] == v
                for k, v in match_tags.iteritems()))


def ensure_tags(vpc_conn, resource_id, tags, add_only, check_mode):
    try:
        cur_tags = get_resource_tags(vpc_conn, resource_id)
        if tags == cur_tags:
            return {'changed': False, 'tags': cur_tags}

        to_delete = dict((k, cur_tags[k]) for k in cur_tags if k not in tags)
        if to_delete and not add_only:
            vpc_conn.delete_tags(resource_id, to_delete, dry_run=check_mode)

        to_add = dict((k, tags[k]) for k in tags if k not in cur_tags)
        if to_add:
            vpc_conn.create_tags(resource_id, to_add, dry_run=check_mode)

        latest_tags = get_resource_tags(vpc_conn, resource_id)
        return {'changed': True, 'tags': latest_tags}
    except EC2ResponseError as e:
        raise AnsibleTagCreationException(
            'Unable to update tags for {0}, error: {1}'.format(resource_id, e))


def get_route_table_by_id(vpc_conn, vpc_id, route_table_id):

    route_table = None
    route_tables = vpc_conn.get_all_route_tables(route_table_ids=[route_table_id], filters={'vpc_id': vpc_id})
    if route_tables:
        route_table = route_tables[0]

    return route_table

def get_route_table_by_tags(vpc_conn, vpc_id, tags):

    count = 0
    route_table = None
    route_tables = vpc_conn.get_all_route_tables(filters={'vpc_id': vpc_id})
    for table in route_tables:
        this_tags = get_resource_tags(vpc_conn, table.id)
        if tags_match(tags, this_tags):
            route_table = table
            count +=1

    if count > 1:
        raise RuntimeError("Tags provided do not identify a unique route table")
    else:
        return route_table


def route_spec_matches_route(route_spec, route):
    key_attr_map = {
        'destination_cidr_block': 'destination_cidr_block',
        'gateway_id': 'gateway_id',
        'instance_id': 'instance_id',
        'interface_id': 'interface_id',
        'vpc_peering_connection_id': 'vpc_peering_connection_id',
    }

    # This is a workaround to catch managed NAT gateways as they do not show
    # up in any of the returned values when describing route tables.
    # The caveat of doing it this way is that if there was an existing
    # route for another nat gateway in this route table there is not a way to
    # change to another nat gateway id. Long term solution would be to utilise
    # boto3 which is a very big task for this module or to update boto.
    if route_spec.get('gateway_id') and 'nat-' in route_spec['gateway_id']:
        if route.destination_cidr_block == route_spec['destination_cidr_block']:
            if all((not route.gateway_id, not route.instance_id, not route.interface_id, not route.vpc_peering_connection_id)):
                return True

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


def ensure_routes(vpc_conn, route_table, route_specs, propagating_vgw_ids,
                  check_mode):
    routes_to_match = list(route_table.routes)
    route_specs_to_create = []
    for route_spec in route_specs:
        i = index_of_matching_route(route_spec, routes_to_match)
        if i is None:
            route_specs_to_create.append(route_spec)
        else:
            del routes_to_match[i]

    # NOTE: As of boto==2.38.0, the origin of a route is not available
    # (for example, whether it came from a gateway with route propagation
    # enabled). Testing for origin == 'EnableVgwRoutePropagation' is more
    # correct than checking whether the route uses a propagating VGW.
    # The current logic will leave non-propagated routes using propagating
    # VGWs in place.
    routes_to_delete = []
    for r in routes_to_match:
        if r.gateway_id:
            if r.gateway_id != 'local' and not r.gateway_id.startswith('vpce-'):
                if not propagating_vgw_ids or r.gateway_id not in propagating_vgw_ids:
                    routes_to_delete.append(r)
        else:
            routes_to_delete.append(r)

    changed = bool(routes_to_delete or route_specs_to_create)
    if changed:
        for route in routes_to_delete:
            try:
                vpc_conn.delete_route(route_table.id,
                                      route.destination_cidr_block,
                                      dry_run=check_mode)
            except EC2ResponseError as e:
                if e.error_code == 'DryRunOperation':
                    pass

        for route_spec in route_specs_to_create:
            try:
                vpc_conn.create_route(route_table.id,
                                      dry_run=check_mode,
                                      **route_spec)
            except EC2ResponseError as e:
                if e.error_code == 'DryRunOperation':
                    pass

    return {'changed': bool(changed)}


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


def ensure_propagation(vpc_conn, route_table, propagating_vgw_ids,
                       check_mode):

    # NOTE: As of boto==2.38.0, it is not yet possible to query the existing
    # propagating gateways. However, EC2 does support this as shown in its API
    # documentation. For now, a reasonable proxy for this is the presence of
    # propagated routes using the gateway in the route table. If such a route
    # is found, propagation is almost certainly enabled.
    changed = False
    for vgw_id in propagating_vgw_ids:
        for r in list(route_table.routes):
            if r.gateway_id == vgw_id:
                return {'changed': False}

        changed = True
        vpc_conn.enable_vgw_route_propagation(route_table.id,
                                              vgw_id,
                                              dry_run=check_mode)

    return {'changed': changed}


def ensure_route_table_absent(connection, module):

    lookup = module.params.get('lookup')
    route_table_id = module.params.get('route_table_id')
    tags = module.params.get('tags')
    vpc_id = module.params.get('vpc_id')

    if lookup == 'tag':
        if tags is not None:
            try:
                route_table = get_route_table_by_tags(connection, vpc_id, tags)
            except EC2ResponseError as e:
                module.fail_json(msg=e.message)
            except RuntimeError as e:
                module.fail_json(msg=e.args[0])
        else:
            route_table = None
    elif lookup == 'id':
        try:
            route_table = get_route_table_by_id(connection, vpc_id, route_table_id)
        except EC2ResponseError as e:
            module.fail_json(msg=e.message)

    if route_table is None:
        return {'changed': False}

    try:
        connection.delete_route_table(route_table.id, dry_run=module.check_mode)
    except EC2ResponseError as e:
        if e.error_code == 'DryRunOperation':
            pass
        else:
            module.fail_json(msg=e.message)

    return {'changed': True}


def get_route_table_info(route_table):

    # Add any routes to array
    routes = []
    for route in route_table.routes:
        routes.append(route.__dict__)

    route_table_info = { 'id': route_table.id,
                         'routes': routes,
                         'tags': route_table.tags,
                         'vpc_id': route_table.vpc_id
                       }

    return route_table_info


def create_route_spec(connection, module, vpc_id):
    routes = module.params.get('routes')

    for route_spec in routes:
        rename_key(route_spec, 'dest', 'destination_cidr_block')

        if route_spec.get('gateway_id') and route_spec['gateway_id'].lower() == 'igw':
            igw = find_igw(connection, vpc_id)
            route_spec['gateway_id'] = igw

    return routes


def ensure_route_table_present(connection, module):

    lookup = module.params.get('lookup')
    propagating_vgw_ids = module.params.get('propagating_vgw_ids')
    route_table_id = module.params.get('route_table_id')
    subnets = module.params.get('subnets')
    tags = module.params.get('tags')
    vpc_id = module.params.get('vpc_id')
    try:
        routes = create_route_spec(connection, module, vpc_id)
    except AnsibleIgwSearchException as e:
        module.fail_json(msg=e[0])

    changed = False
    tags_valid = False

    if lookup == 'tag':
        if tags is not None:
            try:
                route_table = get_route_table_by_tags(connection, vpc_id, tags)
            except EC2ResponseError as e:
                module.fail_json(msg=e.message)
            except RuntimeError as e:
                module.fail_json(msg=e.args[0])
        else:
            route_table = None
    elif lookup == 'id':
        try:
            route_table = get_route_table_by_id(connection, vpc_id, route_table_id)
        except EC2ResponseError as e:
            module.fail_json(msg=e.message)

    # If no route table returned then create new route table
    if route_table is None:
        try:
            route_table = connection.create_route_table(vpc_id, module.check_mode)
            changed = True
        except EC2ResponseError as e:
            if e.error_code == 'DryRunOperation':
                module.exit_json(changed=True)

            module.fail_json(msg=e.message)

    if routes is not None:
        try:
            result = ensure_routes(connection, route_table, routes, propagating_vgw_ids, module.check_mode)
            changed = changed or result['changed']
        except EC2ResponseError as e:
            module.fail_json(msg=e.message)

    if propagating_vgw_ids is not None:
        result = ensure_propagation(connection, route_table,
                                    propagating_vgw_ids,
                                    check_mode=module.check_mode)
        changed = changed or result['changed']

    if not tags_valid and tags is not None:
        result = ensure_tags(connection, route_table.id, tags,
                             add_only=True, check_mode=module.check_mode)
        changed = changed or result['changed']

    if subnets:
        associated_subnets = []
        try:
            associated_subnets = find_subnets(connection, vpc_id, subnets)
        except EC2ResponseError as e:
            raise AnsibleRouteTableException(
                'Unable to find subnets for route table {0}, error: {1}'
                .format(route_table, e)
            )

        try:
            result = ensure_subnet_associations(connection, vpc_id, route_table, associated_subnets, module.check_mode)
            changed = changed or result['changed']
        except EC2ResponseError as e:
            raise AnsibleRouteTableException(
                'Unable to associate subnets for route table {0}, error: {1}'
                .format(route_table, e)
            )

    module.exit_json(changed=changed, route_table=get_route_table_info(route_table))


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            lookup = dict(default='tag', required=False, choices=['tag', 'id']),
            propagating_vgw_ids = dict(default=None, required=False, type='list'),
            route_table_id = dict(default=None, required=False),
            routes = dict(default=[], required=False, type='list'),
            state = dict(default='present', choices=['present', 'absent']),
            subnets = dict(default=None, required=False, type='list'),
            tags = dict(default=None, required=False, type='dict', aliases=['resource_tags']),
            vpc_id = dict(default=None, required=True)
        )
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

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

    lookup = module.params.get('lookup')
    route_table_id = module.params.get('route_table_id')
    state = module.params.get('state', 'present')

    if lookup == 'id' and route_table_id is None:
        module.fail_json("You must specify route_table_id if lookup is set to id")

    try:
        if state == 'present':
            result = ensure_route_table_present(connection, module)
        elif state == 'absent':
            result = ensure_route_table_absent(connection, module)
    except AnsibleRouteTableException as e:
        module.fail_json(msg=str(e))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
