#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: ec2_vpc_vpn
short_description: Create, modify, and delete EC2 VPN connections.
description:
  - This module creates, modifies, and deletes VPN connections. Idempotence is achieved by using the filters
    option or specifying the VPN connection identifier.
version_added: "2.4"
extends_documentation_fragment:
 - ec2
 - aws
requirements: ['boto3', 'botocore']
author: "Sloane Hertel (@s-hertel)"
options:
  state:
    description:
      - The desired state of the VPN connection.
    choices: ['present', 'absent']
    default: present
    required: no
  customer_gateway_id:
    description:
      - The ID of the customer gateway.
  connection_type:
    description:
      - The type of VPN connection.
    choices: ['ipsec.1']
    default: ipsec.1
  vpn_gateway_id:
    description:
      - The ID of the virtual private gateway.
  vpn_connection_id:
    description:
      - The ID of the VPN connection. Required to modify or delete a connection if the filters option does not provide a unique match.
  tags:
    description:
      - Tags to attach to the VPN connection.
  purge_tags:
    description:
      - Whether or not to delete VPN connections tags that are associated with the connection but not specified in the task.
    type: bool
    default: false
  static_only:
    description:
      - Indicates whether the VPN connection uses static routes only. Static routes must be used for devices that don't support BGP.
    default: False
    type: bool
    required: no
  tunnel_options:
    description:
      - An optional list object containing no more than two dict members, each of which may contain 'TunnelInsideCidr'
        and/or 'PreSharedKey' keys with appropriate string values.  AWS defaults will apply in absence of either of
        the aforementioned keys.
    required: no
    version_added: "2.5"
  filters:
    description:
      - An alternative to using vpn_connection_id. If multiple matches are found, vpn_connection_id is required.
        If one of the following suboptions is a list of items to filter by, only one item needs to match to find the VPN
        that correlates. e.g. if the filter 'cidr' is ['194.168.2.0/24', '192.168.2.0/24'] and the VPN route only has the
        destination cidr block of '192.168.2.0/24' it will be found with this filter (assuming there are not multiple
        VPNs that are matched). Another example, if the filter 'vpn' is equal to ['vpn-ccf7e7ad', 'vpn-cb0ae2a2'] and one
        of of the VPNs has the state deleted (exists but is unmodifiable) and the other exists and is not deleted,
        it will be found via this filter. See examples.
    suboptions:
      cgw-config:
        description:
          - The customer gateway configuration of the VPN as a string (in the format of the return value) or a list of those strings.
      static-routes-only:
        description:
          - The type of routing; true or false.
      cidr:
        description:
          - The destination cidr of the VPN's route as a string or a list of those strings.
      bgp:
        description:
          - The BGP ASN number associated with a BGP device. Only works if the connection is attached.
            This filtering option is currently not working.
      vpn:
        description:
          - The VPN connection id as a string or a list of those strings.
      vgw:
        description:
          - The virtual private gateway as a string or a list of those strings.
      tag-keys:
        description:
          - The key of a tag as a string or a list of those strings.
      tag-values:
        description:
          - The value of a tag as a string or a list of those strings.
      tags:
        description:
          - A dict of key value pairs.
      cgw:
        description:
          - The customer gateway id as a string or a list of those strings.
  routes:
    description:
      - Routes to add to the connection.
  purge_routes:
    description:
      - Whether or not to delete VPN connections routes that are not specified in the task.
    type: bool
  wait_timeout:
    description:
      - How long before wait gives up, in seconds.
    default: 600
    type: int
    required: false
    version_added: "2.8"
  delay:
    description:
      - The time to wait before checking operation again. in seconds.
    required: false
    type: int
    default: 15
    version_added: "2.8"
"""

EXAMPLES = """
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.

- name: create a VPN connection
  ec2_vpc_vpn:
    state: present
    vpn_gateway_id: vgw-XXXXXXXX
    customer_gateway_id: cgw-XXXXXXXX

- name: modify VPN connection tags
  ec2_vpc_vpn:
    state: present
    vpn_connection_id: vpn-XXXXXXXX
    tags:
      Name: ansible-tag-1
      Other: ansible-tag-2

- name: delete a connection
  ec2_vpc_vpn:
    vpn_connection_id: vpn-XXXXXXXX
    state: absent

