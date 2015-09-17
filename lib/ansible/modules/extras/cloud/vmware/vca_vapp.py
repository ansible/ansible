#!/usr/bin/python

# Copyright (c) 2015 Ansible, Inc.
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
module: vca_vapp
short_description: create, terminate, start or stop a vm in vca
description:
  - Creates or terminates vca vms.
version_added: "2.0"
author: Peter Sprygada (@privateip)
options:
    username:
      description:
        - The vca username or email address, if not set the environment variable VCA_USER is checked for the username.
      required: false
      default: None
    password:
      description:
        - The vca password, if not set the environment variable VCA_PASS is checked for the password
      required: false
      default: None
    org:
      description:
        - The org to login to for creating vapp, mostly set when the service_type is vdc.
      required: false
      default: None
    service_id:
      description:
        - The service id in a vchs environment to be used for creating the vapp
      required: false
      default: None
    host:
      description:
        - The authentication host to be used when service type  is vcd.
      required: false
      default: None
    api_version:
      description:
        - The api version to be used with the vca
      required: false
      default: "5.7"
    service_type:
      description:
        - The type of service we are authenticating against
      required: false
      default: vca
      choices: [ "vca", "vchs", "vcd" ]
    state:
      description:
        - if the object should be added or removed
      required: false
      default: present
      choices: [ "present", "absent" ]
    catalog_name:
      description:
        - The catalog from which the vm template is used.
      required: false
      default: "Public Catalog"
    script:
      description:
        - The path to script that gets injected to vm during creation.
      required: false
      default: "Public Catalog"
    template_name:
      description:
        - The template name from which the vm should be created.
      required: True
    network_name:
      description:
        - The network name to which the vm should be attached.
      required: false
      default: 'None'
    network_mode:
      description:
        - The network mode in which the ip should be allocated.
      required: false
      default: pool
      choices: [ "pool", "dhcp", 'static' ]
    instance_id::
      description:
        - The instance id of the region in vca flavour where the vm should be created
      required: false
      default: None
    vdc_name:
      description:
        - The name of the vdc where the vm should be created.
      required: false
      default: None
    vm_name:
      description:
        - The name of the vm to be created, the vapp is named the same as the vapp name
      required: false
      default: 'default_ansible_vm1'
    vm_cpus:
      description:
        - The number if cpus to be added to the vm
      required: false
      default: None
    vm_memory:
      description:
        - The amount of memory to be added to vm in megabytes
      required: false
      default: None
'''

EXAMPLES = '''

#Create a vm in an vca environment. The username password is not set as they are set in environment

- hosts: localhost
  connection: local
  tasks:
   - vca_vapp:
       operation: poweroff
       instance_id: 'b15ff1e5-1024-4f55-889f-ea0209726282'
       vdc_name: 'benz_ansible'
       vm_name: benz
       vm_cpus: 2
       vm_memory: 1024
       network_mode: pool
       template_name: "CentOS63-32BIT"
       admin_password: "Password!123"
       network_name: "default-routed-network"

#Create a vm in a vchs environment.

- hosts: localhost
  connection: local
  tasks:
   - vca_app:
       operation: poweron
       service_id: '9-69'
       vdc_name: 'Marketing'
       service_type: 'vchs'
       vm_name: benz
       vm_cpus: 1
       script: "/tmp/configure_vm.sh"
       catalog_name: "Marketing-Catalog"
       template_name: "Marketing-Ubuntu-1204x64"
       vm_memory: 512
       network_name: "M49-default-isolated"

#create a vm in a vdc environment

- hosts: localhost
  connection: local
  tasks:
   - vca_vapp:
       operation: poweron
       org: IT20
       host: "mycloud.vmware.net"
       api_version: "5.5"
       service_type: vcd
       vdc_name: 'IT20 Data Center (Beta)'
       vm_name: benz
       vm_cpus: 1
       catalog_name: "OS Templates"
       template_name: "CentOS 6.5 64Bit CLI"
       network_mode: pool

