#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Anusha Hegde <anushah@vmware.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: vmware_guest_cross_vc_clone

short_description: Cross-vCenter VM/template clone

version_added: '2.10'

description:
  - 'This module can be used for Cross-vCenter vm/template clone'

options:
  name:
    description:
      - Name of the virtual machine or template.
      - This is a required parameter, if parameter C(uuid) or C(moid) is not supplied.
    type: str
  uuid:
    description:
      - UUID of the vm/template instance to clone from, this is VMware's unique identifier.
      - This is a required parameter, if parameter C(name) or C(moid) is not supplied.
    type: str
  moid:
    description:
      - Managed Object ID of the vm/template instance to manage if known, this is a unique identifier only within a single vCenter instance.
      - This is required if C(name) or C(uuid) is not supplied.
    type: str
  use_instance_uuid:
    description:
      - Whether to use the VMware instance UUID rather than the BIOS UUID.
    default: no
    type: bool
  destination_vm_name:
    description:
      - The name of the cloned VM.
    type: str
    required: True
  destination_vcenter:
    description:
      - The hostname or IP address of the destination VCenter.
    type: str
    required: True
  destination_vcenter_username:
    description:
      - The username of the destination VCenter.
    type: str
    required: True
  destination_vcenter_password:
    description:
      - The password of the destination VCenter.
    type: str
    required: True
  destination_vcenter_port:
    description:
      - The port to establish connection in the destination VCenter.
    type: int
    default: 443
  destination_vcenter_validate_certs:
    description:
      - Parameter to indicate if certification validation needs to be done on destination VCenter.
    type: bool
    default: False
  destination_host:
    description:
      - The name of the destination host.
    type: str
    required: True
  destination_datastore:
    description:
      - The name of the destination datastore or the datastore cluster.
      - If datastore cluster name is specified, we will find the Storage DRS recommended datastore in that cluster.
    type: str
    required: True
  destination_vm_folder:
    description:
      - Destination folder, absolute path to deploy the cloned vm.
      - This parameter is case sensitive.
      - 'Examples:'
      - '   folder: vm'
      - '   folder: ha-datacenter/vm'
      - '   folder: /datacenter1/vm'
    type: str
    required: True
  destination_resource_pool:
    description:
      - Destination resource pool.
      - If not provided, the destination host's parent's resource pool will be used.
    type: str
  state:
    description:
      - The state of Virtual Machine deployed.
      - If set to C(present) and VM does not exists, then VM is created.
      - If set to C(present) and VM exists, no action is taken.
      - If set to C(poweredon) and VM does not exists, then VM is created with powered on state.
      - If set to C(poweredon) and VM exists, no action is taken.
    type: str
    required: False
    default: 'present'
    choices: [ 'present', 'poweredon' ]

extends_documentation_fragment:
  - vmware.documentation

author:
  - Anusha Hegde (@anusha94)
'''

EXAMPLES = '''
# Clone template
- name: clone a template across VC
  vmware_guest_cross_vc_clone:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    validate_certs: no
    name: "test_vm1"
    destination_vm_name: "cloned_vm_from_template"
    destination_vcenter: '{{ destination_vcenter_hostname }}'
    destination_vcenter_username: '{{ destination_vcenter_username }}'
    destination_vcenter_password: '{{ destination_vcenter_password }}'
    destination_vcenter_port: '{{ destination_vcenter_port }}'
    destination_vcenter_validate_certs: '{{ destination_vcenter_validate_certs }}'
    destination_host: '{{ destination_esxi }}'
    destination_datastore: '{{ destination_datastore }}'
    destination_vm_folder: '{{ destination_vm_folder }}'
    state: present
  register: cross_vc_clone_from_template

- name: clone a VM across VC
  vmware_guest_cross_vc_clone:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: "{{ vcenter_password }}"
    validate_certs: no
    name: "test_vm1"
    destination_vm_name: "cloned_vm_from_vm"
    destination_vcenter: '{{ destination_vcenter_hostname }}'
    destination_vcenter_username: '{{ destination_vcenter_username }}'
    destination_vcenter_password: '{{ destination_vcenter_password }}'
    destination_host: '{{ destination_esxi }}'
    destination_datastore: '{{ destination_datastore }}'
    destination_vm_folder: '{{ destination_vm_folder }}'
    state: poweredon
  register: cross_vc_clone_from_vm

- name: check_mode support
  vmware_guest_cross_vc_clone:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: "{{ vcenter_password }}"
    validate_certs: no
    name: "test_vm1"
    destination_vm_name: "cloned_vm_from_vm"
    destination_vcenter: '{{ destination_vcenter_hostname }}'
    destination_vcenter_username: '{{ destination_vcenter_username }}'
    destination_vcenter_password: '{{ destination_vcenter_password }}'
    destination_host: '{{ destination_esxi }}'
    destination_datastore: '{{ destination_datastore }}'
    destination_vm_folder: '{{ destination_vm_folder }}'
  check_mode: yes
