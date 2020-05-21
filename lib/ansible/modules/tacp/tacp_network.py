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

short_description: This is my test module

version_added: "2.9"

description:
    - "This is my longer description explaining my test module"

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


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        api_key=dict(type='str', required=True),
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
        module.fail_json(**result, msg=reason)

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

        inputs_valid, missing_params = validate_input(module.params)
        if not inputs_valid:
            fail_with_reason("Invalid inputs - %s" % ', '.join(missing_params))

        network_params['name'] = module.params['name']

        if 'location_uuid' not in network_params.keys():
            location_uuid = tacp_utils.get_component_fields_by_name(
                module.params['site_name'], 'location', api_client)
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
        vlanResource = tacp_utils.VlanResource(api_client)
        body = tacp.ApiVlanPropertiesPayload(
            name=network_params['name'],
            location_uuid=network_params['location_uuid'],
            vlan_tag=network_params['vlan_tag']
        )
        if module._verbosity >= 3:
            result['api_request_body'] = str(body)

        created_vlan_uuid = vlanResource.create(body)
        # try:
        #     api_response = api_instance.create_vlan_using_post(
        #         body)
        #     if module._verbosity >= 3:
        #         result['api_response'] = str(api_response)

        # except ApiException as e:
        #     response_dict = tacp_utils.api_response_to_dict(e)
        #     result['msg'] = response_dict['message']
        #     if "already exists" in response_dict['message']:
        #         result['changed'] = False
        #         result['failed'] = False
        #         module.exit_json(**result)
        #     pass

        result['ansible_module_results'] = vlanResource.get_by_uuid(
            created_vlan_uuid)

        result['changed'] = True
        result['failed'] = False
        module.exit_json(**result)

    def create_vnet_network(network_params):
        vnetResource = tacp_utils.VnetResource(api_client)

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

        created_vnet_uuid = vnetResource.create(body)
        # try:
        #     api_response = api_instance.create_vnet_using_post(body)
        #     if module._verbosity >= 3:
        #         result['api_response'] = str(api_response)

        # except ApiException as e:
        #     response_dict = tacp_utils.api_response_to_dict(e)
        #     result['msg'] = response_dict['message']
        #     if "Error" in response_dict['message']:
        #         result['changed'] = False
        #         result['failed'] = True
        #         fail_with_reason(response_dict['message'])
        #     elif "already exists" in response_dict['message']:
        #         result['changed'] = False
        #         result['failed'] = False
        #         module.exit_json(**result)

        result['ansible_module_results'] = vnetResource.get_by_uuid(
            created_vnet_uuid)
        result['changed'] = True
        result['failed'] = False
        module.exit_json(**result)

    def delete_network(name, network_type, api_client):
        if network_type == 'VLAN':
            vlanResource = tacp_utils.VlanResource(api_client)

            vlan_uuid = vlanResource.get_uuid_by_name(name)

            if vlan_uuid:
                vlanResource.delete(vlan_uuid)
            # try:
            #     # Delete a VNET
            #     api_response = api_instance.delete_vlan_using_delete(vlan_uuid)
            #     if module._verbosity >= 3:
            #         result['api_response'] = str(api_response)
            # except ApiException as e:
            #     response_dict = tacp_utils.api_response_to_dict(e)
            #    # result['msg'] = response_dict['message']
            #     if "Error" in response_dict['message']:
            #         result['changed'] = False
            #         result['failed'] = True
            #         fail_with_reason(response_dict['message'])

            # tacp_utils.wait_for_action_to_complete(
            #     api_response.action_uuid, api_client)
            result['changed'] = True
            result['failed'] = False
            module.exit_json(**result)

        elif network_type == 'VNET':
            vnetResource = tacp_utils.VnetResource(api_client)

            vnet_uuid = vnetResource.get_uuid_by_name(name)

            # Get the NFV instance UUID from the VNET
            nfv_uuid = vnetResource.get_by_uuid(vnet_uuid)['nfv_instance_uuid']

            applicationResource = tacp_utils.ApplicationInstanceResource(
                api_client)

            # Delete the NFV instance
            applicationResource.delete(nfv_uuid)

            vnetResource.delete(vnet_uuid)

            # try:
            #     # Delete a VNET
            #     api_response = api_instance.delete_vnet_using_delete(vnet_uuid)
            #     if module._verbosity >= 3:
            #         result['api_response'] = str(api_response)

            # except ApiException as e:
            #     response_dict = tacp_utils.api_response_to_dict(e)
            #    # result['msg'] = response_dict['message']
            #     module.exit_json(**result)
            #     if "Error" in response_dict['message']:
            #         result['changed'] = False
            #         result['failed'] = True
            #         fail_with_reason(response_dict['message'])

            result['changed'] = True
            result['failed'] = False
            module.exit_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    # Return the inputs for debugging purposes
    result['args'] = module.params

    # Define configuration
    configuration = tacp.Configuration()
    configuration.host = "https://manage.cp.lenovo.com"
    configuration.api_key_prefix['Authorization'] = 'Bearer'
    configuration.api_key['Authorization'] = module.params['api_key']
    api_client = tacp.ApiClient(configuration)

    if module.params['network_type'].upper() == 'VLAN':
        vlanResource = tacp_utils.VlanResource(api_client)
        vlan_uuid = vlanResource.get_uuid_by_name(module.params['name'])
        if module.params['state'] == 'present':
            if vlan_uuid:
                result['msg'] = "VLAN network %s is already present, nothing to do." % module.params['name']
                result['failed'] = False
                result['changed'] = False
                module.exit_json(**result)
            else:
                network_params = generate_network_params(module)

                create_vlan_network(network_params)
        elif module.params['state'] == 'absent':
            if vlan_uuid:
                delete_network(
                    name=module.params['name'], network_type='VLAN', api_client=api_client)
            else:
                result['msg'] = "VLAN network %s is already absent, nothing to do." % module.params['name']
                result['failed'] = False
                result['changed'] = False
                module.exit_json(**result)

    elif module.params['network_type'].upper() == 'VNET':
        vnetResource = tacp_utils.VnetResource(api_client)
        vnet_uuid = vnetResource.get_uuid_by_name(module.params['name'])
        if module.params['state'] == 'present':
            if vnet_uuid:
                result['msg'] = "VNET network %s is already present, nothing to do." % module.params['name']
                result['failed'] = False
                result['changed'] = False
                module.exit_json(**result)
            else:
                network_params = generate_network_params(module)
                create_vnet_network(network_params)
        elif module.params['state'] == 'absent':
            if vnet_uuid:
                delete_network(
                    name=module.params['name'], network_type='VNET', api_client=api_client)
            else:
                result['msg'] = "VNET network %s is already absent, nothing to do." % module.params['name']
                result['failed'] = False
                result['changed'] = False
                module.exit_json(**result)

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    # if module.params['new']:
    #     result['changed'] = True

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