'''

try:
    from pyvcloud.vcloudair import VCA
    HAS_PYVCLOUD = True
except ImportError:
    HAS_PYVCLOUD = False

VAPP_STATE_MAP = {
    'poweron': 'Powered on',
    'poweroff': 'Powered off',
    'reboot': None,
    'reset': None,
    'shutdown': 'Powered off',
    'suspend': 'Suspended',
    'absent': None
}

def modify_vapp(vapp, module):
    vm_name = module.params['vm_name']
    vm_cpus = module.params['vm_cpus']
    vm_memory = module.params['vm_memory']

    changed = False

    try:
        vm = vapp.get_vms_details()[0]
    except IndexError:
        raise VcaError('No VM provisioned for vapp')

    if vm['status'] != 'Powered off':
        raise VcaError('vApp must be powered off to modify')

    if vm_cpus != vm['cpus'] and vm_cpus is not None:
        if not module.check_mode:
            task = vapp.modify_vm_cpu(vm_name, vm_cpus)
        changed = True

    if vm_memory != vm['memory_mb'] and vm_memory is not None:
        if not module.check_mode:
            task = vca.modify_vm_memory(vm_name, vm_memory)
        changed = True

    return changed


def set_vapp_state(vapp, state):
    vm = vapp.get_vms_details()[0]
    try:
        if vm['status'] != VAPP_STATE_MAP[state]:
            func = getattr(vm, state)
            func()
    except KeyError:
        raise VcaError('unknown vapp state', state=str(state), vm=str(vm))


def create_vapp(vca, module):
    vdc_name = module.params['vdc_name']
    vapp_name = module.params['vapp_name']
    template_name = module.params['template_name']
    catalog_name = module.params['catalog_name']
    network_name = module.params['network_name']
    network_mode = module.params['network_mode']
    vm_name = module.params['vm_name']
    vm_cpus = module.params['vm_cpus']
    vm_memory = module.params['vm_memory']
    deploy = module.params['deploy']

    task = vca.create_vapp(vdc_name, vapp_name, template_name, catalog_name,
                           network_name, network_mode, vm_name, vm_cpus,
                           vm_memory, deploy, False)

    vca.block_until_completed(task)

    return vca.get_vapp(vca.get_vdc(vdc_name), vapp_name)

def remove_vapp(vca, module):
    vdc_name = module.params['vdc_name']
    vapp_name = module.params['vapp_name']
    if not vca.delete_vapp(vdc_name, vapp_name):
        raise VcaError('unable to delete %s from %s' % (vapp_name, vdc_name))


def main():
    argument_spec = vca_argument_spec()
    argument_spec.update(
        dict(
            vdc_name=dict(requred=True),
            vapp_name=dict(required=True),
            template_name=dict(required=True),
            catalog_name=dict(default='Public Catalog'),
            network_name=dict(),
            network_mode=dict(default='pool', choices=['dhcp', 'static', 'pool']),
            vm_name=dict(),
            vm_memory=dict(),
            vm_cpus=dict(),
            deploy=dict(default=False),
            state=dict(default='poweron', choices=VAPP_STATE_MAP.keys())
        )
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    vdc_name = module.params['vdc_name']
    vapp_name = module.params['vapp_name']
    state = module.params['state']

    if not HAS_PYVCLOUD:
        module.fail_json(msg="python module pyvcloud is needed for this module")

    vca = vca_login(module)

    vdc = vca.get_vdc(vdc_name)
    if not vdc:
        module.fail_json(msg="Error getting the vdc, Please check the vdc name")

    result = dict(changed=False)

    vapp = vca.get_vapp(vdc, vapp_name)

    try:
        if not vapp and state != 'absent':
            if not module.check_mode:
                vapp = create_vapp(vca, module)
                set_vapp_state(vapp, state)
            result['changed'] = True
        elif vapp and state == 'absent':
            if not module.check_mode:
                remove_vapp(vca, module)
            result['changed'] = True
        elif vapp:
            if not module.check_mode:
                changed = modify_vapp(vapp, module)
                set_vapp_state(vapp, state)
            result['changed'] = True
    except VcaError, e:
        module.fail_json(msg=e.message, **e.kwargs)
    except Exception, e:
        module.fail_json(msg=e.message)

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.vca import *

if __name__ == '__main__':
    main()
