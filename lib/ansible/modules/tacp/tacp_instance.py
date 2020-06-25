#!/usr/bin/python

# Copyright: (c) 2020, Lenovo
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.tacp_ansible.tacp_constants import (
    PlaybookState, ApiState)
from ansible.module_utils.tacp_ansible import tacp_exceptions
from ansible.module_utils.tacp_ansible import tacp_utils

import tacp
from tacp.rest import ApiException
from uuid import uuid4

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


'''
This dict keys are a tuple of the format (current_state, target_state)
where the current state has been retrieved from an API response
and the target_state is provided by the playbook input. The values
are a list of PlaybookStates that when set in order will get an
instance from the current state to the target state.
'''
ACTIONS_TO_CHANGE_FROM_API_STATE_TO_PLAYBOOK_STATE = {
    (ApiState.RUNNING, PlaybookState.STARTED): [],
    (ApiState.RUNNING, PlaybookState.SHUTDOWN): [PlaybookState.SHUTDOWN],
    (ApiState.RUNNING, PlaybookState.STOPPED): [PlaybookState.STOPPED],
    (ApiState.RUNNING, PlaybookState.RESTARTED): [PlaybookState.RESTARTED],
    (ApiState.RUNNING, PlaybookState.FORCE_RESTARTED): [
        PlaybookState.FORCE_RESTARTED],
    (ApiState.RUNNING, PlaybookState.PAUSED): [PlaybookState.PAUSED],
    (ApiState.RUNNING, PlaybookState.ABSENT): [PlaybookState.ABSENT],
    (ApiState.SHUTDOWN, PlaybookState.STARTED): [PlaybookState.STARTED],
    (ApiState.SHUTDOWN, PlaybookState.SHUTDOWN): [],
    (ApiState.SHUTDOWN, PlaybookState.STOPPED): [],
    (ApiState.SHUTDOWN, PlaybookState.RESTARTED): [PlaybookState.STARTED],
    (ApiState.SHUTDOWN, PlaybookState.FORCE_RESTARTED): [
        PlaybookState.STARTED],
    (ApiState.SHUTDOWN, PlaybookState.PAUSED): [
        PlaybookState.STARTED, PlaybookState.PAUSED],
    (ApiState.SHUTDOWN, PlaybookState.ABSENT): [PlaybookState.ABSENT],
    (ApiState.PAUSED, PlaybookState.STARTED): [PlaybookState.RESUMED],
    (ApiState.PAUSED, PlaybookState.SHUTDOWN): [
        PlaybookState.RESUMED, PlaybookState.SHUTDOWN],
    (ApiState.PAUSED, PlaybookState.STOPPED): [PlaybookState.STOPPED],
    (ApiState.PAUSED, PlaybookState.RESTARTED): [
        PlaybookState.RESUMED, PlaybookState.RESTARTED],
    (ApiState.PAUSED, PlaybookState.FORCE_RESTARTED):
        [PlaybookState.RESUMED, PlaybookState.FORCE_RESTARTED],
    (ApiState.PAUSED, PlaybookState.PAUSED): [],
    (ApiState.PAUSED, PlaybookState.ABSENT): [PlaybookState.ABSENT]
}

MODULE_ARGS = {
    'api_key': {'type': 'str', 'required': True},
    'portal_url': {'type': 'str', 'required': False,
                   'default': 'https://manage.cp.lenovo.com'},
    'name': {'type': 'str', 'required': True},
    'state': {'type': 'str', 'required': True,
              'choices': PlaybookState._all()},
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
    'update_app': tacp_utils.ApplicationUpdateResource(API_CLIENT),
    'vlan': tacp_utils.VlanResource(API_CLIENT),
    'vnet': tacp_utils.VnetResource(API_CLIENT)
}


def fail_with_reason(reason):
    RESULT['msg'] = reason
    MODULE.fail_json(**RESULT)


