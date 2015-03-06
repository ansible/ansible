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
module: ec2_vpc
short_description: configure AWS virtual private clouds
description:
    - Create or terminates AWS virtual private clouds.  This module has a dependency on python-boto.
version_added: "1.4"
options:
  cidr_block:
    description:
      - "The cidr block representing the VPC, e.g. 10.0.0.0/16"
    required: false, unless state=present
  instance_tenancy:
    description:
      - "The supported tenancy options for instances launched into the VPC."
    required: false
    default: "default"
    choices: [ "default", "dedicated" ]
  dns_support:
    description:
      - toggles the "Enable DNS resolution" flag
    required: false
    default: "yes"
    choices: [ "yes", "no" ]
  dns_hostnames:
    description:
      - toggles the "Enable DNS hostname support for instances" flag
    required: false
    default: "yes"
    choices: [ "yes", "no" ]
  subnets:
    description:
      - 'A dictionary array of subnets to add of the form: { cidr: ..., az: ... , resource_tags: ... }. Where az is the desired availability zone of the subnet, but it is not required. Tags (i.e.: resource_tags) is also optional and use dictionary form: { "Environment":"Dev", "Tier":"Web", ...}. All VPC subnets not in this list will be removed. As of 1.8, if the subnets parameter is not specified, no existing subnets will be modified.'
    required: false
    default: null
    aliases: []
  vpc_id:
    description:
      - A VPC id to terminate when state=absent
    required: false
    default: null
    aliases: []
  resource_tags:
    description:
      - 'A dictionary array of resource tags of the form: { tag1: value1, tag2: value2 }.  Tags in this list are used in conjunction with CIDR block to uniquely identify a VPC in lieu of vpc_id. Therefore, if CIDR/Tag combination does not exits, a new VPC will be created.  VPC tags not on this list will be ignored. Prior to 1.7, specifying a resource tag was optional.'
    required: true
    default: null
    aliases: []
    version_added: "1.6"
  internet_gateway:
    description:
      - Toggle whether there should be an Internet gateway attached to the VPC
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    aliases: []
  route_tables:
    description:
      - 'A dictionary array of route tables to add of the form: { subnets: [172.22.2.0/24, 172.22.3.0/24,], routes: [{ dest: 0.0.0.0/0, gw: igw},] }. Where the subnets list is those subnets the route table should be associated with, and the routes list is a list of routes to be in the table.  The special keyword for the gw of igw specifies that you should the route should go through the internet gateway attached to the VPC. gw also accepts instance-ids in addition igw. This module is currently unable to affect the "main" route table due to some limitations in boto, so you must explicitly define the associated subnets or they will be attached to the main table implicitly. As of 1.8, if the route_tables parameter is not specified, no existing routes will be modified.'
    required: false
    default: null
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
      - AWS secret key. If not set then the value of the AWS_SECRET_KEY environment variable is used.
    required: false
    default: None
    aliases: ['ec2_secret_key', 'secret_key' ]
  aws_access_key:
    description:
      - AWS access key. If not set then the value of the AWS_ACCESS_KEY environment variable is used.
    required: false
    default: None
    aliases: ['ec2_access_key', 'access_key' ]
  validate_certs:
    description:
      - When set to "no", SSL certificates will not be validated for boto versions >= 2.6.0.
    required: false
    default: "yes"
    choices: ["yes", "no"]
    aliases: []
    version_added: "1.5"

requirements: [ "boto" ]
author: Carson Gee
'''

EXAMPLES = '''
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.

# Basic creation example:
      ec2_vpc:
        state: present
        cidr_block: 172.23.0.0/16
        resource_tags: { "Environment":"Development" }
        region: us-west-2
# Full creation example with subnets and optional availability zones.
# The absence or presence of subnets deletes or creates them respectively.
      ec2_vpc:
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
      ec2_vpc:
        state: absent
        vpc_id: vpc-aaaaaaa
        region: us-west-2
