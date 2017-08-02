#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: cv_server_provision
version_added: "2.4"
author: "EOS+ CS (ansible-dev@arista.com) (@mharista)"
short_description:
    Provision server port by applying or removing template configuration to an
    Arista CloudVision Portal configlet that is applied to a switch.
description:
  - This module allows a server team to provision server network ports for
    new servers without having to access Arista CVP or asking the network team
    to do it for them. Provide the information for connecting to CVP, switch
    rack, port the new server is connected to, optional vlan, and an action
    and the module will apply the configuration to the switch port via CVP.
    Actions are add (applies template config to port),
    remove (defaults the interface config) and
    show (returns the current port config).
options:
  host:
    description:
      - The hostname or IP address of the CVP node being connected to.
    required: true
  port:
    description:
      - The port number to use when making API calls to the CVP node. This
        will default to the default port for the specified protocol. Port 80
        for http and port 443 for https.
    default: None
  protocol:
    description:
      - The protocol to use when making API calls to CVP. CVP defaults to https
        and newer versions of CVP no longer support http.
    default: https
    choices: [https, http]
  username:
    description:
      - The user that will be used to connect to CVP for making API calls.
    required: true
  password:
    description:
      - The password of the user that will be used to connect to CVP for API
        calls.
    required: true
  server_name:
    description:
      - The hostname or identifier for the server that is having it's switch
        port provisioned.
    required: true
  switch_name:
    description:
      - The hostname of the switch is being configured for the server being
        provisioned.
    required: true
  switch_port:
    description:
      - The physical port number on the switch that the new server is
        connected to.
    required: true
  port_vlan:
    description:
      - The vlan that should be applied to the port for this server.
        This parameter is dependent on a proper template that supports single
        vlan provisioning with it. If a port vlan is specified by the template
        specified does not support this the module will exit out with no
        changes. If a template is specified that requires a port vlan but no
        port vlan is specified the module will exit out with no changes.
    default: None
  template:
    description:
      - A path to a Jinja formatted template file that contains the
        configuration block that will be applied to the specified switch port.
        This template will have variable fields replaced by the module before
        being applied to the switch configuration.
    required: true
  action:
    description:
      - The action for the module to take. The actions are add, which applies
        the specified template config to port, remove, which defaults the
        specified interface configuration, and show, which will return the
        current port configuration with no changes.
    default: show
    choices: [show, add, remove]
  auto_run:
    description:
      - Flag that determines whether or not the module will execute the CVP
        task spawned as a result of changes to a switch configlet. When an
        add or remove action is taken which results in a change to a switch
        configlet, CVP will spawn a task that needs to be executed for the
        configuration to be applied to the switch. If this option is True then
        the module will determined the task number created by the configuration
        change, execute it and wait for the task to complete. If the option
        is False then the task will remain in the Pending state in CVP for
        a network administrator to review and execute.
    default: False
    type: bool
notes:
requirements: [Jinja2, cvprac >= 0.7.0]
'''

EXAMPLES = '''
- name: Get current configuration for interface Ethernet2
  cv_server_provision:
    host: cvp_node
    username: cvp_user
    password: cvp_pass
    protocol: https
    server_name: new_server
    switch_name: eos_switch_1
    switch_port: 2
    template: template_file.j2
    action: show

- name: Remove existing configuration from interface Ethernet2. Run task.
  cv_server_provision:
    host: cvp_node
    username: cvp_user
    password: cvp_pass
    protocol: https
    server_name: new_server
    switch_name: eos_switch_1
    switch_port: 2
    template: template_file.j2
    action: remove
    auto_run: True

- name: Add template configuration to interface Ethernet2. No VLAN. Run task.
  cv_server_provision:
    host: cvp_node
    username: cvp_user
    password: cvp_pass
    protocol: https
    server_name: new_server
    switch_name: eos_switch_1
    switch_port: 2
    template: single_attached_trunk.j2
    action: add
    auto_run: True

- name: Add template with VLAN configuration to interface Ethernet2. Run task.
  cv_server_provision:
    host: cvp_node
    username: cvp_user
    password: cvp_pass
    protocol: https
    server_name: new_server
    switch_name: eos_switch_1
    switch_port: 2
    port_vlan: 22
    template: single_attached_vlan.j2
    action: add
    auto_run: True
'''

RETURN = '''
changed:
  description: Signifies if a change was made to the configlet
  returned: success
  type: bool
  sample: true
currentConfigBlock:
  description: The current config block for the user specified interface
  returned: when action = show
  type: string
  sample: |
    interface Ethernet4
    !
newConfigBlock:
  description: The new config block for the user specified interface
  returned: when action = add or remove
  type: string
  sample: |
    interface Ethernet3
        description example
        no switchport
    !
