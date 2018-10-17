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
deprecated:
  removed_in: "2.5"
  why: Replaced by dedicated modules.
  alternative: Use M(ec2_vpc_net) along with supporting modules including M(ec2_vpc_igw), M(ec2_vpc_route_table), M(ec2_vpc_subnet),
               M(ec2_vpc_dhcp_option), M(ec2_vpc_nat_gateway), M(ec2_vpc_nacl).
options:
  cidr_block:
    description:
      - "The cidr block representing the VPC, e.g. C(10.0.0.0/16), required when I(state=present)."
  instance_tenancy:
    description:
      - "The supported tenancy options for instances launched into the VPC."
    default: "default"
    choices: [ "default", "dedicated" ]
  dns_support:
    description:
      - Toggles the "Enable DNS resolution" flag.
    type: bool
    default: 'yes'
  dns_hostnames:
    description:
      - Toggles the "Enable DNS hostname support for instances" flag.
    type: bool
    default: 'yes'
  subnets:
    description:
      - 'A dictionary array of subnets to add of the form C({ cidr: ..., az: ... , resource_tags: ... }).'
      - Where C(az) is the desired availability zone of the subnet, optional.
      - 'Tags C(resource_tags) use dictionary form C({ "Environment":"Dev", "Tier":"Web", ...}), optional.'
      - C(resource_tags) see resource_tags for VPC below. The main difference is subnet tags not specified here will be deleted.
      - All VPC subnets not in this list will be removed as well.
      - As of 1.8, if the subnets parameter is not specified, no existing subnets will be modified.'
  vpc_id:
    description:
      - A VPC id to terminate when I(state=absent).
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
    type: bool
    default: 'no'
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
  wait:
    description:
      - Wait for the VPC to be in state 'available' before returning.
    type: bool
    default: 'no'
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

from ansible.module_utils.common.removed import removed_module

if __name__ == '__main__':
    removed_module()
