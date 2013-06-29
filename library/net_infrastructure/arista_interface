#!/usr/bin/python
# -*- coding: utf-8 -*-
#    
# Copyright (C) 2013, Arista Networks <netdevops@aristanetworks.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
DOCUMENTATION = '''
---
module: arista_interface
author: Peter Sprygada
short_description: Manage physical Ethernet interfaces
requirements:
    - Arista EOS 4.10
    - Netdev extension for EOS
description:
    - Manage physical Ethernet interface resources on Arista EOS network devices
options:
    interface_id:
        description:
            - the full name of the interface
        required: true
    logging:
        description:
            - enables or disables the syslog facility for this module
        required: false
        default: false
        choices: [ 'true', 'false', 'yes', 'no' ]
    admin:
        description:
            - controls the operational state of the interface
        required: false
        choices: [ 'up', 'down' ]
    description:
        description:
            - a single line text string describing the interface
        required: false
    mtu:
        description:
            - configureds the maximum transmission unit for the interface
        required: false
        default: 1500
    speed:
        description:
            - sets the interface speed setting
        required: false
        default: 'auto'
        choices: [ 'auto', '100m', '1g', '10g' ]
    duplex:
        description:
            - sets the interface duplex setting
        required: false
        default: 'auto'
        choices: [ 'auto', 'half', 'full' ]
notes:
    - Requires EOS 4.10 or later 
    - The Netdev extension for EOS must be installed and active in the 
      available extensions (show extensions from the EOS CLI)
    - See http://eos.aristanetworks.com for details
'''
EXAMPLES = '''
Example playbook entries using the arista_interface module to manage resource 
state.  Note that interface names must be the full interface name not shortcut
names (ie Ethernet, not Et1)

    tasks:
    - name: enable interface Ethernet 1
      action: arista_interface interface_id=Ethernet1 admin=up speed=10g duplex=full logging=true
  
    - name: set mtu on Ethernet 1
      action: arista_interface interface_id=Ethernet1 mtu=1600 speed=10g duplex=full logging=true
  
    - name: reset changes to Ethernet 1
      action: arista_interface interface_id=Ethernet1 admin=down mtu=1500 speed=10g duplex=full logging=true
'''
import syslog
import json

class AristaInterface(object):
    """ This is the base class for managing physcial Ethernet interface 
        resources in EOS network devices.  This class acts as a wrapper around 
        the netdev extension in EOS.  You must have the netdev extension 
        installed in order for this module to work properly.   
        
        The following commands are implemented in this module:
            * netdev interface list
            * netdev interface show
            * netdev interface edit
            * netdev interface delete
            
        This module only allows for the management of physical Ethernet 
        interfaces.  
    """
    
    attributes = ['interface_id', 'admin', 'description', 'mtu', 'speed', 'duplex']
    
    def __init__(self, module):
        self.module         = module
        self.interface_id   = module.params['interface_id']
        self.admin          = module.params['admin']
        self.description    = module.params['description']
        self.mtu            = module.params['mtu']
        self.speed          = module.params['speed']
        self.duplex         = module.params['duplex']
        self.logging        = module.params['logging']
        
    @property
    def changed(self):
        """ The changed property provides a boolean response if the currently
            loaded resouces has changed from the resource running in EOS.
            
            Returns True if the object is not in sync 
            Returns False if the object is in sync.
        """
        return len(self.updates()) > 0
        
    def log(self, entry):
        """ This method is responsible for sending log messages to the local
            syslog.
        """
        if self.logging:
            syslog.openlog('ansible-%s' % os.path.basename(__file__))
            syslog.syslog(syslog.LOG_NOTICE, entry)
                    
    def run_command(self, cmd):
        """ Calls the Ansible module run_command method. This method will 
            directly return the results of the run_command method
        """        
        self.log(cmd)
        return self.module.run_command(cmd.split())
        
    def get(self):
        """ This method will return a dictionary with the attributes of the
            physical ethernet interface resource specified in interface_id.  
            The physcial ethernet interface resource has the following 
            stucture:
            
              {
                "interface_id": <interface_id>,
                "description": <description>,
                "admin": [up | down],
                "mtu": <mtu>,
                "speed": [auto | 100m | 1g | 10g]
                "duplex": [auto | half | full]
              }
            
            If the physical ethernet interface specified by interface_id does 
            not exist in the system, this method will return None.
        """
        cmd = "netdev interface show %s" % self.interface_id
        (rc, out, err) = self.run_command(cmd)
        obj = json.loads(out)
        if obj.get('status') != 200: 
            return None
        return obj['result']
        
    def update(self):
        """ Updates an existing physical ethernet resource in the current 
            running configuration.   If the physical ethernet resource does 
            not exist, this method will return an error.
            
            This method implements the following commands:
                * netdev interface edit {interface_id} [attributes]
            
            Returns an updated physical ethernet interafce resoure if the 
            update method was successful
        """
        attribs = list()        
        for attrib in self.updates():
            attribs.append("--%s" % attrib)
            attribs.append(str(getattr(self, attrib)))
        
        if attribs:
            cmd = "netdev interface edit %s " % self.interface_id
            cmd += " ".join(attribs)
        
            (rc, out, err) = self.run_command(cmd)
            resp = json.loads(out)
            if resp.get('status') != 200:
                rc = int(resp['status'])
                err = resp['message']
                out = None
            else:
                out = resp['result']
            return (rc, out, err)
 
        return (0, None, "No attributes have been modified")
        
    def updates(self):
        """ This method will check the current phy resource in the running
            configuration and return a list of attribute that are not in sync
            with the current resource from the running configuration.
        """
        obj = self.get()
        update = lambda a, z: a != z

        updates = list()
        for attrib in self.attributes:
            value = getattr(self, attrib)
            if update(obj[attrib], value) and value is not None:
                updates.append(attrib)

        self.log("updates: %s" % updates)
        return updates
        
        

def main():
    module = AnsibleModule(
        argument_spec = dict(
            interface_id=dict(default=None, type='str'),
            admin=dict(default=None, choices=['up', 'down'], type='str'),
            description=dict(default=None, type='str'),
            mtu=dict(default=None, type='int'),
            speed=dict(default=None, choices=['auto', '100m', '1g', '10g']),
            duplex=dict(default=None, choices=['auto', 'half', 'full']),
            logging=dict(default=False, type='bool')
        ),
        supports_check_mode = True
    )
    
    obj = AristaInterface(module)
    
    rc = None
    result = dict()
    
    if module.check_mode:
        module.exit_json(changed=obj.changed)
    
    else:
        if obj.changed:
            (rc, out, err) = obj.update()
            result['results'] = out
            if rc is not None and rc != 0:
                module.fail_json(msg=err, rc=rc)

    if rc is None:
        result['changed'] = False
    else:
        result['changed'] = True
            
    module.exit_json(**result)
    

# include magic from lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
main()
