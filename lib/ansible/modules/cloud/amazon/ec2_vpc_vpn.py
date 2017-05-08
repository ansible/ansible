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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: ec2_vpn
short_description:
description:
  - This module creates, modifies, and deletes VPN connections
version_added: "2.4"
author: "Sloane Hertel (@s-hertel)"
options:
  state:
    description:
      - the desired state of the vpn connection.
    choices: ['present', 'absent']
    default: present
    required: no
  customer_gateway_id:
    description:
      - The ID of the customer gateway.
  connection_type:
    description:
      - The type of VPN connection
    choices: ['ipsec.1']
    default: ipsec.1
  vpn_gateway_id:
    description:
      - The ID of the virtual private gateway.
  vpn_connection_id:
    description:
      - The ID of the vpn connection. Required to modify or delete a connection if the filters option does not provide a unique match.
  tags:
    description:
      - Tags to attach to the vpn connection
  purge_tags:
    description:
      - Whether or not to delete vpn connections tags that are associated with the connection but not specified in the task
    type: bool
    default: false
  static_only:
    description:
      - Indicates whether the VPN connection uses static routes only. Static routes must be used for devices that don't support BGP.
    default: False
    required: no
  filters:
    description:
      - An alternative to using vpn_connection_id. If multiple matches are found, vpn_connection_id is required.
    type: dict
      keys:
        - customer-gateway-configuration
          type: str
        - option.static-routes-only
          type: bool
        - route.destination-cidr-block
          type: list
        - bgp-asn
          type: str
        - vpn-connection-id
          type: str
        - vpn-gateway-id
          type: str
        - tag-keys
          type: list
        - tag-values
          type: list
        - tag
          type: dict
        - customer-gateway-id
          type: list
  check_mode:
    description:
      - see what changes will be made before making them
    default: False
    type: bool
    required: no
"""

EXAMPLES = """
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.

- name: create a vpn connection
  ec2_vpc_vpn:
    vpn_gateway_id: vgw-XXXXXXXX
    customer_gateway_id: cgw-XXXXXXXX

- name: modify vpn connection tags
  ec2_vpc_vpn:
    vpn_connection_id: vpn-XXXXXXXX
    tags:
      Name: ansible-tag-1
      Other: ansible-tag-2

- name: delete a connection
  ec2_vpc_vpn:
    vpn_connection_id: vpn-XXXXXXXX
    state: absent
"""

RETURN = """
changed:
  description: if the connection has changed
  returned: always
  sample:
    changed: true
customer_gateway_configuration:
  description: the configuration of the connection
  returned: when the connection exists
customer_gateway_id:
  description: the customer gateway connected via the connection
  type: str
  returned: when the connection exists
  sample:
    customer_gateway_id: cgw-1220c87b
vpn_gateway_id:
  description: the virtual private gateway connected via the connection
  type: str
  returned: when the connection exists
  sample:
    vpn_gateway_id: vgw-cb0ae2a2
options:
  static_routes_only:
    description: the type of routing option
    type: str
    returned: when the connection exists
    sample:
      static_routes_only: true
routes:
  description: the connection routes
  type: list
  returned: when the connection exists
  sample:
    routes: []
state:
  description: the status of the connection
  type: string
  returned: when the connection exists and is modifiable (no deleted/deleting connections)
  sample:
    state: available
type:
  description: the type of connection
  type: str
  returned: when the connection exists
  sample:
    type: "ipsec.1"
vgw_telemetry:
  description:
vpn_connection_id:
  description:
"""

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text
from ansible.module_utils.ec2 import (boto3_conn, get_aws_connection_info, ec2_argument_spec,
                                      snake_dict_to_camel_dict, camel_dict_to_snake_dict,
                                      boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_tag_list)
import traceback

try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def find_connection(module, connection, vpn_connection_id=None):
    ''' Looks for a unique VPN connection. Uses find_connection_response() to return the connection found, None,
        or raise an error if there were multiple viable connections. '''

    check_mode = module.params.get('check_mode')
    filters = module.params.get('filters')

    # vpn_connection_id may be provided via module option or parameter; parameter takes precedence
    if not vpn_connection_id and module.params.get('vpn_connection_id'):
        vpn_connection_id = module.params.get('vpn_connection_id')

    if isinstance(vpn_connection_id, str):
        vpn_connection_id = [vpn_connection_id]
    if vpn_connection_id and not isinstance(vpn_connection_id, list):
        vpn_connection_id = list(to_text(vpn_connection_id))

    formatted_filter = []
    # if vpn_connection_id is provided it will take precedence over any filters since it is a unique identifier
    if not vpn_connection_id:
        formatted_filter = create_filter(module, provided_filters=filters)

    # see if there is a unique matching connection
    try:
        if vpn_connection_id:
            existing_conn = connection.describe_vpn_connections(DryRun=check_mode,
                                                                VpnConnectionIds=vpn_connection_id,
                                                                Filters=formatted_filter)
        else:
            existing_conn = connection.describe_vpn_connections(DryRun=check_mode,
                                                                Filters=formatted_filter)
        if 'VpnConnections' not in existing_conn:
            existing_conn = None
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed while describing vpn connection.", exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    return find_connection_response(module, connections=existing_conn)


def create_filter(module, provided_filters):
    ''' Creates a filter using the user-specified parameters and unmodifiable options that may have been specified in the task '''

    # unmodifiable options and their filter name counterpart
    param_to_filter = {"customer_gateway_id": "customer-gateway-id",
                       "vpn_gateway_id": "vpn-gateway-id",
                       "vpn_connection_id": "vpn-connection-id"}
    # permitted filter options
    permitted = ("customer-gateway-configuration", "option.static-routes-only",
                 "route.destination-cidr-block", "bgp-asn", "vpn-connection-id",
                 "vpn-gateway-id", "tag", "tag-key", "tag-value", "customer-gateway-id")

    flat_filter_dict = {}
    formatted_filter = []

    for param in provided_filters:

        if param not in permitted:
            module.fail_json(msg="Unable to filter using parameter: %s. Must be one of: %s" % (param, permitted))

        # tag filter names are concatenated and separate filter options
        if param == 'tag':
            for key in provided_filters[param]:
                formatted_key = 'tag:' + key
                if isinstance(provided_filters[param][key], list):
                    flat_filter_dict[formatted_key] = provided_filters[param][key]
                else:
                    flat_filter_dict[formatted_key] = [provided_filters[param][key]]

        elif param == 'option.static-routes-only':
            flat_filter_dict[param] = [str(provided_filters[param]).lower()]

        else:
            if isinstance(provided_filters[param], list):
                flat_filter_dict[param] = provided_filters[param]
            else:
                flat_filter_dict[param] = [provided_filters[param]]

    # if customer_gateway, vpn_gateway, or vpn_connection was specified in the task but not the filter, add it
    for param in param_to_filter:

        if param_to_filter[param] in flat_filter_dict and module.params.get(param, None):
            if flat_filter_dict[param_to_filter[param]] != [module.params.get(param)]:
                module.fail_json(msg="You are filtering with the unmodifiable attribute %s with the value %s but are trying to \
                                 modify it in the task to %s. Modifiable VPN connection attributes are tags. Create a new VPN \
                                 connection to use this attribute and value." % (param, flat_filter_dict[param], module.params.get(param)))

        elif module.params.get(param, None):
            flat_filter_dict[param_to_filter[param]] = [module.params.get(param)]

    # boto3ify the flat dict
    formatted_filter = [{'Name': key, 'Values': flat_filter_dict[key]} for key in flat_filter_dict]

    return formatted_filter


def find_connection_response(module, connections=None):
    ''' Determine if there is a viable unique match in the connections described '''
    # Too many results
    if connections and len(connections['VpnConnections']) > 1:
        viable = []
        for each in connections['VpnConnections']:
            # deleted connections are not modifiable
            if each['State'] not in ("deleted", "deleting"):
                viable.append(each)
        if len(viable) == 1:
            # Found a result but it was deleted already; since there was only one viable result create a new one
            return viable[0]
        elif len(viable) == 0:
            return None
        else:
            module.fail_json(msg="More than one matching VPN connection was found."
                                 "To modify or delete a VPN please specify vpn_connection_id or add filters.")
    # Found unique match
    elif connections and len(connections['VpnConnections']) == 1:
        # deleted connections are not modifiable
        if connections['VpnConnections'][0]['State'] not in ("deleted", "deleting"):
            return connections['VpnConnections'][0]
        # Found the result but it was deleted already; since there was only one result create a new one
        else:
            return None
    # Found no connections
    else:
        return None


def create_connection(module, connection):
    ''' Creates a VPN connecion '''
    check_mode = module.params.get('check_mode')
    customer_gateway_id = module.params.get('customer_gateway_id')
    static_only = module.params.get('static_only')
    vpn_gateway_id = module.params.get('vpn_gateway_id')
    connection_type = module.params.get('connection_type')
    changed = False

    if not (customer_gateway_id and vpn_gateway_id):
        module.fail_json(msg="No matching connection was found. To create a new connection you must provide both vpn_gateway_id and customer_gateway_id.")
    try:
        vpn = connection.create_vpn_connection(DryRun=check_mode,
                                               Type=connection_type,
                                               CustomerGatewayId=customer_gateway_id,
                                               VpnGatewayId=vpn_gateway_id,
                                               Options={'StaticRoutesOnly': static_only})
        changed = True
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to create VPN Connection: %s" % e, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    return changed, vpn['VpnConnection']


def delete_connection(module, connection, vpn_connection_id):
    ''' Deletes a VPN connection '''
    check_mode = module.params.get('check_mode')

    try:
        connection.delete_vpn_connection(DryRun=check_mode,
                                         VpnConnectionId=vpn_connection_id)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to delete the connection.", exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def tag_connection(module, connection, vpn_connection_id, add=None, remove=None):
    ''' Adds and removes tags from a VPN connection '''
    check_mode = module.params.get('check_mode')
    purge_tags = module.params.get('purge_tags')
    changed = False

    if remove and purge_tags:
        try:
            connection.delete_tags(DryRun=check_mode,
                                   Resources=[vpn_connection_id],
                                   Tags=ansible_dict_to_boto3_tag_list(remove))
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to remove the tags: %s." % remove, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    if add:
        try:
            connection.create_tags(DryRun=check_mode,
                                   Resources=[vpn_connection_id],
                                   Tags=ansible_dict_to_boto3_tag_list(add))
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to add the tags: %s." % add, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    vpn_connection = find_connection(module, connection, vpn_connection_id=vpn_connection_id)

    return changed, vpn_connection


def check_for_update(module, connection, vpn_connection_id):
    ''' Determines if there are any tags that need to be updated. Ensures non-modifiable attributes aren't expected to change. '''
    # get tags and initialize current tags in case the connection currently has none
    tags = module.params.get('tags')
    current_tags = {}

    vpn_connection = find_connection(module, connection, vpn_connection_id=vpn_connection_id)
    current_attrs = camel_dict_to_snake_dict(vpn_connection)

    for attribute in current_attrs:
        # get current tags to use later
        if attribute == "tags":
            current_tags = boto3_tag_list_to_ansible_dict(current_attrs['tags'])
            continue

        # skip state
        elif attribute == "state":
            continue

        # check for attempted modifications for non-modifiable attributes
        is_now = current_attrs[attribute]
        will_be = module.params.get(attribute, None)

        if attribute == "options":
            will_be = module.params.get('static_only', None)
            is_now = bool(current_attrs[attribute]['static_routes_only'])
            attribute = 'static_only'

        elif attribute == "type":
            will_be = module.params.get("connection_type", None)
            attribute = 'type'

        if attribute != "tags" and will_be is not None and to_text(will_be) != to_text(is_now):
            module.fail_json(msg="You cannot modify %s, the current value of which is %s. Modifiable VPN connection \
                             attributes are tags. The value you tried to change it to is %s." % (attribute, is_now, will_be))

    # find tags to add/remove
    tags_to_remove = {t: current_tags[t] for t in current_tags if t not in tags}
    tags_to_add = {t: tags[t] for t in tags if t not in current_tags}

    return tags_to_add, tags_to_remove


def ensure_present(module, connection):
    ''' Creates and adds tags to a VPN connection. If the connection already exists update tags. '''
    vpn_connection = find_connection(module, connection)
    changed = False

    # No match but vpn_connection_id was specified.
    if not vpn_connection and module.params.get('vpn_connection_id'):
        module.fail_json(msg="There is no VPN connection available or pending with that id. Did you delete it?")
    # Unique match was found. Check if attributes provided differ.
    elif vpn_connection:
        tags_to_add, tags_to_remove = check_for_update(module, connection,
                                                       vpn_connection_id=vpn_connection['VpnConnectionId'])
        if tags_to_add or tags_to_remove:
            changed, vpn_connection = tag_connection(module, connection,
                                                     vpn_connection_id=vpn_connection['VpnConnectionId'],
                                                     add=tags_to_add, remove=tags_to_remove)
    # No match was found. Create and tag a connection.
    else:
        changed, vpn_connection = create_connection(module, connection)
        _, vpn_connection = tag_connection(module, connection,
                                           vpn_connection_id=vpn_connection['VpnConnectionId'],
                                           add=module.params.get('tags'))

    return changed, vpn_connection


def ensure_absent(module, connection):
    ''' Deletes a VPN connection if it exists. '''
    vpn_connection = find_connection(module, connection)

    if vpn_connection:
        delete_connection(module, connection, vpn_connection_id=vpn_connection['VpnConnectionId'])
        changed = True
    else:
        changed = False

    return changed, {}


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            filters=dict(type='dict', default={}),
            vpn_gateway_id=dict(type='str'),
            tags=dict(default={}, type='dict'),
            check_mode=dict(default=False, type='bool'),
            connection_type=dict(default='ipsec.1', type='str'),
            static_only=dict(default=False, type='bool'),
            customer_gateway_id=dict(type='str'),
            vpn_connection_id=dict(type='str'),
            purge_tags=dict(type='bool', default=False),
        )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto required for this module')

    # Retrieve any AWS settings from the environment.
    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)

    if not region:
        module.fail_json(msg="Either region or AWS_REGION or EC2_REGION environment variable or boto config aws_region or ec2_region must be set.")

    connection = boto3_conn(module, conn_type='client',
                            resource='ec2', region=region,
                            endpoint=ec2_url, **aws_connect_kwargs)

    if module.params.get('state') == 'present':
        changed, response = ensure_present(module, connection)
    elif module.params.get('state') == 'absent':
        changed, response = ensure_absent(module, connection)

    facts_result = dict(changed=changed, **camel_dict_to_snake_dict(response))

    module.exit_json(**facts_result)

if __name__ == '__main__':
    main()