- name: modify VPN tags (identifying VPN by filters)
  ec2_vpc_vpn:
    state: present
    filters:
      cidr: 194.168.1.0/24
      tag-keys:
        - Ansible
        - Other
    tags:
      New: Tag
    purge_tags: true
    static_only: true

- name: set up VPN with tunnel options utilizing 'TunnelInsideCidr' only
  ec2_vpc_vpn:
    state: present
    filters:
      vpn: vpn-XXXXXXXX
    static_only: true
    tunnel_options:
      -
        TunnelInsideCidr: '169.254.100.1/30'
      -
        TunnelInsideCidr: '169.254.100.5/30'

- name: add routes and remove any preexisting ones
  ec2_vpc_vpn:
    state: present
    filters:
      vpn: vpn-XXXXXXXX
    routes:
      - 195.168.2.0/24
      - 196.168.2.0/24
    purge_routes: true

- name: remove all routes
  ec2_vpc_vpn:
    state: present
    vpn_connection_id: vpn-XXXXXXXX
    routes: []
    purge_routes: true

- name: delete a VPN identified by filters
  ec2_vpc_vpn:
    state: absent
    filters:
      tags:
        Ansible: Tag
"""

RETURN = """
changed:
  description: If the VPN connection has changed.
  type: bool
  returned: always
  sample:
    changed: true
customer_gateway_configuration:
  description: The configuration of the VPN connection.
  returned: I(state=present)
  type: str
customer_gateway_id:
  description: The customer gateway connected via the connection.
  type: str
  returned: I(state=present)
  sample:
    customer_gateway_id: cgw-1220c87b
vpn_gateway_id:
  description: The virtual private gateway connected via the connection.
  type: str
  returned: I(state=present)
  sample:
    vpn_gateway_id: vgw-cb0ae2a2
options:
  description: The VPN connection options (currently only containing static_routes_only).
  type: complex
  returned: I(state=present)
  contains:
    static_routes_only:
      description: If the VPN connection only allows static routes.
      returned: I(state=present)
      type: str
      sample:
        static_routes_only: true
routes:
  description: The routes of the VPN connection.
  type: list
  returned: I(state=present)
  sample:
    routes: [{
              'destination_cidr_block': '192.168.1.0/24',
              'state': 'available'
            }]
state:
  description: The status of the VPN connection.
  type: str
  returned: I(state=present)
  sample:
    state: available
tags:
  description: The tags associated with the connection.
  type: dict
  returned: I(state=present)
  sample:
    tags:
      name: ansible-test
      other: tag
type:
  description: The type of VPN connection (currently only ipsec.1 is available).
  type: str
  returned: I(state=present)
  sample:
    type: "ipsec.1"
vgw_telemetry:
  type: list
  returned: I(state=present)
  description: The telemetry for the VPN tunnel.
  sample:
    vgw_telemetry: [{
                     'outside_ip_address': 'string',
                     'status': 'up',
                     'last_status_change': 'datetime(2015, 1, 1)',
                     'status_message': 'string',
                     'accepted_route_count': 123
                    }]
vpn_connection_id:
  description: The identifier for the VPN connection.
  type: str
  returned: I(state=present)
  sample:
    vpn_connection_id: vpn-781e0e19
