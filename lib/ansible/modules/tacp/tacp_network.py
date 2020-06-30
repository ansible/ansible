#!/usr/bin/python

# Copyright: (c) 2020, Lenovo
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.tacp_ansible import tacp_utils
from ansible.module_utils.tacp_ansible.tacp_exceptions import ActionTimedOutException, InvalidActionUuidException

import json
import tacp
import sys
from tacp.rest import ApiException
from pprint import pprint

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: tacp_network

short_description: Creates and deletes VLAN and VNET networks on ThinkAgile CP.

description:
  - "This module can be used to create new VLAN and VNET networks on the
    ThinkAgile CP cloud platform, as well as delete existing networks."
  - "Currently this module cannot modify the settings of existing
    networks; all settings must be specified at creation time."

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
      - This is the name of the network to be created or deleted.
    required: true
    type: str
  state:
    description:
      - The desired state for the network.
      - Only valid for VLAN networks.
    required: false
    default: present
    type: str
  network_type:
    description:
      - The type of network. Valid choices are either "VNET" or "VLAN".
    required: True
    type: str
  site_name:
    description:
      - The name of the site that the network will be a part of.
      - If only one site exists, that site will be used by default and
        this parameter is unneeded.
    required: False
    type: str
  vlan_tag:
    description:
      - The VLAN ID to tag the network traffic with.
      - Must be in the range of 1-4094.
      - Only valid for VLAN network types.
    required: False
    type: int
  firewall_override:
    description:
      - The name of a firewall override to be assigned to a VNET.
      - Only valid for VNET network types.
    required: False
    type: str
  firewall_profile:
    description:
      - The name of a firewall profile to be assigned to a VNET.
    required: False
    type: str
  autodeploy_nfv:
    description:
      - Whether the network function virtualization (NFV) instance
        will be created along with the VNET network.
      - If this is set to False, the VNET network will need an NFV
        added manually later before it will work properly.
      - Only valid for VNET network types.
    required: False
    type: bool
  nfv:
    description:
      - The settings to create an NFV instance to provide routing and
        DHCP functionality to the VNET.
      - Required if autodeploy_nfv is set to true.
      - Only valid for VNET network types.
    required: False
    type: dict
    suboptions:
      datacenter:
        description:
          - The name of the virtual datacenter that the NFV instance
            will be created in. Only required when creating an NFV
            instance.
        required: false
        type: str
      storage_pool:
        description:
          - The name of the storage pool that the NFV instance's
            disks will be stored in. Only required when creating a
            new instance.
        required: false
        type: str
      migration_zone:
        description:
          - The name of the migration zone that the NFV instance will
            be created in. Only required when creating a new NFV
            instance.
        required: false
        type: str
      cpu_cores:
        description:
          - The number of virtual CPU cores that the NFV instance
            will have when it is created. Only required when
            creating a new NFV instance.
        required: false
        type: int
      memory:
        description:
          - The amount of virtual memory (RAM) that the NFV instance
            will have when it is created. Can be expressed with
            various units. Only required when creating a new NFV
            instance.
        required: false
        type: str
      auto_recovery:
        description:
          - Whether or not the NFV instance should be restarted on a
            different host node in the event that its host node
            fails. Defaults to true.
        required: false
        type: bool
  network_address:
    description:
      - The identifying address for the VNET network.
      - Example - "192.168.0.0" for the 192.168.0.0/24 network.
    required: False
    type: str
  subnet_mask:
    description:
      - The subnet mask for the VNET network.
      - Example - "255.255.255.0" for the 192.168.0.0/24 network.
    required: False
    type: str
  gateway:
    description:
      - The IP address for the gateway for this network.
      - Example - "192.168.0.1"
    required: False
    type: str
  dhcp:
    description:
      - The DHCP configuration for the NFV intance.
      - Required if an NFV instance is being created.
    required: False
    type: dict
    suboptions:
      dhcp_start:
        description:
          - The starting IP address in the DHCP range.
        required: False
        type: str
      dhcp_end:
        description:
          - The ending IP address in the DHCP range.
        required: False
        type: str
      domain_name:
        description:
          - The domain name to be used for hosts in the DHCP range.
        required: False
        type: str
      lease_time:
        description:
          - The length of the DHCP leases, in seconds.
        required: False
        type: int
      dns1:
        description:
          - The primary DNS server for the DHCP configuration.
        required: False
        type: str
      dns2:
        description:
          - The secondary DNS server for the DHCP configuration.
        required: False
        type: str
      static_bindings:
        description:
          - A list of static DHCP bindings, each binding requires at
            least an ip_address and mac_address value as a dict.
        required: False
        type: list
        suboptions:
          hostname:
            description:
              - A hostname to be assigned to a bound to a
                particular IP address.
            required: false
            type: str
          ip_address:
            description:
              - The IP address to be bound to the hostname
                and/or MAC address provided in this entry.
            required: false
            type: str
          mac_address:
            description:
              - The MAC address to be bound to the IP address
                provided in this entry.
            required: false
            type: str
  routing:
    description:
      - Defines the network settings for the outside interface of the NFV
        instance.
    required: False
    type: dict
    suboptions:
      type:
        description:
          - The type of network the outside interface will belong to.
          - Valid choices are either "VNET" or "VLAN".
        required: false
        type: str
      network:
        description:
          - The name of the existing network the outside interface
            will belong to. Must be of the network type specified
            in the type field.
        required: false
        type: str
      address_mode:
        description:
          - The mode of setting the outside interface IP address.
          - Valid choices are either "static" or "DHCP".
        required: false
        type: str
      ip_address:
        description:
          - The IP address of the outside interface.
          - Only valid when address_mode is set to static.
        required: false
        type: str
      subnet_mask:
        description:
          - The subnet mask of the outside interface.
          - Only valid when address_mode is set to static.
        required: false
        type: str
      gateway:
        description:
          - The IP address of the outside interface's gateway.
          - Only valid when address_mode is set to static.
        required: false
        type: str

