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
            - If empty, the route will apply to all traffic.
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
    description: whether the route is present or absent
    returned: success
    type: string
    sample: present

self_link:
    description: route resource uri on GCE
    returned: success
    type: string
    sample: https://www.googleapis.com/compute/v1/projects/myproject/global/routes/myroute

creation_time:
    description: route creation/update timestamp
    returned: success
    type: string
    sample: 2017-06-28T10:59:59.698-07:00

next_hop_resource:
    description: a resource uri or the IP address of the next hop
    type: string
    sample:
        - https://www.googleapis.com/compute/v1/projects/myproject/zones/europe-west1-b/instances/my-instance
        - https://www.googleapis.com/compute/v1/projects/myproject/global/gateways/default-internet-gateway
        - 10.132.0.0
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

# global (declared as global to avoid calling ex_get_node() both here and in main())
next_hop_node = None
def check_parameter_format(module, gce_connection):
    # All the below checks are performed to allow check_mode to give reliable results.
    # Otherwise, we could handle the exceptions raised by libcloud and skip doing
    # duplicate work here.

    msg =''

    # Starts with lowercase letter, contains only lowercase letters, nubmers, hyphens,
    # cannot be empty, cannot end with hyphen. Taken directly for GCE error responses.
    name_regexp = r"^(?:[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?)$"

    # single ipaddr regexp. Using a regexp to avoid loading extra python dependencies (ipaddr)
    ipaddr_regexp = r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"

    # cidr range regexp. Using a regexp to avoid loading extra python dependencies (ipaddr)
    cidr_regexp = r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/([0-9]|[1-2][0-9]|3[0-2]))$"

    # check the route rule name.
    matches = re.match(name_regexp, module.params['name']);
    if not matches:
        msg = "Route names must start with a lowercase letter, can contain only lowercase letters, " \
            + "numbers and hyphens, cannot end with a hyphen and cannot be empty."

    # check length of description (must be less than 2048 characters)
    if len(unicode(module.params['description'], "utf-8")) > 2048:
        msg = "Description must be less thatn 2048 characters in length."

    # check instance tags for valid tags
    if module.params['instance_tags']:
        for tag in module.params['instance_tags']:
            matches = re.match(name_regexp, tag)

            if not matches:
                msg = "Instance tags must start with a lowercase letter, can contain only lowercase letters, " \
                    + "numbers and hyphens, cannot end with a hyphen and cannot be empty."

    # Check if the destination is a valid cidr or addr. Any of the two regexes is enough
    matches = re.match(ipaddr_regexp, module.params['destination'])
    matches = re.match(cidr_regexp, module.params['destination']) or matches

    if not matches:
        msg = "destination must be a valid IP address or cidr range, '%s' is invalid" % module.params['destination']

    # priority should be a number between 0 and 65535 (2bytes)
    if not (0 <= int(module.params['priority']) < 2**16):
        msg = "Priority must be in the range [0-4294967295], %s given" % module.params['priority']

    # check the three different possibilities for next_hop
    # case 1: 'default'
    if module.params['next_hop'] == 'default':
        # No actual check, but we replace 'default' with None, because libcloud expects it this way.
        module.params['next_hop'] = None
    # case 2: potential instance name
    elif re.match(name_regexp, module.params['next_hop']):
        try:
            global next_hop_node
            next_hop_node = gce_connection.ex_get_node(module.params['next_hop'])
        except ResourceNotFoundError:
            msg = 'next_hop is a valid instance name but no node with this name exists'
    # case 3: ip address. This is the last valid case. If matching it fails, then
    # user has supplied garbage in the next_hop option.
    elif not re.match(ipaddr_regexp, module.params[next_hop]):
        msg = 'next_hop is invalid'

    # exit
    if msg:
        module.fail_json(msg = msg, changed = False)

