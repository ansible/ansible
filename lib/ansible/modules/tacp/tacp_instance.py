#!/usr/bin/python

# Copyright: (c) 2020, Lenovo
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.tacp_ansible.tacp_constants import (
    Playbook_State, API_State)
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


PLAYBOOK_STATES = [Playbook_State.STARTED, Playbook_State.SHUTDOWN,
                   Playbook_State.STOPPED, Playbook_State.RESTARTED,
                   Playbook_State.FORCE_RESTARTED, Playbook_State.PAUSED,
                   Playbook_State.ABSENT]

STATE_CHANGES = {
    (API_State.RUNNING, Playbook_State.STARTED): [],
    (API_State.RUNNING, Playbook_State.SHUTDOWN): [Playbook_State.SHUTDOWN],
    (API_State.RUNNING, Playbook_State.STOPPED): [Playbook_State.STOPPED],
    (API_State.RUNNING, Playbook_State.RESTARTED): [Playbook_State.RESTARTED],
    (API_State.RUNNING, Playbook_State.FORCE_RESTARTED): [
        Playbook_State.FORCE_RESTARTED],
    (API_State.RUNNING, Playbook_State.PAUSED): [Playbook_State.PAUSED],
    (API_State.RUNNING, Playbook_State.ABSENT): [Playbook_State.ABSENT],
    (API_State.SHUTDOWN, Playbook_State.STARTED): [Playbook_State.STARTED],
    (API_State.SHUTDOWN, Playbook_State.SHUTDOWN): [],
    (API_State.SHUTDOWN, Playbook_State.STOPPED): [],
    (API_State.SHUTDOWN, Playbook_State.RESTARTED): [Playbook_State.STARTED],
    (API_State.SHUTDOWN, Playbook_State.FORCE_RESTARTED): [
        Playbook_State.STARTED],
    (API_State.SHUTDOWN, Playbook_State.PAUSED): [
        Playbook_State.STARTED, Playbook_State.PAUSED],
    (API_State.SHUTDOWN, Playbook_State.ABSENT): [Playbook_State.ABSENT],
    (API_State.PAUSED, Playbook_State.STARTED): [Playbook_State.RESUMED],
    (API_State.PAUSED, Playbook_State.SHUTDOWN): [
        Playbook_State.RESUMED, Playbook_State.SHUTDOWN],
    (API_State.PAUSED, Playbook_State.STOPPED): [Playbook_State.STOPPED],
    (API_State.PAUSED, Playbook_State.RESTARTED): [
        Playbook_State.RESUMED, Playbook_State.RESTARTED],
    (API_State.PAUSED, Playbook_State.FORCE_RESTARTED):
        [Playbook_State.RESUMED, Playbook_State.FORCE_RESTARTED],
    (API_State.PAUSED, Playbook_State.PAUSED): [],
    (API_State.PAUSED, Playbook_State.ABSENT): [Playbook_State.ABSENT]
}

MODULE_ARGS = {
    'api_key': {'type': 'str', 'required': True},
    'portal_url': {'type': 'str', 'required': False,
                   'default': 'https://manage.cp.lenovo.com'},
    'name': {'type': 'str', 'required': True},
    'state': {'type': 'str', 'required': True,
              'choices': PLAYBOOK_STATES},
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
    'update_app': tacp_utils.UpdateApplicationResource(API_CLIENT),
    'vlan': tacp_utils.VlanResource(API_CLIENT),
    'vnet': tacp_utils.VnetResource(API_CLIENT)
}


def fail_with_reason(reason):
    RESULT['msg'] = reason
    MODULE.fail_json(**RESULT)


def fail_and_rollback_instance_creation(reason, instance_uuid):
    RESULT['msg'] = reason + "\n Rolled back application instance creation."
    RESOURCES['app'].delete(instance_uuid)
    MODULE.fail_json()


