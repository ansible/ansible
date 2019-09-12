#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: aws_direct_connect_virtual_interface
short_description: Manage Direct Connect virtual interfaces.
description:
  - Create, delete, or modify a Direct Connect public or private virtual interface.
version_added: "2.5"
author: "Sloane Hertel (@s-hertel)"
requirements:
  - boto3
  - botocore
options:
  state:
    description:
      - The desired state of the Direct Connect virtual interface.
    choices: [present, absent]
  id_to_associate:
    description:
      - The ID of the link aggregation group or connection to associate with the virtual interface.
    aliases: [link_aggregation_group_id, connection_id]
  public:
    description:
      - The type of virtual interface.
    type: bool
  name:
    description:
      - The name of the virtual interface.
  vlan:
    description:
      - The VLAN ID.
    default: 100
  bgp_asn:
    description:
      - The autonomous system (AS) number for Border Gateway Protocol (BGP) configuration.
    default: 65000
  authentication_key:
    description:
      - The authentication key for BGP configuration.
  amazon_address:
    description:
      - The amazon address CIDR with which to create the virtual interface.
  customer_address:
    description:
      - The customer address CIDR with which to create the virtual interface.
  address_type:
    description:
      - The type of IP address for the BGP peer.
  cidr:
    description:
      - A list of route filter prefix CIDRs with which to create the public virtual interface.
  virtual_gateway_id:
    description:
      - The virtual gateway ID required for creating a private virtual interface.
  virtual_interface_id:
    description:
      - The virtual interface ID.
extends_documentation_fragment:
  - aws
  - ec2
'''

RETURN = '''
address_family:
  description: The address family for the BGP peer.
  returned: always
  type: str
  sample: ipv4
amazon_address:
  description: IP address assigned to the Amazon interface.
  returned: always
  type: str
  sample: 169.254.255.1/30
asn:
  description: The autonomous system (AS) number for Border Gateway Protocol (BGP) configuration.
  returned: always
  type: int
  sample: 65000
auth_key:
  description: The authentication key for BGP configuration.
  returned: always
  type: str
  sample: 0xZ59Y1JZ2oDOSh6YriIlyRE
bgp_peers:
  description: A list of the BGP peers configured on this virtual interface.
  returned: always
  type: complex
  contains:
    address_family:
      description: The address family for the BGP peer.
      returned: always
      type: str
      sample: ipv4
    amazon_address:
      description: IP address assigned to the Amazon interface.
      returned: always
      type: str
      sample: 169.254.255.1/30
    asn:
      description: The autonomous system (AS) number for Border Gateway Protocol (BGP) configuration.
      returned: always
      type: int
      sample: 65000
    auth_key:
      description: The authentication key for BGP configuration.
      returned: always
      type: str
      sample: 0xZ59Y1JZ2oDOSh6YriIlyRE
    bgp_peer_state:
      description: The state of the BGP peer (verifying, pending, available)
      returned: always
      type: str
      sample: available
    bgp_status:
      description: The up/down state of the BGP peer.
      returned: always
      type: str
      sample: up
    customer_address:
      description: IP address assigned to the customer interface.
      returned: always
      type: str
      sample: 169.254.255.2/30
changed:
  description: Indicated if the virtual interface has been created/modified/deleted
  returned: always
  type: bool
  sample: false
connection_id:
  description:
    - The ID of the connection. This field is also used as the ID type for operations that
      use multiple connection types (LAG, interconnect, and/or connection).
  returned: always
  type: str
  sample: dxcon-fgb175av
customer_address:
  description: IP address assigned to the customer interface.
  returned: always
  type: str
  sample: 169.254.255.2/30
customer_router_config:
  description: Information for generating the customer router configuration.
  returned: always
  type: str
location:
  description: Where the connection is located.
  returned: always
  type: str
  sample: EqDC2
owner_account:
  description: The AWS account that will own the new virtual interface.
  returned: always
  type: str
  sample: '123456789012'
route_filter_prefixes:
  description: A list of routes to be advertised to the AWS network in this region (public virtual interface).
  returned: always
  type: complex
  contains:
    cidr:
      description: A routes to be advertised to the AWS network in this region.
      returned: always
      type: str
      sample: 54.227.92.216/30
virtual_gateway_id:
  description: The ID of the virtual private gateway to a VPC. This only applies to private virtual interfaces.
  returned: when I(public=False)
  type: str
  sample: vgw-f3ce259a
virtual_interface_id:
  description: The ID of the virtual interface.
  returned: always
  type: str
  sample: dxvif-fh0w7cex
virtual_interface_name:
  description: The name of the virtual interface assigned by the customer.
  returned: always
  type: str
  sample: test_virtual_interface
virtual_interface_state:
  description: State of the virtual interface (confirming, verifying, pending, available, down, rejected).
  returned: always
  type: str
  sample: available