# global network (declared as global to avoid calling ex_get_network() both here and in main())
network = None
def check_network_exists(gce_connection, module):
    try:
        global network
        network = gce_connection.ex_get_network(module.params['network'])
    except ResourceNotFoundError:
        module.fail_json(
            msg     = "No network '%s' found." % module.params['network'],
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
            priority      = dict(default=500, type='int'),
            instance_tags = dict(default=[], type='list', aliases=['tags']),
            next_hop      = dict(default='default'),
            state         = dict(choices=['absent', 'present'], default='present'),
        ),
        supports_check_mode=True
    )

    gce = gce_connect(module, PROVIDER)

    check_parameter_format(module, gce)

    check_network_exists(gce, module)

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

    if params['state'] == 'present':
        try:
            # below the gce_ prefix in variables means stuff on Google Cloud
            gce_route = gce.ex_get_route(params['name'])
        # this is a new rule
        except ResourceNotFoundError:
            if not module.check_mode:
                if params['next_hop'] == None or re.match(r"^[1-9](.*)$", params['next_hop']):
                    # in re.match() we checked for the first character to see if it is a number. If it is,
                    # it is not a valid instance name. Since we have already checked for garbage values
                    # in check_parameter_format(), it cannot be but an IP address.
                    node = params['next_hop']
                else:
                    # When next_hop is an instance name, libcloud wants us to pass
                    # an instance object (GCENode). In this case,the next_hop_node
                    # global will have already been set in check_parameter_format().
                    node = next_hop_node

                # network is a global, the object of the params['network'], set in check_network_exists()
                gce_route = gce.ex_create_route(name=params['name'], dest_range=params['destination'],
                    priority=params['priority'], network=network, tags=params['instance_tags'],
                    next_hop=node, description=params['description'])
        # Existing rule, check if anything has changed
        else:
            # check: description
            if gce_route.extra['description'] != params['description']:
                changed = True
                gce_route.description = params['description']
            # make sure gce_route.description gets set even if the conditional above failed
            gce_route.description = params['description']

            # check: network
            # extract the network name from the network resource uri (eg projects/myproject/global/networks/*default*)
            gce_network = re.search(r'^.*/([a-zA-Z0-9-]+)$', gce_route.network).group(1)
            if gce_network != params['network']:
                # network is a global, the object of the params['network'], set in check_network_exists()
                gce_route.network = network
                changed = True
            else:
                gce_route.network = network # replace the network resource uri with the object

            # check: destination
            if gce_route.dest_range != params['destination']:
                gce_route.dest_range = params['destination']
                changed = True

            # check: priority
            if gce_route.priority != int(params['priority']):
                gce_route.priority = params['priority']
                changed = True

            # check: instance_tags
            # tags might not be set in the project; cast them to an empty list
            gce_route.tags = gce_route.tags or []
            if gce_route.tags != params['instance_tags']:
                if isinstance(params['instance_tags'], list):
                    if sorted(gce_route.tags) != sorted(params['instance_tags']):
                        gce_route.tags = params['instance_tags']
                        changed = True
                else:
                    gce_route.tags = params['instance_tags']
                    changed = True

            # check: next_hop
            # next_hop can be either None, ip address or instaance name
            if params['next_hop'] == None: # If next_hop is None, ie the default
                try:
                    # if the gce_route is also the default, the 'nextHopGateway' key will be set.
                    # if not, other keys will exist and the below will raise an exception.
                    gce_route.extra['nextHopGateway']
                # Using KeyError exceptions instead of "if 'key' in dict" to keep consinstency
                # in the order in which checks are performed.
                except KeyError:
                    changed = True
                    # Put values into the gce_route object directly for simplicity)
                    # instead of carrying the 'extra' array around that would make life
                    # harder when calling ex_create_route() below.
                    gce_route.next_hop = None
                else:
                    # Due to the above comment, we have to set gce_route.next_hop evenif
                    # nothing change. We could avoid doing the same thing twice, but
                    # leaving here it as it is for clarity. Below, we remove redundancy.
                    gce_route.next_hop = None
            elif re.match(r"^[1-9](.*)$", params['next_hop']): # next_hop is an IP address
                #Wwe checked for the first character to see if it is a number. If it,
                # it is not a valid instance name. Since we have already checked for grabage values
                # in check_parameter_format(), it cannot be but an IP address.
                try:
                    # the key nextHopIp is set when the next hop on GCE is an IP address
                    gce_route.extra['nextHopIp']
                except KeyError:
                    changed = True
                else:
                    if gce_route.extra['nextHopIp'] != params['next_hop']:
                        changed = True
                gce_route.next_hop = params['next_hop']
            else: # next_hop is an instance name (last case of the three possible for next_hop)
                try:
                    # We extract the instance name from the instance resource uri
                    # (eg projects/myproject/zones/europe-west1-b/instances/my-instance).
                    instance = re.search(r'^.*/([a-zA-Z0-9-]+)$', gce_route.extra['nextHopInstance']).group(1)
                except KeyError:
                    changed = True
                    # When next_hop is an instance name, libcloud wants us to pass
                    # an instance object (GCENode). In this case,the next_hop_node
                    # global will have already been set in check_parameter_format().
                else:
                    if instance != params['next_hop']:
                        changed = True
                gce_route.next_hop = next_hop_node

            if changed and not module.check_mode:
                # GCE does not allow modifying routes. We delete and create a new one
                gce.ex_destroy_route(gce_route)
                gce_route = gce.ex_create_route(name=gce_route.name, dest_range=gce_route.dest_range,
                    priority=gce_route.priority, network=gce_route.network,tags=gce_route.tags,
                    next_hop=gce_route.next_hop, description=gce_route.description)

    elif params['state'] == 'absent':
        try:
            gce_route = gce.ex_get_route(params['name'])
        except ResourceNotFoundError:
            pass
        else:
            if not module.check_mode:
                gce.ex_destroy_route(gce_route)
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

    # add extra return values
    extra = dict()
    extra['self_Link'] = gce_route.extra['selfLink']
    extra['creation_time'] = gce_route.extra['creationTimestamp']

    if 'nextHopInstance' in gce_route.extra:
        extra['next_hop_resource'] = gce_route.extra['nextHopInstance']
    if 'nextHopIp' in gce_route.extra:
        extra['next_hop_resource'] = gce_route.extra['nextHopIp']
    if 'nextHopGateway' in gce_route.extra:
        extra['next_hop_resource'] = gce_route.extra['nextHopGateway']
    if 'warnings' in gce_route.extra:
        extra['warnings'] = gce_route.extra.extra['warnings']
    json_output.update(extra)

    module.exit_json(**json_output)

if __name__ == '__main__':
    main()