def fail_and_rollback_instance_creation(reason, instance):
    RESULT['msg'] = reason + "\n Rolled back application instance creation."
    RESOURCES['app'].delete(instance.uuid)
    MODULE.fail_json()


def get_parameters_to_create_new_application(playbook_instance):
    """Given the input configuration for an instance, generate
        parameters for creating the appropriate payload elsewhere.

    Args:
        playbook_instance (dict): The specified instance configuration from
        the playbook input

    Returns:
        dict: The parameters to be provided to an ApiCreateApplicationPayload
            object.
    """
    data = {'instance_name': None,
            'datacenter_uuid': None,
            'migration_zone_uuid': None,
            'storage_pool_uuid': None,
            'template': None,
            'boot_order': None,
            'application_group_uuid': None,
            'networks': None,
            'vcpus': None,
            'memory': None,
            'vm_mode': None,
            'vtx_enabled': None,
            'auto_recovery_enabled': None,
            'description': None
            }

    data['instance_name'] = playbook_instance['name']

    for item in ('datacenter', 'migration_zone', 'storage_pool', 'template'):
        resource_uuid = RESOURCES[item].get_by_name(
            playbook_instance[item]).uuid

        data['{}_uuid'.format(item)] = resource_uuid

        if item != 'template':
            continue

        template = RESOURCES[item].get_by_uuid(resource_uuid)
        template_boot_order = template.boot_order
        data['boot_order'] = template_boot_order

    if playbook_instance['application_group']:
        uuid = RESOURCES['app_group'].get_uuid_by_name(
            playbook_instance['application_group']
        )
        if uuid is None:
            resp = RESOURCES['app_group'].create(
                playbook_instance['application_group'],
                data['datacenter_uuid']
            )
            uuid = resp.object_uuid

        data['application_group_uuid'] = uuid

    network_payloads = []
    template_vnics = [boot_device for boot_device
                      in template_boot_order if boot_device.vnic_uuid]

    playbook_vnics_in_template = {
        playbook_vnic['name']: template_vnic
        for playbook_vnic in playbook_instance['nics']
        for template_vnic in template_vnics
        if template_vnic.name == playbook_vnic['name']
    }
    corresponding_playbook_vnics = [
        vnic for vnic in playbook_instance['nics']
        if vnic['name'] in playbook_vnics_in_template
    ]

    for playbook_vnic in corresponding_playbook_vnics:
        template_vnic = playbook_vnics_in_template[playbook_vnic['name']]
        vnic_uuid = template_vnic.vnic_uuid
        template_order = template_vnic.order

        parameters_to_create_new_vnic = get_parameters_to_create_vnic(
            datacenter_uuid=data['datacenter_uuid'],  # noqa
            playbook_vnic=playbook_vnic,
            template_order=template_order
        )

        add_vnic_payload = get_add_vnic_payload(parameters_to_create_new_vnic)
        add_network_payload = get_add_network_payload(
            add_vnic_payload, vnic_uuid)
        network_payloads.append(add_network_payload)

    data['networks'] = network_payloads
    data['vcpus'] = playbook_instance['vcpu_cores']
    data['memory'] = tacp_utils.convert_memory_abbreviation_to_bytes(
        playbook_instance['memory'])
    data['vm_mode'] = playbook_instance.get('vm_mode').capitalize()
    data['vtx_enabled'] = playbook_instance.get('vtx_enabled')
    data['auto_recovery_enabled'] = playbook_instance.get(
        'auto_recovery_enabled')
    data['description'] = playbook_instance.get('description')

    return data


