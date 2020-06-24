#!/usr/bin/python

# Copyright: (c) 2020, Lenovo
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.tacp_ansible import tacp_utils
from ansible.module_utils.tacp_ansible.tacp_exceptions import ActionTimedOutException, InvalidActionUuidException
from ansible.module_utils.tacp_ansible.tacp_constants import State, Action


import json
import tacp
import sys
from uuid import uuid4
from tacp.rest import ApiException
from pprint import pprint

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: tacp_instance

short_description: Creates and modifies power state of application instances on
                    ThinkAgile CP.

description:
    - 'This module can be used to create new application instances on the
        ThinkAgile CP cloud platform, as well as delete and modify power states
        of existing application instances.'
    - 'Currently this module cannot modify the resources of existing
        application instances aside from performing deletion and power state
        operations.'
author:
    - Lenovo (@lenovo)
    - Xander Madsen (@xmadsen)

requirements:
- tacp

options:
    api_key:
        description:
            - An API key generated in the Developer Options in the ThinkAgile
                CP portal. This is required to perform any operations with this
                module.
        required: true
        type: str
    name:
        description:
            - This is the name of the instance to be created or modified
        required: true
        type: str
    state:
        description:
            - The desired state for the application instance in question. All
                options except 'absent' will perform a power operation if
                necessary, while 'absent' deletes the application instance with
                the provided name if it exists.
        choices:
            - started
            - shutdown
            - stopped
            - restarted
            - force_restarted
            - paused
            - absent
    datacenter:
        description:
            - The name of the virtual datacenter that the instance will be
              created in. Only required when creating a new instance.
        required: false
        type: str
    migration_zone:
        description:
            - The name of the migration zone that the instance will be created
              in. Only required when creating a new instance.
        required: false
        type: str
    template:
        description:
            - The name of the template used as a basis for the creation of the
              instance. Only required when creating a new instance.
        required: false
        type: str
    storage_pool:
        description:
            - The name of the storage pool that the instance's disks will be
              stored in. Only required when creating a new instance.
        required: false
        type: str
    vcpu_cores:
        description:
            - The number of virtual CPU cores that the application instance
              will have when it is created. Only required when creating a new
              instance.
        required: false
        type: int
    memory:
        description:
            - The amount of virtual memory (RAM) that the application instance
              will have when it is created. Can be expressed with various
              units. Only required when creating a new instance.
        required: false
        type: str
    disks:
        description:
            - An array of disks that will be associated with the application
              instance when it is created.
            - Must contain any disks that the template contains, and the names
              must match for any of those such disks. Only required when
              creating a new instance.
        required: false
        type: list
        suboptions:
            name:
                description:
                    - The name of the disk. If the specified disk is not part
                      of the template, it can be named anything (except the
                      name of a disk in the template).
                required: true
                type: str
            size_gb:
                description:
                    - The size of the disk in GB. Can be expressed as a float.
                required: true
                type: float
            boot_order:
                description:
                    - The place in the boot order for the disk. The overall
                      boot order must begin at 1, and every NIC and disk must
                      have an order provided.
                required: true
                type: int
            bandwidth_limit:
                description:
                    - A limit to the bandwidth usage allowed for this disk.
                      Must be at least 5000000 (5 Mbps).
                required: false
                type: int
            iops_limit:
                description:
                    - A limit to the total IOPS allowed for this disk.
                      Must be at least 50.
                required: false
                type: int
    nics:
        description:
            - An array of NICs that will be associated with the application
              instance when it is created.
            - Must contain any NICs that the template contains, and the names
              must match for any of those such NICs. Only required when
              creating a new instance.
        required: false
        type: list
        suboptions:
            name:
                description:
                    - The name of the NIC. If the specified NIC is not part
                      of the template, it can be named anything (except the
                      name of a NIC in the template).
                required: true
                type: str
            type:
                description:
                    - The type of network that the NIC will be a part of.
                    - Valid chocies are either "VNET" or "VLAN".
                required: true
                type: str
            network:
                description:
                    - The name of the network that the NIC will be a part of.
                    - There must be an existing network of the provided type
                      that has the provided network name to succeed.
                required: true
                type: str
            boot_order:
                description:
                    - The place in the boot order for the NIC. The overall boot
                      order must begin at 1, and every NIC and disk must have
                      an order provided.
                required: true
                type: int
            automatic_mac_address:
                description:
                    - Whether this interface should be automatically assigned
                      a MAC address.
                    - Providing a MAC address to the mac_address field sets
                      this value to false.
                required: false
                type: bool
            mac_address:
                description:
                    - A static MAC address to be assigned to the NIC. Should
                      not exist on any other interfaces on the network.
                    - Should be of the format aa:bb:cc:dd:ee:ff
                    - If this is set, 'automatic_mac_address' is automatically
                      set to false.
                required: false
                type: str
            firewall_override:
                description:
                    - The name of a firewall override that exists in the
                      datacenter that the NIC's instance will reside in.
                required: false
                type: str
    vtx_enabled:
        description:
            - Whether or not VT-x nested virtualization features should be
              enabled for the instance. Enabled by default.
        required: false
        type: bool
    auto_recovery_enabled:
        description:
            - Whether or not the instance should be restarted on a different
              host node in the event that its host node fails. Defaults to
              true.
        required: false
        type: bool
    description:
        description:
            - A textual description of the instance. Defaults to any
              description that the source template come with.
        required: false
        type: str
    vm_mode:
        description:
            - Sets the instance mode. Set to "Enhanced" by default.
            - Valid choices are "Enhanced" and "Compatibility"
            - Any instance can boot in Compatibility mode.
            - In Enhanced mode, Virtio drivers must be present in the template
              in order to boot.
            - Additionally, in Enhanced mode:
                - Storage disks are exported as virtio iSCSI devices
                - vNICs are exported as virtio vNICs
                - Snapshots will be application consistent (when ThinkAgile CP
                  Guest Agent is installed) if the guest OS supports freeze and
                  thaw
                - CPU and Memory Statistics are available (When ThinkAgile CP
                  Guest Agent is installed)
        required: false
        type: str
    application_group:
        description:
            - The name of an application group that the instance will be put
              in. Creates it in the virtual datacenter if it does not yet exist
              .
        required: false
        type: str