def get_parameters_to_create_new_application(playbook_instance):
    parameters_to_create_new_application = {}
    parameters_to_create_new_application['instance_name'] = playbook_instance['name']  # noqa

    resources = [
        'datacenter',
        'migration_zone',
        'storage_pool',
        'template'
    ]

    for resource in resources:
        resource_list = RESOURCES[resource].filter(
            name=playbook_instance[resource])
        if not resource_list:
            fail_with_reason("{} resource {} does not exist, cannot continue.".format(  # noqa
                resource, playbook_instance[resource]
            ))
        resource_uuid = resource_list[0].uuid

        parameters_to_create_new_application['{}_uuid'.format(
            resource)] = resource_uuid

        if resource == 'template':
            template_boot_order = resource_list[0].boot_order
            parameters_to_create_new_application['boot_order'] = template_boot_order  # noqa

    if playbook_instance['application_group']:
        uuid = RESOURCES['app_group'].get_uuid_by_name(
            playbook_instance['application_group']
        )
        if uuid is None:
            resp = RESOURCES['app_group'].create(playbook_instance['application_group'],  # noqa
                        parameters_to_create_new_application['datacenter_uuid'])  # noqa
            uuid = resp.object_uuid

        parameters_to_create_new_application['application_group_uuid'] = uuid

    network_payloads = []
    vnic_payloads = []
    template_vnics = [boot_device for boot_device
                      in template_boot_order if boot_device.vnic_uuid]

    for playbook_vnic in playbook_instance['nics']:
        if playbook_vnic['name'] in [vnic.name for vnic in template_vnics]:  # noqa
            corresponding_template_vnic = [vnic for vnic in
                                            template_vnics if
                                            vnic.name == playbook_vnic['name']][0]  # noqa

            vnic_uuid = corresponding_template_vnic.vnic_uuid
            template_order = corresponding_template_vnic.order

            parameters_to_create_new_vnic = get_parameters_to_create_vnic(
                datacenter_uuid=parameters_to_create_new_application['datacenter_uuid'],  # noqa
                playbook_vnic=playbook_vnic,
                template_order=template_order
            )

            add_vnic_payload = get_add_vnic_payload(parameters_to_create_new_vnic)  # noqa
            add_network_payload = get_add_network_payload(
                add_vnic_payload, vnic_uuid)
            network_payloads.append(add_network_payload)

    parameters_to_create_new_application['networks'] = network_payloads
    parameters_to_create_new_application['vnics'] = vnic_payloads
    parameters_to_create_new_application['vcpus'] = playbook_instance['vcpu_cores']  # noqa
    parameters_to_create_new_application['memory'] = tacp_utils.convert_memory_abbreviation_to_bytes(  # noqa
        playbook_instance['memory'])
    parameters_to_create_new_application['vm_mode'] = playbook_instance.get(
        'vm_mode').capitalize()
    parameters_to_create_new_application['vtx_enabled'] = playbook_instance.get('vtx_enabled')  # noqa
    parameters_to_create_new_application['auto_recovery_enabled'] = playbook_instance.get('auto_recovery_enabled')  # noqa
    parameters_to_create_new_application['description'] = playbook_instance.get(  # noqa
        'description')

    return parameters_to_create_new_application


def get_create_new_instance_payload(parameters_to_create_new_application):
    create_new_instance_payload = tacp.ApiCreateApplicationPayload(
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
        vnics=parameters_to_create_new_application.get('vnics'),
        boot_order=parameters_to_create_new_application.get('boot_order'),
        hardware_assisted_virtualization_enabled=parameters_to_create_new_application.get('vtx_enabled'),  # noqa
        enable_automatic_recovery=parameters_to_create_new_application.get(
            'auto_recovery_enabled'),
        description=parameters_to_create_new_application.get('description'),
        application_group_uuid=parameters_to_create_new_application.get(
            'application_group_uuid')
    )

    return create_new_instance_payload


def create_instance(playbook_instance):
    parameters_to_create_new_application = get_parameters_to_create_new_application(  # noqa
        MODULE.params)
    create_new_instance_payload = get_create_new_instance_payload(
        parameters_to_create_new_application)

    created_instance_response = RESOURCES['app'].create(create_new_instance_payload)  # noqa

    return created_instance_response