oldConfigBlock:
  description: The current config block for the user specified interface
               before any changes are made
  returned: when action = add or remove
  type: string
  sample: |
    interface Ethernet3
    !
fullConfig:
  description: The full config of the configlet after being updated
  returned: when action = add or remove
  type: string
  sample: |
    !
    interface Ethernet3
    !
    interface Ethernet4
    !
updateConfigletResponse:
  description: Response returned from CVP when configlet update is triggered
  returned: when action = add or remove and configuration changes
  type: string
  sample: "Configlet veos1-server successfully updated and task initiated."
portConfigurable:
  description: Signifies if the user specified port has an entry in the
               configlet that Ansible has access to
  returned: success
  type: bool
  sample: true
switchConfigurable:
  description: Signifies if the user specified switch has a configlet
               applied to it that CVP is allowed to edit
  returned: success
  type: bool
  sample: true
switchInfo:
  description: Information from CVP describing the switch being configured
  returned: success
  type: dictionary
  sample: {"architecture": "i386",
           "bootupTimeStamp": 1491264298.21,
           "complianceCode": "0000",
           "complianceIndication": "NONE",
           "deviceInfo": "Registered",
           "deviceStatus": "Registered",
           "fqdn": "veos1",
           "hardwareRevision": "",
           "internalBuildId": "12-12",
           "internalVersion": "4.17.1F-11111.4171F",
           "ipAddress": "192.168.1.20",
           "isDANZEnabled": "no",
           "isMLAGEnabled": "no",
           "key": "00:50:56:5d:e5:e0",
           "lastSyncUp": 1496432895799,
           "memFree": 472976,
           "memTotal": 1893460,
           "modelName": "vEOS",
           "parentContainerId": "container_13_5776759195930",
           "serialNumber": "",
           "systemMacAddress": "00:50:56:5d:e5:e0",
           "taskIdList": [],
           "tempAction": null,
           "type": "netelement",
           "unAuthorized": false,
           "version": "4.17.1F",
           "ztpMode": "false"}
taskCompleted:
  description: Signifies if the task created and executed has completed successfully
  returned: when action = add or remove, and auto_run = true,
            and configuration changes
  type: bool
  sample: true
taskCreated:
  description: Signifies if a task was created due to configlet changes
  returned: when action = add or remove, and auto_run = true or false,
            and configuration changes
  type: bool
  sample: true
taskExecuted:
  description: Signifies if the automation executed the spawned task
  returned: when action = add or remove, and auto_run = true,
            and configuration changes
  type: bool
  sample: true
taskId:
  description: The task ID created by CVP because of changes to configlet
  returned: when action = add or remove, and auto_run = true or false,
            and configuration changes
  type: string
  sample: "500"
