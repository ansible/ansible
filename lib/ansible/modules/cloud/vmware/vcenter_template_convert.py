#!/usr/bin/python
# Copyright (c) 2017 Alan Tang
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vcenter_template_convert
short_description: Convert between VM and template on vCenter.
description:
    - Convert between VM and template on vCenter.
version_added: "2.5"
author:
    - Alan Tang (@alantang888)
notes:
    - Tested on ESXi 6.0
requirements:
    - "python >= 2.7"
    - PyVmomi installed
options:
    server:
        description:
            - vCenter hostname to manage.
        required: true
    login:
        description:
            - vCenter username.
        required: true
    passwd:
        description:
            - vCetner password.
        required: true
    name:
        description:
            - Target VM or template name.
        required: true
    state:
        description:
            - Indicate desired state of the target.
        choices: [is_vm, is_template]
        required: true
    cluster:
        description:
            - Cluster where to place the VM, when convert template to VM. Required when state is 'is_vm'.
    resource_pool:
        description:
            - Resource Pool where to place the VM, when convert template to VM. Optional, if not define, will put the VM under cluster root.
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
---
# vCenter is "vcenter01.example.local"
# vCenter username is "administrator@vsphere.local"
# vCenter password is "P@ssword"

# Set target "vm001" to VM place under cluster named "non-prod"
- vcenter_template:
        name: 'vm001'
        server: 'vcenter01.example.local'
        login: 'administrator@vsphere.local'
        passwd: 'P@ssword'
        state: 'is_vm'
        cluster: 'non-prod'

# Set target "vm001" to template
- vcenter_template:
        name: 'vm001'
        server: 'vcenter01.example.local'
        login: 'administrator@vsphere.local'
        passwd: 'P@ssword'
        state: 'is_template'
'''

RETURN = '''
---
meta:
    description: Message of result or error resason
    returned: always
    type: string
    sample:
        - Ordered VM convert to template.
        - Ordered template convert to VM.
        - Already is VM.
        - Already is template.
        - Cluster "xxx" not found.
        - VM "{}" not found.
        - Cluster is required on "is_vm" state.
'''

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
from pyVim import connect
from pyVmomi import vim
__metaclass__ = type


def get_all_vm_under_folder(vm_folder_child_entity):
    vm_list = []
    for item in vm_folder_child_entity:
        if isinstance(item, vim.VirtualMachine):
            vm_list.append(item)
        if isinstance(item, vim.Folder):
            # logger.debug('Found folder: {}, with {} child.'.format(item.name, len(item.childEntity)))
            child_list = (get_all_vm_under_folder(item.childEntity))
            if len(child_list) != 0:
                vm_list += child_list

    return vm_list


def connect_vcenter(server, login, passwd):
    vcenter_si = connect.SmartConnectNoSSL(host=server, user=login, pwd=passwd)

    content = vcenter_si.RetrieveContent()
    datacenter = content.rootFolder.childEntity[0]
    # datastores = datacenter.datastore
    clusters = datacenter.hostFolder.childEntity
    vmfolder = datacenter.vmFolder
    raw_vmlist = vmfolder.childEntity
    vms = get_all_vm_under_folder(raw_vmlist)
    return (clusters, vms)


def is_vm(data):
    if 'cluster' not in data or not data['cluster']:
        return (False, False, 'Cluster is required on "is_vm" state.')
    clusters, vms = connect_vcenter(data['server'], data['login'], data['passwd'])

    target_vm = [vm for vm in vms if vm.name == data['name']]
    if len(target_vm) != 1:
        return (False, False, 'VM "{0}" not found.'.format(data['name']))
    target_vm = target_vm[0]

    # if target_vm has resourcePool, that will be a VM
    if target_vm.resourcePool is not None:
        return (True, False, 'Already is VM.')

    destination = [cluster for cluster in clusters if cluster.name == data['cluster']]
    if len(destination) != 1:
        return (False, False, 'Cluster "{0}" not found.'.format(data['cluster']))
    destination = destination[0].resourcePool

    if 'resource_pool' in data and data['resource_pool']:
        target_resource_pool = [res for res in destination.resourcePool if res.name == data['resource_pool']]
        if len(target_resource_pool) == 1:
            destination = target_resource_pool[0]

    target_vm.MarkAsVirtualMachine(pool=destination)
    return (True, True, "Ordered template convert to VM.")


def is_template(data):
    clusters, vms = connect_vcenter(data['server'], data['login'], data['passwd'])

    target_vm = [vm for vm in vms if vm.name == data['name']]
    if len(target_vm) != 1:
        return (False, False, 'VM name {0} not found.'.format(data['name']))

    target_vm = target_vm[0]

    # if target not in resource pool, that will be a template
    if target_vm.resourcePool is None:
        return (True, False, 'Already is template.')

    target_vm.MarkAsTemplate()
    return (True, True, "Ordered VM convert to template.")


def main():
    fields = {
        'server': {'required': True, 'type': 'str'},
        'login': {'required': True, 'type': 'str'},
        'passwd': {'required': True, 'type': 'str', 'no_log': True},
        'name': {'required': True, 'type': 'str'},
        'state': {'required': True, 'type': 'str', 'choices': ['is_vm', 'is_template']},
        'cluster': {'default': False, 'type': 'str'},
        'resource_pool': {'default': False, 'type': 'str'}
    }

    state_map = {
        'is_vm': is_vm,
        'is_template': is_template
    }

    module = AnsibleModule(argument_spec=fields)

    success, changed, result = state_map.get(module.params['state'])(module.params)

    if success:
        module.exit_json(changed=changed, meta=result)
    else:
        module.fail_json(msg='Error', meta=result)


if __name__ == '__main__':
    main()