def instance_power_action(instance_uuid, action):
    RESOURCES['app'].power_action_on_instance_by_uuid(
        instance_uuid, action
    )
    RESULT['changed'] = True


def get_instance_by_name(instance_name):
    instance = RESOURCES['app'].filter(name=instance_name)[0]

    return instance


def get_instance_uuid(instance_name):
    instance_list = RESOURCES['app'].filter(name=instance_name)
    if instance_list:
        found_instance = instance_list[0]
        instance_uuid = found_instance.uuid
        return instance_uuid
    return None


def instance_exists(instance_name):
    return bool(get_instance_uuid(instance_name))


def get_template_for_instance(instance_uuid):
    instance = RESOURCES['app'].filter(uuid=instance_uuid)[0]

    template_uuid = instance.template_uuid
    template = RESOURCES['template'].filter(uuid=template_uuid)[0]

    return template


def get_current_instance_state(instance_uuid):
    instance = RESOURCES['app'].filter(uuid=instance_uuid)[0]
    instance_state = instance.status

    return instance_state


def update_instance_state(instance_uuid, current_state, target_state):
    if current_state in [API_State.RUNNING,
                         API_State.SHUTDOWN,
                         API_State.PAUSED]:
        for power_action in STATE_CHANGES[(current_state, target_state)]:
            instance_power_action(instance_uuid, power_action)
        RESULT['changed'] = True


def add_playbook_vnics(playbook_vnics, instance_uuid):
    playbook_template = get_template_for_instance(instance_uuid)
    template_boot_order = playbook_template.boot_order

    template_vnics = [
        device.name for device in template_boot_order if device.vnic_uuid]

    for playbook_vnic in playbook_vnics:
        if playbook_vnic['name'] not in template_vnics:
            add_vnic_to_instance(playbook_vnic, instance_uuid)


def add_vnic_to_instance(playbook_vnic, instance_uuid):
    """Adds a vNIC to an instance if a vNIC with the same name is not already
        present in that instance.

    Args:
        network_payload (ApiCreateOrEditApplicationNetworkOptionsPayload): The
            payload for the new vNIC that will be added to the application
            instance.
        instance_uuid (str): The UUID of the application instance to which the
            vNIC will be added.
    """
    datacenter_uuid = RESOURCES['app'].filter(
        uuid=instance_uuid)[0].datacenter_uuid

    failure_reason = None
    try:
        parameters_to_create_vnic = get_parameters_to_create_vnic(
            datacenter_uuid,
            playbook_vnic)
    except tacp_exceptions.InvalidVnicNameException:
        failure_reason = 'Failed to create vNIC payload; an invalid name was provided for a vNIC.'  # noqa
    except tacp_exceptions.InvalidNetworkNameException:
        failure_reason = 'Failed to create vNIC payload; an invalid network name was provided.'  # noqa
    except tacp_exceptions.InvalidNetworkTypeException:
        failure_reason = 'Failed to create vNIC payload; vNICs must have a type of "VNET" or "VLAN"'  # noqa
    except tacp_exceptions.InvalidFirewallOverrideNameException:
        failure_reason = 'Failed to create vNIC payload; an invalid firewall override name was provided for a vNIC'  # noqa

    if failure_reason:
        fail_and_rollback_instance_creation(failure_reason, instance_uuid)
    vnic_payload = get_add_vnic_payload(parameters_to_create_vnic)
    vnic_uuid = str(uuid4())
    network_payload = get_add_network_payload(vnic_payload, vnic_uuid)
    RESOURCES['update_app'].create_vnic(body=network_payload, uuid=instance_uuid)  # noqa