'''

EXAMPLES = '''
- name: Create a basic VM on ThinkAgile CP
  tacp_instance:
      api_key: "{{ api_key }}"
      name: Basic_VM1
      state: started
      datacenter: Datacenter1
      migration_zone: Zone1
      template: CentOS 7.5 (64-bit) - Lenovo Template
      storage_pool: Pool1
      vcpu_cores: 1
      memory: 4096GB
      disks:
      - name: Disk 0
          size_gb: 50
          boot_order: 1
      nics:
      - name: vNIC 0
          type: VNET
          network: VNET-TEST
          boot_order: 2

- name: Create a shutdown VM with multiple disks and set its NIC to the first 
        boot device
  tacp_instance:
      api_key: "{{ api_key }}"
      name: Basic_VM2
      state: started
      datacenter: Datacenter1
      migration_zone: Zone1
      template: RHEL 7.4 (Minimal) - Lenovo Template
      storage_pool: Pool1
      vcpu_cores: 1
      memory: 8G
      disks:
      - name: Disk 0
          size_gb: 50
          boot_order: 2
      - name: Disk 1
          size_gb: 200
          boot_order: 3
      nics:
      - name: vNIC 0
          type: VLAN
          network: VLAN-300
          boot_order: 1

- name: Create a VM with multiple disks with limits, and two NICs with static
        MAC addresses, and don't power it on after creation
  tacp_instance:
      api_key: "{{ api_key }}"
      name: Basic_VM3
      state: shutdown
      datacenter: Datacenter1
      migration_zone: Zone1
      template: RHEL 7.4 (Minimal) - Lenovo Template
      storage_pool: Pool1
      vcpu_cores: 1
      memory: 8GB
      disks:
      - name: Disk 0
          size_gb: 50
          boot_order: 2
          iops_limit: 200
      - name: Disk 1
          size_gb: 200
          boot_order: 3
          bandwidth_limit: 10000000
      nics:
      - name: vNIC 0
          type: VLAN
          network: VLAN-300
          boot_order: 4
          firewall_override: Allow-All
      - name: vNIC 1
          type: VNET
          network: PXE-VNET
          boot_order: 1
          mac_address: b4:d1:35:00:00:01