virtual_interface_type:
  description: The type of virtual interface (private, public).
  returned: always
  type: str
  sample: private
vlan:
  description: The VLAN ID.
  returned: always
  type: int
  sample: 100
'''

EXAMPLES = '''
---
- name: create an association between a LAG and connection
  aws_direct_connect_virtual_interface:
    state: present
    name: "{{ name }}"
    link_aggregation_group_id: LAG-XXXXXXXX
    connection_id: dxcon-XXXXXXXX

- name: remove an association between a connection and virtual interface
  aws_direct_connect_virtual_interface:
    state: absent
    connection_id: dxcon-XXXXXXXX
    virtual_interface_id: dxv-XXXXXXXX

'''

import traceback
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.aws.direct_connect import DirectConnectError, delete_virtual_interface
from ansible.module_utils.ec2 import (AWSRetry, HAS_BOTO3, boto3_conn,
                                      ec2_argument_spec, get_aws_connection_info,
                                      camel_dict_to_snake_dict)

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    # handled by HAS_BOTO3
    pass


def try_except_ClientError(failure_msg):
    '''
        Wrapper for boto3 calls that uses AWSRetry and handles exceptions
    '''
    def wrapper(f):
        def run_func(*args, **kwargs):
            try:
                result = AWSRetry.backoff(tries=8, delay=5, catch_extra_error_codes=['DirectConnectClientException'])(f)(*args, **kwargs)
            except (ClientError, BotoCoreError) as e:
                raise DirectConnectError(failure_msg, traceback.format_exc(), e)
            return result
        return run_func
    return wrapper


def find_unique_vi(client, connection_id, virtual_interface_id, name):
    '''
        Determines if the virtual interface exists. Returns the virtual interface ID if an exact match is found.
        If multiple matches are found False is returned. If no matches are found None is returned.
    '''

    # Get the virtual interfaces, filtering by the ID if provided.
    vi_params = {}
    if virtual_interface_id:
        vi_params = {'virtualInterfaceId': virtual_interface_id}

    virtual_interfaces = try_except_ClientError(
        failure_msg="Failed to describe virtual interface")(
        client.describe_virtual_interfaces)(**vi_params).get('virtualInterfaces')

    # Remove deleting/deleted matches from the results.
    virtual_interfaces = [vi for vi in virtual_interfaces if vi['virtualInterfaceState'] not in ('deleting', 'deleted')]

    matching_virtual_interfaces = filter_virtual_interfaces(virtual_interfaces, name, connection_id)
    return exact_match(matching_virtual_interfaces)


def exact_match(virtual_interfaces):
    '''
        Returns the virtual interface ID if one was found,
        None if the virtual interface ID needs to be created,
        False if an exact match was not found
    '''

    if not virtual_interfaces:
        return None
    if len(virtual_interfaces) == 1:
        return virtual_interfaces[0]['virtualInterfaceId']
    else:
        return False


def filter_virtual_interfaces(virtual_interfaces, name, connection_id):
    '''
        Filters the available virtual interfaces to try to find a unique match
    '''
    # Filter by name if provided.
    if name:
        matching_by_name = find_virtual_interface_by_name(virtual_interfaces, name)
        if len(matching_by_name) == 1:
            return matching_by_name
    else:
        matching_by_name = virtual_interfaces

    # If there isn't a unique match filter by connection ID as last resort (because connection_id may be a connection yet to be associated)
    if connection_id and len(matching_by_name) > 1:
        matching_by_connection_id = find_virtual_interface_by_connection_id(matching_by_name, connection_id)
        if len(matching_by_connection_id) == 1:
            return matching_by_connection_id
    else:
        matching_by_connection_id = matching_by_name

    return matching_by_connection_id


def find_virtual_interface_by_connection_id(virtual_interfaces, connection_id):
    '''
        Return virtual interfaces that have the connection_id associated
    '''
    return [vi for vi in virtual_interfaces if vi['connectionId'] == connection_id]


def find_virtual_interface_by_name(virtual_interfaces, name):
    '''
        Return virtual interfaces that match the provided name
    '''
    return [vi for vi in virtual_interfaces if vi['virtualInterfaceName'] == name]


def vi_state(client, virtual_interface_id):
    '''
        Returns the state of the virtual interface.
    '''
    err_msg = "Failed to describe virtual interface: {0}".format(virtual_interface_id)
    vi = try_except_ClientError(failure_msg=err_msg)(client.describe_virtual_interfaces)(virtualInterfaceId=virtual_interface_id)
    return vi['virtualInterfaces'][0]


def assemble_params_for_creating_vi(params):
    '''
        Returns kwargs to use in the call to create the virtual interface

        Params for public virtual interfaces:
        virtualInterfaceName, vlan, asn, authKey, amazonAddress, customerAddress, addressFamily, cidr
        Params for private virtual interfaces:
        virtualInterfaceName, vlan, asn, authKey, amazonAddress, customerAddress, addressFamily, virtualGatewayId
    '''

    public = params['public']
    name = params['name']
    vlan = params['vlan']
    bgp_asn = params['bgp_asn']
    auth_key = params['authentication_key']
    amazon_addr = params['amazon_address']
    customer_addr = params['customer_address']
    family_addr = params['address_type']
    cidr = params['cidr']
    virtual_gateway_id = params['virtual_gateway_id']

    parameters = dict(virtualInterfaceName=name, vlan=vlan, asn=bgp_asn)
    opt_params = dict(authKey=auth_key, amazonAddress=amazon_addr, customerAddress=customer_addr, addressFamily=family_addr)

    for name, value in opt_params.items():
        if value:
            parameters[name] = value

    # virtual interface type specific parameters
    if public and cidr:
        parameters['routeFilterPrefixes'] = [{'cidr': c} for c in cidr]
    if not public:
        parameters['virtualGatewayId'] = virtual_gateway_id

    return parameters


def create_vi(client, public, associated_id, creation_params):
    '''
        :param public: a boolean
        :param associated_id: a link aggregation group ID or connection ID to associate
                              with the virtual interface.
        :param creation_params: a dict of parameters to use in the boto call
        :return The ID of the created virtual interface
    '''
    err_msg = "Failed to create virtual interface"
    if public:
        vi = try_except_ClientError(failure_msg=err_msg)(client.create_public_virtual_interface)(connectionId=associated_id,
                                                                                                 newPublicVirtualInterface=creation_params)
    else:
        vi = try_except_ClientError(failure_msg=err_msg)(client.create_private_virtual_interface)(connectionId=associated_id,
                                                                                                  newPrivateVirtualInterface=creation_params)
    return vi['virtualInterfaceId']


def modify_vi(client, virtual_interface_id, connection_id):
    '''
        Associate a new connection ID
    '''
    err_msg = "Unable to associate {0} with virtual interface {1}".format(connection_id, virtual_interface_id)
    try_except_ClientError(failure_msg=err_msg)(client.associate_virtual_interface)(virtualInterfaceId=virtual_interface_id,
                                                                                    connectionId=connection_id)


def needs_modification(client, virtual_interface_id, connection_id):
    '''
        Determine if the associated connection ID needs to be updated
    '''
    return vi_state(client, virtual_interface_id).get('connectionId') != connection_id


def ensure_state(connection, module):
    changed = False

    state = module.params['state']
    connection_id = module.params['id_to_associate']
    public = module.params['public']
    name = module.params['name']

    virtual_interface_id = find_unique_vi(connection, connection_id, module.params.get('virtual_interface_id'), name)

    if virtual_interface_id is False:
        module.fail_json(msg="Multiple virtual interfaces were found. Use the virtual_interface_id, name, "
                         "and connection_id options if applicable to find a unique match.")

    if state == 'present':

        if not virtual_interface_id and module.params['virtual_interface_id']:
            module.fail_json(msg="The virtual interface {0} does not exist.".format(module.params['virtual_interface_id']))

        elif not virtual_interface_id:
            assembled_params = assemble_params_for_creating_vi(module.params)
            virtual_interface_id = create_vi(connection, public, connection_id, assembled_params)
            changed = True

        if needs_modification(connection, virtual_interface_id, connection_id):
            modify_vi(connection, virtual_interface_id, connection_id)
            changed = True

        latest_state = vi_state(connection, virtual_interface_id)

    else:
        if virtual_interface_id:
            delete_virtual_interface(connection, virtual_interface_id)
            changed = True

        latest_state = {}

    return changed, latest_state


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent']),
        id_to_associate=dict(required=True, aliases=['link_aggregation_group_id', 'connection_id']),
        public=dict(type='bool'),
        name=dict(),
        vlan=dict(type='int', default=100),
        bgp_asn=dict(type='int', default=65000),
        authentication_key=dict(),
        amazon_address=dict(),
        customer_address=dict(),
        address_type=dict(),
        cidr=dict(type='list'),
        virtual_gateway_id=dict(),
        virtual_interface_id=dict()
    ))

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_one_of=[['virtual_interface_id', 'name']],
                              required_if=[['state', 'present', ['public']],
                                           ['public', False, ['virtual_gateway_id']],
                                           ['public', True, ['amazon_address']],
                                           ['public', True, ['customer_address']],
                                           ['public', True, ['cidr']]])

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    connection = boto3_conn(module, conn_type='client', resource='directconnect', region=region, endpoint=ec2_url, **aws_connect_kwargs)

    try:
        changed, latest_state = ensure_state(connection, module)
    except DirectConnectError as e:
        if e.exception:
            module.fail_json_aws(exception=e.exception, msg=e.msg)
        else:
            module.fail_json(msg=e.msg)

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(latest_state))


if __name__ == '__main__':
    main()
