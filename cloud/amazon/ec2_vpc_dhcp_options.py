#!/usr/bin/python

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

DOCUMENTATION = """
---
module: ec2_vpc_dhcp_options
short_description: Ensures the DHCP options for the given VPC match what's
  requested
description:
  - Converges the DHCP option set for the given VPC to the variables requested.
    If any of the optional values are missing, they will either be treated
    as a no-op (i.e., inherit what already exists for the VPC) or a purge of
    existing options. Most of the options should be self-explanatory.
author: "Joel Thompson (@joelthompson)"
version_added: 2.1
options:
  domain_name:
    description:
      - The domain name to set in the DHCP option sets
    required: false
    default: ""
  dns_servers:
    description:
      - A list of hosts to set the DNS servers for the VPC to. (Should be a
        list of IP addresses rather than host names.)
    required: false
    default: []
  ntp_servers:
    description:
      - List of hosts to advertise as NTP servers for the VPC.
    required: false
    default: []
  netbios_name_servers:
    description:
      - List of hosts to advertise as NetBIOS servers.
    required: false
    default: []
  netbios_node_type:
    description:
      - NetBIOS node type to advertise in the DHCP options. The
        default is 2, per AWS recommendation
        http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_DHCP_Options.html
    required: false
    default: 2
  vpc_id:
    description:
      - VPC ID to associate with the requested DHCP option set
    required: true
  delete_old:
    description:
      - Whether to delete the old VPC DHCP option set when creating a new one.
        This is primarily useful for debugging/development purposes when you
        want to quickly roll back to the old option set. Note that this setting
        will be ignored, and the old DHCP option set will be preserved, if it
        is in use by any other VPC. (Otherwise, AWS will return an error.)
    required: false
    default: true
  inherit_existing:
    description:
      - For any DHCP options not specified in these parameters, whether to
        inherit them from the options set already applied to vpc_id, or to
        reset them to be empty.
    required: false
    default: false
extends_documentation_fragment: aws
requirements:
    - boto
"""

RETURN = """
new_options:
  description: The new DHCP options associated with your VPC
  returned: changed
  type: dict
  sample:
    domain-name-servers:
      - 10.0.0.1
      - 10.0.1.1
    netbois-name-servers:
      - 10.0.0.1
      - 10.0.1.1
    ntp-servers: None
    netbios-node-type: 2
    domain-name: "my.example.com"
"""

EXAMPLES = """
# Completely overrides the VPC DHCP options associated with VPC vpc-123456 and deletes any existing
# DHCP option set that may have been attached to that VPC.
- ec2_vpc_dhcp_options:
    domain_name: "foo.example.com"
    region: us-east-1
    dns_servers:
        - 10.0.0.1
        - 10.0.1.1
    ntp_servers:
        - 10.0.0.2
        - 10.0.1.2
    netbios_name_servers:
        - 10.0.0.1
        - 10.0.1.1
    netbios_node_type: 2
    vpc_id: vpc-123456
    delete_old: True
    inherit_existing: False


# Ensure the DHCP option set for the VPC has 10.0.0.4 and 10.0.1.4 as the specified DNS servers, but
# keep any other existing settings. Also, keep the old DHCP option set around.
- ec2_vpc_dhcp_options:
    region: us-east-1
    dns_servers:
      - "{{groups['dns-primary']}}"
      - "{{groups['dns-secondary']}}"
    vpc_id: vpc-123456
    inherit_existing: True
    delete_old: False
"""

import boto.vpc
import socket
import collections

def _get_associated_dhcp_options(vpc_id, vpc_connection):
    """
    Returns the DHCP options object currently associated with the requested VPC ID using the VPC
    connection variable.
    """
    vpcs = vpc_connection.get_all_vpcs(vpc_ids=[vpc_id])
    if len(vpcs) != 1:
      return None
    dhcp_options = vpc_connection.get_all_dhcp_options(dhcp_options_ids=[vpcs[0].dhcp_options_id])
    if len(dhcp_options) != 1:
      return None
    return dhcp_options[0]


def _get_vpcs_by_dhcp_options(dhcp_options_id, vpc_connection):
    return vpc_connection.get_all_vpcs(filters={'dhcpOptionsId': dhcp_options_id})


def _get_updated_option(requested, existing, inherit):
    if inherit and (not requested or requested == ['']):
        return existing
    else:
        return requested


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        domain_name=dict(type='str', default=''),
        dns_servers=dict(type='list', default=[]),
        ntp_servers=dict(type='list', default=[]),
        netbios_name_servers=dict(type='list', default=[]),
        netbios_node_type=dict(type='int', default=2),
        vpc_id=dict(type='str', required=True),
        delete_old=dict(type='bool', default=True),
        inherit_existing=dict(type='bool', default=False)
        )
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    params = module.params

  
    region, ec2_url, boto_params = get_aws_connection_info(module)
    connection = connect_to_aws(boto.vpc, region, **boto_params)
  
    inherit_existing = params['inherit_existing']
  
    existing_options = _get_associated_dhcp_options(params['vpc_id'], connection)
    new_options = collections.defaultdict(lambda: None)
  
    new_options['domain-name-servers'] = _get_updated_option( params['dns_servers'],
            existing_options.options.get('domain-name-servers'), inherit_existing)
  
    new_options['netbios-name-servers'] = _get_updated_option(params['netbios_name_servers'],
            existing_options.options.get('netbios-name-servers'), inherit_existing)
  
  
    new_options['ntp-servers'] = _get_updated_option(params['ntp_servers'],
            existing_options.options.get('ntp-servers'), inherit_existing)
  
    # HACK: Why do I make the next two lists? The boto api returns a list if present, so
    # I need this to properly compare so == works.
  
    # HACK: netbios-node-type is an int, but boto returns a string. So, asking for an int from Ansible
    # for data validation, but still need to cast it to a string
    new_options['netbios-node-type'] = _get_updated_option(
            [str(params['netbios_node_type'])], existing_options.options.get('netbios-node-type'),
            inherit_existing)
  
    new_options['domain-name'] = _get_updated_option(
            [params['domain_name']], existing_options.options.get('domain-name'), inherit_existing)
  
    if existing_options and new_options == existing_options.options:
        module.exit_json(changed=False)
  
    if new_options['netbios-node-type']:
        new_options['netbios-node-type'] = new_options['netbios-node-type'][0]
  
    if new_options['domain-name']:
        new_options['domain-name'] = new_options['domain-name'][0]
  
    if not module.check_mode:
        dhcp_option = connection.create_dhcp_options(new_options['domain-name'],
                new_options['domain-name-servers'], new_options['ntp-servers'],
                new_options['netbios-name-servers'], new_options['netbios-node-type'])
        connection.associate_dhcp_options(dhcp_option.id, params['vpc_id'])
        if params['delete_old'] and existing_options:
            other_vpcs = _get_vpcs_by_dhcp_options(existing_options.id, connection)
            if len(other_vpcs) == 0 or (len(other_vpcs) == 1 and other_vpcs[0].id == params['vpc_id']):
                connection.delete_dhcp_options(existing_options.id)
  
    module.exit_json(changed=True, new_options=new_options)
  

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == "__main__":
    main()
