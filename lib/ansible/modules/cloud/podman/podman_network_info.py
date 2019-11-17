#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
module: podman_network_info
author:
  - "Sagi Shnaidman (@sshnaidm)"
version_added: '2.10'
short_description: Gather info about podman networks
notes: []
description:
  - Gather info about podman networks with podman inspect command.
requirements:
  - "Podman installed on host"
options:
  name:
    description:
      - Name of the network
    type: str
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
"""
EXAMPLES = """
- name: Gather info about all present networks
  podman_network_info:

- name: Gather info about specific network
  podman_network_info:
    name: podman
"""
RETURN = """
networks:
    description: Facts from all or specified networks
    returned: always
    type: list
    sample: [
              {
                "cniVersion": "0.4.0",
                "name": "podman",
                "plugins": [
                    {
                        "bridge": "cni-podman0",
                        "ipMasq": true,
                        "ipam": {
                            "ranges": [
                                [
                                    {
                                        "gateway": "10.88.0.1",
                                        "subnet": "10.88.0.0/16"
                                    }
                                ]
                            ],
                            "routes": [
                                {
                                    "dst": "0.0.0.0/0"
                                }
                            ],
                            "type": "host-local"
                        },
                        "isGateway": true,
                        "type": "bridge"
                    },
                    {
                        "capabilities": {
                            "portMappings": true
                        },
                        "type": "portmap"
                    },
                    {
                        "backend": "iptables",
                        "type": "firewall"
                    }
                ]
            }
        ]
"""

import json
from ansible.module_utils.basic import AnsibleModule


def get_network_info(module, executable, name):
    command = [executable, 'network', 'inspect']
    if not name:
        all_names = [executable, 'network', 'ls', '-q']
        rc, out, err = module.run_command(all_names)
        if rc != 0:
            module.fail_json(msg="Unable to get list of networks: %s" % err)
        name = out.split()
        if not name:
            return [], out, err
        command += name
    else:
        command.append(name)
    rc, out, err = module.run_command(command)
    if rc != 0 or 'unable to find network configuration' in err:
        module.fail_json(msg="Unable to gather info for %s: %s" % (name, err))
    if not out or json.loads(out) is None:
        return [], out, err
    return json.loads(out), out, err


def main():
    module = AnsibleModule(
        argument_spec=dict(
            executable=dict(type='str', default='podman'),
            name=dict(type='str')
        ),
        supports_check_mode=True,
    )

    name = module.params['name']
    executable = module.get_bin_path(module.params['executable'], required=True)

    inspect_results, out, err = get_network_info(module, executable, name)

    results = {
        "changed": False,
        "networks": inspect_results,
        "stderr": err
    }

    module.exit_json(**results)


if __name__ == '__main__':
    main()
