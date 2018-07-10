#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: lldp
requirements: [ lldpctl ]
version_added: 1.6
short_description: get details reported by lldp
description:
  - Reads data out of lldpctl
options: {}
author: "Andy Hill (@andyhky)"
notes:
  - Requires lldpd running and lldp enabled on switches
'''

EXAMPLES = '''
# Retrieve switch/port information
 - name: Gather information from lldp
   lldp:

 - name: Print each switch/port
   debug:
    msg: "{{ lldp[item]['chassis']['name'] }} / {{ lldp[item]['port']['ifname'] }}"
   with_items: "{{ lldp.keys() }}"

# TASK: [Print each switch/port] ***********************************************************
# ok: [10.13.0.22] => (item=eth2) => {"item": "eth2", "msg": "switch1.example.com / Gi0/24"}
# ok: [10.13.0.22] => (item=eth1) => {"item": "eth1", "msg": "switch2.example.com / Gi0/3"}
# ok: [10.13.0.22] => (item=eth0) => {"item": "eth0", "msg": "switch3.example.com / Gi0/3"}

'''

from ansible.module_utils.basic import AnsibleModule


def gather_lldp(module):
    cmd = ['lldpctl', '-f', 'keyvalue']
    rc, output, err = module.run_command(cmd)
    if output:
        output_dict = {}
        current_dict = {}
        lldp_entries = output.split("\n")

        for entry in lldp_entries:
            if entry.startswith('lldp'):
                path, value = entry.strip().split("=", 1)
                path = path.split(".")
                path_components, final = path[:-1], path[-1]
            else:
                value = current_dict[final] + '\n' + entry

            current_dict = output_dict
            for path_component in path_components:
                current_dict[path_component] = current_dict.get(path_component, {})
                current_dict = current_dict[path_component]
            current_dict[final] = value
        return output_dict


def main():
    module = AnsibleModule({})

    lldp_output = gather_lldp(module)
    try:
        data = {'lldp': lldp_output['lldp']}
        module.exit_json(ansible_facts=data)
    except TypeError:
        module.fail_json(msg="lldpctl command failed. is lldpd running?")


if __name__ == '__main__':
    main()
