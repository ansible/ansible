#!/usr/bin/python
#
# (c) 2019 Extreme Networks Inc.
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
#
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: exos_interface
version_added: "2.6"
author: 
  - "Olen Stokes (@ostokes)"
short_description: Manage Interfaces on Extreme EXOS network devices
description:
  - This module provides declarative management of Interfaces
    on Extreme EXOS network devices.
notes:
  - Tested against EXOS 22.7.1.x 
options:
  name:
    description:
      - Full name of the interface, i.e. Port 1, Port 1:4, Port 3:4.
    required: true
    aliases: ['interface']
  description:
    description:
      - Description of Interface.
  enabled:
    description:
      - Interface link status.
    default: True
    type: bool
  speed:
    description:
      - Interface link speed.
  mtu:
    description:
      - Maximum size of transmit packet. Must be a number between 1500 and 9216.
  tx_rate:
    description:
      - Transmit rate in bits per second (bps).
      - This is state check parameter only.
  rx_rate:
    description:
      - Receiver rate in bits per second (bps).
      - This is state check parameter only.
  neighbors:
    description:
      - Check the operational state of given interface C(name) for LLDP neighbor.
      - This is state check parameter only.
      - The following suboptions are available. 
    suboptions:
        host:
          description:
            - "LLDP neighbor host for given interface C(name)."
        port:
          description:
            - "LLDP neighbor port to which given interface C(name) is connected."
  aggregate:
    description: List of Interfaces definitions.
  delay:
    description:
      - Time in seconds to wait before checking for the operational state on remote
        device. This wait is applicable for operational state argument which are
        I(state) with values C(up)/C(down), I(tx_rate) and I(rx_rate).
    default: 10
  state:
    description:
      - State of the Interface configuration, C(up) means present and
        operationally up and C(down) means present and operationally C(down)
    default: present
    choices: ['present', 'absent', 'up', 'down']
  duplex:
    description:
      - Interface link status.
      default: full
      choices: ['full', 'half', 'auto']
"""

EXAMPLES = """
- name: configure interface
  exos_interface:
      name: Port 2
      description: test-interface
      speed: 1000
      mtu: 9216

- name: make interface up
  exos_interface:
    name: Port 2
    enabled: True

- name: make interface down
  exos_interface:
    name: Port 3
    enabled: False

- name: Check intent arguments
  exos_interface:
    name: Port 2
    state: up
    tx_rate: 1000
    rx_rate: 1000

- name: Check neighbors intent arguments
  exos_interface:
    name: Port 1
    neighbors:
    - port: Port 1
      host: EXOS

- name: Config + intent
  exos_interface:
    name: Port 4
    enabled: False
    state: down

- name: Add interface using aggregate
  exos_interface:
    aggregate:
    - { name: Port 1, mtu: 1548, description: test-interface-1 }
    - { name: Port 2, mtu: 1548, description: test-interface-2 }
    speed: 10000
    state: present

"""

RETURN = """
commands:
  description: The list of configuration commands sent to the device.
  returned: Always.
  type: list
  sample:
  - enable jumbo-frame port 3
  - configure port 1 auto off speed 1000 duplex full
  - disable port 3