def get_parameters_to_create_vnic(datacenter_uuid, playbook_vnic,
                                  template_order=None):
    """[summary]

    Args:
        datacenter_uuid (str): The UUI of the datacenter the vNIC will be in.
        playbook_vnic (dict): The vNIC entry as specified in the Ansible
            playbook.
    """
    parameters_to_create_vnic = {}

    name = playbook_vnic.get('name')
    if not name:
        raise tacp_exceptions.InvalidVnicNameException

    parameters_to_create_vnic['name'] = name

    mac_address = playbook_vnic.get('mac_address')
    parameters_to_create_vnic['mac_address'] = mac_address

    automatic_mac_address = not bool(mac_address)
    parameters_to_create_vnic['automatic_mac_address'] = automatic_mac_address

    network_type = playbook_vnic.get('type').lower()
    if network_type not in ['vnet', 'vlan']:
        raise tacp_exceptions.InvalidNetworkTypeException

    network_resource = RESOURCES[network_type]

    networks = network_resource.filter(name=playbook_vnic['network'])
    if not networks:
        raise tacp_exceptions.InvalidNetworkNameException

    network_uuid = networks[0].uuid
    parameters_to_create_vnic['network_uuid'] = network_uuid

    firewall_override_name = playbook_vnic.get('firewall_override')
    if firewall_override_name:
        firewall_override_uuid = get_firewall_override_uuid(
            datacenter_uuid,
            firewall_override_name)
        if not firewall_override_uuid:
            raise tacp_exceptions.InvalidFirewallOverrideNameException
    else:
        firewall_override_uuid = None
    parameters_to_create_vnic['firewall_override_uuid'] = firewall_override_uuid  # noqa

    parameters_to_create_vnic['boot_order'] = template_order

    return parameters_to_create_vnic


def get_firewall_override_uuid(datacenter_uuid, firewall_override_name):
    """Get the UUID for a firewall override for the provided datacenter.

    Args:
        datacenter_uuid (str): The UUID of the datacenter that the firewall
            override is a part of.
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
        firewall_override_uuid = None

    return firewall_override_uuid


def get_add_vnic_payload(parameters_to_create_vnic):
    """Creates an ApiAddVnicPayload that can be used to add a vNIC to a new
        instance, or used as a basis to create an
        ApiCreateOrEditApplicationNetworkOptionsPayload.

    Args:
        parameters_to_create_vnic (dict): The UUID of the datacenter 
            the vNIC will be in.

    Returns:
        ApiAddVnicPayload: The payload that can be used in the 'vnics' field
            when creating an ApiCreateApplicationPayload.
    """

    vnic_payload = tacp.ApiAddVnicPayload(
        boot_order=parameters_to_create_vnic['boot_order'],
        automatic_mac_address=parameters_to_create_vnic['automatic_mac_address'],  # noqa
        firewall_override_uuid=parameters_to_create_vnic['firewall_override_uuid'],  # noqa
        mac_address=parameters_to_create_vnic['mac_address'],
        name=parameters_to_create_vnic['name'],
        network_uuid=parameters_to_create_vnic['network_uuid'])

    return vnic_payload


def get_add_network_payload(vnic_payload, vnic_uuid):
    """Create an API Network payload based on a provided ApiAddVnicPayload
        payload

    Args:
        vnic (ApiAddVnicPayload): A payload for adding a vNIC to a new
            application instance.

    Returns:
        ApiCreateOrEditApplicationNetworkOptionsPayload:

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


def add_playbook_disks(playbook_disks, instance_uuid):
    playbook_template = get_template_for_instance(instance_uuid)
    template_boot_order = playbook_template.boot_order

    template_disks = [
        device.name for device in template_boot_order if device.disk_uuid]

    for playbook_disk in playbook_disks:
        if playbook_disk['name'] not in template_disks:
            add_disk_to_instance(playbook_disk, instance_uuid)


def add_disk_to_instance(playbook_disk, instance_uuid):
    """Adds a new disk to an application instance if a disk with the same name
        is not already present in that instance.

    Args:
        disk_payload (ApiDiskSizeAndLimitPayload): [description]
        instance_uuid (str): [description]
    """
    failure_reason = None

    try:
        disk_payload = create_disk_payload(playbook_disk)
    except tacp_exceptions.InvalidDiskNameException:
        failure_reason = 'Could not add disk to instance; disks must have a name provided.'  # noqa
    except tacp_exceptions.InvalidDiskIopsLimitException:
        failure_reason = 'Could not add disk to instance; disks must have a total IOPS limit of at least 50.'  # noqa
    except tacp_exceptions.InvalidDiskBandwidthLimitException:
        failure_reason = 'Could not add disk to instance; disks must have a bandwidth limit of at least 5 MBps (5000000).'  # noqa
    except tacp_exceptions.InvalidDiskSizeException:
        failure_reason = 'Could not add disk to instance; disks must have a positive size in GB provided.'  # noqa

    if failure_reason:
        fail_and_rollback_instance_creation()

    RESOURCES['update_app'].create_disk(body=disk_payload, uuid=instance_uuid)


