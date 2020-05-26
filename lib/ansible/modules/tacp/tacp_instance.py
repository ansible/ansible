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


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        api_key=dict(type='str', required=True),
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
                                                              'compatibility', 'Compatibility'])
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
                    network_uuid=network_uuid,
                    boot_order=vnic_boot_order,
                    mac_address=mac_address
                )
                vnic_payloads.append(vnic_payload)

            network_payload = tacp.ApiCreateOrEditApplicationNetworkOptionsPayload(
                name=vnic_name,
                automatic_mac_assignment=automatic_mac_address,
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

            return instance_params

    def create_instance(instance_params, api_client):
        applicationInstanceResource = tacp_utils.ApplicationInstanceResource(
            api_client)

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
            description=instance_params['description'])

        if module._verbosity >= 3:
            result['api_request_body'] = str(body)
        created_instance_uuid = applicationInstanceResource.create(body)

        result['ansible_module_results'] = applicationInstanceResource.get_by_uuid(
            created_instance_uuid)
        result['changed'] = True

    def instance_power_action(name, api_client, action):
        assert action in [Action.STARTED, Action.SHUTDOWN, Action.STOPPED,
                          Action.RESTARTED, Action.FORCE_RESTARTED,
                          Action.PAUSED, Action.ABSENT, Action.RESUMED]

        applicationInstanceResource = tacp_utils.ApplicationInstanceResource(
            api_client)
        instance_uuid = applicationInstanceResource.get_uuid_by_name(name)

        applicationInstanceResource.power_action_on_instance_by_uuid(
            instance_uuid, action)

        result['changed'] = True

    def powerstate_do_nothing():
        pass

    def powerstate_absent():
        instance_power_action(
            module.params['name'], api_client, Action.ABSENT)

    def powerstate_stop():
        instance_power_action(
            module.params['name'], api_client, Action.STOPPED)

    def powerstate_shutdown():
        instance_power_action(
            module.params['name'], api_client, Action.SHUTDOWN)

    def powerstate_start():
        instance_power_action(
            module.params['name'], api_client, Action.STARTED)

    def powerstate_restart():
        instance_power_action(
            module.params['name'], api_client, Action.RESTARTED)

    def powerstate_force_restart():
        instance_power_action(
            module.params['name'], api_client, Action.FORCE_RESTARTED)

    def powerstate_pause():
        instance_power_action(
            module.params['name'], api_client, Action.PAUSED)

    def powerstate_resume():
        instance_power_action(
            module.params['name'], api_client, Action.RESUMED)

    def powerstate_resume_shutdown():
        instance_power_action(
            module.params['name'], api_client, Action.RESUMED)
        instance_power_action(
            module.params['name'], api_client, Action.SHUTDOWN)

    def powerstate_resume_restart():
        instance_power_action(
            module.params['name'], api_client, Action.RESUMED)
        instance_power_action(
            module.params['name'], api_client, Action.RESTARTED)

    def powerstate_resume_force_restart():
        instance_power_action(
            module.params['name'], api_client, Action.RESUMED)
        instance_power_action(
            module.params['name'], api_client, Action.FORCE_RESTARTED)

    def powerstate_start_pause():
        instance_power_action(
            module.params['name'], api_client, Action.STARTED)
        instance_power_action(
            module.params['name'], api_client, Action.PAUSED)

    # Current state is first dimension
    # Specified state is second dimension
    power_state_dict = {
        (State.RUNNING, Action.STARTED): powerstate_do_nothing,
        (State.RUNNING, Action.SHUTDOWN): powerstate_shutdown,
        (State.RUNNING, Action.STOPPED): powerstate_stop,
        (State.RUNNING, Action.RESTARTED): powerstate_restart,
        (State.RUNNING, Action.FORCE_RESTARTED): powerstate_force_restart,
        (State.RUNNING, Action.PAUSED): powerstate_pause,
        (State.RUNNING, Action.ABSENT): powerstate_absent,
        (State.SHUTDOWN, Action.STARTED): powerstate_start,
        (State.SHUTDOWN, Action.SHUTDOWN): powerstate_do_nothing,
        (State.SHUTDOWN, Action.STOPPED): powerstate_do_nothing,
        (State.SHUTDOWN, Action.RESTARTED): powerstate_start,
        (State.SHUTDOWN, Action.FORCE_RESTARTED): powerstate_start,
        (State.SHUTDOWN, Action.PAUSED): powerstate_start_pause,
        (State.SHUTDOWN, Action.ABSENT): powerstate_absent,
        (State.PAUSED, Action.STARTED): powerstate_resume,
        (State.PAUSED, Action.SHUTDOWN): powerstate_resume_shutdown,
        (State.PAUSED, Action.STOPPED): powerstate_stop,
        (State.PAUSED, Action.RESTARTED): powerstate_resume_restart,
        (State.PAUSED, Action.FORCE_RESTARTED): powerstate_resume_force_restart,
        (State.PAUSED, Action.PAUSED): powerstate_do_nothing,
        (State.PAUSED, Action.ABSENT): powerstate_absent
    }

    # Return the inputs for debugging purposes
    result['args'] = module.params

    # Define configuration
    configuration = tacp.Configuration()
    configuration.host = "https://manage.cp.lenovo.com"
    configuration.api_key_prefix['Authorization'] = 'Bearer'
    configuration.api_key['Authorization'] = module.params['api_key']
    api_client = tacp.ApiClient(configuration)

    applicationInstanceResource = tacp_utils.ApplicationInstanceResource(
        api_client)
    instance_uuid = applicationInstanceResource.get_uuid_by_name(
        module.params['name'])

    desired_state = module.params['state']

    if instance_uuid:
        instance_properties = applicationInstanceResource.get_by_uuid(
            instance_uuid)
        current_state = instance_properties['status']
    else:
        if module.params['state'] == 'absent':
            powerstate_absent()
        else:
            # Application does not exist yet, so create it
            instance_params = generate_instance_params(module)
            create_instance(instance_params, api_client)
            current_state = State.SHUTDOWN

    if current_state in [State.RUNNING, State.SHUTDOWN, State.PAUSED]:
        power_state_dict[(current_state, desired_state)]()

    # AnsibleModule.fail_json() to pass in the message and the result

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