'''

EXAMPLES = '''
- name: Create a VLAN network on ThinkAgile CP
    tacp_network:
      api_key: "{{ api_key }}"
      name: VLAN-15
      state: present
      network_type: VLAN
      vlan_tag: 15

- name: Delete a VLAN network on ThinkAgile CP
    tacp_network:
      api_key: "{{ api_key }}"
      name: VLAN-15
      state: absent
      network_type: VLAN

- name: Create a VNET network with an NFV on TACP
    tacp_network:
      api_key: "{{ api_key }}"
      name:  Private VNET
      state: present
      network_type: VNET
      autodeploy_nfv: True
      network_address: 192.168.1.0
      subnet_mask: 255.255.255.0
      gateway: 192.168.1.1
      dhcp:
        dhcp_start: 192.168.1.100
        dhcp_end: 192.168.1.200
        domain_name: test.local
        lease_time: 86400 # seconds, 24 hours
        dns1: 1.1.1.1
        dns2: 8.8.8.8
      routing:
        type: VLAN
        network: Lab-VLAN
        address_mode: static
        ip_address: 192.168.100.201
        subnet_mask: 255.255.255.0
        gateway: 192.168.100.1
      nfv:
        datacenter: Datacenter1
        storage_pool: Pool1
        migration_zone: Zone1
        cpu_cores: 1
        memory: 1G
        auto_recovery: True

- name: Create a VNET network with an NFV and static bindings on TACP
    tacp_network:
      api_key: "{{ api_key }}"
      name:  Private VNET
      state: present
      network_type: VNET
      autodeploy_nfv: True
      network_address: 192.168.1.0
      subnet_mask: 255.255.255.0
      gateway: 192.168.1.1
      dhcp:
        dhcp_start: 192.168.1.100
        dhcp_end: 192.168.1.200
        domain_name: test.local
        lease_time: 86400 # seconds, 24 hours
        dns1: 1.1.1.1
        dns2: 8.8.8.8
        static_bindings:
          - hostname: Host1
            ip_address: 192.168.1.101
            mac_address: b4:d1:35:00:0f:f1
          - hostname: Host2
            ip_address: 192.168.1.102
            mac_address: b4:d1:35:00:0f:f2
      routing:
        type: VLAN
        network: Lab-VLAN
        address_mode: static
        ip_address: 192.168.100.201
        subnet_mask: 255.255.255.0
        gateway: 192.168.100.1
      nfv:
        datacenter: Datacenter1
        storage_pool: Pool1
        migration_zone: Zone1
        cpu_cores: 1
        memory: 1G
        auto_recovery: True
