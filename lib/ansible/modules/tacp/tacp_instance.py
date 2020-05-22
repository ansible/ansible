#!/usr/bin/python

# Copyright: (c) 2020, Lenovo
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.tacp_ansible import tacp_utils
from ansible.module_utils.tacp_ansible import tacp_exceptions



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
STATE_running = "Running"
STATE_shutdown = "Shut down"
STATE_paused = "Paused"
STATE_restarting = "Restarting"
STATE_resuming = "Resuming"
STATE_creating = "Creating"
STATE_deleting = "Deleting"

ACTION_started = "started"
ACTION_shutdown = "shutdown"
ACTION_stopped = "stopped"
ACTION_restarted = "restarted"
ACTION_force_restarted = "force-restarted"
ACTION_paused = "paused"
ACTION_absent = "absent"

STATE_ACTIONS = [ACTION_started, ACTION_shutdown, ACTION_stopped,
                 ACTION_restarted, ACTION_force_restarted, ACTION_paused,
                 ACTION_absent]


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
                # TODO - his will eventually need to be modified so that any
                # boot order is possible for any extra NICs

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
        api_instance = tacp.ApplicationsApi(api_client)

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
            boot_order=instance_params['boot_order'],
            hardware_assisted_virtualization_enabled=instance_params['vtx_enabled'],
            enable_automatic_recovery=instance_params['auto_recovery_enabled'],
            description=instance_params['description'])

        if module._verbosity >= 3:
            result['api_request_body'] = str(body)
        try:
            # Create an application from a template
            api_response = api_instance.create_application_from_template_using_post(
                body)
            if module._verbosity >= 3:
                result['api_response'] = str(api_response)
        except ApiException as e:
            return "Exception when calling ApplicationsApi->create_application_from_template_using_post: %s\n" % e

        try:
            tacp_utils.wait_for_action_to_complete(
                api_response.action_uuid, api_client)
        except ActionTimedOutException:
            fail_with_reason(
                "Exception when waiting for action to complete, action timed out.")
        except InvalidActionUuidException:
            fail_with_reason(
                "Exception when waiting for action to complete, invalid action UUID.")
        result['ansible_module_results'] = tacp_utils.get_resource_by_uuid(
            api_response.object_uuid, 'application', api_client)
        result['changed'] = True

    def instance_power_action(name, api_client, action):
        instance_uuid = tacp_utils.get_component_fields_by_name(
            module.params['name'], 'application', api_client)
        api_instance = tacp.ApplicationsApi(api_client)

        actions = {"start": api_instance.start_application_using_put,
                   "stop": api_instance.stop_application_using_put,
                   "force-restart": api_instance.force_restart_application_using_put,
                   "restart": api_instance.restart_application_using_put,
                   "shutdown": api_instance.shutdown_application_using_put,
                   "pause": api_instance.pause_application_using_put,
                   "resume": api_instance.resume_application_using_put,
                   "delete": api_instance.delete_application_using_delete}

        try:
            api_response = actions[action](
                instance_uuid)
            if module._verbosity >= 3:
                result['api_response'] = str(api_response)
        except ApiException as e:
            response_dict = tacp_utils.api_response_to_dict(e)
            result['changed'] = False
            result['failed'] = True
            fail_with_reason(response_dict['message'])

        try:
            tacp_utils.wait_for_action_to_complete(
                api_response.action_uuid, api_client)
        except ActionTimedOutException:
            fail_with_reason(
                "Exception when waiting for action to complete, action timed out.")
        except InvalidActionUuidException:
            fail_with_reason(
                "Exception when waiting for action to complete, invalid action UUID.")
        result['changed'] = True

    def powerstate_absent():
        instance_power_action(module.params['name'], api_client, "delete")

    def powerstate_do_nothing():
        pass

    def powerstate_absent():
        instance_power_action(module.params['name'], api_client, "delete")

    def powerstate_stop():
        instance_power_action(module.params['name'], api_client, "stop")

    def powerstate_shutdown():
        instance_power_action(
            module.params['name'], api_client, "shutdown")

    def powerstate_start():
        instance_power_action(
            module.params['name'], api_client, "start")

    def powerstate_restart():
        instance_power_action(
            module.params['name'], api_client, "restart")

    def powerstate_force_restart():
        instance_power_action(
            module.params['name'], api_client, "force-restart")

    def powerstate_pause():
        instance_power_action(
            module.params['name'], api_client, "pause")

    def powerstate_resume():
        instance_power_action(
            module.params['name'], api_client, "resume")

    def powerstate_resume_shutdown():
        instance_power_action(
            module.params['name'], api_client, "resume")
        instance_power_action(
            module.params['name'], api_client, "shutdown")

    def powerstate_resume_restart():
        instance_power_action(
            module.params['name'], api_client, "resume")
        instance_power_action(
            module.params['name'], api_client, "restart")

    def powerstate_resume_force_restart():
        instance_power_action(
            module.params['name'], api_client, "resume")
        instance_power_action(
            module.params['name'], api_client, "force-restart")

    def powerstate_start_pause():
        instance_power_action(
            module.params['name'], api_client, "start")
        instance_power_action(
            module.params['name'], api_client, "pause")

    # Current state is first dimension
    # Specified state is second dimension
    power_state_dict = {
        (STATE_running, ACTION_started): powerstate_do_nothing,
        (STATE_running, ACTION_shutdown): powerstate_shutdown,
        (STATE_running, ACTION_stopped): powerstate_stop,
        (STATE_running, ACTION_restarted): powerstate_restart,
        (STATE_running, ACTION_force_restarted): powerstate_force_restart,
        (STATE_running, ACTION_paused): powerstate_pause,
        (STATE_running, ACTION_absent): powerstate_absent,
        (STATE_shutdown, ACTION_started): powerstate_start,
        (STATE_shutdown, ACTION_shutdown): powerstate_do_nothing,
        (STATE_shutdown, ACTION_stopped): powerstate_do_nothing,
        (STATE_shutdown, ACTION_restarted): powerstate_start,
        (STATE_shutdown, ACTION_force_restarted): powerstate_start,
        (STATE_shutdown, ACTION_paused): powerstate_start_pause,
        (STATE_shutdown, ACTION_absent): powerstate_absent,
        (STATE_paused, ACTION_started): powerstate_resume,
        (STATE_paused, ACTION_shutdown): powerstate_resume_shutdown,
        (STATE_paused, ACTION_stopped): powerstate_stop,
        (STATE_paused, ACTION_restarted): powerstate_resume_restart,
        (STATE_paused, ACTION_force_restarted): powerstate_resume_force_restart,
        (STATE_paused, ACTION_paused): powerstate_do_nothing,
        (STATE_paused, ACTION_absent): powerstate_absent
    }

    # Return the inputs for debugging purposes
    result['args'] = module.params

    # Define configuration
    configuration = tacp.Configuration()
    configuration.host = "https://manage.cp.lenovo.com"
    configuration.api_key_prefix['Authorization'] = 'Bearer'
    configuration.api_key['Authorization'] = module.params['api_key']
    api_client = tacp.ApiClient(configuration)

    instance_uuid = tacp_utils.get_component_fields_by_name(
        module.params['name'], 'application', api_client)
    if instance_uuid:
        instance_is_present = True
    else:
        instance_is_present = False

    desired_state = module.params['state']

    if instance_is_present:
        instance_properties = tacp_utils.get_resource_by_uuid(
            instance_uuid, 'application', api_client)

        current_state = instance_properties['status']

        if current_state in [STATE_running, STATE_shutdown, STATE_paused]:
            power_state_dict[(current_state, desired_state)]()

    else:
        if module.params['state'] != 'absent':
            # Application does not exist yet, so create it
            instance_params = generate_instance_params(module)
            create_instance(instance_params, api_client)
            
            instance_uuid = tacp_utils.get_component_fields_by_name(
                module.params['name'], 'application', api_client)

            instance_properties = tacp_utils.get_resource_by_uuid(
                instance_uuid, 'application', api_client)

            current_state = instance_properties['status']

            power_state_dict[(STATE_shutdown, desired_state)]()
        else:
            powerstate_absent()

    module.exit_json(**result)

    # AnsibleModule.fail_json() to pass in the message and the result

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