If you have added elements not managed by this module, e.g. instances, NATs, etc then
the delete will fail until those dependencies are removed.
'''


import sys
import time

try:
    import boto.ec2
    import boto.vpc
    from boto.exception import EC2ResponseError
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)

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

    if vpc_id == None and cidr == None:
        module.fail_json(
            msg='You must specify either a vpc_id or a cidr block + list of unique tags, aborting'
        )

    found_vpcs = []

    resource_tags = module.params.get('resource_tags')

    # Check for existing VPC by cidr_block or id
    if vpc_id is not None:
        found_vpcs = vpc_conn.get_all_vpcs(None, {'vpc-id': vpc_id, 'state': 'available',})

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
                except boto.exception.BotoServerError, e:
                    if e.error_code != 'InvalidVpcID.NotFound':
                        raise
                if pending:
                    time.sleep(5)
            if wait and wait_timeout <= time.time():
                # waiting took too long
                module.fail_json(msg = "wait for vpc availability timeout on %s" % time.asctime())

        except boto.exception.BotoServerError, e:
            module.fail_json(msg = "%s: %s" % (e.error_code, e.error_message))

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

        current_subnets = vpc_conn.get_all_subnets(filters={ 'vpc_id': vpc.id })

        # First add all new subnets
        for subnet in subnets:
            add_subnet = True
            for csn in current_subnets:
                if subnet['cidr'] == csn.cidr_block:
                    add_subnet = False
            if add_subnet:
                try:
                    new_subnet = vpc_conn.create_subnet(vpc.id, subnet['cidr'], subnet.get('az', None))
                    new_subnet_tags = subnet.get('resource_tags', None)
                    if new_subnet_tags:
                        # Sometimes AWS takes its time to create a subnet and so using new subnets's id
                        # to create tags results in exception.
                        # boto doesn't seem to refresh 'state' of the newly created subnet, i.e.: it's always 'pending'
                        # so i resorted to polling vpc_conn.get_all_subnets with the id of the newly added subnet
                        while len(vpc_conn.get_all_subnets(filters={ 'subnet-id': new_subnet.id })) == 0:
                            time.sleep(0.1)

                        vpc_conn.create_tags(new_subnet.id, new_subnet_tags)

                    changed = True
                except EC2ResponseError, e:
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
                except EC2ResponseError, e:
                    module.fail_json(msg='Unable to delete subnet {0}, error: {1}'.format(csubnet.cidr_block, e))

    # Handle Internet gateway (create/delete igw)
    igw = None
    igws = vpc_conn.get_all_internet_gateways(filters={'attachment.vpc-id': vpc.id})
    if len(igws) > 1:
        module.fail_json(msg='EC2 returned more than one Internet Gateway for id %s, aborting' % vpc.id)
    if internet_gateway:
        if len(igws) != 1:
            try:
                igw = vpc_conn.create_internet_gateway()
                vpc_conn.attach_internet_gateway(igw.id, vpc.id)
                changed = True
            except EC2ResponseError, e:
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
            except EC2ResponseError, e:
                module.fail_json(msg='Unable to delete Internet Gateway, error: {0}'.format(e))

    # Handle route tables - this may be worth splitting into a
    # different module but should work fine here. The strategy to stay
    # indempotent is to basically build all the route tables as
    # defined, track the route table ids, and then run through the
    # remote list of route tables and delete any that we didn't
    # create.  This shouldn't interrupt traffic in theory, but is the
    # only way to really work with route tables over time that I can
    # think of without using painful aws ids.  Hopefully boto will add
    # the replace-route-table API to make this smoother and
    # allow control of the 'main' routing table.
    if route_tables is not None:
        if not isinstance(route_tables, list):
            module.fail_json(msg='route tables need to be a list of dictionaries')

        # Work through each route table and update/create to match dictionary array
        all_route_tables = []
        for rt in route_tables:
            try:
                new_rt = vpc_conn.create_route_table(vpc.id)
                for route in rt['routes']:
                    route_kwargs = {}
                    if route['gw'] == 'igw':
                        if not internet_gateway:
                            module.fail_json(
                                msg='You asked for an Internet Gateway ' \
                                '(igw) route, but you have no Internet Gateway'
                            )
                        route_kwargs['gateway_id'] = igw.id
                    elif route['gw'].startswith('i-'):
                        route_kwargs['instance_id'] = route['gw']
                    else:
                        route_kwargs['gateway_id'] = route['gw']
                    vpc_conn.create_route(new_rt.id, route['dest'], **route_kwargs)

                # Associate with subnets
                for sn in rt['subnets']:
                    rsn = vpc_conn.get_all_subnets(filters={'cidr': sn, 'vpc_id': vpc.id })
                    if len(rsn) != 1:
                        module.fail_json(
                            msg='The subnet {0} to associate with route_table {1} ' \
                            'does not exist, aborting'.format(sn, rt)
                        )
                    rsn = rsn[0]

                    # Disassociate then associate since we don't have replace
                    old_rt = vpc_conn.get_all_route_tables(
                        filters={'association.subnet_id': rsn.id, 'vpc_id': vpc.id}
                    )
                    old_rt = [ x for x in old_rt if x.id != None ]
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
            except EC2ResponseError, e:
                module.fail_json(
                    msg='Unable to create and associate route table {0}, error: ' \
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
                except EC2ResponseError, e:
                    module.fail_json(msg='Unable to delete old route table {0}, error: {1}'.format(rt.id, e))

    vpc_dict = get_vpc_info(vpc)
    created_vpc_id = vpc.id
    returned_subnets = []
    current_subnets = vpc_conn.get_all_subnets(filters={ 'vpc_id': vpc.id })

    for sn in current_subnets:
        returned_subnets.append({
            'resource_tags': dict((t.name, t.value) for t in vpc_conn.get_all_tags(filters={'resource-id': sn.id})),
            'cidr': sn.cidr_block,
            'az': sn.availability_zone,
            'id': sn.id,
        })

    # Sort subnets by the order they were listed in the play
    order = {}
    for idx, val in enumerate(subnets):
        order[val['cidr']] = idx

    # Number of subnets in the play
    subnets_in_play = len(subnets)
    returned_subnets.sort(key=lambda x: order.get(x['cidr'], subnets_in_play))

    return (vpc_dict, created_vpc_id, returned_subnets, changed)

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
            terminated_vpc_id=vpc.id
            vpc_dict=get_vpc_info(vpc)
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
            except EC2ResponseError, e:
                module.fail_json(
                    msg='Unable to delete VPC {0}, error: {1}'.format(vpc.id, e)
                )
            changed = True

    return (changed, vpc_dict, terminated_vpc_id)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            cidr_block = dict(),
            instance_tenancy = dict(choices=['default', 'dedicated'], default='default'),
            wait = dict(type='bool', default=False),
            wait_timeout = dict(default=300),
            dns_support = dict(type='bool', default=True),
            dns_hostnames = dict(type='bool', default=True),
            subnets = dict(type='list'),
            vpc_id = dict(),
            internet_gateway = dict(type='bool', default=False),
            resource_tags = dict(type='dict', required=True),
            route_tables = dict(type='list'),
            state = dict(choices=['present', 'absent'], default='present'),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    state = module.params.get('state')

    ec2_url, aws_access_key, aws_secret_key, region = get_ec2_creds(module)

    # If we have a region specified, connect to its endpoint.
    if region:
        try:
            vpc_conn = boto.vpc.connect_to_region(
                region,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
        except boto.exception.NoAuthHandlerFound, e:
            module.fail_json(msg = str(e))
    else:
        module.fail_json(msg="region must be specified")

    if module.params.get('state') == 'absent':
        vpc_id = module.params.get('vpc_id')
        cidr = module.params.get('cidr_block')
        (changed, vpc_dict, new_vpc_id) = terminate_vpc(module, vpc_conn, vpc_id, cidr)
        subnets_changed = None
    elif module.params.get('state') == 'present':
        # Changed is always set to true when provisioning a new VPC
        (vpc_dict, new_vpc_id, subnets_changed, changed) = create_vpc(module, vpc_conn)

    module.exit_json(changed=changed, vpc_id=new_vpc_id, vpc=vpc_dict, subnets=subnets_changed)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