'''

RETURN = r'''
vm_info:
    description: metadata about the virtual machine
    returned: always
    type: dict
    sample: {
        "vm_name": "",
        "vcenter": "",
        "host": "",
        "datastore": "",
        "vm_folder": "",
        "power_on": ""
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (PyVmomi, find_hostsystem_by_name,
                                         find_datastore_by_name,
                                         find_folder_by_name, find_vm_by_name,
                                         connect_to_api, vmware_argument_spec,
                                         gather_vm_facts, find_obj, find_resource_pool_by_name,
                                         wait_for_task, TaskError)
from ansible.module_utils._text import to_native
try:
    from pyVmomi import vim
except ImportError:
    pass


class CrossVCCloneManager(PyVmomi):
    def __init__(self, module):
        super(CrossVCCloneManager, self).__init__(module)
        self.config_spec = vim.vm.ConfigSpec()
        self.clone_spec = vim.vm.CloneSpec()
        self.relocate_spec = vim.vm.RelocateSpec()
        self.service_locator = vim.ServiceLocator()
        self.destination_vcenter = self.params['destination_vcenter']
        self.destination_vcenter_username = self.params['destination_vcenter_username']
        self.destination_vcenter_password = self.params['destination_vcenter_password']
        self.destination_vcenter_port = self.params.get('port', 443)
        self.destination_vcenter_validate_certs = self.params.get('destination_vcenter_validate_certs', None)

    def get_new_vm_info(self, vm):
        # to check if vm has been cloned in the destination vc
        # query for the vm in destination vc
        # get the host and datastore info
        # get the power status of the newly cloned vm
        info = {}
        vm_obj = find_vm_by_name(content=self.destination_content, vm_name=vm)
        if vm_obj is None:
            self.module.fail_json(msg="Newly cloned VM is not found in the destination VCenter")
        else:
            vm_facts = gather_vm_facts(self.destination_content, vm_obj)
            info['vm_name'] = vm
            info['vcenter'] = self.destination_vcenter
            info['host'] = vm_facts['hw_esxi_host']
            info['datastore'] = vm_facts['hw_datastores']
            info['vm_folder'] = vm_facts['hw_folder']
            info['power_on'] = vm_facts['hw_power_status']
        return info

    def clone(self):
        # clone the vm/template on destination VC
        vm_folder = find_folder_by_name(content=self.destination_content, folder_name=self.params['destination_vm_folder'])
        if not vm_folder:
            self.module.fail_json(msg="Destination folder does not exist. Please refer to the documentation to correctly specify the folder.")
        vm_name = self.params['destination_vm_name']
        task = self.vm_obj.Clone(folder=vm_folder, name=vm_name, spec=self.clone_spec)
        wait_for_task(task)
        if task.info.state == 'error':
            result = {'changed': False, 'failed': True, 'msg': task.info.error.msg}
        else:
            vm_info = self.get_new_vm_info(vm_name)
            result = {'changed': True, 'failed': False, 'vm_info': vm_info}
        return result

    def sanitize_params(self):
        '''
        this method is used to verify user provided parameters
        '''
        self.vm_obj = self.get_vm()
        if self.vm_obj is None:
            vm_id = self.vm_uuid or self.vm_name or self.moid
            self.module.fail_json(msg="Failed to find the VM/template with %s" % vm_id)

        # connect to destination VC
        self.destination_content = connect_to_api(
            self.module,
            hostname=self.destination_vcenter,
            username=self.destination_vcenter_username,
            password=self.destination_vcenter_password,
            port=self.destination_vcenter_port,
            validate_certs=self.destination_vcenter_validate_certs)

        # Check if vm name already exists in the destination VC
        vm = find_vm_by_name(content=self.destination_content, vm_name=self.params['destination_vm_name'])
        if vm:
            self.module.exit_json(changed=False, msg="A VM with the given name already exists")

        datastore_name = self.params['destination_datastore']
        datastore_cluster = find_obj(self.destination_content, [vim.StoragePod], datastore_name)
        if datastore_cluster:
            # If user specified datastore cluster so get recommended datastore
            datastore_name = self.get_recommended_datastore(datastore_cluster_obj=datastore_cluster)
            # Check if get_recommended_datastore or user specified datastore exists or not
        self.destination_datastore = find_datastore_by_name(content=self.destination_content, datastore_name=datastore_name)
        if self.destination_datastore is None:
            self.module.fail_json(msg="Destination datastore not found.")

        self.destination_host = find_hostsystem_by_name(content=self.destination_content, hostname=self.params['destination_host'])
        if self.destination_host is None:
            self.module.fail_json(msg="Destination host not found.")

        if self.params['destination_resource_pool']:
            self.destination_resource_pool = find_resource_pool_by_name(
                content=self.destination_content,
                resource_pool_name=self.params['destination_resource_pool'])
        else:
            self.destination_resource_pool = self.destination_host.parent.resourcePool

    def populate_specs(self):
        # populate service locator
        self.service_locator.instanceUuid = self.destination_content.about.instanceUuid
        self.service_locator.url = "https://" + self.destination_vcenter + ":" + str(self.params['port']) + "/sdk"
        creds = vim.ServiceLocatorNamePassword()
        creds.username = self.destination_vcenter_username
        creds.password = self.destination_vcenter_password
        self.service_locator.credential = creds

        # populate relocate spec
        self.relocate_spec.datastore = self.destination_datastore
        self.relocate_spec.pool = self.destination_resource_pool
        self.relocate_spec.service = self.service_locator
        self.relocate_spec.host = self.destination_host

        # populate clone spec
        self.clone_spec.config = self.config_spec
        self.clone_spec.powerOn = True if self.params['state'].lower() == 'poweredon' else False
        self.clone_spec.location = self.relocate_spec

    def get_recommended_datastore(self, datastore_cluster_obj=None):
        """
        Function to return Storage DRS recommended datastore from datastore cluster
        Args:
            datastore_cluster_obj: datastore cluster managed object
        Returns: Name of recommended datastore from the given datastore cluster
        """
        if datastore_cluster_obj is None:
            return None
        # Check if Datastore Cluster provided by user is SDRS ready
        sdrs_status = datastore_cluster_obj.podStorageDrsEntry.storageDrsConfig.podConfig.enabled
        if sdrs_status:
            # We can get storage recommendation only if SDRS is enabled on given datastorage cluster
            pod_sel_spec = vim.storageDrs.PodSelectionSpec()
            pod_sel_spec.storagePod = datastore_cluster_obj
            storage_spec = vim.storageDrs.StoragePlacementSpec()
            storage_spec.podSelectionSpec = pod_sel_spec
            storage_spec.type = 'create'

            try:
                rec = self.content.storageResourceManager.RecommendDatastores(storageSpec=storage_spec)
                rec_action = rec.recommendations[0].action[0]
                return rec_action.destination.name
            except Exception:
                # There is some error so we fall back to general workflow
                pass
        datastore = None
        datastore_freespace = 0
        for ds in datastore_cluster_obj.childEntity:
            if isinstance(ds, vim.Datastore) and ds.summary.freeSpace > datastore_freespace:
                # If datastore field is provided, filter destination datastores
                if not self.is_datastore_valid(datastore_obj=ds):
                    continue

                datastore = ds
                datastore_freespace = ds.summary.freeSpace
        if datastore:
            return datastore.name
        return None


def main():
    """
    Main method
    """
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        uuid=dict(type='str'),
        moid=dict(type='str'),
        use_instance_uuid=dict(type='bool', default=False),
        destination_vm_name=dict(type='str', required=True),
        destination_datastore=dict(type='str', required=True),
        destination_host=dict(type='str', required=True),
        destination_vcenter=dict(type='str', required=True),
        destination_vcenter_username=dict(type='str', required=True),
        destination_vcenter_password=dict(type='str', required=True, no_log=True),
        destination_vcenter_port=dict(type='int', default=443),
        destination_vcenter_validate_certs=dict(type='bool', default=False),
        destination_vm_folder=dict(type='str', required=True),
        destination_resource_pool=dict(type='str', default=None),
        state=dict(type='str', default='present',
                   choices=['present', 'poweredon'])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[
            ['uuid', 'name', 'moid'],
        ],
        mutually_exclusive=[
            ['uuid', 'name', 'moid'],
        ],
    )
    result = {'failed': False, 'changed': False}
    if module.check_mode:
        if module.params['state'] in ['present']:
            result.update(
                vm_name=module.params['destination_vm_name'],
                vcenter=module.params['destination_vcenter'],
                host=module.params['destination_host'],
                datastore=module.params['destination_datastore'],
                vm_folder=module.params['destination_vm_folder'],
                state=module.params['state'],
                changed=True,
                desired_operation='Create VM with PowerOff State'
            )
        if module.params['state'] == 'poweredon':
            result.update(
                vm_name=module.params['destination_vm_name'],
                vcenter=module.params['destination_vcenter'],
                host=module.params['destination_host'],
                datastore=module.params['destination_datastore'],
                vm_folder=module.params['destination_vm_folder'],
                state=module.params['state'],
                changed=True,
                desired_operation='Create VM with PowerON State'
            )
        module.exit_json(**result)

    clone_manager = CrossVCCloneManager(module)
    clone_manager.sanitize_params()
    clone_manager.populate_specs()
    result = clone_manager.clone()

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
