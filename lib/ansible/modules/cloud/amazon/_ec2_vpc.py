#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
---
module: ec2_vpc
short_description: configure AWS virtual private clouds
description:
    - Create or terminates AWS virtual private clouds.  This module has a dependency on python-boto.
version_added: "1.4"
deprecated: >-
  Deprecated in 2.3. Use M(ec2_vpc_net) along with supporting modules including
  M(ec2_vpc_igw), M(ec2_vpc_route_table), M(ec2_vpc_subnet), M(ec2_vpc_dhcp_options),
  M(ec2_vpc_nat_gateway), M(ec2_vpc_nacl).
options:
  cidr_block:
    description:
      - "The cidr block representing the VPC, e.g. C(10.0.0.0/16), required when I(state=present)."
    required: false
  instance_tenancy:
    description:
      - "The supported tenancy options for instances launched into the VPC."
    required: false
    default: "default"
    choices: [ "default", "dedicated" ]
  dns_support:
    description:
      - Toggles the "Enable DNS resolution" flag.
    required: false
    default: "yes"
    choices: [ "yes", "no" ]
  dns_hostnames:
    description:
      - Toggles the "Enable DNS hostname support for instances" flag.
    required: false
    default: "yes"
    choices: [ "yes", "no" ]
  subnets:
    description:
      - 'A dictionary array of subnets to add of the form C({ cidr: ..., az: ... , resource_tags: ... }).'
      - Where C(az) is the desired availability zone of the subnet, optional.
      - 'Tags C(resource_tags) use dictionary form C({ "Environment":"Dev", "Tier":"Web", ...}), optional.'
      - C(resource_tags) see resource_tags for VPC below. The main difference is subnet tags not specified here will be deleted.
      - All VPC subnets not in this list will be removed as well.
      - As of 1.8, if the subnets parameter is not specified, no existing subnets will be modified.'
    required: false
    default: null
  vpc_id:
    description:
      - A VPC id to terminate when I(state=absent).
    required: false
    default: null
  resource_tags:
    description:
      - 'A dictionary array of resource tags of the form C({ tag1: value1, tag2: value2 }).
      - Tags in this list are used in conjunction with CIDR block to uniquely identify a VPC in lieu of vpc_id. Therefore,
        if CIDR/Tag combination does not exist, a new VPC will be created.  VPC tags not on this list will be ignored. Prior to 1.7,
        specifying a resource tag was optional.'
    required: true
    version_added: "1.6"
  internet_gateway:
    description:
      - Toggle whether there should be an Internet gateway attached to the VPC.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  route_tables:
    description:
      - >
        A dictionary array of route tables to add of the form:
        C({ subnets: [172.22.2.0/24, 172.22.3.0/24,], routes: [{ dest: 0.0.0.0/0, gw: igw},], resource_tags: ... }). Where the subnets list is
        those subnets the route table should be associated with, and the routes list is a list of routes to be in the table.  The special keyword
        for the gw of igw specifies that you should the route should go through the internet gateway attached to the VPC. gw also accepts instance-ids,
        interface-ids, and vpc-peering-connection-ids in addition igw. resource_tags is optional and uses dictionary form: C({ "Name": "public", ... }).
        This module is currently unable to affect the "main" route table due to some limitations in boto, so you must explicitly define the associated
        subnets or they will be attached to the main table implicitly. As of 1.8, if the route_tables parameter is not specified, no existing routes
        will be modified.
    required: false
    default: null
  wait:
    description:
      - Wait for the VPC to be in state 'available' before returning.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  wait_timeout:
    description:
      - How long before wait gives up, in seconds.
    default: 300
  state:
    description:
      - Create or terminate the VPC.
    required: true
    choices: [ "present", "absent" ]
author: "Carson Gee (@carsongee)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.

# Basic creation example:
    - ec2_vpc:
        state: present
        cidr_block: 172.23.0.0/16
        resource_tags: { "Environment":"Development" }
        region: us-west-2
