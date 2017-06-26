#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gce_route
version_added: "2.4"
short_description: Create or Destroy GCE routes
description:
    - This module can create and destroy Google Compute Engine routes
      U(https://cloud.google.com/compute/docs/vpc/routes).
      Installation/configuration instructions for the gce* modules can
      be found at U(https://docs.ansible.com/ansible/guide_gce.html).
requirements:
- "python >= 2.6"
- "apache-libcloud >= 0.17.0"
notes:
- GCE does not support updating routes. This module "emulates" updating by deleting an existing route and then creating a new one.
- This module's underlying library does not support VPNs as next hops.
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
            - Example: [tag1, tag2]
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
'''

EXAMPLES = '''
# Create an A record.
- gcdns_record:
    record: 'www1.example.com'
    zone: 'example.com'
    type: A
    value: '1.2.3.4'
'''

RETURN = '''
name:
    description: the name of the created rule
    returned: success
    type: string
    sample: ids-route
description:
    description: the description of the route
    returned: success
    type: string
    sample: As given in the task definition.
network:
    description: the network the route applied to
    returned: success
    type: string
    sample: custom-net1
destination:
    description: packet destination the route applied to
    returned: success
    type: string
    sample: 10.200.0.0/20
priority:
    description: priority of the route
    returned: success
    type: integer
    sample: 700
instance_tags:
    description: tags of instances the route applied to
    returned: success
    type: list
    sample: [vpn, ids]
next_hop:
    description: where the route delivers traffic to
    returned: success
    type: string
    sample:
        - 10.138.0.13
        - vpn_instance
        - default
state:
    description: Whether the route is present or absent
    returned: success
    type: string
    sample: present
'''

################################################################################
# Imports
################################################################################

try:
    # import libcloud
    from libcloud import __version__ as LIBCLOUD_VERSION
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import Provider
    from libcloud.common.google import GoogleBaseError, QuotaExceededError, \
        ResourceExistsError, ResourceInUseError, ResourceNotFoundError

    _ = Provider.GCE
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False

try:
    # module specific imports
    import socket, re
    from distutils.version import LooseVersion

    # import module snippets
    from ansible.module_utils.basic import AnsibleModule
    from ansible.module_utils.gce import gce_connect
except ImportError:
    module.fail_json(
        msg     = "An unexpected error has occured during import.",
        changed = False
    )


################################################################################
# Constants
################################################################################

# ex_create_route was introduced in libcloud 0.17.0
MINIMUM_LIBCLOUD_VERSION = '0.17.0'

PROVIDER = Provider.GCE


################################################################################
# Functions
################################################################################

def check_libcloud():
    # Apache libcloud needs to be installed and at least the minimum version.
    if not HAS_LIBCLOUD:
        module.fail_json(
            msg     = 'This module requires Apache libcloud %s or greater' % MINIMUM_LIBCLOUD_VERSION,
            changed = False
        )
    elif LooseVersion(LIBCLOUD_VERSION) < MINIMUM_LIBCLOUD_VERSION:
        module.fail_json(
            msg     = 'This module requires Apache libcloud %s or greater' % MINIMUM_LIBCLOUD_VERSION,
            changed = False
        )


################################################################################
# Main
################################################################################

def main():
    changed = False

    check_libcloud()

    module = AnsibleModule(
        argument_spec = dict(
            name          = dict(required=True),
            description   = dict(default=''),
            network       = dict(default='default'),
            destination   = dict(required=True),
            priority      = dict(default=500),
            instance_tags = dict(default=[], type='list', aliases=['tags']),
            next_hop      = dict(default='default'),
            state         = dict(choices=['absent', 'present'], default='present'),
        ),
        supports_check_mode=True
    )

    params = {
        'name'          : module.params['name'],
        'description'   : module.params['description'],
        'network'       : module.params['network'],
        'destination'   : module.params['destination'],
        'priority'      : module.params['priority'],
        'instance_tags' : module.params['instance_tags'],
        'next_hop'      : module.params['next_hop'],
        'state'         : module.params['state'],
    }

    gce = gce_connect(module, PROVIDER)

    if params['state'] == 'present':
        # alter some parameters for easier processing later
        node = None
        if params['next_hop'] == 'default':
            params['next_hop'] = None
        else:
            try:
                socket.inet_aton(params['next_hop'])
            except socket.error:
                try:
                    node = gce.ex_get_node(params['next_hop'])
                except ResourceNotFoundError:
                    module.fail_json(
                        msg     = 'next_hop is a string but no node with this name exists',
                        changed = False
                    )
                else:
                    params['next_hop'] = node

        # done with preparations, actual logic begins
        try:
            route = gce.ex_get_route(params['name'])
        except ResourceNotFoundError:
            # this is a new rule
            if not module.check_mode:
                gce.ex_create_route(name=params['name'], dest_range=params['destination'],
                    priority=params['priority'], network=params['network'],
                    tags=params['instance_tags'], next_hop=params['next_hop'],
                    description=params['description'])
        else:
            # Existing rule, check if anything has changed

            # check: description
            if route.extra['description'] != params['description']:
                route.extra['description'] = params['description']
                changed = True

            # check: network
            network = re.search(r'^.*/([a-zA-Z0-9-]+)$', route.network).group(1)
            if network != params['network']:
                try:
                    network = gce.ex_get_network(params['network'])
                except ResourceNotFoundError:
                    module.fail_json(
                        msg     = "No network named '%s'  was found" % params['network'],
                        changed = False
                    )
                else:
                    route.network = network
                    changed = True
            else:
                # route.network is unicode which breaks the ex_create_route code.
                route.network = str(network)

            # check: destination
            if route.dest_range != params['destination']:
                route.dest_range = params['destination']
                changed = True

            # check: priority
            if route.priority != int(params['priority']):
                route.priority = params['priority']
                changed = True

            # check: instance_tags
            # tags might not be set in the project; cast it to an empty list
            route.tags = route.tags or []
            if route.tags != params['instance_tags']:
                if isinstance(params['instance_tags'], list):
                    if sorted(route.tags) != sorted(params['instance_tags']):
                        route.tags = params['instance_tags']
                        changed = True
                else:
                    route.tags = params['instance_tags']
                    changed = True

            # check: next_hop
            # next_hop can be either None, str (ie ip address) or Node
            if params['next_hop'] == None: # If next_hop is None
                try:
                    route.extra['nextHopGateway'] # it only will be the default gateway
                except KeyError:
                    changed = True
                    route.next_hop = None
                else:
                    route.next_hop = None
            else:
                if node != None: # If next_hop is instance name
                    try:
                        instance = re.search(r'^.*/([a-zA-Z0-9-]+)$', route.extra['nextHopInstance']).group(1)
                    except KeyError:
                        changed = True
                        route.next_hop = node
                    else:
                        if instance != params['next_hop']:
                            changed = True
                            route.next_hop = node
                        else:
                            route.next_hop = gce.ex_get_node(instance)
                else: # If next_hop is ip address
                    try:
                        route.extra['nextHopIp']
                    except KeyError:
                        changed = True
                        route.next_hop = params['next_hop']
                    else:
                        if route.extra['nextHopIp'] != params['next_hop']:
                            changed = True
                            route.next_hop = params['next_hop']
                        else:
                            route.next_hop = route.extra['nextHopIp']

            if changed and not module.check_mode:
                # GCE does not allow modifying routes. We delete and create a new one
                gce.ex_destroy_route(route)
                gce.ex_create_route(name=route.name, dest_range=route.dest_range,
                    priority=route.priority, network=route.network,
                    tags=route.tags, next_hop=route.next_hop,
                    description=route.extra['description'])

    elif params['state'] == 'absent':
        try:
            route = gce.ex_get_route(params['name'])
        except ResourceNotFoundError:
            pass
        else:
            if not module.check_mode:
                gce.ex_destroy_route(route)
                changed = True
    else:
        module.fail_json(
            msg     = "Invalid value for state parameter",
            changed = False
        )

    # revert original value of next_hop because, maybe, we have replaced it with an object
    params['next_hop'] = module.params.get('next_hop')

    json_output = {'changed': changed}
    json_output.update(params)
    json_output['priority'] = int(params['priority'])
    module.exit_json(**json_output)

if __name__ == '__main__':
    main()
