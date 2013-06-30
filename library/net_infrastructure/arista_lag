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
module: arista_lag
author: Peter Sprygada
short_description: Manage port channel (lag) interfaces
requirements:
    - Arista EOS 4.10
    - Netdev extension for EOS
description:
    - Manage port channel interface resources on Arista EOS network devices
options:
    interface_id:
        description:
            - the full name of the interface
        required: true
    state:
        description:
            - describe the desired state of the interface related to the config
        required: false
        default: 'present'
        choices: [ 'present', 'absent' ]
    logging:
        description:
            - enables or disables the syslog facility for this module
        required: false
        default: false
        choices: [ 'true', 'false', 'yes', 'no' ]
    links:
        description:
            - array of physical interface links to include in this lag
        required: false
    minimum_links:
        description:
            - the minimum number of physical interaces that must be operationally up to consider the lag operationally up
        required: false
    lacp:
        description:
            - enables the use of the LACP protocol for managing link bundles
        required: false
        default: 'active'
        choices: [ 'active', 'passive', 'off' ]
notes:
    - Requires EOS 4.10 or later 
    - The Netdev extension for EOS must be installed and active in the 
      available extensions (show extensions from the EOS CLI)
    - See http://eos.aristanetworks.com for details
'''

EXAMPLES = '''
Example playbook entries using the arista_lag module to manage resource 
state.  Note that interface names must be the full interface name not shortcut
names (ie Ethernet, not Et1)

    tasks:
    - name: create lag interface
      action: arista_lag interface_id=Port-Channel1 links=Ethernet1,Ethernet2 logging=true

    - name: add member links
      action: arista_lag interface_id=Port-Channel1 links=Ethernet1,Ethernet2,Ethernet3 logging=true

    - name: remove member links
      action: arista_lag interface_id=Port-Channel1 links=Ethernet2,Ethernet3 logging=true
    
    - name: remove lag interface
      action: arista_lag interface_id=Port-Channel1 state=absent logging=true
'''
import syslog
import json

class AristaLag(object):
    """ This is the base class managing port-channel (lag) interfaces 
        resources in Arista EOS network devices.  This class provides an 
        implementation for creating, updating and deleting port-channel 
        interfaces.
        
        Note: The netdev extension for EOS must be installed in order of this
        module to work properly.
        
        The following commands are implemented in this module:
            * netdev lag list
            * netdev lag show
            * netdev lag edit
            * netdev lag delete
        
    """
    
    attributes = ['links', 'minimum_links', 'lacp']
    
    def __init__(self, module):
        self.module         = module
        self.interface_id   = module.params['interface_id']
        self.state          = module.params['state']
        self.links          = module.params['links']
        self.minimum_links  = module.params['minimum_links']
        self.lacp           = module.params['lacp']
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
        self.log("Command: %s" % cmd)
        return self.module.run_command(cmd.split())

        
    def get(self):
        """ This method will return a dictionary with the attributes of the
            lag interface resource specified in interface_id.  The lag
            interface resource has the following stucture:
            
              {
                "interface_id": <interface_id>,
                "links": <array of member interfaces>,
                "minimum_links": <minimum_links>,
                "lacp": [active* | passive | off]
              }
            
            If the lag interface specified by interface_id does not
            exist in the system, this method will return None.
        """
        cmd = "netdev lag show %s" % self.interface_id
        (rc, out, err) = self.run_command(cmd)
        obj = json.loads(out)
        if obj.get('status') != 200: 
            return None
        return obj['result']
        
    def create(self):
        """ Creates a lag interface resource in the current running 
            configuration.  If the lag interface already exists, the 
            function will return successfully.  
            
            This function implements the following commands:
                * netdev lag create {interface_id} [attributes]
            
            Returns the lag interface resource if the create method was 
            successful
            Returns an error message if there as a problem creating the lag
            interface
        """
        attribs = []
        for attrib in self.attributes:
            if getattr(self, attrib):
                attribs.append("--%s" % attrib)
                attribs.append(getattr(self, attrib))
        
            cmd = "netdev lag create %s " % self.interface_id
            cmd += " ".join(attribs)
            
            (rc, out, err) = self.run_command(cmd)
            resp = json.loads(out)
            if resp.get('status') != 201:
                rc = int(resp['status'])
                err = resp['message']
                out = None
            else:
                out = self.get()
        return (rc, out, err)
        
    def update(self):    
        """ Updates an existing lag resource in the current running 
            configuration.   If the lag resource does not exist, this method
            will return an error.
            
            This method implements the following commands:
                * netdev lag edit {interface_id} [attributes]
            
            Returns an updated lag interafce resoure if the update method 
            was successful
        """
        attribs = list()        
        for attrib in self.updates():
            attribs.append("--%s" % attrib)
            attribs.append(getattr(self, attrib))
        
            cmd = "netdev lag edit %s " % self.interface_id
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
 
        return (2, None, "No attributes have been modified")
        
    def delete(self):
        """ Deletes an existing lag interface resource from the current 
            running configuration.  A nonexistent lag interface will 
            return successful for this operation.
            
            This method implements the following commands:
                * netdev lag delete {interface_id}
            
            Returns nothing if the delete was successful
            Returns error message if there was a problem deleting the resource 
        """
        cmd = "netdev lag delete %s" % self.interface_id
        (rc, out, err) = self.run_command(cmd)
        resp = json.loads(out)
        if resp.get('status') != 200: 
            rc = resp['status']
            err = resp['message']
            out = None
        return (rc, out, err)
        
    def updates(self):
        """ This method will check the current lag interface resource in the
            running configuration and return a list of attributes that are
            not in sync with the current resource.
        """
        obj = self.get()
        update = lambda a, z: a != z

        updates = list()
        for attrib in self.attributes:
            if update(obj[attrib], getattr(self, attrib)):
                updates.append(attrib)

        return updates

    def exists(self):
        """ Returns True if the current lag interface resource exists and 
            returns False if it does not.   This method only checks for the 
            existence of the interface as specified in interface_id.
        """
        (rc, out, err) = self.run_command("netdev lag list")
        collection = json.loads(out)
        return self.interface_id in collection.get('result')
        

def main():
    module = AnsibleModule(
        argument_spec = dict(
            interface_id=dict(default=None, type='str'),
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            links=dict(default=None, type='str'),
            lacp=dict(default=None, choices=['active', 'passive', 'off'], type='str'),
            minimum_links=dict(default=None, type='int'),
            logging=dict(default=False, type='bool')
        ),
        supports_check_mode = True
    )
    
    obj = AristaLag(module)
    
    rc = None
    result = dict()

    if obj.state == 'absent':
        if obj.exists():
            if module.check_mode: 
                module.exit_json(changed=True)
            (rc, out, err) = obj.delete()
            if rc !=0: 
                module.fail_json(msg=err, rc=rc)                

    elif obj.state == 'present':
        if not obj.exists():
            if module.check_mode: 
                module.exit_json(changed=True)
            (rc, out, err) = obj.create()
            result['results'] = out
        else:
            if module.check_mode: 
                module.exit_json(changed=obj.changed)
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