- name: Create a VM from a custom template without virtio drivers
  tacp_instance:
      api_key: "{{ api_key }}"
      name: Custom_VM
      state: started
      datacenter: Datacenter1
      migration_zone: Zone1
      template: MyCustomTemplate
      storage_pool: Pool1
      vcpu_cores: 1
      memory: 4G
      vm_mode: Compatibility
      disks:
      - name: Disk 0
          size_gb: 50
          boot_order: 1
      nics:
      - name: vNIC 0
          type: VNET
          network: VNET-TEST
          boot_order: 2

- name: Pause Basic_VM1 on ThinkAgile CP
  tacp_instance:
      api_key: "{{ api_key }}"
      name: Basic_VM1
      state: paused

- name: Restart all of my Basic_VMs on ThinkAgile CP
  tacp_instance:
      api_key: "{{ api_key }}"
      name: "{{ instance }}"
      state: restarted
  loop:
    - Basic_VM1
    - Basic_VM2
    - Basic_VM3
  loop_control:
    loop_var: instance

- name: Delete Basic_VM1 from ThinkAgile CP
  tacp_instance:
      api_key: "{{ api_key }}"
      name: Basic_VM1
      state: absent

- name: Create a variety of VMs on TACP in a loop
  tacp_instance:
      api_key: "{{ api_key }}"
      name: "{{ instance.name }}"
      state: "{{ instance.state }}"
      datacenter: Datacenter2
      migration_zone: Zone2
      template: "{{ instance.template }}"
      storage_pool: Pool2
      vcpu_cores: "{{ instance.vcpu_cores }}"
      memory: "{{ instance.memory }}"
      disks:
        - name: Disk 0
          size_gb: 100
          boot_order: 1
      nics:
        - name: vNIC 0
          type: "{{ instance.network_type }}"
          network: "{{ instance.network_name }}"
          mac_address: "{{ instance.mac_address }}"
          boot_order: 2
  loop:
      - { name: CentOS VM 1,
          state: started,
          template: "CentOS 7.5 (64-bit) - Lenovo Template",
          vcpu_cores: 2,
          memory: 4096MB,
          network_type: VLAN,
          network_name: VLAN-15,
          mac_address: b4:d1:35:00:0f:f0 }
      - { name: RHEL VM 11,
          state: stopped,
          template: "RHEL 7.4 (Minimal) - Lenovo Template",
          vcpu_cores: 6,
          memory: 6g,
          network_type: VNET,
          network_name: Production-VNET,
          mac_address: b4:d1:35:00:0f:f1 }
      - { name: Windows Server 2019 VM 1,
          state: started,
          template: "Windows Server 2019 Standard - Lenovo Template",
          vcpu_cores: 8,
          memory: 16GB,
          network_type: VNET,
          network_name: Internal-VNET,
          mac_address: b4:d1:35:00:0f:f2 }
  loop_control:
      loop_var: instance
'''

RETURN = '''
instance:
    description: The final state of the application instance if it still exists.
    type: dict
    returned: success

msg:
    description: An error message in the event of invalid input or other
        unexpected behavior during module execution.
    type: str
    returned: failure
