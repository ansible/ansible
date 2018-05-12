#!/usr/bin/python
# Copyright 2013 Google Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gce_net
version_added: "1.5"
short_description: create/destroy GCE networks and firewall rules
description:
    - This module can create and destroy Google Compute Engine networks and
      firewall rules U(https://cloud.google.com/compute/docs/networking).
      The I(name) parameter is reserved for referencing a network while the
      I(fwname) parameter is used to reference firewall rules.
      IPv4 Address ranges must be specified using the CIDR
      U(http://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing) format.
      Full install/configuration instructions for the gce* modules can
      be found in the comments of ansible/test/gce_tests.py.
options:
  allowed:
    description:
      - the protocol:ports to allow (I(tcp:80) or I(tcp:80,443) or I(tcp:80-800;udp:1-25))
        this parameter is mandatory when creating or updating a firewall rule
  ipv4_range:
    description:
      - the IPv4 address range in CIDR notation for the network
        this parameter is not mandatory when you specified existing network in name parameter,
        but when you create new network, this parameter is mandatory
    aliases: ['cidr']
  fwname:
    description:
      - name of the firewall rule
    aliases: ['fwrule']
  name:
    description:
      - name of the network
  src_range:
    description:
      - the source IPv4 address range in CIDR notation
    default: []
    aliases: ['src_cidr']
  src_tags:
    description:
      - the source instance tags for creating a firewall rule
    default: []
  target_tags:
    version_added: "1.9"
    description:
      - the target instance tags for creating a firewall rule
    default: []
  state:
    description:
      - desired state of the network or firewall
    default: "present"
    choices: ["active", "present", "absent", "deleted"]
  service_account_email:
    version_added: "1.6"
    description:
      - service account email
  pem_file:
    version_added: "1.6"
    description:
      - path to the pem file associated with the service account email
        This option is deprecated. Use C(credentials_file).
  credentials_file:
    version_added: "2.1.0"
    description:
      - path to the JSON file associated with the service account email
  project_id:
    version_added: "1.6"
    description:
      - your GCE project ID
  mode:
    version_added: "2.2"
    description:
      - network mode for Google Cloud
        C(legacy) indicates a network with an IP address range;
        C(auto) automatically generates subnetworks in different regions;
        C(custom) uses networks to group subnets of user specified IP address ranges
        https://cloud.google.com/compute/docs/networking#network_types
    default: "legacy"
    choices: ["legacy", "auto", "custom"]
  subnet_name:
    version_added: "2.2"
    description:
      - name of subnet to create
  subnet_region:
    version_added: "2.2"
    description:
      - region of subnet to create
  subnet_desc:
    version_added: "2.2"
    description:
      - description of subnet to create

requirements:
    - "python >= 2.6"
    - "apache-libcloud >= 0.13.3, >= 0.17.0 if using JSON credentials"
author: "Eric Johnson (@erjohnso) <erjohnso@google.com>, Tom Melendez (@supertom) <supertom@google.com>"
'''

EXAMPLES = '''
# Create a 'legacy' Network
- name: Create Legacy Network
  gce_net:
    name: legacynet
    ipv4_range: '10.24.17.0/24'
    mode: legacy
    state: present

# Create an 'auto' Network
- name: Create Auto Network
  gce_net:
    name: autonet
    mode: auto
    state: present

# Create a 'custom' Network
- name: Create Custom Network
  gce_net:
    name: customnet
    mode: custom
    subnet_name: "customsubnet"
    subnet_region: us-east1
    ipv4_range: '10.240.16.0/24'
    state: "present"

# Create Firewall Rule with Source Tags
- name: Create Firewall Rule w/Source Tags
  gce_net:
    name: default
    fwname: "my-firewall-rule"
    allowed: tcp:80
    state: "present"
    src_tags: "foo,bar"

# Create Firewall Rule with Source Range
- name: Create Firewall Rule w/Source Range
  gce_net:
    name: default
    fwname: "my-firewall-rule"
    allowed: tcp:80
    state: "present"
    src_range: ['10.1.1.1/32']

# Create Custom Subnetwork
- name: Create Custom Subnetwork
  gce_net:
    name: privatenet
    mode: custom
    subnet_name: subnet_example
    subnet_region: us-central1
    ipv4_range: '10.0.0.0/16'
'''

RETURN = '''
allowed:
    description: Rules (ports and protocols) specified by this firewall rule.
    returned: When specified
    type: string
    sample: "tcp:80;icmp"

fwname:
    description: Name of the firewall rule.
    returned: When specified
    type: string
    sample: "my-fwname"

ipv4_range:
    description: IPv4 range of the specified network or subnetwork.
    returned: when specified or when a subnetwork is created
    type: string
    sample: "10.0.0.0/16"

name:
    description: Name of the network.
    returned: always
    type: string
    sample: "my-network"

src_range:
    description: IP address blocks a firewall rule applies to.
    returned: when specified
    type: list
    sample: [ '10.1.1.12/8' ]

src_tags:
    description: Instance Tags firewall rule applies to.
    returned: when specified while creating a firewall rule
    type: list
    sample: [ 'foo', 'bar' ]

state:
    description: State of the item operated on.
    returned: always
    type: string
    sample: "present"

subnet_name:
    description: Name of the subnetwork.
    returned: when specified or when a subnetwork is created
    type: string
    sample: "my-subnetwork"

subnet_region:
    description: Region of the specified subnet.
    returned: when specified or when a subnetwork is created
    type: string
    sample: "us-east1"

target_tags:
    description: Instance Tags with these tags receive traffic allowed by firewall rule.
    returned: when specified while creating a firewall rule
    type: list
    sample: [ 'foo', 'bar' ]
'''
try:
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    from libcloud.common.google import GoogleBaseError, QuotaExceededError, ResourceExistsError, ResourceNotFoundError
    _ = Provider.GCE
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gce import gce_connect, unexpected_error_msg


def format_allowed_section(allowed):
    """Format each section of the allowed list"""
    if allowed.count(":") == 0:
        protocol = allowed
        ports = []
    elif allowed.count(":") == 1:
        protocol, ports = allowed.split(":")
    else:
        return []
    if ports.count(","):
        ports = ports.split(",")
    elif ports:
        ports = [ports]
    return_val = {"IPProtocol": protocol}
    if ports:
        return_val["ports"] = ports
    return return_val


def format_allowed(allowed):
    """Format the 'allowed' value so that it is GCE compatible."""
    return_value = []
    if allowed.count(";") == 0:
        return [format_allowed_section(allowed)]
    else:
        sections = allowed.split(";")
        for section in sections:
            return_value.append(format_allowed_section(section))
    return return_value


def sorted_allowed_list(allowed_list):
    """Sort allowed_list (output of format_allowed) by protocol and port."""
    # sort by protocol
    allowed_by_protocol = sorted(allowed_list, key=lambda x: x['IPProtocol'])
    # sort the ports list
    return sorted(allowed_by_protocol, key=lambda y: y.get('ports', []).sort())


def main():
    module = AnsibleModule(
        argument_spec=dict(
            allowed=dict(),
            ipv4_range=dict(),
            fwname=dict(),
            name=dict(),
            src_range=dict(default=[], type='list'),
            src_tags=dict(default=[], type='list'),
            target_tags=dict(default=[], type='list'),
            state=dict(default='present'),
            service_account_email=dict(),
            pem_file=dict(type='path'),
            credentials_file=dict(type='path'),
            project_id=dict(),
            mode=dict(default='legacy', choices=['legacy', 'auto', 'custom']),
            subnet_name=dict(),
            subnet_region=dict(),
            subnet_desc=dict(),
        )
    )

    if not HAS_LIBCLOUD:
        module.fail_json(msg='libcloud with GCE support (0.17.0+) required for this module')

    gce = gce_connect(module)

    allowed = module.params.get('allowed')
    ipv4_range = module.params.get('ipv4_range')
    fwname = module.params.get('fwname')
    name = module.params.get('name')
    src_range = module.params.get('src_range')
    src_tags = module.params.get('src_tags')
    target_tags = module.params.get('target_tags')
    state = module.params.get('state')
    mode = module.params.get('mode')
    subnet_name = module.params.get('subnet_name')
    subnet_region = module.params.get('subnet_region')
    subnet_desc = module.params.get('subnet_desc')

    changed = False
    json_output = {'state': state}

    if state in ['active', 'present']:
        network = None
        subnet = None
        try:
            network = gce.ex_get_network(name)
            json_output['name'] = name
            if mode == 'legacy':
                json_output['ipv4_range'] = network.cidr
            if network and mode == 'custom' and subnet_name:
                if not hasattr(gce, 'ex_get_subnetwork'):
                    module.fail_json(msg="Update libcloud to a more recent version (>1.0) that supports network 'mode' parameter", changed=False)

                subnet = gce.ex_get_subnetwork(subnet_name, region=subnet_region)
                json_output['subnet_name'] = subnet_name
                json_output['ipv4_range'] = subnet.cidr
        except ResourceNotFoundError:
            pass
        except Exception as e:
            module.fail_json(msg=unexpected_error_msg(e), changed=False)

        # user wants to create a new network that doesn't yet exist
        if name and not network:
            if not ipv4_range and mode != 'auto':
                module.fail_json(msg="Network '" + name + "' is not found. To create network in legacy or custom mode, 'ipv4_range' parameter is required",
                                 changed=False)
            args = [ipv4_range if mode == 'legacy' else None]
            kwargs = {}
            if mode != 'legacy':
                kwargs['mode'] = mode

            try:
                network = gce.ex_create_network(name, *args, **kwargs)
                json_output['name'] = name
                json_output['ipv4_range'] = ipv4_range
                changed = True
            except TypeError:
                module.fail_json(msg="Update libcloud to a more recent version (>1.0) that supports network 'mode' parameter", changed=False)
            except Exception as e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)

        if (subnet_name or ipv4_range) and not subnet and mode == 'custom':
            if not hasattr(gce, 'ex_create_subnetwork'):
                module.fail_json(msg='Update libcloud to a more recent version (>1.0) that supports subnetwork creation', changed=changed)
            if not subnet_name or not ipv4_range or not subnet_region:
                module.fail_json(msg="subnet_name, ipv4_range, and subnet_region required for custom mode", changed=changed)

            try:
                subnet = gce.ex_create_subnetwork(subnet_name, cidr=ipv4_range, network=name, region=subnet_region, description=subnet_desc)
                json_output['subnet_name'] = subnet_name
                json_output['ipv4_range'] = ipv4_range
                changed = True
            except Exception as e:
                module.fail_json(msg=unexpected_error_msg(e), changed=changed)

        if fwname:
            # user creating a firewall rule
            if not allowed and not src_range and not src_tags:
                if changed and network:
                    module.fail_json(
                        msg="Network created, but missing required " + "firewall rule parameter(s)", changed=True)
                module.fail_json(
                    msg="Missing required firewall rule parameter(s)",
                    changed=False)

            allowed_list = format_allowed(allowed)

            # Fetch existing rule and if it exists, compare attributes
            # update if attributes changed.  Create if doesn't exist.
            try:
                fw_changed = False
                fw = gce.ex_get_firewall(fwname)

                # If old and new attributes are different, we update the firewall rule.
                # This implicitly lets us clear out attributes as well.
                # allowed_list is required and must not be None for firewall rules.
                if allowed_list and (sorted_allowed_list(allowed_list) != sorted_allowed_list(fw.allowed)):
                    fw.allowed = allowed_list
                    fw_changed = True

                # source_ranges might not be set in the project; cast it to an empty list
                fw.source_ranges = fw.source_ranges or []

                # If these attributes are lists, we sort them first, then compare.
                # Otherwise, we update if they differ.
                if fw.source_ranges != src_range:
                    if isinstance(src_range, list):
                        if sorted(fw.source_ranges) != sorted(src_range):
                            fw.source_ranges = src_range
                            fw_changed = True
                    else:
                        fw.source_ranges = src_range
                        fw_changed = True

                # source_tags might not be set in the project; cast it to an empty list
                fw.source_tags = fw.source_tags or []

                if fw.source_tags != src_tags:
                    if isinstance(src_tags, list):
                        if sorted(fw.source_tags) != sorted(src_tags):
                            fw.source_tags = src_tags
                            fw_changed = True
                    else:
                        fw.source_tags = src_tags
                        fw_changed = True

                # target_tags might not be set in the project; cast it to an empty list
                fw.target_tags = fw.target_tags or []

                if fw.target_tags != target_tags:
                    if isinstance(target_tags, list):
                        if sorted(fw.target_tags) != sorted(target_tags):
                            fw.target_tags = target_tags
                            fw_changed = True
                    else:
                        fw.target_tags = target_tags
                        fw_changed = True

                if fw_changed is True:
                    try:
                        gce.ex_update_firewall(fw)
                        changed = True
                    except Exception as e:
                        module.fail_json(msg=unexpected_error_msg(e), changed=False)

            # Firewall rule not found so we try to create it.
            except ResourceNotFoundError:
                try:
                    gce.ex_create_firewall(fwname, allowed_list, network=name,
                                           source_ranges=src_range, source_tags=src_tags, target_tags=target_tags)
                    changed = True

                except Exception as e:
                    module.fail_json(msg=unexpected_error_msg(e), changed=False)

            except Exception as e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)

            json_output['fwname'] = fwname
            json_output['allowed'] = allowed
            json_output['src_range'] = src_range
            json_output['src_tags'] = src_tags
            json_output['target_tags'] = target_tags

    if state in ['absent', 'deleted']:
        if fwname:
            json_output['fwname'] = fwname
            fw = None
            try:
                fw = gce.ex_get_firewall(fwname)
            except ResourceNotFoundError:
                pass
            except Exception as e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)
            if fw:
                gce.ex_destroy_firewall(fw)
                changed = True
        elif subnet_name:
            if not hasattr(gce, 'ex_get_subnetwork') or not hasattr(gce, 'ex_destroy_subnetwork'):
                module.fail_json(msg='Update libcloud to a more recent version (>1.0) that supports subnetwork creation', changed=changed)
            json_output['name'] = subnet_name
            subnet = None
            try:
                subnet = gce.ex_get_subnetwork(subnet_name, region=subnet_region)
            except ResourceNotFoundError:
                pass
            except Exception as e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)
            if subnet:
                gce.ex_destroy_subnetwork(subnet)
                changed = True
        elif name:
            json_output['name'] = name
            network = None
            try:
                network = gce.ex_get_network(name)

            except ResourceNotFoundError:
                pass
            except Exception as e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)
            if network:
                try:
                    gce.ex_destroy_network(network)
                except Exception as e:
                    module.fail_json(msg=unexpected_error_msg(e), changed=False)
                changed = True

    json_output['changed'] = changed
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
