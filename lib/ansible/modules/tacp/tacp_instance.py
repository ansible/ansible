#!/usr/bin/python

# Copyright: (c) 2020, Lenovo
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from uuid import UUID
from ansible.module_utils.basic import AnsibleModule

import tacp
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
    - azure

author:
    - Your Name (@yourhandle)
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
        datacenter=dict(type='str', required=True),
        mz=dict(type='str', required=True),
        storage_pool=dict(type='str', required=True),
        template=dict(type='str', required=True),
        vcpu_cores=dict(type='int', required=True),
        memory_mb=dict(type='int', required=True),
        disks=dict(type='list', required=True),
        nics=dict(type='list', required=True)
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

    def fail_with_reason(reason):
        result['failed'] = True
        result['failure_reason'] = reason
        module.exit_json(**result)
        return

    def is_valid_uuid(uuid_to_test, version=4):
        """
        Check if uuid_to_test is a valid UUID.

        Parameters
        ----------
        uuid_to_test : str
        version : {1, 2, 3, 4}

        Returns
        -------
        `True` if uuid_to_test is a valid UUID, otherwise `False`.

        Examples
        --------
        >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
        True
        >>> is_valid_uuid('c9bf9e58')
        False
        """
        try:
            uuid_obj = UUID(uuid_to_test, version=version)
        except ValueError:
            return False

        return str(uuid_obj) == uuid_to_test

    def get_component_uuid_by_name(name, component, api_client):
        """
        Returns the UUID of a named component if it exists in a given 
        ThinkAgile CP cloud, otherwise return None.

        :param name The name of the component that may or may not exist yet
        :type name str
        :param component The type of component in question, must be one of 
        """
        fields = ['uuid']

        valid_components = ["storage_pool", "application",
                            "template", "datacenter", "migration_zone"]

        if component not in valid_components:
            return "Invalid component"
        if component == "storage_pool":
            api_instance = tacp.FlashPoolsApi(api_client)
            try:
                # View flash pools for an organization
                api_response = api_instance.get_flash_pools_using_get(
                    fields=fields)
            except ApiException as e:
                return "Exception when calling get_component_uuid_by_name: %s\n" % e
        elif component == "application":
            api_instance = tacp.ApplicationsApi(api_client)
            try:
                # View flash pools for an organization
                api_response = api_instance.get_applications_using_get(
                    fields=fields)
            except ApiException as e:
                return "Exception when calling get_component_uuid_by_name: %s\n" % e
        elif component == "template":
            api_instance = tacp.TemplatesApi(api_client)
            try:
                # View flash pools for an organization
                api_response = api_instance.get_templates_using_get(
                    fields=fields)
            except ApiException as e:
                return "Exception when calling get_component_uuid_by_name: %s\n" % e
        elif component == "datacenter":
            api_instance = tacp.DatacentersApi(api_client)
            try:
                # View flash pools for an organization
                api_response = api_instance.get_datacenters_using_get(
                    fields=fields)
            except ApiException as e:
                return "Exception when calling get_component_uuid_by_name: %s\n" % e
        elif component == "migration_zone":
            api_instance = tacp.MigrationZonesApi(api_client)
            try:
                # View flash pools for an organization
                api_response = api_instance.get_migration_zones_using_get(
                    fields=fields)
            except ApiException as e:
                return "Exception when calling get_component_uuid_by_name: %s\n" % e
        elif component == "vlan":
            api_instance = tacp.VlansApi(api_client)
            try:
                # View flash pools for an organization
                api_response = api_instance.get_vlans_using_get(
                    fields=fields)
            except ApiException as e:
                return "Exception when calling get_component_uuid_by_name: %s\n" % e
        elif component == "vnet":
            api_instance = tacp.VnetsApi(api_client)
            try:
                # View flash pools for an organization
                api_response = api_instance.get_vnets_using_get(
                    fields=fields)
            except ApiException as e:
                return "Exception when calling get_component_uuid_by_name: %s\n" % e

        if (api_response):
            if hasattr(api_response[0], 'uuid'):
                return api_response[0].uuid
        return None

    instance_params = {}

    # Check if VM instance with this name exists already
    instance_uuid = get_component_uuid_by_name(
        module.params['name'], 'application', api_client)
    # if is_valid_uuid(instance_uuid):
    #     # VM does exist - so for now we need to just break without changing anything,
    #     # but in the future this would mean we go to edit the existing VM with this name/uuid
    #     # vm_exists = True
    #     module.exit_json(**result)
    # else:
    #     # VM does not exist yet, so we must create it
    instance_params['instance_name'] = module.params['name']

    # Check if storage pool exists, it must in order to continue
    storage_pool_uuid = get_component_uuid_by_name(
        module.params['storage_pool'], 'storage_pool', api_client)
    if is_valid_uuid(storage_pool_uuid):
        instance_params['storage_pool_uuid'] = storage_pool_uuid
    else:
        # Pool does not exist - must fail the task
        pass

    # Check if datacenter exists, it must in order to continue
    datacenter_uuid = get_component_uuid_by_name(
        module.params['datacenter'], 'datacenter', api_client)
    if is_valid_uuid(datacenter_uuid):
        instance_params['datacenter_uuid'] = datacenter_uuid
    else:
        # Datacenter does not exist - must fail the task
        pass

    # Check if migration_zone exists, it must in order to continue
    migration_zone_uuid = get_component_uuid_by_name(
        module.params['mz'], 'migration_zone', api_client)
    if is_valid_uuid(migration_zone_uuid):
        instance_params['migration_zone_uuid'] = migration_zone_uuid
    else:
        # Migration zone does not exist - must fail the task
        pass

    # Check if migration_zone exists, it must in order to continue
    template_uuid = get_component_uuid_by_name(
        module.params['template'], 'template', api_client)
    if is_valid_uuid(template_uuid):
        instance_params['template_uuid'] = template_uuid
    else:
        # Migration zone does not exist - must fail the task
        pass

    network_payloads = []
    vnic_payloads = []
    for nic in module.params['nics']:
        if nic['type'].lower() == "vnet":
            network_uuid = get_component_uuid_by_name(
                nic['network'], 'vnet', api_client)
        elif nic['type'].lower() == "vlan":
            network_uuid = get_component_uuid_by_name(
                nic['network'], 'vlan', api_client)

        network_payload = tacp.ApiCreateOrEditApplicationNetworkOptionsPayload(
            name=nic['network'],
            automatic_mac_assignment=True,
            network_uuid=network_uuid)
        network_payloads.append(network_payload)

        vnic_payload = tacp.ApiAddVnicPayload(
            automatic_mac_address=True,
            name=nic['name'],
            network_uuid=network_uuid
        )
        vnic_payloads.append(vnic_payload)

    instance_params['networks'] = network_payloads
    instance_params['vnics'] = vnic_payloads
    instance_params['vcpus'] = module.params['vcpu_cores']
    # We will want to parse out the units on the memory provided to convert it to bytes,
    # which this parameter requires
    instance_params['memory'] = module.params['memory_mb'] * 1024 * 1024
    instance_params['vm_mode'] = "Enhanced"

    def create_instance(instance_params):
        api_instance = tacp.ApplicationsApi(tacp.ApiClient(configuration))

        # Need to create boot disk ahead of time and provide it in the
        # ApiCreateApplicationPayload parameters

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
            hardware_assisted_virtualization_enabled=True)

        try:
            # Create an application from a template
            api_response = api_instance.create_application_from_template_using_post(
                body)
            return api_response

        except ApiException as e:
            return "Exception when calling ApplicationsApi->create_application_from_template_using_post: %s\n" % e

    create_instance_response = create_instance(instance_params)

    result['create_instance_response'] = create_instance_response
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
