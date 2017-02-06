#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright IBM Corp. 2017
# Author(s): Andreas Nafpliotis <nafpliot@de.ibm.com>

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
# along with Ansible.  If not, see <http://www.gnu.org/licenses/

DOCUMENTATION = '''
---
module: vmware_cfg_backup
short_description: Backup / Restore / Reset ESXi host configuration
description:
    - Backup / Restore / Reset ESXi host configuration
version_added: "2.3"
author: Andreas Nafpliotis
notes:
    - Tested on ESXi 6.0
    - Works only for ESXi hosts
    - For configuration save or reset, the host will be switched automatically to maintenance mode.
    - For configuration save, the backup file will be saved in the dest folder with the original filename / format (.tgz) generated from the ESXi server.
requirements:
    - "python >= 2.6"
    - PyVmomi installed
options:
    dest:
        description:
            - The destination folder where the ESXi configuration bundle will be saved
        required: False
    src:
        description:
            - The file containing the ESXi configuration that will be restored
        required: False
    state:
        description:
            - If C(saved), the .tgz backup bundle will be saved in the I(dest) folder.
            - If C(absent), the host configuration will be resetted to default values.
            - If C(loaded), the backup file in I(src) will be loaded to the ESXi host rewriting the hosts settings.
        choices: ['saved', 'absent', 'loaded']
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
#save the ESXi configuration locally
- name: ESXI backup test
  local_action:
      module: vmware_cfg_backup
      hostname: esxi_host
      username: user
      password: pass
      state: saved
      dest: /tmp/
'''

RETURN = '''
dest_file:
    description: The full path of where the file holding the ESXi configurations was stored
    returned: changed
    type: string
    sample: /tmp/configBundle-esxi.host.domain.tgz
'''

import os
import urllib2
from base64 import b64encode

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


class VMwareConfigurationBackup(object):
    def __init__(self, module):
        self.module = module
        self.state = self.module.params['state']
        self.dest = self.module.params['dest']
        self.src = self.module.params['src']
        self.hostname = self.module.params['hostname']
        self.username = self.module.params['username']
        self.password = self.module.params['password']
        self.content = connect_to_api(self.module)
        self.host = self.find_host_system()

    def find_host_system(self):
        host_system = get_all_objs(self.content, [vim.HostSystem])
        return host_system.keys()[0]

    def process_state(self):
        if self.state == 'saved':
            self.save_configuration()

        if self.state == 'absent':
            self.reset_configuration()

        if self.state == 'loaded':
            self.load_configuration()
            
    def load_configuration(self):
        if not os.path.isfile(self.src):
            self.module.fail_json(msg="Source file {} does not exist".format(self.src))
            
        url = self.host.configManager.firmwareSystem.QueryFirmwareConfigUploadURL()
        #if http, change it manually to https because urllib2 doesn't do automatic redirects for PUT requests
        url = url.replace('http://', 'https://')
        url = url.replace('*', self.hostname)
        
        with open(self.src, 'rb') as file:
            data = file.read()
        request = urllib2.Request(url)
        request.add_data(data)
        request.add_header('Authorization', 'Basic ' + b64encode(self.username + ':' + self.password))
        request.get_method = lambda: 'PUT'
        r = urllib2.urlopen(request)
        
        if not self.host.runtime.inMaintenanceMode:
            self.enter_maintenance()   
        try:
            self.host.configManager.firmwareSystem.RestoreFirmwareConfiguration(force=True)
            self.module.exit_json(changed=True)
        except Exception as e:
            self.exit_maintenance()
            self.module.fail_json(msg=str(e))
        
    def reset_configuration(self):
        if not self.host.runtime.inMaintenanceMode:
            self.enter_maintenance()        
        try:
            self.host.configManager.firmwareSystem.ResetFirmwareToFactoryDefaults()
            self.module.exit_json(changed=True)
        except Exception as e:
            self.exit_maintenance()
            self.module.fail_json(msg=str(e))
            
    def save_configuration(self): 
        if os.path.isdir(self.dest):
            url = self.host.configManager.firmwareSystem.BackupFirmwareConfiguration()
            #if http, change it manually to https because urllib2 doesn't do automatic redirects for PUT requests
            url = url.replace('http://', 'https://')
            url = url.replace('*', self.hostname)
            filename = url.rsplit('/', 1)[1]
            self.dest = os.path.join(self.dest, filename)
        else:
            self.module.fail_json(msg="Dest directory {} does not exist".format(self.dest))            
                             
        try:
            request = urllib2.Request(url)
            r = urllib2.urlopen(request)
            with open(self.dest, "wb") as file:
                file.write(r.read())
            self.module.exit_json(changed=True, dest_file=self.dest)
        except Exception as e:
            self.module.fail_json(msg=str(e))

    def enter_maintenance(self):
        try:
            task = self.host.EnterMaintenanceMode_Task(timeout=15)
            success, result = wait_for_task(task)
        except Exception as e:
            self.module.fail_json(msg=str(e))
            
    def exit_maintenance(self):
        try:
            task = self.host.ExitMaintenanceMode_Task(timeout=15)
            success, result = wait_for_task(task)
        except Exception as e:
            self.module.fail_json(msg=str(e))
      
    
def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(dest=dict(required=False, type='path'),
                              src=dict(required=False, type='path'),
                              state=dict(required=True, choices=['saved', 'absent', 'loaded'], type='str')))
    required_if = [('state', 'saved', ['dest']),
                   ('state', 'loaded', ['src'])]
    
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')
        
    vmware_cfg_backup = VMwareConfigurationBackup(module)
    vmware_cfg_backup.process_state()

from ansible.module_utils.vmware import *
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
