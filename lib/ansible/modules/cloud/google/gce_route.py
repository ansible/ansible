#!/usr/bin/python
#
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gce_route
version_added: "2.5"
short_description: Create or Destroy GCE routes
description:
    - This module can create and destroy Google Compute Engine routes
      U(https://cloud.google.com/compute/docs/vpc/routes).
      Installation/configuration instructions for the gce* modules can
      be found at U(https://docs.ansible.com/ansible/guide_gce.html).
requirements:
  - 'python >= 2.6'
  - 'google-api-python-client >= 1.6.2'
  - 'google-auth >= 1.0.0'
  - 'google-auth-httplib2 >= 0.0.2'
author:
- "Nikolaos Kakouros (@tterranigma) <tterranigma@gmail.com>"
options:
    name:
        description:
            - The name of the route. Up to 63 lowercase letters, numbers or hyphens.
            - It cannot end with a hyphen and it must start with a lowercase letter.
        required: true
    description:
        description:
            - A description for the route.
    network:
        description:
            - The network that the route applies to.
        default: "default"
    destination:
        description:
            - Packets destined to this destination will be routed according to the route.
            - It should be either an IP address or a subnet range in CIDR notation.
        required: true
    priority:
        description:
            - The priority of the rule.
            - Lower numeric values mean higher priority.
        default: 500
    instance_tags:
        description:
            - The route will apply only to traffic stemming from instances that have these tags.
            - If empty, the route will apply to all traffic.
            - Example [tag1, tag2]
        aliases: ['value']
    next_hop:
        description:
            - Where traffic should be directed next.
            - Traffic from instances that the route is valid for (eg those have the I(instance_tags)) will be directed to the I(next_hop).
            - Valid values are either an instance name or an IP address from the I(network) range.
            - A value of I(default) means the default GCE gateway.
        default: "default"
    state:
        description:
            - Whether the given resource record should or should not be present.
        choices: ["present", "absent"]
        default: "present"
notes:
- GCE does not support updating routes. This module "emulates" updating by deleting an existing route and then creating a new one.
- This module does not yet support VPNs as next hops.
'''

EXAMPLES = '''
# Create a route with cidr destination and instace as next hop
- gce_route:
      name: myroute
      network: default
      destination: 10.200.0.0/20
      priority: 1000
      description: a description here
      next_hop: an-instance

# Create a route with single node destination and IP address as next hop
- gce_route:
      name: myroute
      network: default
      destination: 10.200.0.2
      next_hop: 10.132.0.22

# Create a route with the default gateway as next hop and all the other defaults
- gce_route:
      name: myroute
      destination: 10.200.0.0/20
'''

RETURN = '''
name:
    description: the name of the created rule
    returned: Always.
    type: string
    sample: ids-route

description:
    description: the description of the route
    returned: Always.
    type: string
    sample: As given in the task definition.

network:
    description: the network the route applied to
    returned: Always.
    type: string
    sample: custom-net1

network_url:
    description: the network resource uri for the network specified
    returned: Always.
    type: string
    sample: custom-net1

destination:
    description: packet destination the route applied to
    returned: Always.
    type: string
    sample: 10.200.0.0/20

priority:
    description: priority of the route
    returned: Always.
    type: int
    sample: 700

instance_tags:
    description: tags of instances the route applied to
    returned: Always.
    type: list
    sample: [vpn, ids]

next_hop:
    description: where the route delivers traffic to
    returned: Always.
    type: string
    sample:
        - 10.138.0.13
        - vpn_instance
        - default

nextHopInstance:
    description: the resource uri for the next_hop instance specified
    returned: I(state) == 'present' and I(next_hop) is a valid instance name
    type: string
    sample: https://www.googleapis.com/compute/v1/projects/myproject/zones/europe-west1-b/instances/my-instance

nextHopIp:
    description: the ip address of the next_hop
    returned: I(state) == 'present' and I(next_hop) is an IP address
    type: string
    sample: 10.0.0.12

nextHopGateway:
    description: the resource uri for the default gateway
    returned: I(state) == 'present' and I(next_hop) == 'default'
    type: string
    sample: https://www.googleapis.com/compute/v1/projects/myproject/global/gateways/default-internet-gateway

state:
    description: whether the route is present or absent
    returned: Always.
    type: string
    sample: present
'''

################################################################################
# Imports
################################################################################

try:
    from ast import literal_eval
    HAS_PYTHON26 = True
except ImportError:
    HAS_PYTHON26 = False

# Ansible
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gcp import get_google_api_client, GCPUtils

# module specific imports
import re
from sys import version_info

try:
    from netaddr import AddrFormatError, IPNetwork, IPRange, IPAddress
    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False


################################################################################
# Constants
################################################################################

UA_PRODUCT = 'ansible-gce_route'
UA_VERSION = '0.0.1'
GCE_API_VERSION = 'v1'


################################################################################
# Functions
################################################################################

def check_python(module):
    if not HAS_PYTHON26:
        module.fail_json(
            msg="GCE module requires python's 'ast' module, python v2.6+")

    if not HAS_NETADDR:
        module.fail_json(
            msg="The gce_route module requires python-netaddr be installed on the ansible controller")


def get_resources(module, client, cparams):

    params = module.params

    # A dict to store resources retrieved from GCE. A value of 'None' means that
    # no resource was found.
    resources = {
        'instances': None,
        'route': None,
        'network': None,
    }

    # INSTANCE
    # Starts with lowercase letter, contains only lowercase letters, nubmers,
    # hyphens, cannot be empty, cannot end with hyphen. Taken directly for GCE
    # error responses.
    name_regexp = r"^(?:[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?)$"

    # Although we repeat this check in `check_parameter_format()`, we are also
    # doing it here on order to contact GCE only if necessary and save some
    # time.
    if re.match(name_regexp, params['next_hop']):
        resources['instances'] = client.instances().aggregatedList(
            project=cparams['project_id'],
            filter="name eq %s" % params['next_hop'],
            maxResults=1
        ).execute()

    # NETWORK
    req = client.networks().get(project=cparams['project_id'], network=params['network'])
    resources['network'] = GCPUtils.execute_api_client_req(req, client=client, raise_404=False)

    # SUBNETS
    resources['subnets'] = client.subnetworks().aggregatedList(
        project=cparams['project_id'],
        filter="network eq %s" % resources['network']['selfLink']
    ).execute()

    # ROUTE
    req = client.routes().get(project=cparams['project_id'], route=params['name'])
    resources['route'] = GCPUtils.execute_api_client_req(req, client=client, raise_404=False)

    return resources


def check_parameter_format(module, resources):
    # All the below checks are performed to allow check_mode to give reliable
    # results.

    params = module.params

    # The (potential) error message
    msg = ''

    # Starts with lowercase letter, contains only lowercase letters, numbers,
    # hyphens, cannot be empty, cannot end with hyphen. Taken directly for GCE
    # error responses.
    name_regexp = r"^(?:[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?)$"

    # check: route name.
    matches = re.match(name_regexp, params['name'])
    if not matches:
        msg = "Route names must start with a lowercase letter, can contain only lowercase letters, " \
            + "numbers and hyphens, cannot end with a hyphen and cannot be empty."

    # check: description (length must be less than 2048 characters)
    if version_info < (3,):
        description_length = len(unicode(params['description'], "utf-8"))  # pylint: disable=E0602
    else:
        description_length = len(params['description'])

    if description_length > 2048:
        msg = "Description must be less thatn 2048 characters in length."

    # check: instance tags
    # We are also converting a single tag from string to list.
    if not isinstance(params['instance_tags'], list):
        params['instance_tags'] = [params['instance_tags']]

    if params['instance_tags']:
        for tag in params['instance_tags']:
            matches = re.match(name_regexp, tag)

            if not matches:
                msg = "Instance tags must start with a lowercase letter, can contain only lowercase letters, " \
                    + "numbers and hyphens, cannot end with a hyphen and cannot be empty."

    # check: destination (must be a valid cidr or addr)
    try:
        IPNetwork(params['destination'])
    except AddrFormatError:
        msg = "destination must be a valid IP address or cidr range, '%s' is invalid" % params['destination']

    # check: destination (should not hide existing network/subnet range)
    if check_cidr_masking(params, resources):
        msg = "The given destination %s hides the reserved address space for a network/subnet." % params['destination']

    # check: priority (should be a number between 0 and 65535 (2bytes))
    if not (0 <= int(params['priority']) < 2**16):
        msg = "Priority must be in the range [0-4294967295], %s given" % params['priority']

    # check: next_hop (three different possibilities)
    # TODO: add support for nextHopVpnTunnel - 4th possibility
    # case 1/3: 'default'
    if params['next_hop'] == 'default':
        pass
    # case 2/3: potential instance name
    elif re.match(name_regexp, params['next_hop']):
        found = False

        # Check if given instance name exists in the instances list loaded from
        # GCE. When we loaded the resource from GCE, we used a filter to return
        # only instances with the same name as the one supplied by the user. As
        # instance names are unique, we expect at most one positive result.
        # "Positive" here means to have an "instances" key in one of the 'items'
        # in the resources['instances'] dict (the "instances" key is set only
        # when an instance is found).
        for result in resources['instances']['items']:
            if 'instances' in resources['instances']['items'][result]:
                found = True
                params['next_hop_instance_url'] = resources['instances']['items'][result]['instances'][0]['selfLink']
        if not found:
            msg = 'next_hop is a valid instance name but no node with this name exists'
    # case 3/3: ip address. This is the last valid case. If matching it fails, then
    # the user has supplied garbage in the next_hop option.
    else:
        try:
            # If the user supplies sth like `123`, IPAddress will still succeed
            # and consider it the ip 0.0.0.123. So, we check for a dot first.
            if params['next_hop'].find('.') == -1:
                raise AddrFormatError

            IPAddress(params['next_hop'], version=4).__str__()

        except AddrFormatError:
            msg = 'next_hop is invalid'

    # exit
    if msg:
        module.fail_json(msg=msg, changed=False)


def check_cidr_masking(params, resources):
    # We want an IPRange object to use the IPNetwork.__contains__ method.
    dest_range = IPNetwork(params['destination'])
    dest_range = IPRange(dest_range.first, dest_range.last)

    overlap = False

    # Legacy network
    if 'IPv4Range' in resources['network']:
        net = IPNetwork('10.240.0.0/16')
        overlap |= net.__contains__(dest_range)

    # Custom / Auto mode networks
    subnets = (subnet for region in resources['subnets']['items'] for subnet in resources['subnets']['items'][region]['subnetworks'])
    for subnet in subnets:
        net = IPNetwork(subnet['ipCidrRange'])
        overlap |= net.__contains__(dest_range)

        if 'secondaryIpRanges' in subnet:
            for secondary_range in subnet['secondaryIpRanges']:
                net = IPNetwork(secondary_range['ipCidrRange'])
                overlap |= net.__contains__(dest_range)

    return overlap


def check_network_exists(module, resources):

    params = module.params
    msg = ''

    if resources['network'] is None:
        msg = 'No network %s was found' % params['network']

    if msg:
        module.fail_json(msg=msg, changed=False)
    else:
        params['network_url'] = resources['network']['selfLink']


def format_next_hop(module):
    next_hop = {}
    params = module.params

    # DEFAULT GATEWAY
    if params['next_hop'] == 'default':
        next_hop['nextHopGateway'] = 'global/gateways/default-internet-gateway'

    # IP ADDRESS
    elif re.match(r"^[1-9](.*)$", params['next_hop']):
        # in re.match() we check for the first character to see if
        # it is a number. If it is, it cannot be a valid instance
        # name. Since we have already checked for garbage values in
        # check_parameter_format(), it cannot be but an IP address.
        next_hop['nextHopIp'] = params['next_hop']
    # INSTANCE NAME
    else:
        next_hop['nextHopInstance'] = params['next_hop_instance_url']

    return next_hop


################################################################################
# Main
################################################################################

def main():
    changed = False

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            description=dict(default=''),
            network=dict(default='default'),
            destination=dict(required=True, aliases=['destRange']),
            priority=dict(default=500, type='int'),
            instance_tags=dict(default=[], type='list', aliases=['tags']),
            next_hop=dict(default='default'),
            state=dict(choices=['absent', 'present'], default='present'),
        ),
        supports_check_mode=True
    )

    params = module.params

    check_python(module)

    client, cparams = get_google_api_client(module, 'compute',
                                            user_agent_product=UA_PRODUCT,
                                            user_agent_version=UA_VERSION,
                                            api_version=GCE_API_VERSION)

    resources = get_resources(module, client, cparams)

    check_parameter_format(module, resources)

    check_network_exists(module, resources)

    # This will hold any response values grom GCE after inserting a route. The
    # response according to GCE docs is a `GlobalOperations` resource.
    glob_ops = {}

    # This will hold the next_hop setting in a way that GCE expectes it to be.
    next_hop = {}

    if params['state'] == 'present':
        # NEW ROUTE
        if resources['route'] is None:

            if not module.check_mode:

                next_hop = format_next_hop(module)

                body = {
                    "destRange": params['destination'],
                    "name": params['name'],
                    "network": params['network_url'],
                    "priority": params['priority'],
                    "tags": params['instance_tags'],
                    "description": params['description'],
                }

                body.update(next_hop)

                glob_ops = client.routes().insert(project=cparams['project_id'], body=body).execute()
                changed = True

        # EXISTING ROUTE
        else:
            # check: description
            if resources['route']['description'] != params['description']:
                changed = True

            # check: network
            # extract the network name from the network resource uri
            # (eg projects/myproject/global/networks/*default*)
            # TODO: use GCPUtils.parse_gcp_url
            gce_network = re.search(r'^.*/([a-zA-Z0-9-]+)$', resources['route']['network']).group(1)
            if gce_network != params['network']:
                changed = True

            # check: destination
            if resources['route']['destRange'] != params['destination']:
                changed = True

            # check: priority
            if resources['route']['priority'] != int(params['priority']):
                changed = True

            # check: instance_tags
            # Tags might not be set in the project; cast them to an empty list
            resources['route']['tags'] = resources['route']['tags'] or []  # pylint: disable=E1137

            # params['instance_tags'] will always be a list at this point. We
            # are converting to unordered sets for the comparison.
            if set(resources['route']['tags']) != set(params['instance_tags']):
                changed = True

            # check: next_hop
            next_hop_changed = False
            next_hop = format_next_hop(module)

            # The resource will have either a nextHopGateway, a nextHopIp or
            # nextHopInstance key.
            if 'nextHopGateway' in resources['route']:
                # This key has only one possible value, the default gateway. If
                # the user supplied `next_hop: default` we have a match.
                if params['next_hop'] != 'default':
                    next_hop_changed = True

            elif 'nextHopIp' in resources['route']:
                if resources['route']['nextHopIp'] != params['next_hop']:
                    next_hop_changed = True

            elif 'nextHopInstance' in resources['route']:
                if 'next_hop_instance_url' not in params:
                    # If the user has not set the next_hop to an instance, this
                    # key will not exist (it is set in check_params by us if
                    # next_hop is found to be an instance).
                    next_hop_changed = True
                elif resources['route']['nextHopInstance'] != params['next_hop_instance_url']:
                    next_hop_changed = True

            if next_hop_changed:
                changed = True

            if changed and not module.check_mode:
                # GCE does not allow modifying routes. We delete the old routes
                # and create a new one.

                # Delete the route. Using GCPUtils.execute_api_client_req to
                # poll for completeness of the delete operation. Without it,
                # the `insert` would happen to fast.
                del_req = client.routes().delete(project=cparams['project_id'], route=params['name'])
                GCPUtils.execute_api_client_req(del_req, client=client, raw=False)

                # Create the `new` route.
                body = {
                    "destRange": params['destination'],
                    "name": params['name'],
                    "network": params['network_url'],
                    "priority": params['priority'],
                    "tags": params['instance_tags'],
                    "description": params['description'],
                }

                body.update(next_hop)
                glob_ops = client.routes().insert(project=cparams['project_id'], body=body).execute()

    elif params['state'] == 'absent':
        del_req = client.routes().delete(project=cparams['project_id'], route=params['name'])
        glob_ops = GCPUtils.execute_api_client_req(del_req, client=client, raise_404=False)

        # If there is nothing to delete, `resp` will be None. If there was
        # sth deleted, there will something returned in the response.
        if glob_ops is not None:
            changed = True

    # Update ansible output with useful bits
    json_output = {'changed': changed}
    json_output.update(params)
    json_output.update(next_hop)
    json_output['priority'] = int(params['priority'])
    if bool(glob_ops):
        json_output['glob_ops'] = glob_ops

    # Unset some duplicate keys
    json_output.pop('next_hop_instance_url', None)

    module.exit_json(**json_output)

if __name__ == '__main__':
    main()