def get_instance_payload(parameters_to_create_new_application):
    """Create a ApiCreateApplicationPayload with the input parameters.

    Args:
        parameters_to_create_new_application (dict): All the parameters
            necessary to populate an ApiCreateApplicationPayload.

    Returns:
        ApiCreateApplicationPayload: A populated payload for creating
            a new application instance.
    """
    data = tacp.ApiCreateApplicationPayload(
        name=parameters_to_create_new_application.get('instance_name'),
        datacenter_uuid=parameters_to_create_new_application.get(
            'datacenter_uuid'),
        flash_pool_uuid=parameters_to_create_new_application.get(
            'storage_pool_uuid'),
        migration_zone_uuid=parameters_to_create_new_application.get(
            'migration_zone_uuid'),
        template_uuid=parameters_to_create_new_application.get(
            'template_uuid'),
        vcpus=parameters_to_create_new_application.get('vcpus'),
        memory=parameters_to_create_new_application.get('memory'),
        vm_mode=parameters_to_create_new_application.get('vm_mode'),
        networks=parameters_to_create_new_application.get('networks'),
        boot_order=parameters_to_create_new_application.get('boot_order'),
        hardware_assisted_virtualization_enabled=parameters_to_create_new_application.get('vtx_enabled'),  # noqa
        enable_automatic_recovery=parameters_to_create_new_application.get(
            'auto_recovery_enabled'),
        description=parameters_to_create_new_application.get('description'),
        application_group_uuid=parameters_to_create_new_application.get(
            'application_group_uuid')
    )

    return data


def create_instance(playbook_instance):
    """Create an application instance and return the API response object.

    Args:
        playbook_instance (dict): The specified instance configuration from
        the playbook input

    Returns:
        ApiResponsePayload: The response from the create application request.
    """
    parameters_to_create_new_application = get_parameters_to_create_new_application(  # noqa
        playbook_instance)
    create_instance_payload = get_instance_payload(
        parameters_to_create_new_application)

    created_instance_response = RESOURCES['app'].create(
        create_instance_payload)

    return created_instance_response


def instance_power_action(instance, action):
    RESOURCES['app'].power_action_on_instance_by_uuid(
        instance.uuid, action
    )
    RESULT['changed'] = True


def update_instance_state(instance, current_state, target_state):
    if current_state in [ApiState.RUNNING,
                         ApiState.SHUTDOWN,
                         ApiState.PAUSED]:
        for action in ACTIONS_TO_CHANGE_FROM_API_STATE_TO_PLAYBOOK_STATE[
                (current_state, target_state)]:
            instance_power_action(instance, action)
        RESULT['changed'] = True


def add_playbook_vnics(playbook_vnics, instance):
    """Given a list of vnics as dicts, add them to the given instance if they
        are not already part of the instance template, since they would
        necessarily already be part of the instance at creation time.

    Args:
        playbook_vnics (list): The vNICs from the playbook to be added.
        instance (ApiApplicationInstancePropertiesPayload): A payload
            containing the properties of the instance
    """
    playbook_template = RESOURCES['template'].get_by_uuid(
        instance.template_uuid)
    template_boot_order = playbook_template.boot_order

    template_vnics = [
        device.name for device in template_boot_order if device.vnic_uuid]

    for playbook_vnic in playbook_vnics:
        if playbook_vnic['name'] not in template_vnics:
            add_vnic_to_instance(playbook_vnic, instance)


def add_vnic_to_instance(playbook_vnic, instance):
    """Adds a vNIC to an instance if a vNIC with the same name is not already
        present in that instance.

    Args:
        playbook_vnic (dict): The vNIC configuration as given by the Ansible
            playbook.
        instance (ApiApplicationInstancePropertiesPayload): A payload
            containing the properties of the instance
    """
    datacenter_uuid = instance.datacenter_uuid

    failure_reason = None
    try:
        parameters_to_create_vnic = get_parameters_to_create_vnic(
            datacenter_uuid,
            playbook_vnic)
    except Exception as e:
        fail_and_rollback_instance_creation(str(e), instance)

    vnic_payload = get_add_vnic_payload(parameters_to_create_vnic)
    vnic_uuid = str(uuid4())
    network_payload = get_add_network_payload(vnic_payload, vnic_uuid)
    RESOURCES['update_app'].create_vnic(body=network_payload, uuid=instance.uuid)  # noqa