"""

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils._text import to_text
from ansible.module_utils.ec2 import (
    camel_dict_to_snake_dict,
    boto3_tag_list_to_ansible_dict,
    compare_aws_tags,
    ansible_dict_to_boto3_tag_list,
)

try:
    from botocore.exceptions import BotoCoreError, ClientError, WaiterError
except ImportError:
    pass  # Handled by AnsibleAWSModule


class VPNConnectionException(Exception):
    def __init__(self, msg, exception=None):
        self.msg = msg
        self.exception = exception


def find_connection(connection, module_params, vpn_connection_id=None):
    ''' Looks for a unique VPN connection. Uses find_connection_response() to return the connection found, None,
        or raise an error if there were multiple viable connections. '''

    filters = module_params.get('filters')

    # vpn_connection_id may be provided via module option; takes precedence over any filter values
    if not vpn_connection_id and module_params.get('vpn_connection_id'):
        vpn_connection_id = module_params.get('vpn_connection_id')

    if not isinstance(vpn_connection_id, list) and vpn_connection_id:
        vpn_connection_id = [to_text(vpn_connection_id)]
    elif isinstance(vpn_connection_id, list):
        vpn_connection_id = [to_text(connection) for connection in vpn_connection_id]

    formatted_filter = []
    # if vpn_connection_id is provided it will take precedence over any filters since it is a unique identifier
    if not vpn_connection_id:
        formatted_filter = create_filter(module_params, provided_filters=filters)

    # see if there is a unique matching connection
    try:
        if vpn_connection_id:
            existing_conn = connection.describe_vpn_connections(VpnConnectionIds=vpn_connection_id,
                                                                Filters=formatted_filter)
        else:
            existing_conn = connection.describe_vpn_connections(Filters=formatted_filter)
    except (BotoCoreError, ClientError) as e:
        raise VPNConnectionException(msg="Failed while describing VPN connection.",
                                     exception=e)

    return find_connection_response(connections=existing_conn)


def add_routes(connection, vpn_connection_id, routes_to_add):
    for route in routes_to_add:
        try:
            connection.create_vpn_connection_route(VpnConnectionId=vpn_connection_id,
                                                   DestinationCidrBlock=route)
        except (BotoCoreError, ClientError) as e:
            raise VPNConnectionException(msg="Failed while adding route {0} to the VPN connection {1}.".format(route, vpn_connection_id),
                                         exception=e)


def remove_routes(connection, vpn_connection_id, routes_to_remove):
    for route in routes_to_remove:
        try:
            connection.delete_vpn_connection_route(VpnConnectionId=vpn_connection_id,
                                                   DestinationCidrBlock=route)
        except (BotoCoreError, ClientError) as e:
            raise VPNConnectionException(msg="Failed to remove route {0} from the VPN connection {1}.".format(route, vpn_connection_id),
                                         exception=e)


def create_filter(module_params, provided_filters):
    """ Creates a filter using the user-specified parameters and unmodifiable options that may have been specified in the task """
    boto3ify_filter = {'cgw-config': 'customer-gateway-configuration',
                       'static-routes-only': 'option.static-routes-only',
                       'cidr': 'route.destination-cidr-block',
                       'bgp': 'bgp-asn',
                       'vpn': 'vpn-connection-id',
                       'vgw': 'vpn-gateway-id',
                       'tag-keys': 'tag-key',
                       'tag-values': 'tag-value',
                       'tags': 'tag',
                       'cgw': 'customer-gateway-id'}

    # unmodifiable options and their filter name counterpart
    param_to_filter = {"customer_gateway_id": "customer-gateway-id",
                       "vpn_gateway_id": "vpn-gateway-id",
                       "vpn_connection_id": "vpn-connection-id"}

    flat_filter_dict = {}
    formatted_filter = []

    for raw_param in dict(provided_filters):

        # fix filter names to be recognized by boto3
        if raw_param in boto3ify_filter:
            param = boto3ify_filter[raw_param]
            provided_filters[param] = provided_filters.pop(raw_param)
        elif raw_param in list(boto3ify_filter.items()):
            param = raw_param
        else:
            raise VPNConnectionException(msg="{0} is not a valid filter.".format(raw_param))

        # reformat filters with special formats
        if param == 'tag':
            for key in provided_filters[param]:
                formatted_key = 'tag:' + key
                if isinstance(provided_filters[param][key], list):
                    flat_filter_dict[formatted_key] = str(provided_filters[param][key])
                else:
                    flat_filter_dict[formatted_key] = [str(provided_filters[param][key])]
        elif param == 'option.static-routes-only':
            flat_filter_dict[param] = [str(provided_filters[param]).lower()]
        else:
            if isinstance(provided_filters[param], list):
                flat_filter_dict[param] = provided_filters[param]
            else:
                flat_filter_dict[param] = [str(provided_filters[param])]

    # if customer_gateway, vpn_gateway, or vpn_connection was specified in the task but not the filter, add it
    for param in param_to_filter:
        if param_to_filter[param] not in flat_filter_dict and module_params.get(param):
            flat_filter_dict[param_to_filter[param]] = [module_params.get(param)]

    # change the flat dict into something boto3 will understand
    formatted_filter = [{'Name': key, 'Values': value} for key, value in flat_filter_dict.items()]

    return formatted_filter


def find_connection_response(connections=None):
    """ Determine if there is a viable unique match in the connections described. Returns the unique VPN connection if one is found,
        returns None if the connection does not exist, raise an error if multiple matches are found. """

    # Found no connections
    if not connections or 'VpnConnections' not in connections:
        return None

    # Too many results
    elif connections and len(connections['VpnConnections']) > 1:
        viable = []
        for each in connections['VpnConnections']:
            # deleted connections are not modifiable
            if each['State'] not in ("deleted", "deleting"):
                viable.append(each)
        if len(viable) == 1:
            # Found one viable result; return unique match
            return viable[0]
        elif len(viable) == 0:
            # Found a result but it was deleted already; since there was only one viable result create a new one
            return None
        else:
            raise VPNConnectionException(msg="More than one matching VPN connection was found. "
                                         "To modify or delete a VPN please specify vpn_connection_id or add filters.")

    # Found unique match
    elif connections and len(connections['VpnConnections']) == 1:
        # deleted connections are not modifiable
        if connections['VpnConnections'][0]['State'] not in ("deleted", "deleting"):
            return connections['VpnConnections'][0]


def create_connection(connection, customer_gateway_id, static_only, vpn_gateway_id, connection_type, max_attempts, delay, tunnel_options=None):
    """ Creates a VPN connection """

    options = {'StaticRoutesOnly': static_only}
    if tunnel_options and len(tunnel_options) <= 2:
        t_opt = []
        for m in tunnel_options:
            # See Boto3 docs regarding 'create_vpn_connection'
            # tunnel options for allowed 'TunnelOptions' keys.
            if not isinstance(m, dict):
                raise TypeError("non-dict list member")
            t_opt.append(m)
        if t_opt:
            options['TunnelOptions'] = t_opt

    if not (customer_gateway_id and vpn_gateway_id):
        raise VPNConnectionException(msg="No matching connection was found. To create a new connection you must provide "
                                     "both vpn_gateway_id and customer_gateway_id.")
    try:
        vpn = connection.create_vpn_connection(Type=connection_type,
                                               CustomerGatewayId=customer_gateway_id,
                                               VpnGatewayId=vpn_gateway_id,
                                               Options=options)
        connection.get_waiter('vpn_connection_available').wait(
            VpnConnectionIds=[vpn['VpnConnection']['VpnConnectionId']],
            WaiterConfig={'Delay': delay, 'MaxAttempts': max_attempts}
        )
    except WaiterError as e:
        raise VPNConnectionException(msg="Failed to wait for VPN connection {0} to be available".format(vpn['VpnConnection']['VpnConnectionId']),
                                     exception=e)
    except (BotoCoreError, ClientError) as e:
        raise VPNConnectionException(msg="Failed to create VPN connection",
                                     exception=e)

    return vpn['VpnConnection']


def delete_connection(connection, vpn_connection_id, delay, max_attempts):
    """ Deletes a VPN connection """
    try:
        connection.delete_vpn_connection(VpnConnectionId=vpn_connection_id)
        connection.get_waiter('vpn_connection_deleted').wait(
            VpnConnectionIds=[vpn_connection_id],
            WaiterConfig={'Delay': delay, 'MaxAttempts': max_attempts}
        )
    except WaiterError as e:
        raise VPNConnectionException(msg="Failed to wait for VPN connection {0} to be removed".format(vpn_connection_id),
                                     exception=e)
    except (BotoCoreError, ClientError) as e:
        raise VPNConnectionException(msg="Failed to delete the VPN connection: {0}".format(vpn_connection_id),
                                     exception=e)


def add_tags(connection, vpn_connection_id, add):
    try:
        connection.create_tags(Resources=[vpn_connection_id],
                               Tags=add)
    except (BotoCoreError, ClientError) as e:
        raise VPNConnectionException(msg="Failed to add the tags: {0}.".format(add),
                                     exception=e)


def remove_tags(connection, vpn_connection_id, remove):
    # format tags since they are a list in the format ['tag1', 'tag2', 'tag3']
    key_dict_list = [{'Key': tag} for tag in remove]
    try:
        connection.delete_tags(Resources=[vpn_connection_id],
                               Tags=key_dict_list)
    except (BotoCoreError, ClientError) as e:
        raise VPNConnectionException(msg="Failed to remove the tags: {0}.".format(remove),
                                     exception=e)


def check_for_update(connection, module_params, vpn_connection_id):
    """ Determines if there are any tags or routes that need to be updated. Ensures non-modifiable attributes aren't expected to change. """
    tags = module_params.get('tags')
    routes = module_params.get('routes')
    purge_tags = module_params.get('purge_tags')
    purge_routes = module_params.get('purge_routes')

    vpn_connection = find_connection(connection, module_params, vpn_connection_id=vpn_connection_id)
    current_attrs = camel_dict_to_snake_dict(vpn_connection)

    # Initialize changes dict
    changes = {'tags_to_add': [],
               'tags_to_remove': [],
               'routes_to_add': [],
               'routes_to_remove': []}

    # Get changes to tags
    current_tags = boto3_tag_list_to_ansible_dict(current_attrs.get('tags', []), u'key', u'value')
    tags_to_add, changes['tags_to_remove'] = compare_aws_tags(current_tags, tags, purge_tags)
    changes['tags_to_add'] = ansible_dict_to_boto3_tag_list(tags_to_add)
    # Get changes to routes
    if 'Routes' in vpn_connection:
        current_routes = [route['DestinationCidrBlock'] for route in vpn_connection['Routes']]
        if purge_routes:
            changes['routes_to_remove'] = [old_route for old_route in current_routes if old_route not in routes]
        changes['routes_to_add'] = [new_route for new_route in routes if new_route not in current_routes]

    # Check if nonmodifiable attributes are attempted to be modified
    for attribute in current_attrs:
        if attribute in ("tags", "routes", "state"):
            continue
        elif attribute == 'options':
            will_be = module_params.get('static_only', None)
            is_now = bool(current_attrs[attribute]['static_routes_only'])
            attribute = 'static_only'
        elif attribute == 'type':
            will_be = module_params.get("connection_type", None)
            is_now = current_attrs[attribute]
        else:
            is_now = current_attrs[attribute]
            will_be = module_params.get(attribute, None)

        if will_be is not None and to_text(will_be) != to_text(is_now):
            raise VPNConnectionException(msg="You cannot modify {0}, the current value of which is {1}. Modifiable VPN "
                                         "connection attributes are tags and routes. The value you tried to change it to "
                                         "is {2}.".format(attribute, is_now, will_be))

    return changes


