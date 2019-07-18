# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2018 Red Hat Inc.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from __future__ import (absolute_import, division, print_function)

import time

from ansible.module_utils.connection import Connection


checkpoint_argument_spec_for_objects = dict(
    auto_publish_session=dict(type='bool'),
    wait_for_task=dict(type='bool', default=True),
    state=dict(type='str', choices=['present', 'absent'], default='present'),
    version=dict(type='str')
)

checkpoint_argument_spec_for_facts = dict(
    version=dict(type='str')
)

checkpoint_argument_spec_for_commands = dict(
    wait_for_task=dict(type='bool', default=True),
    version=dict(type='str')
)


# send the request to checkpoint
def send_request(connection, version, url, payload=None):
    code, response = connection.send_request('/web_api/' + version + url, payload)

    return code, response


# get the payload from the user parameters
def is_checkpoint_param(parameter):
    if parameter == 'auto_publish_session' or\
            parameter == 'state' or\
            parameter == 'wait_for_task' or\
            parameter == 'version':
        return False
    return True


# build the payload from the parameters which has value (not None), and they are parameter of checkpoint API as well
def get_payload_from_parameters(module):
    payload = {}
    for parameter in module.params:
        if module.params[parameter] and is_checkpoint_param(parameter):
            payload[parameter.replace("_", "-")] = module.params[parameter]
    return payload


# wait for task
def wait_for_task(module, version, connection, task_id):
    task_id_payload = {'task-id': task_id}
    task_complete = False
    current_iteration = 0
    max_num_iterations = 300

    # As long as there is a task in progress
    while not task_complete and current_iteration < max_num_iterations:
        current_iteration += 1
        # Check the status of the task
        code, response = send_request(connection, version, 'show-task', task_id_payload)

        attempts_counter = 0
        while code != 200:
            if attempts_counter < 5:
                attempts_counter += 1
                time.sleep(2)
                code, response = send_request(connection, version, 'show-task', task_id_payload)
            else:
                response['message'] = "ERROR: Failed to handle asynchronous tasks as synchronous, tasks result is" \
                                      " undefined.\n" + response['message']
                module.fail_json(msg=response)

        # Count the number of tasks that are not in-progress
        completed_tasks = 0
        for task in response['tasks']:
            if task['status'] == 'failed':
                module.fail_json(msg='Task {0} with task id {1} failed. Look at the logs for more details'
                                 .format(task['task-name'], task['task-id']))
            if task['status'] == 'in progress':
                break
            completed_tasks += 1

        # Are we done? check if all tasks are completed
        if completed_tasks == len(response["tasks"]):
            task_complete = True
        else:
            time.sleep(2)  # Wait for two seconds
    if not task_complete:
        module.fail_json(msg="ERROR: Timeout.\nTask-id: {0}.".format(task_id_payload['task-id']))


# handle publish command, and wait for it to end if the user asked so
def handle_publish(module, connection, version):
    if module.params['auto_publish_session']:
        publish_code, publish_response = send_request(connection, version, 'publish')
        if publish_code != 200:
            module.fail_json(msg=publish_response)
        if module.params['wait_for_task']:
            wait_for_task(module, version, connection, publish_response['task-id'])


# handle a command
def api_command(module, command):
    payload = get_payload_from_parameters(module)
    connection = Connection(module._socket_path)
    # if user insert a specific version, we add it to the url
    version = ('v' + module.params['version'] + '/') if module.params.get('version') else ''

    code, response = send_request(connection, version, command, payload)
    result = {'changed': True}

    if code == 200:
        if module.params['wait_for_task']:
            if 'task-id' in response:
                wait_for_task(module, version, connection, response['task-id'])
            elif 'tasks' in response:
                for task_id in response['tasks']:
                    wait_for_task(module, version, connection, task_id)

        result[command] = response
    else:
        module.fail_json(msg='Checkpoint device returned error {0} with message {1}'.format(code, response))

    return result


# handle api call
def api_call(module, api_call_object):
    payload = get_payload_from_parameters(module)
    connection = Connection(module._socket_path)
    # if user insert a specific version, we add it to the url
    version = ('v' + module.params['version'] + '/') if module.params.get('version') else ''

    payload_for_equals = {'type': api_call_object, 'params': payload}
    equals_code, equals_response = send_request(connection, version, 'equals', payload_for_equals)
    # if code is 400 (bad request) or 500 (internal error) - fail
    if equals_code == 400 or equals_code == 500:
        module.fail_json(msg=equals_response)
    result = {'changed': False}

    if module.params['state'] == 'present':
        if not module.check_mode:
            if equals_code == 200:
                if not equals_response['equals']:
                    code, response = send_request(connection, version, 'set-' + api_call_object, payload)
                    if code != 200:
                        module.fail_json(msg=response)

                    handle_publish(module, connection, version)

                    result['changed'] = True
                    result[api_call_object] = response
                else:
                    # objects are equals and there is no need for set request
                    pass
            elif equals_code == 404:
                code, response = send_request(connection, version, 'add-' + api_call_object, payload)
                if code != 200:
                    module.fail_json(msg=response)

                handle_publish(module, connection, version)

                result['changed'] = True
                result[api_call_object] = response
    elif module.params['state'] == 'absent':
        if not module.check_mode:
            if equals_code == 200:
                code, response = send_request(connection, version, 'delete-' + api_call_object, payload)
                if code != 200:
                    module.fail_json(msg=response)

                handle_publish(module, connection, version)

                result['changed'] = True
            elif equals_code == 404:
                # no need to delete because object dose not exist
                pass

    result['checkpoint_session_uid'] = connection.get_session_uid()
    return result


checkpoint_argument_spec = dict(auto_publish_session=dict(type='bool', default=True),
                                policy_package=dict(type='str', default='standard'),
                                auto_install_policy=dict(type='bool', default=True),
                                targets=dict(type='list')
                                )


def publish(connection, uid=None):
    payload = None

    if uid:
        payload = {'uid': uid}

    connection.send_request('/web_api/publish', payload)


def discard(connection, uid=None):
    payload = None

    if uid:
        payload = {'uid': uid}

    connection.send_request('/web_api/discard', payload)


def install_policy(connection, policy_package, targets):
    payload = {'policy-package': policy_package,
               'targets': targets}

    connection.send_request('/web_api/install-policy', payload)