# Full creation example with subnets and optional availability zones.
# The absence or presence of subnets deletes or creates them respectively.
    - ec2_vpc:
        state: present
        cidr_block: 172.22.0.0/16
        resource_tags: { "Environment":"Development" }
        subnets:
          - cidr: 172.22.1.0/24
            az: us-west-2c
            resource_tags: { "Environment":"Dev", "Tier" : "Web" }
          - cidr: 172.22.2.0/24
            az: us-west-2b
            resource_tags: { "Environment":"Dev", "Tier" : "App" }
          - cidr: 172.22.3.0/24
            az: us-west-2a
            resource_tags: { "Environment":"Dev", "Tier" : "DB" }
        internet_gateway: True
        route_tables:
          - subnets:
              - 172.22.2.0/24
              - 172.22.3.0/24
            routes:
              - dest: 0.0.0.0/0
                gw: igw
          - subnets:
              - 172.22.1.0/24
            routes:
              - dest: 0.0.0.0/0
                gw: igw
        region: us-west-2
      register: vpc

# Removal of a VPC by id
    - ec2_vpc:
        state: absent
        vpc_id: vpc-aaaaaaa
        region: us-west-2
# If you have added elements not managed by this module, e.g. instances, NATs, etc then
# the delete will fail until those dependencies are removed.
'''

import time

try:
    import boto
    import boto.ec2
    import boto.vpc
    from boto.exception import EC2ResponseError

    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import connect_to_aws, ec2_argument_spec, get_aws_connection_info


def get_vpc_info(vpc):
    """
    Retrieves vpc information from an instance
    ID and returns it as a dictionary
    """

    return({
        'id': vpc.id,
        'cidr_block': vpc.cidr_block,
        'dhcp_options_id': vpc.dhcp_options_id,
        'region': vpc.region.name,
        'state': vpc.state,
    })


def find_vpc(module, vpc_conn, vpc_id=None, cidr=None):
    """
    Finds a VPC that matches a specific id or cidr + tags

    module : AnsibleModule object
    vpc_conn: authenticated VPCConnection connection object

    Returns:
        A VPC object that matches either an ID or CIDR and one or more tag values
    """

    if vpc_id is None and cidr is None:
        module.fail_json(
            msg='You must specify either a vpc_id or a cidr block + list of unique tags, aborting'
        )

    found_vpcs = []

    resource_tags = module.params.get('resource_tags')

    # Check for existing VPC by cidr_block or id
    if vpc_id is not None:
        found_vpcs = vpc_conn.get_all_vpcs(None, {'vpc-id': vpc_id, 'state': 'available', })

    else:
        previous_vpcs = vpc_conn.get_all_vpcs(None, {'cidr': cidr, 'state': 'available'})

        for vpc in previous_vpcs:
            # Get all tags for each of the found VPCs
            vpc_tags = dict((t.name, t.value) for t in vpc_conn.get_all_tags(filters={'resource-id': vpc.id}))

            # If the supplied list of ID Tags match a subset of the VPC Tags, we found our VPC
            if resource_tags and set(resource_tags.items()).issubset(set(vpc_tags.items())):
                found_vpcs.append(vpc)

    found_vpc = None

    if len(found_vpcs) == 1:
        found_vpc = found_vpcs[0]

    if len(found_vpcs) > 1:
        module.fail_json(msg='Found more than one vpc based on the supplied criteria, aborting')

    return (found_vpc)


def routes_match(rt_list=None, rt=None, igw=None):
    """
    Check if the route table has all routes as in given list

    rt_list      : A list if routes provided in the module
    rt           : The Remote route table object
    igw          : The internet gateway object for this vpc

    Returns:
        True when there provided routes and remote routes are the same.
        False when provided routes and remote routes are different.
    """

    local_routes = []
    remote_routes = []
    for route in rt_list:
        route_kwargs = {
            'gateway_id': None,
            'instance_id': None,
            'interface_id': None,
            'vpc_peering_connection_id': None,
            'state': 'active'
        }
        if route['gw'] == 'igw':
            route_kwargs['gateway_id'] = igw.id
        elif route['gw'].startswith('i-'):
            route_kwargs['instance_id'] = route['gw']
        elif route['gw'].startswith('eni-'):
            route_kwargs['interface_id'] = route['gw']
        elif route['gw'].startswith('pcx-'):
            route_kwargs['vpc_peering_connection_id'] = route['gw']
        else:
            route_kwargs['gateway_id'] = route['gw']
        route_kwargs['destination_cidr_block'] = route['dest']
        local_routes.append(route_kwargs)
    for j in rt.routes:
        remote_routes.append(j.__dict__)
    match = []
    for i in local_routes:
        change = "false"
        for j in remote_routes:
            if set(i.items()).issubset(set(j.items())):
                change = "true"
        match.append(change)
    if 'false' in match:
        return False
    else:
        return True


def rtb_changed(route_tables=None, vpc_conn=None, module=None, vpc=None, igw=None):
    """
    Checks if the remote routes match the local routes.

    route_tables : Route_tables parameter in the module
    vpc_conn     : The VPC connection object
    module       : The module object
    vpc          : The vpc object for this route table
    igw          : The internet gateway object for this vpc

    Returns:
        True when there is difference between the provided routes and remote routes and if subnet associations are different.
        False when both routes and subnet associations matched.

    """
    # We add a one for the main table
    rtb_len = len(route_tables) + 1
    remote_rtb_len = len(vpc_conn.get_all_route_tables(filters={'vpc_id': vpc.id}))
    if remote_rtb_len != rtb_len:
        return True
    for rt in route_tables:
        rt_id = None
        for sn in rt['subnets']:
            rsn = vpc_conn.get_all_subnets(filters={'cidr': sn, 'vpc_id': vpc.id})
            if len(rsn) != 1:
                module.fail_json(
                    msg='The subnet {0} to associate with route_table {1} '
                    'does not exist, aborting'.format(sn, rt)
                )
            nrt = vpc_conn.get_all_route_tables(filters={'vpc_id': vpc.id, 'association.subnet-id': rsn[0].id})
            if not nrt:
                return True
            else:
                nrt = nrt[0]
                if not rt_id:
                    rt_id = nrt.id
                    if not routes_match(rt['routes'], nrt, igw):
                        return True
                    continue
                else:
                    if rt_id == nrt.id:
                        continue
                    else:
                        return True
            return True
    return False


def create_vpc(module, vpc_conn):
    """
    Creates a new or modifies an existing VPC.

    module : AnsibleModule object
    vpc_conn: authenticated VPCConnection connection object

    Returns:
        A dictionary with information
        about the VPC and subnets that were launched
    """

    id = module.params.get('vpc_id')
    cidr_block = module.params.get('cidr_block')
    instance_tenancy = module.params.get('instance_tenancy')
    dns_support = module.params.get('dns_support')
    dns_hostnames = module.params.get('dns_hostnames')
    subnets = module.params.get('subnets')
    internet_gateway = module.params.get('internet_gateway')
    route_tables = module.params.get('route_tables')
    vpc_spec_tags = module.params.get('resource_tags')
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))
    changed = False

    # Check for existing VPC by cidr_block + tags or id
    previous_vpc = find_vpc(module, vpc_conn, id, cidr_block)

    if previous_vpc is not None:
        changed = False
        vpc = previous_vpc
    else:
        changed = True
        try:
            vpc = vpc_conn.create_vpc(cidr_block, instance_tenancy)
            # wait here until the vpc is available
            pending = True
            wait_timeout = time.time() + wait_timeout
            while wait and wait_timeout > time.time() and pending:
                try:
                    pvpc = vpc_conn.get_all_vpcs(vpc.id)
                    if hasattr(pvpc, 'state'):
                        if pvpc.state == "available":
                            pending = False
                    elif hasattr(pvpc[0], 'state'):
                        if pvpc[0].state == "available":
                            pending = False
                # sometimes vpc_conn.create_vpc() will return a vpc that can't be found yet by vpc_conn.get_all_vpcs()
                # when that happens, just wait a bit longer and try again
                except boto.exception.BotoServerError as e:
                    if e.error_code != 'InvalidVpcID.NotFound':
                        raise
                if pending:
                    time.sleep(5)
            if wait and wait_timeout <= time.time():
                # waiting took too long
                module.fail_json(msg="wait for vpc availability timeout on %s" % time.asctime())

        except boto.exception.BotoServerError as e:
            module.fail_json(msg="%s: %s" % (e.error_code, e.error_message))

    # Done with base VPC, now change to attributes and features.

    # Add resource tags
    vpc_tags = dict((t.name, t.value) for t in vpc_conn.get_all_tags(filters={'resource-id': vpc.id}))

    if not set(vpc_spec_tags.items()).issubset(set(vpc_tags.items())):
        new_tags = {}

        for (key, value) in set(vpc_spec_tags.items()):
            if (key, value) not in set(vpc_tags.items()):
                new_tags[key] = value

        if new_tags:
            vpc_conn.create_tags(vpc.id, new_tags)

    # boto doesn't appear to have a way to determine the existing
    # value of the dns attributes, so we just set them.
    # It also must be done one at a time.
    vpc_conn.modify_vpc_attribute(vpc.id, enable_dns_support=dns_support)
    vpc_conn.modify_vpc_attribute(vpc.id, enable_dns_hostnames=dns_hostnames)

    # Process all subnet properties
    if subnets is not None:
        if not isinstance(subnets, list):
            module.fail_json(msg='subnets needs to be a list of cidr blocks')

        current_subnets = vpc_conn.get_all_subnets(filters={'vpc_id': vpc.id})

        # First add all new subnets
        for subnet in subnets:
            add_subnet = True
            subnet_tags_current = True
            new_subnet_tags = subnet.get('resource_tags', {})
            subnet_tags_delete = []

            for csn in current_subnets:
                if subnet['cidr'] == csn.cidr_block:
                    add_subnet = False

                    # Check if AWS subnet tags are in playbook subnet tags
                    existing_tags_subset_of_new_tags = (set(csn.tags.items()).issubset(set(new_subnet_tags.items())))
                    # Check if subnet tags in playbook are in AWS subnet tags
                    new_tags_subset_of_existing_tags = (set(new_subnet_tags.items()).issubset(set(csn.tags.items())))

                    if existing_tags_subset_of_new_tags is False:
                        try:
                            for item in csn.tags.items():
                                if item not in new_subnet_tags.items():
                                    subnet_tags_delete.append(item)

                            subnet_tags_delete = [key[0] for key in subnet_tags_delete]
                            delete_subnet_tag = vpc_conn.delete_tags(csn.id, subnet_tags_delete)
                            changed = True
                        except EC2ResponseError as e:
                            module.fail_json(msg='Unable to delete resource tag, error {0}'.format(e))
                    # Add new subnet tags if not current

                    if new_tags_subset_of_existing_tags is False:
                        try:
                            changed = True
                            create_subnet_tag = vpc_conn.create_tags(csn.id, new_subnet_tags)

                        except EC2ResponseError as e:
                            module.fail_json(msg='Unable to create resource tag, error: {0}'.format(e))

            if add_subnet:
                try:
                    new_subnet = vpc_conn.create_subnet(vpc.id, subnet['cidr'], subnet.get('az', None))
                    new_subnet_tags = subnet.get('resource_tags', {})
                    if new_subnet_tags:
                        # Sometimes AWS takes its time to create a subnet and so using new subnets's id
                        # to create tags results in exception.
                        # boto doesn't seem to refresh 'state' of the newly created subnet, i.e.: it's always 'pending'
                        # so i resorted to polling vpc_conn.get_all_subnets with the id of the newly added subnet
                        while len(vpc_conn.get_all_subnets(filters={'subnet-id': new_subnet.id})) == 0:
                            time.sleep(0.1)

                        vpc_conn.create_tags(new_subnet.id, new_subnet_tags)

                    changed = True
                except EC2ResponseError as e:
                    module.fail_json(msg='Unable to create subnet {0}, error: {1}'.format(subnet['cidr'], e))

        # Now delete all absent subnets
        for csubnet in current_subnets:
            delete_subnet = True
            for subnet in subnets:
                if csubnet.cidr_block == subnet['cidr']:
                    delete_subnet = False
            if delete_subnet:
                try:
                    vpc_conn.delete_subnet(csubnet.id)
                    changed = True
                except EC2ResponseError as e:
                    module.fail_json(msg='Unable to delete subnet {0}, error: {1}'.format(csubnet.cidr_block, e))

    # Handle Internet gateway (create/delete igw)
    igw = None
    igw_id = None
    igws = vpc_conn.get_all_internet_gateways(filters={'attachment.vpc-id': vpc.id})
    if len(igws) > 1:
        module.fail_json(msg='EC2 returned more than one Internet Gateway for id %s, aborting' % vpc.id)
    if internet_gateway:
        if len(igws) != 1:
            try:
                igw = vpc_conn.create_internet_gateway()
                vpc_conn.attach_internet_gateway(igw.id, vpc.id)
                changed = True
            except EC2ResponseError as e:
                module.fail_json(msg='Unable to create Internet Gateway, error: {0}'.format(e))
        else:
            # Set igw variable to the current igw instance for use in route tables.
            igw = igws[0]
    else:
        if len(igws) > 0:
            try:
                vpc_conn.detach_internet_gateway(igws[0].id, vpc.id)
                vpc_conn.delete_internet_gateway(igws[0].id)
                changed = True
            except EC2ResponseError as e:
                module.fail_json(msg='Unable to delete Internet Gateway, error: {0}'.format(e))

    if igw is not None:
        igw_id = igw.id

    # Handle route tables - this may be worth splitting into a
    # different module but should work fine here. The strategy to stay
    # idempotent is to basically build all the route tables as
    # defined, track the route table ids, and then run through the
    # remote list of route tables and delete any that we didn't
    # create.  This shouldn't interrupt traffic in theory, but is the
    # only way to really work with route tables over time that I can
    # think of without using painful aws ids.  Hopefully boto will add
    # the replace-route-table API to make this smoother and
    # allow control of the 'main' routing table.
    if route_tables is not None:
        rtb_needs_change = rtb_changed(route_tables, vpc_conn, module, vpc, igw)
    if route_tables is not None and rtb_needs_change:
        if not isinstance(route_tables, list):
            module.fail_json(msg='route tables need to be a list of dictionaries')

        # Work through each route table and update/create to match dictionary array
        all_route_tables = []
        for rt in route_tables:
            try:
                new_rt = vpc_conn.create_route_table(vpc.id)
                new_rt_tags = rt.get('resource_tags', None)
                if new_rt_tags:
                    vpc_conn.create_tags(new_rt.id, new_rt_tags)
                for route in rt['routes']:
                    route_kwargs = {}
                    if route['gw'] == 'igw':
                        if not internet_gateway:
                            module.fail_json(
                                msg='You asked for an Internet Gateway '
                                '(igw) route, but you have no Internet Gateway'
                            )
                        route_kwargs['gateway_id'] = igw.id
                    elif route['gw'].startswith('i-'):
                        route_kwargs['instance_id'] = route['gw']
                    elif route['gw'].startswith('eni-'):
                        route_kwargs['interface_id'] = route['gw']
                    elif route['gw'].startswith('pcx-'):
                        route_kwargs['vpc_peering_connection_id'] = route['gw']
                    else:
                        route_kwargs['gateway_id'] = route['gw']
                    vpc_conn.create_route(new_rt.id, route['dest'], **route_kwargs)

                # Associate with subnets
                for sn in rt['subnets']:
                    rsn = vpc_conn.get_all_subnets(filters={'cidr': sn, 'vpc_id': vpc.id})
                    if len(rsn) != 1:
                        module.fail_json(
                            msg='The subnet {0} to associate with route_table {1} '
                            'does not exist, aborting'.format(sn, rt)
                        )
                    rsn = rsn[0]

                    # Disassociate then associate since we don't have replace
                    old_rt = vpc_conn.get_all_route_tables(
                        filters={'association.subnet_id': rsn.id, 'vpc_id': vpc.id}
                    )
                    old_rt = [x for x in old_rt if x.id is not None]
                    if len(old_rt) == 1:
                        old_rt = old_rt[0]
                        association_id = None
                        for a in old_rt.associations:
                            if a.subnet_id == rsn.id:
                                association_id = a.id
                        vpc_conn.disassociate_route_table(association_id)

                    vpc_conn.associate_route_table(new_rt.id, rsn.id)

                all_route_tables.append(new_rt)
                changed = True
            except EC2ResponseError as e:
                module.fail_json(
                    msg='Unable to create and associate route table {0}, error: '
                    '{1}'.format(rt, e)
                )

        # Now that we are good to go on our new route tables, delete the
        # old ones except the 'main' route table as boto can't set the main
        # table yet.
        all_rts = vpc_conn.get_all_route_tables(filters={'vpc-id': vpc.id})
        for rt in all_rts:
            if rt.id is None:
                continue
            delete_rt = True
            for newrt in all_route_tables:
                if newrt.id == rt.id:
                    delete_rt = False
                    break
            if delete_rt:
                rta = rt.associations
                is_main = False
                for a in rta:
                    if a.main:
                        is_main = True
                        break
                try:
                    if not is_main:
                        vpc_conn.delete_route_table(rt.id)
                        changed = True
                except EC2ResponseError as e:
                    module.fail_json(msg='Unable to delete old route table {0}, error: {1}'.format(rt.id, e))

    vpc_dict = get_vpc_info(vpc)

    created_vpc_id = vpc.id
    returned_subnets = []
    current_subnets = vpc_conn.get_all_subnets(filters={'vpc_id': vpc.id})

    for sn in current_subnets:
        returned_subnets.append({
            'resource_tags': dict((t.name, t.value) for t in vpc_conn.get_all_tags(filters={'resource-id': sn.id})),
            'cidr': sn.cidr_block,
            'az': sn.availability_zone,
            'id': sn.id,
        })

    if subnets is not None:
        # Sort subnets by the order they were listed in the play
        order = {}
        for idx, val in enumerate(subnets):
            order[val['cidr']] = idx

        # Number of subnets in the play
        subnets_in_play = len(subnets)
        returned_subnets.sort(key=lambda x: order.get(x['cidr'], subnets_in_play))

    return (vpc_dict, created_vpc_id, returned_subnets, igw_id, changed)


def terminate_vpc(module, vpc_conn, vpc_id=None, cidr=None):
    """
    Terminates a VPC

    module: Ansible module object
    vpc_conn: authenticated VPCConnection connection object
    vpc_id: a vpc id to terminate
    cidr: The cidr block of the VPC - can be used in lieu of an ID

    Returns a dictionary of VPC information
    about the VPC terminated.

    If the VPC to be terminated is available
    "changed" will be set to True.

    """
    vpc_dict = {}
    terminated_vpc_id = ''
    changed = False

    vpc = find_vpc(module, vpc_conn, vpc_id, cidr)

    if vpc is not None:
        if vpc.state == 'available':
            terminated_vpc_id = vpc.id
            vpc_dict = get_vpc_info(vpc)
            try:
                subnets = vpc_conn.get_all_subnets(filters={'vpc_id': vpc.id})
                for sn in subnets:
                    vpc_conn.delete_subnet(sn.id)

                igws = vpc_conn.get_all_internet_gateways(
                    filters={'attachment.vpc-id': vpc.id}
                )
                for igw in igws:
                    vpc_conn.detach_internet_gateway(igw.id, vpc.id)
                    vpc_conn.delete_internet_gateway(igw.id)

                rts = vpc_conn.get_all_route_tables(filters={'vpc_id': vpc.id})
                for rt in rts:
                    rta = rt.associations
                    is_main = False
                    for a in rta:
                        if a.main:
                            is_main = True
                    if not is_main:
                        vpc_conn.delete_route_table(rt.id)

                vpc_conn.delete_vpc(vpc.id)
            except EC2ResponseError as e:
                module.fail_json(
                    msg='Unable to delete VPC {0}, error: {1}'.format(vpc.id, e)
                )
            changed = True
            vpc_dict['state'] = "terminated"

    return (changed, vpc_dict, terminated_vpc_id)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        cidr_block=dict(),
        instance_tenancy=dict(choices=['default', 'dedicated'], default='default'),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(default=300),
        dns_support=dict(type='bool', default=True),
        dns_hostnames=dict(type='bool', default=True),
        subnets=dict(type='list'),
        vpc_id=dict(),
        internet_gateway=dict(type='bool', default=False),
        resource_tags=dict(type='dict', required=True),
        route_tables=dict(type='list'),
        state=dict(choices=['present', 'absent'], default='present'),
    )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    state = module.params.get('state')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)

    # If we have a region specified, connect to its endpoint.
    if region:
        try:
            vpc_conn = connect_to_aws(boto.vpc, region, **aws_connect_kwargs)
        except boto.exception.NoAuthHandlerFound as e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

    igw_id = None
    if module.params.get('state') == 'absent':
        vpc_id = module.params.get('vpc_id')
        cidr = module.params.get('cidr_block')
        (changed, vpc_dict, new_vpc_id) = terminate_vpc(module, vpc_conn, vpc_id, cidr)
        subnets_changed = None
    elif module.params.get('state') == 'present':
        # Changed is always set to true when provisioning a new VPC
        (vpc_dict, new_vpc_id, subnets_changed, igw_id, changed) = create_vpc(module, vpc_conn)

    module.exit_json(changed=changed, vpc_id=new_vpc_id, vpc=vpc_dict, igw_id=igw_id, subnets=subnets_changed)


if __name__ == '__main__':
    main()
