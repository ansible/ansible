#!/usr/bin/python

# Copyright: (c) 2020, Lenovo
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
from pprint import pprint
from uuid import uuid4

import tacp
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.tacp_ansible import tacp_utils
from ansible.module_utils.tacp_ansible.tacp_constants import Action, State
from ansible.module_utils.tacp_ansible.tacp_exceptions import (
<<<<<<< HEAD
    ActionTimedOutException, InvalidActionUuidException
)
from ansible.module_utils.tacp_ansible.tacp_constants import State, Action


import json
import tacp
<<<<<<< HEAD
import sys
from time import sleep
=======

>>>>>>> f84617e268... OL-9822  Remove sys import and stdout.write debug lines
from uuid import uuid4
=======
    ActionTimedOutException, InvalidActionUuidException)
>>>>>>> 0648ccf6c0... OL-9822 Do some major refactoring - don't push this yet
from tacp.rest import ApiException

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: tacp_instance

short_description: This is my test module

version_added: '2.9'

description:
    - 'This is my longer description explaining my test module'

options:
    name:
        description:
            - This is the message to send to the test module
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false

extends_documentation_fragment:
    - tacp

author:
    - Xander Madsen (@xmadsen)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  tacp_instance:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  tacp_instance:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  tacp_instance:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
    returned: always
message:
    description: The output message that the test module generates
    type: str
    returned: always
