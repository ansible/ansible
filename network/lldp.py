#!/usr/bin/python -tt
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

import subprocess

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
   debug: msg="{{ lldp[item]['chassis']['name'] }} / {{ lldp[item]['port']['ifalias'] }}
   with_items: lldp.keys()

# TASK: [Print each switch/port] ***********************************************************
# ok: [10.13.0.22] => (item=eth2) => {"item": "eth2", "msg": "switch1.example.com / Gi0/24"}
# ok: [10.13.0.22] => (item=eth1) => {"item": "eth1", "msg": "switch2.example.com / Gi0/3"}
# ok: [10.13.0.22] => (item=eth0) => {"item": "eth0", "msg": "switch3.example.com / Gi0/3"}

'''

def gather_lldp():
    cmd = ['lldpctl', '-f', 'keyvalue']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    (output, err) = proc.communicate()
    if output:
        output_dict = {}
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

    lldp_output = gather_lldp()
    try:
        data = {'lldp': lldp_output['lldp']}
        module.exit_json(ansible_facts=data)
    except TypeError:
        module.fail_json(msg="lldpctl command failed. is lldpd running?")    
   
# import module snippets
from ansible.module_utils.basic import *
main()