"""
import time
import json
from copy import deepcopy
from time import sleep

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.exos.exos import send_requests

#%%
def get_interface_path():
    interface_path = "/rest/restconf/data/openconfig_interfaces:interfaces/"
    return interface_path
#%%
def make_interface_body(description, mtu, speed, duplex, enabled):
    interface_body = {
      "openconfig_interfaces:interface":[{
              "config": {
                      "description": description, 
                      "enabled": enabled, 
                      "mtu": mtu, 
                      }, 
              "openconfig-if-ethernet:ethernet":{
                      "config":{
                              "port-speed": speed,
                              "duplex-mode": duplex
                              }
                      }
              }]
    }
    
    return json.dumps(interface_body)
 
#%%    
def map_config_to_list(module):
    path = get_interface_path()
    requests = [{"path": path}]
    resp = send_requests(module, requests=requests)
    old_config_list = list()
    for intf_json in resp:
        for intf in intf_json['openconfig_interfaces:interfaces']['interface']:
            if intf['config']['type'] == 'ethernetCsmacd':
                old_config_list.append({"name": intf['name'],
                                        "description":intf['config']['description'],
                                        "speed":intf['openconfig-if-ethernet:ethernet']['config']['port-speed'],
                                        "mtu":intf['config']['mtu'],
                                        "enabled":intf['config']['enabled'],
                                        "duplex":intf['openconfig-if-ethernet:ethernet']['config']['duplex-mode'],
                                        "state":'present' #while mapping config should we assign default value or assign based on enabled value???
                                        })
    
    return old_config_list
#%%

def map_params_to_list(module):
    params = module.params
    new_config_list = list()
    aggregate = params['aggregate']
    if aggregate:
        # Completes each dictionary with the common parameters in the element spec
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]
            d = item.copy()
            #d['mtu'] = int(d['mtu'])
            validate_mtu(module, d['mtu'])
            validate_duplex(module, d['duplex'])
            new_config_list.append(d)
    else:
        validate_mtu(module, (params['mtu']))
        validate_duplex(module, params['duplex'])
        new_config_list.append({"name": params['name'],
                                "description": params['description'],
                                "speed": params['speed'],
                                "mtu": params['mtu'],
                                "enabled": params['enabled'],
                                "duplex": params['duplex'],
                                "state": params['state'],
                                "delay": module.params['delay'],
                                "tx_rate": module.params['tx_rate'],
                                "rx_rate": module.params['rx_rate'],
                                "neighbors": module.params['neighbors']})
    return new_config_list

#%%
def search_name_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o
    return None

#%%
def map_diff_to_requests(module, old_config_list, new_config_list):
    requests = list()
    
    args = ('description', 'mtu', 'speed', 'duplex', 'enabled')
    
    for new_config in new_config_list:
        description = new_config['description']
        name = new_config['name']
        speed = new_config['speed']
        mtu = new_config['mtu']
        enabled = new_config['enabled']
        duplex = new_config['duplex']
        state = new_config['state']
        
             
        old_intf_dict = search_name_in_list(name, old_config_list)
        if state == 'absent':
            if old_intf_dict:
                path = get_interface_path() + "interface=" + str(name)
                requests.append({"path": path,
                                 "method": "DELETE"})
        elif state in ('present', 'up', 'down'):
            if not old_intf_dict:
                path = get_interface_path()
                body = make_interface_body(description, mtu, speed, duplex, enabled)
                requests.append({"path": path,
                                 "method": "POST",
                                 "data": body})
            else:
               for item in args:
                   if new_config.get(item) == old_intf_dict.get(item):
                       continue
                   path = get_interface_path() + 'interface=' + str(name)
                   body = make_interface_body(description, mtu, speed, duplex, enabled)
                   requests.append({"path": path,
                                    "method": "PATCH",
                                    "data": body})

                
    return requests
#%%

def validate_mtu(module, mtu):
    if mtu and not 1500 <= int(mtu) <= 9216:
        module.fail_json(msg='mtu must be between 1500 and 9216')

#%%
def validate_duplex(module, duplex):
    if duplex and duplex.lower() != 'auto':
        if module.params.get('speed') and not isinstance(module.params.get('speed'), int):
            module.fail_json(msg='speed needs to be specified when duplex setting is not auto')

#%%
def change_configuration(module, requests):
    send_requests(module, requests=requests)
   
#%%    
def check_declarative_intent_params(new_config_list, module):
    if module.params['name']:
        time.sleep(module.params['delay'])
        
        old_config_list = map_config_to_list(module)
        for newconfs in new_config_list:
            
            name_dict = search_name_in_list(newconfs['name'], old_config_list)
            
            neighbor_dict = dict()
            neighbor_path = "/rest/restconf/data/openconfig-lldp:lldp/interfaces/interface="+str(newconfs['name'])+"/neighbors/"
            for neighbor in neighbor_path['neighbor']:
                neighbor_dict.append(
                        {
                            "host": neighbor['id'],
                            "port": neighbor['state']['port-id']
                        }
                )
                        
            if not name_dict:
                module.fail_json(msg="Switch information after changes for interface %s not present" % (newconfs['name']))
                continue
            
            if name_dict['state'] != 'up' and name_dict['state'] != 'down':
                module.fail_json(msg="Unknown linkState %s for interface %s" % (name_dict['state'], newconfs['name']))
                continue
        
            if newconfs['state'] is not None and name_dict['state'] != newconfs['state']:
                module.fail_json(msg="Wanted state %s Actual state is %s Interface %s" % (newconfs['state'], name_dict['state'], newconfs['name']))
                
            if newconfs['tx_rate'] is not None and name_dict['speed'] != newconfs['tx_rate']:
                module.fail_json(msg="Wanted tx_rate %s Actual tx_rate is %s Interface %s" % (newconfs['tx_rate'], name_dict['speed'], newconfs['name']))
            
            if newconfs['rx_rate'] is not None and name_dict['speed'] != newconfs['rx_rate']:
                module.fail_json(msg="Wanted rx_rate %s Actual rx_rate is %s Interface %s" % (newconfs['rx_rate'], name_dict['speed'], newconfs['name']))
                
            if newconfs['neighbors']:
                for item in newconfs['neighbors']:
                    found = False
                    for obj in neighbor_dict: 
                        if obj['host'] == item.get('host') and obj['port'] == item.get('port'):
                            found = True
                    if not found:
                        module.fail_json(msg="Port %s expected neighbor name %s, port %s" % (newconfs['name'], item.get('host'), item.get('port')))
            
#%%    
        
def main():
    """ main entry point for module execution
    """
    neighbors_spec = dict(
        host=dict(),
        port=dict()
    )

    element_spec = dict(
        name=dict(aliases=['interface']),
        description=dict(),
        speed=dict(),
        mtu=dict(type='int'),
        enabled=dict(type='bool', default=True),
        tx_rate=dict(),
        rx_rate=dict(),
        neighbors=dict(type='list', elements='dict', options=neighbors_spec),
        delay=dict(default=10, type='int'),
        state=dict(default='present',
                   choices=['present', 'absent', 'up', 'down']),
        duplex=dict(choices=['full', 'half', 'auto'])
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['name'] = dict(aliases=['interface'], required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
    )

    argument_spec.update(element_spec)

    required_one_of = [['name', 'aggregate']]
    mutually_exclusive = [['name', 'aggregate']]
    required_if = [('duplex', 'full', ['speed']), ('duplex', 'half', ['speed'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True,
                           required_if=required_if)
    warnings = list()
    requests = list()
    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings
        
    old_config_list = map_config_to_list(module)
    new_config_list = map_params_to_list(module)

#    requests = map_diff_to_requests(module, old_config_list, new_config_list)
#    result['requests'] = requests
#    module.exit_json(**result)
        '''    if requests:
        if not module.check_mode:
            change_configuration(module, requests)
        for request in requests:
            if 'data' in request:
                if request['data']:
                    request['data'] = json.loads(request['data'])
        result['changed'] = True

    if result['changed']:'''
        # Check that the commands resulted in the expected configuration
    check_declarative_intent_params(new_config_list, old_config_list) #module
       # if failed_conditions:
        #    msg = 'One or more conditional statements have not been satisfied'
         #   module.fail_json(msg=msg, failed_conditions=failed_conditions)

    module.exit_json(**result)


if __name__ == '__main__':
    main()