'''


STATE_ACTIONS = [Action.STARTED, Action.SHUTDOWN, Action.STOPPED,
                 Action.RESTARTED, Action.FORCE_RESTARTED, Action.PAUSED,
                 Action.ABSENT]

STATE_CHANGE_ACTIONS = {
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
    (State.PAUSED, Action.FORCE_RESTARTED):
        [Action.RESUMED, Action.FORCE_RESTARTED],
    (State.PAUSED, Action.PAUSED): [],
    (State.PAUSED, Action.ABSENT): [Action.ABSENT]
}

MODULE_ARGS = {
    'api_key': {'type': 'str', 'required': True},
    'portal_url': {'type': 'str', 'required': False,
                   'default': 'https://manage.cp.lenovo.com'},
    'name': {'type': 'str', 'required': True},
    'state': {'type': 'str', 'required': True,
              'choices': STATE_ACTIONS},
    'datacenter': {'type': 'str', 'required': False},
    'migration_zone': {'type': 'str', 'required': False},
    'storage_pool': {'type': 'str', 'required': False},
    'template': {'type': 'str', 'required': False},
    'vcpu_cores': {'type': 'int', 'required': False},
    'memory': {'type': 'str', 'required': False},
    'disks': {'type': 'list', 'required': False},
    'nics': {'type': 'list', 'required': False},
    'boot_order': {'type': 'list', 'required': False},
    'vtx_enabled': {'type': 'bool', 'default': True, 'required': False},
    'auto_recovery_enabled': {'type': 'bool', 'default': True,
                              'required': False},
    'description': {'type': 'str', 'required': False},
    'vm_mode': {'type': 'str', 'default': 'Enhanced',
                'choices': ['enhanced', 'Enhanced',
                            'compatibility', 'Compatibility']},
    'application_group': {
        'type': 'str',
        'required': False,
    }
}

MINIMUM_BW_FIVE_MBPS_IN_BYTES = 5000000
MINIMUM_IOPS = 50

RESULT = {
    'changed': False,
    'args': []
}

MODULE = AnsibleModule(
    argument_spec=MODULE_ARGS,
    supports_check_mode=True
)

RESULT['args'] = MODULE.params

# Define configuration
CONFIGURATION = tacp_utils.get_configuration(MODULE.params['api_key'],
                                             MODULE.params['portal_url'])
API_CLIENT = tacp.ApiClient(CONFIGURATION)

RESOURCES = {
    'app': tacp_utils.ApplicationResource(API_CLIENT),
    'app_group': tacp_utils.ApplicationGroupResource(API_CLIENT),
    'datacenter': tacp_utils.DatacenterResource(API_CLIENT),
    'migration_zone': tacp_utils.MigrationZoneResource(API_CLIENT),
    'storage_pool': tacp_utils.StoragePoolResource(API_CLIENT),
    'template': tacp_utils.TemplateResource(API_CLIENT),
    'update_app': tacp_utils.UpdateApplicationResource(API_CLIENT),
    'vlan': tacp_utils.VlanResource(API_CLIENT),
    'vnet': tacp_utils.VnetResource(API_CLIENT)
}


def fail_with_reason(reason):
    RESULT['msg'] = reason
    MODULE.fail_json(**RESULT)


def instance_power_action(instance_uuid, action):
    RESOURCES['app'].power_action_on_instance_by_uuid(
        instance_uuid, action
    )
    RESULT['changed'] = True


def get_firewall_override_uuid(datacenter_uuid, firewall_override_name):
    """Get the UUID for a firewall override for the provided datacenter.

    Args:
        datacenter_uuid (str): The UUID of the datacenter that the firewall override is a part of.
        firewall_override_name (str): The name of the firewall override.

    Returns:
        str: The UUID of the firewall override.
    """
    datacenter_api = tacp.DatacentersApi(API_CLIENT)
    firewall_overrides = datacenter_api.get_datacenter_firewall_overrides_using_get(  # noqa
        uuid=datacenter_uuid, filters='name=="{}"'.format(  # noqa
            firewall_override_name))
    if firewall_overrides:
        firewall_override_uuid = firewall_overrides[0].uuid
    else:
        fail_with_reason('An invalid firewall override name was specified: {}'.format(  # noqa
            firewall_override_name))
    return firewall_override_uuid


def create_vnic_payload(instance, playbook_vnic):
    """Creates an ApiAddVnicPayload that can be used to add a vNIC to a new
        instance, or used as a basis to create an
        ApiCreateOrEditApplicationNetworkOptionsPayload.

    Args:
        instance (ApiApplicationInstancePropertiesPayload): The application
            instance that the new vNIC will be added to.
        playbook_vnic (dict): The vNIC entry as specified in the Ansible
            playbook.

    Returns:
        ApiAddVnicPayload: The payload that can be used in the 'vnics' field
            when creating an ApiCreateApplicationPayload.
    """

    name = playbook_vnic.get('name')
    if not name:
        fail_with_reason(
            'Failed to create vNIC payload; vNICs must have a name provided.')  # noqa

    mac_address = playbook_vnic.get('mac_address')
    automatic_mac_address = not bool(mac_address)

    network_type = playbook_vnic.get('type')
    if not network_type:
        fail_with_reason(
            'Failed to create vNIC payload; vNICs must have a type provided: VNET or VLAN.')  # noqa

    network_resource = RESOURCES[network_type.lower()]

    networks = network_resource.filter(name=playbook_vnic['network'])
    if not networks:
        fail_with_reason(
            'Failed to create vNIC payload; an invalid network name was provided for vNIC {}'.format(
                playbook_vnic['network']))
    network_uuid = networks[0].uuid

    firewall_override_uuid = playbook_vnic.get(['firewall_override'])
    if not firewall_override_uuid:
        fail_with_reason(
            'Failed to create vNIC payload; an invalid firewall override name was provided for vNIC {}'.format(
                playbook_vnic['network']))
    firewall_override_uuid = get_firewall_override_uuid(
        instance.datacenter_uuid,
        playbook_vnic['firewall_override'])

    vnic_payload = tacp.ApiAddVnicPayload(
        automatic_mac_assignment=automatic_mac_address,
        firewall_override_uuid=firewall_override_uuid,
        mac_address=mac_address,
        name=name,
        network_uuid=network_uuid)
    return vnic_payload


def create_network_payload(vnic_payload):
    """Create an API Network payload based on a provided ApiAddVnicPayload payload

    Args:
        vnic (ApiAddVnicPayload): A payload for adding a vNIC to a new application instance.

    Returns:
        ApiCreateOrEditApplicationNetworkOptionsPayload: 

    """

    network_payload = tacp.ApiCreateOrEditApplicationNetworkOptionsPayload(  # noqa
        automatic_mac_assignment=vnic_payload.automatic_mac_address,
        firewall_override_uuid=vnic_payload.firewall_override_uuid,
        mac_address=vnic_payload.mac_address,
        name=vnic_payload.name,
        network_uuid=vnic_payload.network_uuid,
        vnic_uuid=str(uuid4())
    )

    return network_payload


<<<<<<< HEAD
        network_payloads = []
        vnic_payloads = []
        vlan_resource = tacp_utils.VlanResource(api_client)
        vnet_resource = tacp_utils.VnetResource(api_client)
        for nic in module.params['nics']:

            vnic_uuids = [device.vnic_uuid for device in boot_order if
                          (device.vnic_uuid and
                           device.name == nic['name'])]
            if not vnic_uuids:
                # The vnic is not in the template, so move on
                continue
            vnic_uuid = vnic_uuids[0]

            if nic['type'].lower() == 'vlan':
                network_uuid = vlan_resource.filter(
                    name=("==", nic['network']))[0].uuid
            else:
                network_uuid = vnet_resource.filter(
                    name=("==", nic['network']))[0].uuid

            mac_address = nic.get('mac_address')
            automatic_mac_address = not bool(mac_address)
            name = nic['name']

            network_payload = tacp.ApiCreateOrEditApplicationNetworkOptionsPayload(  # noqa
                name=name,
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
        instance_params['memory'] = tacp_utils.convert_memory_abbreviation_to_bytes(  # noqa
            module.params['memory'])
        instance_params['vm_mode'] = module.params['vm_mode'].capitalize()
        instance_params['vtx_enabled'] = module.params['vtx_enabled']
        instance_params['auto_recovery_enabled'] = module.params['auto_recovery_enabled']  # noqa
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
            hardware_assisted_virtualization_enabled=instance_params['vtx_enabled'],  # noqa
            enable_automatic_recovery=instance_params['auto_recovery_enabled'],
            description=instance_params['description'],
            application_group_uuid=instance_params.get(
                'application_group_uuid')
        )
=======
def add_vnic_to_instance(network_payload):
    """Adds a vNIC to an instance if a vNIC with the same name is not already
        present in that instance.

    Args:
        network_payload (ApiCreateOrEditApplicationNetworkOptionsPayload): [description]
    """
    RESOURCES['update_app'].create_vnic(body=network_payload, uuid=instance_uuid)  # noqa


def add_disk_to_instance(instance, playbook_disk):
    """Adds a new disk to an application instance if a disk with the same name
        is not already present in that instance.

    Args:
        instance (ApiApplicationInstancePropertiesPayload): The application
            instance that the new disk will be added to.
        playbook_disk (dict): The disk entry as specified in the Ansible
            playbook.
    """
    bandwidth_limit = playbook_disk.get('bandwidth_limit')
    if bandwidth_limit:
        if int(bandwidth_limit) < MINIMUM_BW_FIVE_MBPS_IN_BYTES:
            fail_with_reason(
                'Could not add disk to instance {}; disks must have a bandwidth limit of at least 5 MBps (5000000).'.format(instance.name))  # noqa

    iops_limit = playbook_disk.get('iops_limit')
    if iops_limit:
        if int(iops_limit) < MINIMUM_IOPS:
            fail_with_reason(
                'Could not add disk to instance {}; disks must have a total IOPS limit of at least 50.'.format(instance.name))

    size_gb = playbook_disk.get('size_gb')
    if not size_gb:
        fail_with_reason(
            'Could not add disk to instance {}; disks must have a size in GB provided.'.format(instance.name))
    size_bytes = tacp_utils.convert_memory_abbreviation_to_bytes(str(disk['size_gb']) + 'GB')  # noqa

    name = playbook_disk.get('name')
    if not name:
        fail_with_reason(
            'Could not add disk to instance {}; disks must have a name provided.'.format(instance.name))

    body = tacp.ApiDiskSizeAndLimitPayload(bandwidth_limit=bandwidth_limit,  # noqa
                                            iops_limit=iops_limit,
                                            name=name,
                                            size=size_bytes,
                                            uuid=str(uuid4()))

    RESOURCES['update_app'].create_disk(body=body, uuid=instance.uuid)


def update_boot_order(instance_uuid):
    existing_boot_order = RESOURCES['app'].filter(
        uuid=('==', instance_uuid))[0].boot_order

    new_boot_order = []
    # Create ApiEditApplicationPayload to update boot order
    for device in existing_boot_order:
        name = device.name

        if device.vnic_uuid:
            vnic_uuid = device.vnic_uuid
            disk_uuid = None
            playbook_nic = [nic for nic in module.params['nics']
                            if nic['name'] == name][0]
            order = playbook_nic['boot_order']
        else:
            vnic_uuid = None
            disk_uuid = device.disk_uuid
            playbook_disk = [disk for disk in module.params['disks']
                             if disk['name'] == name][0]
            order = playbook_disk['boot_order']

        boot_order_payload = tacp.ApiBootOrderPayload(disk_uuid=disk_uuid,
                                                      name=name,
                                                      order=order,
                                                      vnic_uuid=vnic_uuid)
        new_boot_order.append(boot_order_payload)

    new_boot_order = sorted(new_boot_order, key=lambda payload: payload.order)  # noqa
    body = tacp.ApiEditApplicationPayload(boot_order=new_boot_order)

    RESOURCES['update_app'].edit_boot_order(body, instance_uuid)


def get_boot_order(module, template_dict):

    # Get boot devices uuids and order from the template
    template_boot_order = template_dict['boot_order']

    template_boot_device_names = [boot_device['name'] for
                                  boot_device in template_boot_order]

    # Make sure all disks and nics have a boot_order assigned
    if not all([bool(device.get('boot_order')) for device in
                module.params['disks'] + module.params['nics']]):
        fail_with_reason(
            'All disks and NICs must have a boot_order specified, starting with 1.')  # noqa

    playbook_devices = [dev for dev in module.params['disks']
                        + module.params['nics']]
    disks_and_nics_names = [dev['name'] for dev in playbook_devices]

    # Make sure that all template boot devices are present
    #  in disks_and_nics_names
    if not all([template_device in disks_and_nics_names for
                template_device in template_boot_device_names]):
        fail_with_reason('All devices for template {} must be present in disks and nics fields: [{}]'.format(  # noqa
            template_dict['name'], ', '.join(template_boot_device_names)))

    # initialize the boot order with blank entries times the
    # number of disks + nics
    instance_boot_order = [None] * len(disks_and_nics_names)

    # Now set the boot device into the correct order by the index provided
    for boot_device in playbook_devices:
        if boot_device['name'] in template_boot_device_names:
            order = boot_device['boot_order']
            boot_device_dict = [device for device
                                in template_boot_order
                                if boot_device['name'] == device['name']][0]  # noqa
            disk_uuid = boot_device_dict['disk_uuid']
            name = boot_device_dict['name']
            vnic_uuid = boot_device_dict['vnic_uuid']
        else:
            if boot_device in [disk['name'] for disk in module.params['disks']]:  # noqa
                disk_uuid = str(uuid4())
                vnic_uuid = None
            else:
                disk_uuid = None
                vnic_uuid = str(uuid4())
            name = boot_device['name']
            order = boot_device['boot_order']
        payload = tacp.ApiBootOrderPayload(disk_uuid=disk_uuid,
                                           name=name,
                                           order=order,
                                           vnic_uuid=vnic_uuid)
        instance_boot_order[order - 1] = payload

    return instance_boot_order


def create_new_application_instance_payload(playbook_instance):
    # VM does not exist yet, so we must create it
    instance_params = {}
    instance_params['instance_name'] = module.params['name']

    components = ['storage_pool', 'datacenter', 'migration_zone']
    for component in components:
        component_uuid = tacp_utils.get_component_fields_by_name(
            module.params[component], component, API_CLIENT)
        if not component_uuid:
            reason = '{} {} does not exist, cannot continue.'.format(
                component.capitalize(), module.params[component])
            fail_with_reason(reason)
        instance_params['{}_uuid'.format(component)] = component_uuid
>>>>>>> 0648ccf6c0... OL-9822 Do some major refactoring - don't push this yet

    # Check if template exists, it must in order to continue
    template_results = TEMPLATE_RESOURCE.filter(
        name=playbook_instance['template'])

    # There should only be one template returned if it exists
    template_dict = template_results[0].to_dict()

    template_uuid = template_dict.get('uuid')

    if template_uuid:
        instance_params['template_uuid'] = template_uuid
        template_boot_order = template_results[0].boot_order
    else:
        # Template does not exist - must fail the task
        reason = 'Template %s does not exist, cannot continue.' % module.params[  # noqa
            'template']
        fail_with_reason(reason)

    network_payloads = []
    vnic_payloads = []
    for vnic in module.params['nics']:
        if vnic['name'] in [template_boot_device.name for template_boot_device in
                            template_boot_order if template_boot_device.vnic_uuid]:
            vnic_payload =

        network_payload = create_network_payload(vnic)
        vnic_payloads.append(vnic_payload)
        network_payloads.append(network_payload)

    instance_params['boot_order'] = template_boot_order
    instance_params['networks'] = network_payloads
    instance_params['vnics'] = vnic_payloads
    instance_params['vcpus'] = module.params['vcpu_cores']
    instance_params['memory'] = tacp_utils.convert_memory_abbreviation_to_bytes(  # noqa
        module.params['memory'])
    instance_params['vm_mode'] = module.params['vm_mode'].capitalize()
    instance_params['vtx_enabled'] = module.params['vtx_enabled']
    instance_params['auto_recovery_enabled'] = module.params['auto_recovery_enabled']  # noqa
    instance_params['description'] = module.params['description']

    if module.params['application_group']:

        uuid = AG_RESOURCE.get_uuid_by_name(
            module.params['application_group']
        )
        if uuid is None:
            resp = AG_RESOURCE.create(module.params['application_group'],
                                      instance_params['datacenter_uuid'])
            uuid = resp.object_uuid

        instance_params['application_group_uuid'] = uuid

    return instance_params

    create_instance_payload = tacp.ApiCreateApplicationPayload(
        name=create_application_parameters.get('instance_name'),
        datacenter_uuid=create_application_parameters.get('datacenter_uuid'),
        flash_pool_uuid=create_application_parameters.get('storage_pool_uuid'),
        migration_zone_uuid=create_application_parameters.get(
            'migration_zone_uuid'),
        template_uuid=create_application_parameters.get('template_uuid'),
        vcpus=create_application_parameters.get('vcpus'),
        memory=create_application_parameters.get('memory'),
        vm_mode=create_application_parameters.get('vm_mode'),
        networks=create_application_parameters.get('networks'),
        vnics=create_application_parameters.get('vnics'),
        boot_order=create_application_parameters.get('boot_order'),
        hardware_assisted_virtualization_enabled=create_application_parameters.get('vtx_enabled'),  # noqa
        enable_automatic_recovery=create_application_parameters.get(
            'auto_recovery_enabled'),
        description=create_application_parameters.get('description'),
        application_group_uuid=create_application_parameters.get(
            'application_group_uuid')
    )

    return create_instance_payload


def create_instance(create_instance_payload):
    response = RESOURCES['app'].create(create_instance_payload)

    return response


def run_module():
    # define available arguments/parameters a user can pass to the module
    if MODULE.check_mode:
        MODULE.exit_json(**RESULT)

    def add_vnics_and_disks_and_update_boot_order(instance_uuid, boot_order):  # noqa

        # We need this to be the tacp version of DatacenterResource
        # so we can easily fetch firewall overrides

        instance = RESOURCES['app'].filter(uuid=('==', instance_uuid))[0]

        add_disk_to_instance(boot_order, disk, instance_uuid)  # noqa

        update_boot_order(instance_uuid)

    # Current state is first dimension
    # Specified state is second dimension

    # Return the inputs for debugging purposes

    application_resource = tacp_utils.ApplicationResource(API_CLIENT)
    instance_uuid = application_resource.get_uuid_by_name(
        MODULE.params['name'])

    desired_state = MODULE.params['state']

    if instance_uuid:
        instance_properties = application_resource.get_by_uuid(
            instance_uuid).to_dict()
        current_state = instance_properties['status']
    else:
        if MODULE.params['state'] == 'absent':
            instance_power_action(
                MODULE.params['name'], API_CLIENT, Action.ABSENT)
        else:
            # Application does not exist yet, so create it
            instance_params = generate_instance_params(MODULE)

            # Create instance with disks + vnics from the template ONLY
            created_instance_uuid = create_instance(
                instance_params, API_CLIENT).object_uuid
            current_state = State.SHUTDOWN

            # Add vnics + disks from playbook specification
            # and modify boot order to match
            template_results = TEMPLATE_RESOURCE.filter(
                name=MODULE.params['template'])

            if template_results:
                template_dict = template_results[0].to_dict()
            else:
                fail_with_reason('Template {} is not present.'.format(
                    MODULE.params['template']))

            boot_order = get_boot_order(MODULE, template_dict)

            if len(boot_order) > len(template_dict['boot_order']):
                add_vnics_and_disks_and_update_boot_order(MODULE,
                                                          created_instance_uuid, boot_order)  # noqa

    if current_state in [State.RUNNING, State.SHUTDOWN, State.PAUSED]:
        for power_action in STATE_CHANGE_ACTIONS[(current_state, desired_state)]:
            instance_power_action(
                MODULE.params['name'], API_CLIENT, power_action)

    MODULE.exit_json(**RESULT)


def main():
    run_module()


if __name__ == '__main__':
    main()
