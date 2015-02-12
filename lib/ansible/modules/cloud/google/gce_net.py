#!/usr/bin/python
# Copyright 2013 Google Inc.
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

DOCUMENTATION = '''
---
module: gce_net
version_added: "1.5"
short_description: create/destroy GCE networks and firewall rules
description:
    - This module can create and destroy Google Compue Engine networks and
      firewall rules U(https://developers.google.com/compute/docs/networking).
      The I(name) parameter is reserved for referencing a network while the
      I(fwname) parameter is used to reference firewall rules.
      IPv4 Address ranges must be specified using the CIDR
      U(http://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing) format.
      Full install/configuration instructions for the gce* modules can
      be found in the comments of ansible/test/gce_tests.py.
options:
  allowed:
    description:
      - the protocol:ports to allow ('tcp:80' or 'tcp:80,443' or 'tcp:80-800')
    required: false
    default: null
    aliases: []
  ipv4_range:
    description:
      - the IPv4 address range in CIDR notation for the network
    required: false
    aliases: ['cidr']
  fwname:
    description:
      - name of the firewall rule
    required: false
    default: null
    aliases: ['fwrule']
  name:
    description:
      - name of the network
    required: false
    default: null
    aliases: []
  src_range:
    description:
      - the source IPv4 address range in CIDR notation
    required: false
    default: null
    aliases: ['src_cidr']
  src_tags:
    description:
      - the source instance tags for creating a firewall rule
    required: false
    default: null
    aliases: []
  target_tags:
    version_added: "1.9"
    description:
      - the target instance tags for creating a firewall rule
    required: false
    default: null
    aliases: []
  state:
    description:
      - desired state of the persistent disk
    required: false
    default: "present"
    choices: ["active", "present", "absent", "deleted"]
    aliases: []
  service_account_email:
    version_added: "1.6"
    description:
      - service account email
    required: false
    default: null
    aliases: []
  pem_file:
    version_added: "1.6"
    description:
      - path to the pem file associated with the service account email
    required: false
    default: null
    aliases: []
  project_id:
    version_added: "1.6"
    description:
      - your GCE project ID
    required: false
    default: null
    aliases: []

requirements: [ "libcloud" ]
author: Eric Johnson <erjohnso@google.com>
'''

EXAMPLES = '''
# Simple example of creating a new network
- local_action:
    module: gce_net
    name: privatenet
    ipv4_range: '10.240.16.0/24'

# Simple example of creating a new firewall rule
- local_action:
    module: gce_net
    name: privatenet
    fwname: all-web-webproxy
    allowed: tcp:80,8080
    src_tags: ["web", "proxy"]

'''

import sys

try:
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    from libcloud.common.google import GoogleBaseError, QuotaExceededError, \
            ResourceExistsError, ResourceNotFoundError
    _ = Provider.GCE
except ImportError:
    print("failed=True " + \
            "msg='libcloud with GCE support required for this module.'")
    sys.exit(1)


def format_allowed(allowed):
    """Format the 'allowed' value so that it is GCE compatible."""
    if allowed.count(":") == 0:
        protocol = allowed
        ports = []
    elif allowed.count(":") == 1:
        protocol, ports = allowed.split(":")
    else:
        return []
    if ports.count(","):
        ports = ports.split(",")
    else:
        ports = [ports]
    return_val = {"IPProtocol": protocol}
    if ports:
        return_val["ports"] = ports
    return [return_val]


def main():
    module = AnsibleModule(
        argument_spec = dict(
            allowed = dict(),
            ipv4_range = dict(),
            fwname = dict(),
            name = dict(),
            src_range = dict(type='list'),
            src_tags = dict(type='list'),
            target_tags = dict(type='list'),
            state = dict(default='present'),
            service_account_email = dict(),
            pem_file = dict(),
            project_id = dict(),
        )
    )

    gce = gce_connect(module)

    allowed = module.params.get('allowed')
    ipv4_range = module.params.get('ipv4_range')
    fwname = module.params.get('fwname')
    name = module.params.get('name')
    src_range = module.params.get('src_range')
    src_tags = module.params.get('src_tags')
    target_tags = module.params.get('target_tags')
    state = module.params.get('state')

    changed = False
    json_output = {'state': state}

    if state in ['active', 'present']:
        network = None
        try:
            network = gce.ex_get_network(name)
            json_output['name'] = name
            json_output['ipv4_range'] = network.cidr
        except ResourceNotFoundError:
            pass
        except Exception, e:
            module.fail_json(msg=unexpected_error_msg(e), changed=False)

        # user wants to create a new network that doesn't yet exist
        if name and not network:
            if not ipv4_range:
                module.fail_json(msg="Missing required 'ipv4_range' parameter",
                    changed=False)

            try:
                network = gce.ex_create_network(name, ipv4_range)
                json_output['name'] = name
                json_output['ipv4_range'] = ipv4_range
                changed = True
            except Exception, e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)

        if fwname:
            # user creating a firewall rule
            if not allowed and not src_range and not src_tags:
                if changed and network:
                    module.fail_json(
                        msg="Network created, but missing required " + \
                        "firewall rule parameter(s)", changed=True)
                module.fail_json(
                    msg="Missing required firewall rule parameter(s)",
                    changed=False)

            allowed_list = format_allowed(allowed)

            try:
                gce.ex_create_firewall(fwname, allowed_list, network=name,
                        source_ranges=src_range, source_tags=src_tags, target_tags=target_tags)
                changed = True
            except ResourceExistsError:
                pass
            except Exception, e:
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
            except Exception, e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)
            if fw:
                gce.ex_destroy_firewall(fw)
                changed = True
        if name:
            json_output['name'] = name
            network = None
            try:
                network = gce.ex_get_network(name)
#                json_output['d1'] = 'found network name %s' % name
            except ResourceNotFoundError:
#                json_output['d2'] = 'not found network name %s' % name
                pass
            except Exception, e:
#                json_output['d3'] = 'error with %s' % name
                module.fail_json(msg=unexpected_error_msg(e), changed=False)
            if network:
#                json_output['d4'] = 'deleting %s' % name
                gce.ex_destroy_network(network)
#                json_output['d5'] = 'deleted %s' % name
                changed = True

    json_output['changed'] = changed
    print json.dumps(json_output)
    sys.exit(0)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.gce import *

main()