def get_parameters_to_create_vnic(datacenter_uuid, playbook_vnic,
                                  template_order=None):
    """Generates a dict of the parameters necessary to create an
        ApiAddVnicPayload.

    Args:
        datacenter_uuid (str): UUID of the vNIC's instance's datacenter
        playbook_vnic (dict): Configuration of vNIC from Ansible playbook.
        template_order (int, optional): The boot order number from the template
            if applicable. Defaults to None.

    Raises:
        tacp_exceptions.InvalidVnicNameException
        tacp_exceptions.InvalidNetworkTypeException
        tacp_exceptions.InvalidNetworkNameException
        tacp_exceptions.InvalidFirewallOverrideNameException

    Returns:
        dict: The parameters necessary to create an ApiAddVnicPayload.
    """
    data = {
        'name': None,
        'mac_address': None,
        'automatic_mac_address': None,
        'network_type': None,
        'network_uuid': None,
        'firewall_override_uuid': None,
        'boot_order': None
    }

    data['name'] = playbook_vnic.get('name')

    data['mac_address'] = playbook_vnic.get('mac_address')

    data['automatic_mac_address'] = not bool(
        playbook_vnic.get('mac_address'))

    network_type = playbook_vnic.get('type').lower()
    if network_type not in ['vnet', 'vlan']:
        raise tacp_exceptions.InvalidNetworkTypeException(
            'Failed to create vNIC payload; vNICs must have a type of "VNET" or "VLAN"'  # noqa
        )

    network_resource = RESOURCES[network_type]

    network = network_resource.get_by_name(playbook_vnic['network'])
    if not network:
        raise tacp_exceptions.InvalidNetworkNameException(
            'Failed to create vNIC payload; an invalid network name was provided.'  # noqa
    )

    data['network_uuid'] = network.uuid

    if 'firewall_override' in playbook_vnic:
        firewall_override = RESOURCES['datacenter'].get_firewall_override_by_name(  # noqa
            datacenter_uuid, playbook_vnic['firewall_override']
        )
        data['firewall_override_uuid'] = firewall_override.uuid

    data['boot_order'] = template_order

    return data


def get_add_vnic_payload(vnic_parameters):
    """Creates an ApiAddVnicPayload that can be used to add a vNIC to a new
        instance, or used as a basis to create an
        ApiCreateOrEditApplicationNetworkOptionsPayload.

    Args:
        vnic_parameters (dict): The parameters necessary to create an
        ApiAddVnicPayload.

    Returns:
        ApiAddVnicPayload: The payload that can be used in the 'vnics' field
            when creating an ApiCreateApplicationPayload.
    """

    vnic_payload = tacp.ApiAddVnicPayload(
        boot_order=vnic_parameters['boot_order'],
        automatic_mac_address=vnic_parameters['automatic_mac_address'],  # noqa
        firewall_override_uuid=vnic_parameters['firewall_override_uuid'],  # noqa
        mac_address=vnic_parameters['mac_address'],
        name=vnic_parameters['name'],
        network_uuid=vnic_parameters['network_uuid'])

    return vnic_payload


def get_add_network_payload(vnic_payload, vnic_uuid):
    """Create an API Network payload based on a provided ApiAddVnicPayload
        payload and UUID.

    Args:
        vnic_payload (ApiAddVnicPayload): A payload for adding a vNIC to a new
            application instance.

        vnic_uuid (str): The UUID of the corresponding vNIC

    Returns:
        ApiCreateOrEditApplicationNetworkOptionsPayload: The object provided
            to actually run the create vNIC operation.

    """

    network_payload = tacp.ApiCreateOrEditApplicationNetworkOptionsPayload(  # noqa
        automatic_mac_assignment=vnic_payload.automatic_mac_address,
        firewall_override_uuid=vnic_payload.firewall_override_uuid,
        mac_address=vnic_payload.mac_address,
        name=vnic_payload.name,
        network_uuid=vnic_payload.network_uuid,
        vnic_uuid=vnic_uuid
    )

    return network_payload