'''

import re
import time
from ansible.module_utils.basic import AnsibleModule
try:
    import jinja2
    from jinja2 import meta
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False
try:
    from cvprac.cvp_client import CvpClient
    from cvprac.cvp_client_errors import CvpLoginError, CvpApiError
    HAS_CVPRAC = True
except ImportError:
    HAS_CVPRAC = False


def connect(module):
    ''' Connects to CVP device using user provided credentials from playbook.

    :param module: Ansible module with parameters and client connection.
    :return: CvpClient object with connection instantiated.
    '''
    client = CvpClient()
    try:
        client.connect([module.params['host']],
                       module.params['username'],
                       module.params['password'],
                       protocol=module.params['protocol'],
                       port=module.params['port'])
    except CvpLoginError as e:
        module.fail_json(msg=str(e))
    return client


def switch_info(module):
    ''' Get dictionary of switch info from CVP.

    :param module: Ansible module with parameters and client connection.
    :return: Dict of switch info from CVP or exit with failure if no
             info for device is found.
    '''
    switch_name = module.params['switch_name']
    switch_info = module.client.api.get_device_by_name(switch_name)
    if not switch_info:
        module.fail_json(msg=str("Device with name '%s' does not exist."
                                 % switch_name))
    return switch_info


def switch_in_compliance(module, sw_info):
    ''' Check if switch is currently in compliance.

    :param module: Ansible module with parameters and client connection.
    :param sw_info: Dict of switch info.
    :return: Nothing or exit with failure if device is not in compliance.
    '''
    compliance = module.client.api.check_compliance(sw_info['key'],
                                                    sw_info['type'])
    if compliance['complianceCode'] != '0000':
        module.fail_json(msg=str('Switch %s is not in compliance. Returned'
                                 ' compliance code %s.'
                                 % (sw_info['fqdn'],
                                    compliance['complianceCode'])))


def server_configurable_configlet(module, sw_info):
    ''' Check CVP that the user specified switch has a configlet assigned to
        it that Ansible is allowed to edit.

    :param module: Ansible module with parameters and client connection.
    :param sw_info: Dict of switch info.
    :return: Dict of configlet information or None.
    '''
    configurable_configlet = None
    configlet_name = module.params['switch_name'] + '-server'
    switch_configlets = module.client.api.get_configlets_by_device_id(
        sw_info['key'])
    for configlet in switch_configlets:
        if configlet['name'] == configlet_name:
            configurable_configlet = configlet
    return configurable_configlet


def port_configurable(module, configlet):
    ''' Check configlet if the user specified port has a configuration entry
        in the configlet to determine if Ansible is allowed to configure the
        port on this switch.

    :param module: Ansible module with parameters and client connection.
    :param configlet: Dict of configlet info.
    :return: True or False.
    '''
    configurable = False
    regex = r'^interface Ethernet%s' % module.params['switch_port']
    for config_line in configlet['config'].split('\n'):
        if re.match(regex, config_line):
            configurable = True
    return configurable


def configlet_action(module, configlet):
    ''' Take appropriate action based on current state of device and user
        requested action.

        Return current config block for specified port if action is show.

        If action is add or remove make the appropriate changes to the
        configlet and return the associated information.

    :param module: Ansible module with parameters and client connection.
    :param configlet: Dict of configlet info.
    :return: Dict of information to updated results with.
    '''
    result = dict()
    existing_config = current_config(module, configlet['config'])
    if module.params['action'] == 'show':
        result['currentConfigBlock'] = existing_config
        return result
    elif module.params['action'] == 'add':
        result['newConfigBlock'] = config_from_template(module)
    elif module.params['action'] == 'remove':
        result['newConfigBlock'] = ('interface Ethernet%s\n!'
                                    % module.params['switch_port'])
    result['oldConfigBlock'] = existing_config
    result['fullConfig'] = updated_configlet_content(module,
                                                     configlet['config'],
                                                     result['newConfigBlock'])
    resp = module.client.api.update_configlet(result['fullConfig'],
                                              configlet['key'],
                                              configlet['name'])
    if 'data' in resp:
        result['updateConfigletResponse'] = resp['data']
        if 'task' in resp['data']:
            result['changed'] = True
            result['taskCreated'] = True
    return result


def current_config(module, config):
    ''' Parse the full port configuration for the user specified port out of
        the full configlet configuration and return as a string.

    :param module: Ansible module with parameters and client connection.
    :param config: Full config to parse specific port config from.
    :return: String of current config block for user specified port.
    '''
    regex = r'^interface Ethernet%s' % module.params['switch_port']
    match = re.search(regex, config, re.M)
    if not match:
        module.fail_json(msg=str('interface section not found - %s'
                                 % config))
    block_start, line_end = match.regs[0]

    match = re.search(r'!', config[line_end:], re.M)
    if not match:
        return config[block_start:]
    _, block_end = match.regs[0]

    block_end = line_end + block_end
    return config[block_start:block_end]


def valid_template(port, template):
    ''' Test if the user provided Jinja template is valid.

    :param port: User specified port.
    :param template: Contents of Jinja template.
    :return: True or False
    '''
    valid = True
    regex = r'^interface Ethernet%s' % port
    match = re.match(regex, template, re.M)
    if not match:
        valid = False
    return valid


def config_from_template(module):
    ''' Load the Jinja template and apply user provided parameters in necessary
        places. Fail if template is not found. Fail if rendered template does
        not reference the correct port. Fail if the template requires a VLAN
        but the user did not provide one with the port_vlan parameter.

    :param module: Ansible module with parameters and client connection.
    :return: String of Jinja template rendered with parameters or exit with
             failure.
    '''
    template_loader = jinja2.FileSystemLoader('./templates')
    env = jinja2.Environment(loader=template_loader,
                             undefined=jinja2.DebugUndefined)
    template = env.get_template(module.params['template'])
    if not template:
        module.fail_json(msg=str('Could not find template - %s'
                                 % module.params['template']))

    data = {'switch_port': module.params['switch_port'],
            'server_name': module.params['server_name']}

    temp_source = env.loader.get_source(env, module.params['template'])[0]
    parsed_content = env.parse(temp_source)
    temp_vars = list(meta.find_undeclared_variables(parsed_content))
    if 'port_vlan' in temp_vars:
        if module.params['port_vlan']:
            data['port_vlan'] = module.params['port_vlan']
        else:
            module.fail_json(msg=str('Template %s requires a vlan. Please'
                                     ' re-run with vlan number provided.'
                                     % module.params['template']))

    template = template.render(data)
    if not valid_template(module.params['switch_port'], template):
        module.fail_json(msg=str('Template content does not configure proper'
                                 ' interface - %s' % template))
    return template


def updated_configlet_content(module, existing_config, new_config):
    ''' Update the configlet configuration with the new section for the port
        specified by the user.

    :param module: Ansible module with parameters and client connection.
    :param existing_config: String of current configlet configuration.
    :param new_config: String of configuration for user specified port to
                       replace in the existing config.
    :return: String of the full updated configuration.
    '''
    regex = r'^interface Ethernet%s' % module.params['switch_port']
    match = re.search(regex, existing_config, re.M)
    if not match:
        module.fail_json(msg=str('interface section not found - %s'
                                 % existing_config))
    block_start, line_end = match.regs[0]

    updated_config = existing_config[:block_start] + new_config
    match = re.search(r'!\n', existing_config[line_end:], re.M)
    if match:
        _, block_end = match.regs[0]
        block_end = line_end + block_end
        updated_config += '\n%s' % existing_config[block_end:]
    return updated_config


def configlet_update_task(module):
    ''' Poll device info of switch from CVP up to three times to see if the
        configlet updates have spawned a task. It sometimes takes a second for
        the task to be spawned after configlet updates. If a task is found
        return the task ID. Otherwise return None.

    :param module: Ansible module with parameters and client connection.
    :return: Task ID or None.
    '''
    for num in range(3):
        device_info = switch_info(module)
        if (('taskIdList' in device_info) and
                (len(device_info['taskIdList']) > 0)):
            for task in device_info['taskIdList']:
                if ('Configlet Assign' in task['description'] and
                        task['data']['WORKFLOW_ACTION'] == 'Configlet Push'):
                    return task['workOrderId']
        time.sleep(1)
    return None


def wait_for_task_completion(module, task):
    ''' Poll CVP for the executed task to complete. There is currently no
        timeout. Exits with failure if task status is Failed or Cancelled.

    :param module: Ansible module with parameters and client connection.
    :param task: Task ID to poll for completion.
    :return: True or exit with failure if task is cancelled or fails.
    '''
    task_complete = False
    while not task_complete:
        task_info = module.client.api.get_task_by_id(task)
        task_status = task_info['workOrderUserDefinedStatus']
        if task_status == 'Completed':
            return True
        elif task_status in ['Failed', 'Cancelled']:
            module.fail_json(msg=str('Task %s has reported status %s. Please'
                                     ' consult the CVP admins for more'
                                     ' information.' % (task, task_status)))
        time.sleep(2)


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        host=dict(required=True),
        port=dict(required=False, default=None),
        protocol=dict(default='https', choices=['http', 'https']),
        username=dict(required=True),
        password=dict(required=True, no_log=True),
        server_name=dict(required=True),
        switch_name=dict(required=True),
        switch_port=dict(required=True),
        port_vlan=dict(required=False, default=None),
        template=dict(require=True),
        action=dict(default='show', choices=['show', 'add', 'remove']),
        auto_run=dict(type='bool', default=False))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)
    if not HAS_JINJA2:
        module.fail_json(msg='The Jinja2 python module is required.')
    if not HAS_CVPRAC:
        module.fail_json(msg='The cvprac python module is required.')
    result = dict(changed=False)
    module.client = connect(module)

    try:
        result['switchInfo'] = switch_info(module)
        if module.params['action'] in ['add', 'remove']:
            switch_in_compliance(module, result['switchInfo'])
        switch_configlet = server_configurable_configlet(module,
                                                         result['switchInfo'])
        if not switch_configlet:
            module.fail_json(msg=str('Switch %s has no configurable server'
                                     ' ports.' % module.params['switch_name']))
        result['switchConfigurable'] = True
        if not port_configurable(module, switch_configlet):
            module.fail_json(msg=str('Port %s is not configurable as a server'
                                     ' port on switch %s.'
                                     % (module.params['switch_port'],
                                        module.params['switch_name'])))
        result['portConfigurable'] = True
        result['taskCreated'] = False
        result['taskExecuted'] = False
        result['taskCompleted'] = False
        result.update(configlet_action(module, switch_configlet))
        if module.params['auto_run'] and module.params['action'] != 'show':
            task_id = configlet_update_task(module)
            if task_id:
                result['taskId'] = task_id
                note = ('Update config on %s with %s action from Ansible.'
                        % (module.params['switch_name'],
                           module.params['action']))
                module.client.api.add_note_to_task(task_id, note)
                module.client.api.execute_task(task_id)
                result['taskExecuted'] = True
                task_completed = wait_for_task_completion(module, task_id)
                if task_completed:
                    result['taskCompleted'] = True
            else:
                result['taskCreated'] = False
    except CvpApiError as e:
        module.fail_json(msg=str(e))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
