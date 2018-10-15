#!/usr/bin/python
# Copyright: (c) 2015, Ansible, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: vca_vapp
short_description: Manages vCloud Air vApp instances.
description:
  - This module will actively managed vCloud Air vApp instances.  Instances
    can be created and deleted as well as both deployed and undeployed.
version_added: "2.0"
author:
- Peter Sprygada (@privateip)
notes:
- VMware sold their vCloud Air service in Q2 2017.
- VMware made significant changes to the pyvcloud interface around this time.  The C(vca_vapp) module relies on now deprecated code.
- Mileage with C(vca_vapp) may vary as vCloud Director APIs advance.
- A viable alternative maybe U(https://github.com/vmware/ansible-module-vcloud-director)
requirements:
- pyvcloud <= 18.2.2
options:
  vapp_name:
    description:
      - The name of the vCloud Air vApp instance
    required: yes
  template_name:
    description:
      - The name of the vApp template to use to create the vApp instance.  If
        the I(state) is not `absent` then the I(template_name) value must be
        provided.  The I(template_name) must be previously uploaded to the
        catalog specified by I(catalog_name)
  network_name:
    description:
      - The name of the network that should be attached to the virtual machine
        in the vApp.  The virtual network specified must already be created in
        the vCloud Air VDC.  If the I(state) is not 'absent' then the
        I(network_name) argument must be provided.
  network_mode:
    description:
      - Configures the mode of the network connection.
    default: pool
    choices: ['pool', 'dhcp', 'static']
  vm_name:
    description:
      - The name of the virtual machine instance in the vApp to manage.
  vm_cpus:
    description:
      - The number of vCPUs to configure for the VM in the vApp.   If the
        I(vm_name) argument is provided, then this becomes a per VM setting
        otherwise it is applied to all VMs in the vApp.
  vm_memory:
    description:
      - The amount of memory in MB to allocate to VMs in the vApp.  If the
        I(vm_name) argument is provided, then this becomes a per VM setting
        otherise it is applied to all VMs in the vApp.
  operation:
    description:
      - Specifies an operation to be performed on the vApp.
    default: noop
    choices: ['noop', 'poweron', 'poweroff', 'suspend', 'shutdown', 'reboot', 'reset']
  state:
    description:
      - Configures the state of the vApp.
    default: present
    choices: ['present', 'absent', 'deployed', 'undeployed']
  username:
    description:
      - The vCloud Air username to use during authentication
  password:
    description:
      - The vCloud Air password to use during authentication
  org:
    description:
      - The org to login to for creating vapp, mostly set when the service_type is vdc.
  instance_id:
    description:
      - The instance id in a vchs environment to be used for creating the vapp
  host:
    description:
      - The authentication host to be used when service type  is vcd.
  api_version:
    description:
      - The api version to be used with the vca
    default: "5.7"
  service_type:
    description:
      - The type of service we are authenticating against
    default: vca
    choices: [ "vca", "vchs", "vcd" ]
  vdc_name:
    description:
      - The name of the virtual data center (VDC) where the vm should be created or contains the vAPP.
extends_documentation_fragment: vca
'''

EXAMPLES = '''
- name: Creates a new vApp in a VCA instance
  vca_vapp:
    vapp_name: tower
    state: present
    template_name: 'Ubuntu Server 12.04 LTS (amd64 20150127)'
    vdc_name: VDC1
    instance_id: '<your instance id here>'
    username: '<your username here>'
    password: '<your password here>'
  delegate_to: localhost
'''

from ansible.module_utils.vca import VcaAnsibleModule, VcaError

DEFAULT_VAPP_OPERATION = 'noop'

VAPP_STATUS = {
    'Powered off': 'poweroff',
    'Powered on': 'poweron',
    'Suspended': 'suspend'
}

VAPP_STATES = ['present', 'absent', 'deployed', 'undeployed']
VAPP_OPERATIONS = ['poweron', 'poweroff', 'suspend', 'shutdown',
                   'reboot', 'reset', 'noop']


def get_instance(module):
    vapp_name = module.params['vapp_name']
    inst = dict(vapp_name=vapp_name, state='absent')
    try:
        vapp = module.get_vapp(vapp_name)
        if vapp:
            status = module.vca.get_status(vapp.me.get_status())
            inst['status'] = VAPP_STATUS.get(status, 'unknown')
            inst['state'] = 'deployed' if vapp.me.deployed else 'undeployed'
        return inst
    except VcaError:
        return inst


def create(module):
    vdc_name = module.params['vdc_name']
    vapp_name = module.params['vapp_name']
    template_name = module.params['template_name']
    catalog_name = module.params['catalog_name']
    network_name = module.params['network_name']
    network_mode = module.params['network_mode']
    vm_name = module.params['vm_name']
    vm_cpus = module.params['vm_cpus']
    vm_memory = module.params['vm_memory']
    deploy = module.params['state'] == 'deploy'
    poweron = module.params['operation'] == 'poweron'

    task = module.vca.create_vapp(vdc_name, vapp_name, template_name,
                                  catalog_name, network_name, 'bridged',
                                  vm_name, vm_cpus, vm_memory, deploy, poweron)

    if task is False:
        module.fail('Failed to create vapp: %s' % vapp_name)

    module.vca.block_until_completed(task)

    # Connect the network to the Vapp/VM and return asigned IP
    if network_name is not None:
        vm_ip = connect_to_network(module, vdc_name, vapp_name, network_name, network_mode)
        return vm_ip


def delete(module):
    vdc_name = module.params['vdc_name']
    vapp_name = module.params['vapp_name']
    module.vca.delete_vapp(vdc_name, vapp_name)


def do_operation(module):
    vapp_name = module.params['vapp_name']
    operation = module.params['operation']

    vm_name = module.params.get('vm_name')
    vm = None
    if vm_name:
        vm = module.get_vm(vapp_name, vm_name)

    if operation == 'poweron':
        operation = 'powerOn'
    elif operation == 'poweroff':
        operation = 'powerOff'

    cmd = 'power:%s' % operation
    module.get_vapp(vapp_name).execute(cmd, 'post', targetVM=vm)


def set_state(module):
    state = module.params['state']
    vapp = module.get_vapp(module.params['vapp_name'])
    if state == 'deployed':
        action = module.params['operation'] == 'poweron'
        if not vapp.deploy(action):
            module.fail('unable to deploy vapp')
    elif state == 'undeployed':
        action = module.params['operation']
        if action == 'poweroff':
            action = 'powerOff'
        elif action != 'suspend':
            action = None
        if not vapp.undeploy(action):
            module.fail('unable to undeploy vapp')


def connect_to_network(module, vdc_name, vapp_name, network_name, network_mode):
    nets = filter(lambda n: n.name == network_name, module.vca.get_networks(vdc_name))
    if len(nets) != 1:
        module.fail_json("Unable to find network %s " % network_name)

    the_vdc = module.vca.get_vdc(vdc_name)
    the_vapp = module.vca.get_vapp(the_vdc, vapp_name)

    if the_vapp and the_vapp.name != vapp_name:
        module.fail_json(msg="Failed to find vapp named %s" % the_vapp.name)

    # Connect vApp
    task = the_vapp.connect_to_network(nets[0].name, nets[0].href)
    result = module.vca.block_until_completed(task)

    if result is None:
        module.fail_json(msg="Failed to complete task")

    # Connect VM
    ip_allocation_mode = None
    if network_mode == 'pool':
        ip_allocation_mode = 'POOL'
    elif network_mode == 'dhcp':
        ip_allocation_mode = 'DHCP'

    task = the_vapp.connect_vms(nets[0].name, connection_index=0, ip_allocation_mode=ip_allocation_mode)
    if result is None:
        module.fail_json(msg="Failed to complete task")

    result = module.vca.block_until_completed(task)
    if result is None:
        module.fail_json(msg="Failed to complete task")

    # Update VApp info and get VM IP
    the_vapp = module.vca.get_vapp(the_vdc, vapp_name)
    if the_vapp is None:
        module.fail_json(msg="Failed to get vapp named %s" % vapp_name)

    return get_vm_details(module)


def get_vm_details(module):
    vdc_name = module.params['vdc_name']
    vapp_name = module.params['vapp_name']
    vm_name = module.params['vm_name']
    the_vdc = module.vca.get_vdc(vdc_name)
    the_vapp = module.vca.get_vapp(the_vdc, vapp_name)
    if the_vapp and the_vapp.name != vapp_name:
        module.fail_json(msg="Failed to find vapp named %s" % the_vapp.name)
    the_vm_details = dict()

    for vm in the_vapp.me.Children.Vm:
        sections = vm.get_Section()

        customization_section = (
            filter(lambda section:
                   section.__class__.__name__ ==
                   "GuestCustomizationSectionType",
                   sections)[0])
        if customization_section.get_AdminPasswordEnabled():
            the_vm_details["vm_admin_password"] = customization_section.get_AdminPassword()

        virtual_hardware_section = (
            filter(lambda section:
                   section.__class__.__name__ ==
                   "VirtualHardwareSection_Type",
                   sections)[0])
        items = virtual_hardware_section.get_Item()
        ips = []
        _url = '{http://www.vmware.com/vcloud/v1.5}ipAddress'
        for item in items:
            if item.Connection:
                for c in item.Connection:
                    if c.anyAttributes_.get(
                            _url):
                        ips.append(c.anyAttributes_.get(
                            _url))
    if len(ips) > 0:
        the_vm_details["vm_ip"] = ips[0]

    return the_vm_details


def main():
    argument_spec = dict(
        vapp_name=dict(required=True),
        vdc_name=dict(required=True),
        template_name=dict(),
        catalog_name=dict(default='Public Catalog'),
        network_name=dict(),
        network_mode=dict(default='pool', choices=['dhcp', 'static', 'pool']),
        vm_name=dict(),
        vm_cpus=dict(),
        vm_memory=dict(),
        operation=dict(default=DEFAULT_VAPP_OPERATION, choices=VAPP_OPERATIONS),
        state=dict(default='present', choices=VAPP_STATES)
    )

    module = VcaAnsibleModule(argument_spec=argument_spec,
                              supports_check_mode=True)

    state = module.params['state']
    operation = module.params['operation']

    instance = get_instance(module)

    result = dict(changed=False)

    if instance and state == 'absent':
        if not module.check_mode:
            delete(module)
        result['changed'] = True

    elif state != 'absent':
        if instance['state'] == 'absent':
            if not module.check_mode:
                result['ansible_facts'] = create(module)
            result['changed'] = True

        elif instance['state'] != state and state != 'present':
            if not module.check_mode:
                set_state(module)
            result['changed'] = True

        if operation != instance.get('status') and operation != 'noop':
            if not module.check_mode:
                do_operation(module)
            result['changed'] = True
        result['ansible_facts'] = get_vm_details(module)

    return module.exit(**result)


if __name__ == '__main__':
    main()