def create_disk_payload(playbook_disk):
    """

    Args:
        playbook_disk (dict): The disk entry as specified in the Ansible
            playbook.
    """
    bandwidth_limit = playbook_disk.get('bandwidth_limit')
    if bandwidth_limit:
        if int(bandwidth_limit) < MINIMUM_BW_FIVE_MBPS_IN_BYTES:
            raise tacp_exceptions.InvalidDiskBandwidthLimitException

    iops_limit = playbook_disk.get('iops_limit')
    if iops_limit:
        if int(iops_limit) < MINIMUM_IOPS:
            raise tacp_exceptions.InvalidDiskIopsLimitException

    size_gb = playbook_disk.get('size_gb')
    if not size_gb:
        raise tacp_exceptions.InvalidDiskSizeException

    size_bytes = tacp_utils.convert_memory_abbreviation_to_bytes(str(playbook_disk['size_gb']) + 'GB')  # noqa

    name = playbook_disk.get('name')
    if not name:
        raise tacp_exceptions.InvalidDiskNameException

    disk_payload = tacp.ApiDiskSizeAndLimitPayload(bandwidth_limit=bandwidth_limit,  # noqa
                                            iops_limit=iops_limit,
                                            name=name,
                                            size=size_bytes,
                                            uuid=str(uuid4()))

    return disk_payload


def update_boot_order(playbook_instance):
    boot_order_payload = get_full_boot_order_payload_for_playbook(
        playbook_instance)
    instance_uuid = get_instance_by_name(playbook_instance['name']).uuid

    RESOURCES['update_app'].edit_boot_order(boot_order_payload, instance_uuid)


def get_full_boot_order_payload_for_playbook(playbook_instance):
    playbook_devices = {}
    playbook_devices['disks'] = playbook_instance['disks']
    playbook_devices['nics'] = playbook_instance['nics']

    existing_instance = get_instance_by_name(playbook_instance['name'])
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
    new_boot_order_entry = {}

    name = boot_device.name
    new_boot_order_entry['name'] = name

    if boot_device.vnic_uuid:
        new_boot_order_entry['vnic_uuid'] = boot_device.vnic_uuid
        new_boot_order_entry['disk_uuid'] = None
        playbook_nic = [nic for nic in playbook_devices['nics']
                        if nic['name'] == name][0]
        new_boot_order_entry['order'] = playbook_nic['boot_order']
    else:
        new_boot_order_entry['vnic_uuid'] = None
        new_boot_order_entry['disk_uuid'] = boot_device.disk_uuid
        playbook_disk = [disk for disk in playbook_devices['disks']
                         if disk['name'] == name][0]
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
    instance_uuid = None

    if not instance_exists(instance_name):
        create_instance(playbook_instance)

        instance_uuid = get_instance_uuid(instance_name)

        add_playbook_vnics(playbook_instance['nics'], instance_uuid)
        add_playbook_disks(playbook_instance['disks'], instance_uuid)

        update_boot_order(playbook_instance)

    if not instance_uuid:
        instance_uuid = get_instance_uuid(instance_name)

    current_state = get_current_instance_state(instance_uuid)
    target_state = playbook_instance['state']

    update_instance_state(instance_uuid, current_state, target_state)

    if target_state != Playbook_State.ABSENT:
        final_instance = RESOURCES['app'].filter(uuid=instance_uuid)[0]
        RESULT['instance'] = final_instance.to_dict()

    MODULE.exit_json(**RESULT)


def main():
    run_module()


if __name__ == '__main__':
    main()