'''


STATE_ACTIONS = [Action.STARTED, Action.SHUTDOWN, Action.STOPPED,
                 Action.RESTARTED, Action.FORCE_RESTARTED, Action.PAUSED,
                 Action.ABSENT]


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        api_key=dict(type='str', required=True),
        portal_url=dict(type='str', required=False,
                        default="https://manage.cp.lenovo.com"),
        name=dict(type='str', required=True),
        state=dict(type='str', required=True,
                   choices=STATE_ACTIONS),
        datacenter=dict(type='str', required=False),
        migration_zone=dict(type='str', required=False),
        storage_pool=dict(type='str', required=False),
        template=dict(type='str', required=False),
        vcpu_cores=dict(type='int', required=False),
        memory=dict(type='str', required=False),
        disks=dict(type='list', required=False),
        nics=dict(type='list', required=False),
        vtx_enabled=dict(type='bool', default=True, required=False),
        auto_recovery_enabled=dict(type='bool', default=True, required=False),
        description=dict(type='str', required=False),
        vm_mode=dict(type='str', default='Enhanced', choices=['enhanced', 'Enhanced',
                                                              'compatibility', 'Compatibility']),
        application_group={
            'type': 'str',
            'required': False,
        },

    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        args=[]
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    def fail_with_reason(reason):
        result['msg'] = reason
        module.fail_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    def generate_instance_params(module):
        # VM does not exist yet, so we must create it
        instance_params = {}
        instance_params['instance_name'] = module.params['name']

        components = ['storage_pool', 'datacenter', 'migration_zone']
        for component in components:
            component_uuid = tacp_utils.get_component_fields_by_name(
                module.params[component], component, api_client)
            if not component_uuid:
                reason = "%s %s does not exist, cannot continue." % component.capitalize(
                ) % module.params[component]
                fail_with_reason(reason)
            instance_params['{}_uuid'.format(component)] = component_uuid

        # Check if template exists, it must in order to continue
        template_uuid = tacp_utils.get_component_fields_by_name(
            module.params['template'], 'template', api_client)
        if template_uuid:
            instance_params['template_uuid'] = template_uuid
            boot_order = tacp_utils.get_component_fields_by_name(
                module.params['template'], 'template', api_client, fields=['name', 'uuid', 'bootOrder'])
        else:
            # Template does not exist - must fail the task
            reason = "Template %s does not exist, cannot continue." % module.params[
                'template']
            fail_with_reason(reason)

        network_payloads = []
        vnic_payloads = []
        for i, nic in enumerate(module.params['nics']):
            network_uuid = tacp_utils.get_component_fields_by_name(
                nic['network'], nic['type'].lower(), api_client)

            mac_address = nic.get('mac_address')
            automatic_mac_address = not bool(mac_address)

            firewall_override_uuid = None
            if 'firewall_override' in nic:
                firewall_override_uuid = tacp_utils.get_component_fields_by_name(
                    nic['firewall_override'], 'firewall_override', api_client)

            if i == 0:
                for boot_order_item in boot_order:
                    if boot_order_item.vnic_uuid:
                        vnic_uuid = boot_order_item.vnic_uuid
                        vnic_name = boot_order_item.name

            else:
                vnic_uuid = str(uuid4())
                vnic_boot_order = len(boot_order) + i

                vnic_payload = tacp.ApiAddVnicPayload(
                    automatic_mac_address=automatic_mac_address,
                    name=vnic_name,
                    firewall_override_uuid=firewall_override_uuid,
                    network_uuid=network_uuid,
                    boot_order=vnic_boot_order,
                    mac_address=mac_address
                )
                vnic_payloads.append(vnic_payload)

            network_payload = tacp.ApiCreateOrEditApplicationNetworkOptionsPayload(
                name=vnic_name,
                automatic_mac_assignment=automatic_mac_address,
                firewall_override_uuid=firewall_override_uuid,
                network_uuid=network_uuid,
                vnic_uuid=vnic_uuid,
                mac_address=mac_address
            )
            network_payloads.append(network_payload)

        instance_params['boot_order'] = boot_order
        instance_params['networks'] = network_payloads
        instance_params['vnics'] = vnic_payloads
        instance_params['vcpus'] = module.params['vcpu_cores']
        instance_params['memory'] = tacp_utils.convert_memory_abbreviation_to_bytes(
            module.params['memory'])
        instance_params['vm_mode'] = module.params['vm_mode'].capitalize()
        instance_params['vtx_enabled'] = module.params['vtx_enabled']
        instance_params['auto_recovery_enabled'] = module.params['auto_recovery_enabled']
        instance_params['description'] = module.params['description']

        if module.params['application_group']:
            ag_resource = tacp_utils.ApplicationGroupResource(api_client)
            uuid = ag_resource.get_uuid_by_name(
                module.params['application_group']
            )
            if uuid is None:
                resp = ag_resource.create(module.params['application_group'],
                                          instance_params['datacenter_uuid'])
                uuid = resp.object_uuid

            instance_params['application_group_uuid'] = uuid

        return instance_params

    def create_instance(instance_params, api_client):
        application_resource = tacp_utils.ApplicationResource(api_client)

        body = tacp.ApiCreateApplicationPayload(
            name=instance_params['instance_name'],
            datacenter_uuid=instance_params['datacenter_uuid'],
            flash_pool_uuid=instance_params['storage_pool_uuid'],
            migration_zone_uuid=instance_params['migration_zone_uuid'],
            template_uuid=instance_params['template_uuid'],
            vcpus=instance_params['vcpus'],
            memory=instance_params['memory'],
            vm_mode=instance_params['vm_mode'],
            networks=instance_params['networks'],
            vnics=instance_params['vnics'],
            boot_order=instance_params['boot_order'],
            hardware_assisted_virtualization_enabled=instance_params['vtx_enabled'],
            enable_automatic_recovery=instance_params['auto_recovery_enabled'],
            description=instance_params['description'],
            application_group_uuid=instance_params.get(
                'application_group_uuid')
        )

        if module._verbosity >= 3:
            result['api_request_body'] = str(body)

        response = application_resource.create(body)

        result['ansible_module_results'] = application_resource.get_by_uuid(
            response.object_uuid
        ).to_dict()
        result['changed'] = True

    def instance_power_action(name, api_client, action):
        assert action in STATE_ACTIONS + [Action.RESUMED]

        application_resource = tacp_utils.ApplicationResource(api_client)

        instance_uuid = application_resource.get_uuid_by_name(name)

        application_resource.power_action_on_instance_by_uuid(
            instance_uuid, action
        )

        result['changed'] = True

    # Current state is first dimension
    # Specified state is second dimension
    power_state_dict = {
        (State.RUNNING, Action.STARTED): [],
        (State.RUNNING, Action.SHUTDOWN): [Action.SHUTDOWN],
        (State.RUNNING, Action.STOPPED): [Action.STOPPED],
        (State.RUNNING, Action.RESTARTED): [Action.RESTARTED],
        (State.RUNNING, Action.FORCE_RESTARTED): [Action.FORCE_RESTARTED],
        (State.RUNNING, Action.PAUSED): [Action.PAUSED],
        (State.RUNNING, Action.ABSENT): [Action.ABSENT],
        (State.SHUTDOWN, Action.STARTED): [Action.STARTED],
        (State.SHUTDOWN, Action.SHUTDOWN): [],
        (State.SHUTDOWN, Action.STOPPED): [],
        (State.SHUTDOWN, Action.RESTARTED): [Action.STARTED],
        (State.SHUTDOWN, Action.FORCE_RESTARTED): [Action.STARTED],
        (State.SHUTDOWN, Action.PAUSED): [Action.STARTED, Action.PAUSED],
        (State.SHUTDOWN, Action.ABSENT): [Action.ABSENT],
        (State.PAUSED, Action.STARTED): [Action.RESUMED],
        (State.PAUSED, Action.SHUTDOWN): [Action.RESUMED, Action.SHUTDOWN],
        (State.PAUSED, Action.STOPPED): [Action.STOPPED],
        (State.PAUSED, Action.RESTARTED): [Action.RESUMED, Action.RESTARTED],
        (State.PAUSED, Action.FORCE_RESTARTED): [Action.RESUMED, Action.FORCE_RESTARTED],
        (State.PAUSED, Action.PAUSED): [],
        (State.PAUSED, Action.ABSENT): [Action.ABSENT]
    }

    # Return the inputs for debugging purposes
    result['args'] = module.params

    # Define configuration
    configuration = tacp_utils.get_configuration(module.params['api_key'],
                                                 module.params['portal_url'])
    api_client = tacp.ApiClient(configuration)

    application_resource = tacp_utils.ApplicationResource(api_client)
    instance_uuid = application_resource.get_uuid_by_name(
        module.params['name'])

    desired_state = module.params['state']

    if instance_uuid:
        instance_properties = application_resource.get_by_uuid(
            instance_uuid).to_dict()
        current_state = instance_properties['status']
    else:
        if module.params['state'] == 'absent':
            instance_power_action(
                module.params['name'], api_client, Action.ABSENT)
        else:
            # Application does not exist yet, so create it
            instance_params = generate_instance_params(module)
            create_instance(instance_params, api_client)
            current_state = State.SHUTDOWN

    if current_state in [State.RUNNING, State.SHUTDOWN, State.PAUSED]:
        for power_action in power_state_dict[(current_state, desired_state)]:
            instance_power_action(
                module.params['name'], api_client, power_action)

    # AnsibleModule.fail_json() to pass in the message and the result

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