def add_playbook_disks(playbook_disks, instance):
    """Given a list of disks from the Ansible playbook, add them to the
        specified instance.

    Args:
        playbook_disks (list): The list of dicts of disk configurations
            specified in the Ansible playbook.
        instance (ApiApplicationInstancePropertiesPayload): A payload
            containing the properties of the instance
    """
    playbook_template = RESOURCES['template'].get_by_uuid(
        instance.template_uuid)
    template_boot_order = playbook_template.boot_order

    template_disks = [
        device.name for device in template_boot_order if device.disk_uuid]

    for playbook_disk in playbook_disks:
        if playbook_disk['name'] not in template_disks:
            add_disk_to_instance(playbook_disk, instance)


def add_disk_to_instance(playbook_disk, instance):
    """Adds a new disk to an application instance if a disk with the same name
        is not already present in that instance.

    Args:
        playbook_disk (dict): The configuration of a single disk from the
            Ansible playbook
        instance (ApiApplicationInstancePropertiesPayload): A payload
            containing the properties of the instance
    """
    failure_reason = None

    try:
        disk_payload = get_disk_payload(playbook_disk)
    except Exception as e:
        fail_and_rollback_instance_creation(str(e), instance)

    RESOURCES['update_app'].create_disk(body=disk_payload, uuid=instance.uuid)


def get_disk_payload(playbook_disk):
    """Generates a payload for creating a new disk in an application.

    Args:
        playbook_disk (dict): The configuration of a single disk from the
            Ansible playbook

    Raises:
        tacp_exceptions.InvalidDiskBandwidthLimitException
        tacp_exceptions.InvalidDiskIopsLimitException
        tacp_exceptions.InvalidDiskSizeException
        tacp_exceptions.InvalidDiskNameException

    Returns:
        ApiDiskSizeAndLimitPayload: The populated payload object to be provided
            to the function that actually creates the disk.
    """
    bandwidth_limit = playbook_disk.get('bandwidth_limit')
    if bandwidth_limit:
        if int(bandwidth_limit) < MINIMUM_BW_FIVE_MBPS_IN_BYTES:
            raise tacp_exceptions.InvalidDiskBandwidthLimitException(
                'Could not add disk to instance; disks must have a bandwidth limit of at least 5 MBps (5000000).'  # noqa
        )

    iops_limit = playbook_disk.get('iops_limit')
    if iops_limit:
        if int(iops_limit) < MINIMUM_IOPS:
            raise tacp_exceptions.InvalidDiskIopsLimitException(
                'Could not add disk to instance; disks must have a total IOPS limit of at least 50.'  # noqa
        )

    size_gb = playbook_disk.get('size_gb')
    if not size_gb:
        raise tacp_exceptions.InvalidDiskSizeException(
            'Could not add disk to instance; disks must have a positive size in GB provided.'  # noqa
    )

    size_bytes = tacp_utils.convert_memory_abbreviation_to_bytes(
        str(playbook_disk['size_gb']) + 'GB')

    name = playbook_disk.get('name')
    if not name:
        raise tacp_exceptions.InvalidDiskNameException(
            'Could not add disk to instance; disks must have a name provided.'
        )

    disk_payload = tacp.ApiDiskSizeAndLimitPayload(
        bandwidth_limit=bandwidth_limit,
        iops_limit=iops_limit,
        name=name,
        size=size_bytes,
        uuid=str(uuid4())
    )

    return disk_payload


def update_boot_order(playbook_instance):
    """Updates the boot order of an instance using the boot order information
        provided in the Ansible playbook input.

    Args:
        playbook_instance (dict): The specified instance configuration from
        the playbook input
    """
    boot_order_payload = get_full_boot_order_payload_for_playbook(
        playbook_instance)
    instance_uuid = RESOURCES['app'].get_by_name(
        playbook_instance['name']).uuid

    RESOURCES['update_app'].edit_boot_order(boot_order_payload, instance_uuid)