def make_changes(connection, vpn_connection_id, changes):
    """ changes is a dict with the keys 'tags_to_add', 'tags_to_remove', 'routes_to_add', 'routes_to_remove',
        the values of which are lists (generated by check_for_update()).
    """
    changed = False

    if changes['tags_to_add']:
        changed = True
        add_tags(connection, vpn_connection_id, changes['tags_to_add'])

    if changes['tags_to_remove']:
        changed = True
        remove_tags(connection, vpn_connection_id, changes['tags_to_remove'])

    if changes['routes_to_add']:
        changed = True
        add_routes(connection, vpn_connection_id, changes['routes_to_add'])

    if changes['routes_to_remove']:
        changed = True
        remove_routes(connection, vpn_connection_id, changes['routes_to_remove'])

    return changed


def get_check_mode_results(connection, module_params, vpn_connection_id=None, current_state=None):
    """ Returns the changes that would be made to a VPN Connection """
    state = module_params.get('state')
    if state == 'absent':
        if vpn_connection_id:
            return True, {}
        else:
            return False, {}

    changed = False
    results = {'customer_gateway_configuration': '',
               'customer_gateway_id': module_params.get('customer_gateway_id'),
               'vpn_gateway_id': module_params.get('vpn_gateway_id'),
               'options': {'static_routes_only': module_params.get('static_only')},
               'routes': [module_params.get('routes')]}

    # get combined current tags and tags to set
    present_tags = module_params.get('tags')
    if current_state and 'Tags' in current_state:
        current_tags = boto3_tag_list_to_ansible_dict(current_state['Tags'])
        if module_params.get('purge_tags'):
            if current_tags != present_tags:
                changed = True
        elif current_tags != present_tags:
            if not set(present_tags.keys()) < set(current_tags.keys()):
                changed = True
            # add preexisting tags that new tags didn't overwrite
            present_tags.update((tag, current_tags[tag]) for tag in current_tags if tag not in present_tags)
        elif current_tags.keys() == present_tags.keys() and set(present_tags.values()) != set(current_tags.values()):
            changed = True
    elif module_params.get('tags'):
        changed = True
    if present_tags:
        results['tags'] = present_tags

    # get combined current routes and routes to add
    present_routes = module_params.get('routes')
    if current_state and 'Routes' in current_state:
        current_routes = [route['DestinationCidrBlock'] for route in current_state['Routes']]
        if module_params.get('purge_routes'):
            if set(current_routes) != set(present_routes):
                changed = True
        elif set(present_routes) != set(current_routes):
            if not set(present_routes) < set(current_routes):
                changed = True
            present_routes.extend([route for route in current_routes if route not in present_routes])
    elif module_params.get('routes'):
        changed = True
    results['routes'] = [{"destination_cidr_block": cidr, "state": "available"} for cidr in present_routes]

    # return the vpn_connection_id if it's known
    if vpn_connection_id:
        results['vpn_connection_id'] = vpn_connection_id
    else:
        changed = True
        results['vpn_connection_id'] = 'vpn-XXXXXXXX'

    return changed, results