'''

RETURN = '''
msg:
  description:
    - An error message in the event of invalid input or other
      unexpected behavior during module execution.
  type: str
  returned: failure
'''


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        api_key=dict(type='str', required=True),
        portal_url=dict(type='str', required=False,
                        default="https://manage.cp.lenovo.com"),
        name=dict(type='str', required=True),
        state=dict(type='str', default='present',
                   choices=['present', 'absent']),
        network_type=dict(type='str', required=True, choices=[
                          'VLAN', 'vlan', 'VNET', 'vnet']),
        site_name=dict(type='str', required=False),
        vlan_tag=dict(type='int', required=False),
        firewall_override=dict(type='str', required=False),
        firewall_profile=dict(type='str', required=False),
        autodeploy_nfv=dict(type='bool', required=False, default=True),
        nfv=dict(type='dict', required=False),
        network_address=dict(type='str', required=False),
        subnet_mask=dict(type='str', required=False),
        gateway=dict(type='str', required=False),
        dhcp=dict(type='dict', required=False),
        routing=dict(type='dict', required=False)
    )

    result = dict(
        changed=False,
        args=[]
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)

    def fail_with_reason(reason):
        module.fail_json(msg=reason, **result)

    def get_site_list():
        api_instance = tacp.LocationsApi(api_client)
        try:
            # View sites for an organization
            api_response = api_instance.get_locations_for_organization_using_get()
        except ApiException as e:
            return "Exception when calling get_locations_for_organization_using_get: %s\n" % e

        if api_response:
            return api_response
        else:
            return None

    def validate_input(params):
        # Check if there is more than one site already
        # If there is only one, default to that one.
        # Otherwise require a site_name to be provided
        required_params = []
        missing_params = []

        site_list = get_site_list()
        if len(site_list) != 1:
            required_params.append('site_name')

        inputs_valid = True
        if params['network_type'].upper() == 'VLAN':
            if params['state'] == 'present':
                required_params += ['name', 'vlan_tag']
                for param in required_params:
                    if not params[param]:
                        missing_params.append(param)
                        inputs_valid = False
                return inputs_valid, missing_params

        elif params['network_type'].upper() == 'VNET':
            if params['state'] == 'present':
                required_params += ['network_address', 'subnet_mask',
                                    'gateway', 'dhcp', 'routing']
                for param in required_params:
                    if not params[param]:
                        missing_params.append(param)
                        inputs_valid = False
                return inputs_valid, missing_params

    def generate_network_params(module):
        network_params = {}

        site_list = get_site_list()
        if len(site_list) == 1:
            network_params['location_uuid'] = site_list[0].uuid

        # inputs_valid, missing_params = validate_input(module.params)
        # if not inputs_valid:
        #     fail_with_reason("Invalid inputs - %s" % ', '.join(missing_params))

        network_params['name'] = module.params['name']

        if 'location_uuid' not in network_params.keys():
            site = next(site for site in site_list if
                        site.name == module.params['site_name'])
            location_uuid = site.uuid
            if not location_uuid:
                fail_with_reason(
                    "Could not get a UUID for the provided site name. Verify that a site with name %s exists and try again." % module.params['site_name'])
            network_params['location_uuid'] = location_uuid

        if module.params['network_type'].upper() == 'VNET':
            base_params = ['autodeploy_nfv',
                           'network_address', 'subnet_mask', 'gateway']

            for param in base_params:
                if param in module.params.keys():
                    network_params[param] = module.params[param]
                else:
                    network_params[param] = None

            if 'firewall_override' in module.params.keys():
                network_params['firewall_override_uuid'] = tacp_utils.get_component_fields_by_name(
                    module.params['firewall_override'], 'firewall_override', api_client)
            else:
                network_params['firewall_override_uuid'] = None

            if 'firewall_profile' in module.params.keys():
                network_params['firewall_profile_uuid'] = tacp_utils.get_component_fields_by_name(
                    module.params['firewall_profile'], 'firewall_profile', api_client)
            else:
                network_params['firewall_profile_uuid'] = None

            dhcp_params = ['dhcp_start', 'dhcp_end',
                           'domain_name', 'lease_time', 'dns1', 'dns2',
                           'static_bindings']
            network_params['dhcp'] = {}
            for param in dhcp_params:
                if param in module.params['dhcp'].keys():
                    network_params['dhcp'][param] = module.params['dhcp'][param]
                else:
                    network_params['dhcp'][param] = None

            routing_params = ['network', 'type', 'address_mode', 'ip_address', 'subnet_mask',
                              'gateway']
            network_params['routing'] = {}
            for param in routing_params:
                if param in module.params['routing'].keys():
                    network_params['routing'][param] = module.params['routing'][param]
                else:
                    network_params['routing'][param] = None
            try:
                if module.params['routing']['firewall_override']:
                    network_params['routing']['firewall_override_uuid'] = tacp_utils.get_component_fields_by_name(
                        network_params['routing']['firewall_override'],
                        'firewall_override', api_client)
            except Exception:
                network_params['routing']['firewall_override_uuid'] = None

            network_params['routing']['network_uuid'] = tacp_utils.get_component_fields_by_name(
                network_params['routing']['network'],
                network_params['routing']['type'].lower(), api_client)

            nfv_params = ['datacenter', 'storage_pool',
                          'migration_zone', 'cpu_cores', 'memory', 'auto_recovery']
            network_params['nfv'] = {}
            for param in nfv_params:
                if param in module.params['nfv'].keys():
                    if param == 'memory':
                        network_params['nfv'][param] = tacp_utils.convert_memory_abbreviation_to_bytes(
                            module.params['nfv'][param])
                    else:
                        network_params['nfv'][param] = module.params['nfv'][param]
                else:
                    network_params['nfv'][param] = None

        elif module.params['network_type'].upper() == 'VLAN':
            if module.params['vlan_tag'] in range(1, 4095):
                network_params['vlan_tag'] = module.params['vlan_tag']
            else:
                fail_with_reason(
                    "vlan_tag parameter is invalid - must be in range 1-4094")
        return network_params

    def create_vlan_network(network_params):
        vlan_resource = tacp_utils.VlanResource(api_client)
        body = tacp.ApiVlanPropertiesPayload(
            name=network_params['name'],
            location_uuid=network_params['location_uuid'],
            vlan_tag=network_params['vlan_tag']
        )
        if module._verbosity >= 3:
            result['api_request_body'] = str(body)

        response = vlan_resource.create(body)

        result['ansible_module_results'] = vlan_resource.get_by_uuid(
            response.object_uuid
        ).to_dict()

        result['changed'] = True
        result['failed'] = False
        module.exit_json(**result)

    def create_vnet_network(network_params):
        vnet_resource = tacp_utils.VnetResource(api_client)

        # Package static bindings input as a list of ApiStaticBindingRulePayloads
        static_binding_payloads = []
        try:
            for binding in network_params['dhcp']['static_bindings']:
                params = ['hostname', 'ip_address', 'mac_address']
                for param in params:
                    if param not in binding.keys():
                        binding[param] = None
                payload = tacp.ApiStaticBindingRulePayload(
                    hostname=binding['hostname'],
                    ip_address=binding['ip_address'],
                    mac_address=binding['mac_address'])
                static_binding_payloads.append(payload)
        except Exception:
            # If there are no static_bindings we can just move on with an empty list
            pass

        # Create ApiVnetDhcpServicePayload from inputs and static binding list
        dhcp_service = tacp.ApiVnetDhcpServicePayload(
            domain_name=network_params['dhcp']['domain_name'],
            start_ip_range=network_params['dhcp']['dhcp_start'],
            end_ip_range=network_params['dhcp']['dhcp_end'],
            lease_time=network_params['dhcp']['lease_time'],
            primary_dns_server_ip_address=network_params['dhcp']['dns1'],
            secondary_dns_server_ip_address=network_params['dhcp']['dns2'],
            static_bindings=static_binding_payloads
        )

        params = ['address_mode', 'firewall_override', 'gateway',
                  'ip_address', 'subnet_mask', 'type']
        for param in params:
            if param not in network_params['routing'].keys():
                network_params['routing'][param] = None

        routing_service = tacp.ApiVnetRoutingServicePayload(
            address_mode=network_params['routing']['address_mode'],
            firewall_override_uuid=network_params['routing']['firewall_override_uuid'],
            gateway=network_params['routing']['gateway'],
            ip_address=network_params['routing']['ip_address'],
            network_uuid=network_params['routing']['network_uuid'],
            subnet_mask=network_params['routing']['subnet_mask'],
            type=network_params['routing']['type']
        )

        params = ['datacenter', 'storage_pool', 'migration_zone',
                  'cpu_cores', 'memory', 'auto_recovery']
        for param in params:
            if param not in network_params['nfv'].keys():
                if param == 'cpu_cores':
                    network_params['nfv']['cpu_cores'] = 1
                elif param == 'memory':
                    network_params['nfv']['memory'] = 1073741824  # 1 GB
                elif param == 'auto_recovery':
                    network_params['nfv']['auto_recovery'] = True
                else:
                    network_params['nfv'][param] = None
            if param == 'datacenter':
                network_params['nfv']['datacenter_uuid'] = tacp_utils.get_component_fields_by_name(
                    network_params['nfv']['datacenter'], 'datacenter', api_client)
            elif param == 'storage_pool':
                network_params['nfv']['storage_pool_uuid'] = tacp_utils.get_component_fields_by_name(
                    network_params['nfv']['storage_pool'], 'storage_pool', api_client)
            elif param == 'migration_zone':
                network_params['nfv']['migration_zone_uuid'] = tacp_utils.get_component_fields_by_name(
                    network_params['nfv']['migration_zone'], 'migration_zone', api_client)

        nfv_instance = tacp.ApiCreateApplicationPayload(
            datacenter_uuid=network_params['nfv']['datacenter_uuid'],
            enable_automatic_recovery=network_params['nfv']['auto_recovery'],
            flash_pool_uuid=network_params['nfv']['storage_pool_uuid'],
            memory=network_params['nfv']['memory'],
            migration_zone_uuid=network_params['nfv']['migration_zone_uuid'],
            vcpus=network_params['nfv']['cpu_cores']
        )

        body = tacp.ApiCreateVnetPayload(
            automatic_deployment=network_params['autodeploy_nfv'],
            default_gateway=network_params['gateway'],
            deploy_now=True,
            dhcp_service=dhcp_service,
            firewall_override_uuid=network_params['firewall_override_uuid'],
            firewall_profile_uuid=network_params['firewall_profile_uuid'],
            name=network_params['name'],
            network_address=network_params['network_address'],
            nfv_instance=nfv_instance,
            routing_service=routing_service,
            subnet_mask=network_params['subnet_mask']
        )
        if module._verbosity >= 3:
            result['api_request_body'] = str(body)

        response = vnet_resource.create(body)

        result['ansible_module_results'] = vnet_resource.get_by_uuid(
            response.object_uuid
        ).to_dict()
        result['changed'] = True
        result['failed'] = False
        module.exit_json(**result)

    def delete_network(name, network_type, api_client):
        if network_type == 'VLAN':
            vlan_resource = tacp_utils.VlanResource(api_client)

            vlan_uuid = vlan_resource.get_by_name(name).uuid

            if vlan_uuid:
                response = vlan_resource.delete(vlan_uuid)
                if not hasattr(response, 'object_uuid'):
                    fail_with_reason(response)

        elif network_type == 'VNET':
            vnet_resource = tacp_utils.VnetResource(api_client)
            application_resource = tacp_utils.ApplicationResource(api_client)

            vnet_uuid = vnet_resource.get_by_name(name).uuid

            if vnet_uuid:
                nfv_uuid = vnet_resource.get_by_uuid(vnet_uuid).to_dict()[
                    'nfv_instance_uuid']

                if nfv_uuid:
                    # Delete the NFV instance
                    response = application_resource.delete(nfv_uuid)
                    if not hasattr(response, 'object_uuid'):
                        fail_with_reason(response)

                response = vnet_resource.delete(vnet_uuid)
                if not hasattr(response, 'object_uuid'):
                    fail_with_reason(response)
            else:
                fail_with_reason("No VNET found with name %s " % name)

        result['changed'] = True
        result['failed'] = False
        module.exit_json(**result)

    def bad_inputs_for_state_change(playbook_network):
        non_state_change_inputs = [
            'vlan_tag', 'firewall_override',
            'firewall_profile', 'nfv', 'network_address',
            'subnet_mask', 'gateway', 'dhcp', 'routing'
        ]

        bad_inputs_in_playbook = [bad_input for bad_input in
                                  non_state_change_inputs
                                  if playbook_network[bad_input]
                                  ]

        return bad_inputs_in_playbook

    # Define configuration
    configuration = tacp_utils.get_configuration(module.params['api_key'],
                                                 module.params['portal_url'])
    api_client = tacp.ApiClient(configuration)

    if module.params['network_type'].upper() == 'VLAN':
        vlan_resource = tacp_utils.VlanResource(api_client)
        vlan_uuid = None
        vlan = vlan_resource.get_by_name(module.params['name'])
        if vlan:
            vlan_uuid = vlan.uuid

        if module.params['state'] == 'present':
            if vlan_uuid:
                bad_inputs = bad_inputs_for_state_change(
                    module.params)
                if bad_inputs:
                    fail_with_reason(
                        "Currently tacp_network cannot modify existing "
                        "virtual networks' configurations apart from"
                        " creation and deletion - since network {} already"
                        " exists the following parameter(s) are invalid"
                        ": {}".format(
                            module.params['name'],
                            ", ".join(bad_inputs)))
                result['msg'] = "VLAN network %s is already present, nothing to do." % module.params['name']

            else:
                network_params = generate_network_params(module)
                create_vlan_network(network_params)

        elif module.params['state'] == 'absent':
            if vlan_uuid:
                delete_network(
                    name=module.params['name'], network_type='VLAN', api_client=api_client)
            else:
                result['msg'] = "VLAN network %s is already absent, nothing to do." % module.params['name']

    elif module.params['network_type'].upper() == 'VNET':
        vnet_resource = tacp_utils.VnetResource(api_client)
        vnet_uuid = None
        vnet = vnet_resource.get_by_name(module.params['name'])
        if vnet:
            vnet_uuid = vnet.uuid

        if module.params['state'] == 'present':
            if vnet_uuid:
                bad_inputs = bad_inputs_for_state_change(
                    module.params)
                if bad_inputs:
                    fail_with_reason(
                        "Currently tacp_network cannot modify existing "
                        "virtual networks' configurations apart from"
                        " creation and deletion - since network {} already"
                        " exists the following parameter(s) are invalid"
                        ": {}".format(
                            module.params['name'],
                            ", ".join(bad_inputs)))
                result['msg'] = "VNET network %s is already present, nothing to do." % module.params['name']

            else:
                network_params = generate_network_params(module)
                create_vnet_network(network_params)
        elif module.params['state'] == 'absent':
            if vnet_uuid:
                delete_network(
                    name=module.params['name'], network_type='VNET', api_client=api_client)
            else:
                result['msg'] = "VNET network %s is already absent, nothing to do." % module.params['name']

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