def get_full_boot_order_payload_for_playbook(playbook_instance):
    """Given the playbook input, generate a payload to update the boot order
        for the created instance.

    Args:
        playbook_instance (dict): The specified instance configuration from
        the playbook input

    Returns:
        ApiEditApplicationPayload: A payload object containing all the boot
            order objects needed to perform the update operation.
    """
    playbook_devices = {}
    playbook_devices['disks'] = playbook_instance['disks']
    playbook_devices['nics'] = playbook_instance['nics']

    existing_instance = RESOURCES['app'].get_by_name(playbook_instance['name'])
    existing_instance_boot_devices = existing_instance.boot_order

    new_boot_order = []

    for boot_device in existing_instance_boot_devices:
        new_boot_order_entry = get_new_boot_order_entry_for_device(
            boot_device, playbook_devices)

        boot_order_payload = get_boot_order_payload(new_boot_order_entry)
        new_boot_order.append(boot_order_payload)

    new_boot_order = sorted(new_boot_order, key=lambda payload: payload.order)
    full_boot_order_payload = tacp.ApiEditApplicationPayload(
        boot_order=new_boot_order)

    return full_boot_order_payload


def get_new_boot_order_entry_for_device(boot_device, playbook_devices):
    """Generates a dict of values necessary to populate an ApiBootOrderPayload
        object for updating the boot order.

    Args:
        boot_device (ApiBootOrderPayload): The preexisting boot device
            in the instance in question.
        playbook_devices (list): A list of the vNICs and disks as provided
            in the Ansible playbook, especially indicating the desired boot
            order.

    Returns:
        dict: [description]
    """
    new_boot_order_entry = {}

    name = boot_device.name
    new_boot_order_entry['name'] = name

    if boot_device.vnic_uuid:
        new_boot_order_entry['vnic_uuid'] = boot_device.vnic_uuid
        new_boot_order_entry['disk_uuid'] = None
        playbook_nic = next(nic for nic in playbook_devices['nics']
                            if nic['name'] == name)
        new_boot_order_entry['order'] = playbook_nic['boot_order']
    else:
        new_boot_order_entry['vnic_uuid'] = None
        new_boot_order_entry['disk_uuid'] = boot_device.disk_uuid
        playbook_disk = next(disk for disk in playbook_devices['disks']
                             if disk['name'] == name)
        new_boot_order_entry['order'] = playbook_disk['boot_order']

    return new_boot_order_entry


def get_boot_order_payload(boot_order_entry):
    boot_order_payload = tacp.ApiBootOrderPayload(
        disk_uuid=boot_order_entry['disk_uuid'],
        name=boot_order_entry['name'],
        order=boot_order_entry['order'],
        vnic_uuid=boot_order_entry['vnic_uuid'])

    return boot_order_payload


def run_module():
    # define available arguments/parameters a user can pass to the module
    if MODULE.check_mode:
        MODULE.exit_json(**RESULT)

    playbook_instance = MODULE.params

    instance_name = playbook_instance['name']

    instance = RESOURCES['app'].get_by_name(instance_name)
    if not instance:
        instance_payload = create_instance(playbook_instance)

        instance = RESOURCES['app'].get_by_name(instance_name)

        add_playbook_vnics(playbook_instance['nics'], instance)
        add_playbook_disks(playbook_instance['disks'], instance)

        update_boot_order(playbook_instance)

    current_state = instance.status
    target_state = playbook_instance['state']

    update_instance_state(instance, current_state, target_state)

    if target_state != PlaybookState.ABSENT:
        final_instance = RESOURCES['app'].get_by_name(instance_name)

        RESULT['instance'] = final_instance.to_dict()

    MODULE.exit_json(**RESULT)


def main():
    run_module()


if __name__ == '__main__':
    main()