def ensure_present(connection, module_params, check_mode=False):
    """ Creates and adds tags to a VPN connection. If the connection already exists update tags. """
    vpn_connection = find_connection(connection, module_params)
    changed = False
    delay = module_params.get('delay')
    max_attempts = module_params.get('wait_timeout') // delay

    # No match but vpn_connection_id was specified.
    if not vpn_connection and module_params.get('vpn_connection_id'):
        raise VPNConnectionException(msg="There is no VPN connection available or pending with that id. Did you delete it?")

    # Unique match was found. Check if attributes provided differ.
    elif vpn_connection:
        vpn_connection_id = vpn_connection['VpnConnectionId']
        # check_for_update returns a dict with the keys tags_to_add, tags_to_remove, routes_to_add, routes_to_remove
        changes = check_for_update(connection, module_params, vpn_connection_id)
        if check_mode:
            return get_check_mode_results(connection, module_params, vpn_connection_id, current_state=vpn_connection)
        changed = make_changes(connection, vpn_connection_id, changes)

    # No match was found. Create and tag a connection and add routes.
    else:
        changed = True
        if check_mode:
            return get_check_mode_results(connection, module_params)
        vpn_connection = create_connection(connection,
                                           customer_gateway_id=module_params.get('customer_gateway_id'),
                                           static_only=module_params.get('static_only'),
                                           vpn_gateway_id=module_params.get('vpn_gateway_id'),
                                           connection_type=module_params.get('connection_type'),
                                           tunnel_options=module_params.get('tunnel_options'),
                                           max_attempts=max_attempts,
                                           delay=delay)
        changes = check_for_update(connection, module_params, vpn_connection['VpnConnectionId'])
        _ = make_changes(connection, vpn_connection['VpnConnectionId'], changes)

    # get latest version if a change has been made and make tags output nice before returning it
    if vpn_connection:
        vpn_connection = find_connection(connection, module_params, vpn_connection['VpnConnectionId'])
        if 'Tags' in vpn_connection:
            vpn_connection['Tags'] = boto3_tag_list_to_ansible_dict(vpn_connection['Tags'])

    return changed, vpn_connection


def ensure_absent(connection, module_params, check_mode=False):
    """ Deletes a VPN connection if it exists. """
    vpn_connection = find_connection(connection, module_params)

    if check_mode:
        return get_check_mode_results(connection, module_params, vpn_connection['VpnConnectionId'] if vpn_connection else None)

    delay = module_params.get('delay')
    max_attempts = module_params.get('wait_timeout') // delay

    if vpn_connection:
        delete_connection(connection, vpn_connection['VpnConnectionId'], delay=delay, max_attempts=max_attempts)
        changed = True
    else:
        changed = False

    return changed, {}


def main():
    argument_spec = dict(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        filters=dict(type='dict', default={}),
        vpn_gateway_id=dict(type='str'),
        tags=dict(default={}, type='dict'),
        connection_type=dict(default='ipsec.1', type='str'),
        tunnel_options=dict(no_log=True, type='list', default=[]),
        static_only=dict(default=False, type='bool'),
        customer_gateway_id=dict(type='str'),
        vpn_connection_id=dict(type='str'),
        purge_tags=dict(type='bool', default=False),
        routes=dict(type='list', default=[]),
        purge_routes=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default=600),
        delay=dict(type='int', default=15),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True)
    connection = module.client('ec2')

    state = module.params.get('state')
    parameters = dict(module.params)

    try:
        if state == 'present':
            changed, response = ensure_present(connection, parameters, module.check_mode)
        elif state == 'absent':
            changed, response = ensure_absent(connection, parameters, module.check_mode)
    except VPNConnectionException as e:
        if e.exception:
            module.fail_json_aws(e.exception, msg=e.msg)
        else:
            module.fail_json(msg=e.msg)

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(response))


if __name__ == '__main__':
    main()
