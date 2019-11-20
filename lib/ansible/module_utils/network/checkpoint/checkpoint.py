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

delete_params = ['name', 'uid', 'layer', 'exception-group-name', 'layer', 'rule-name']


# send the request to checkpoint
def send_request(connection, version, url, payload=None):
    code, response = connection.send_request('/web_api/' + version + url, payload)

    return code, response


# get the payload from the user parameters
def is_checkpoint_param(parameter):
    if parameter == 'auto_publish_session' or \
            parameter == 'state' or \
            parameter == 'wait_for_task' or \
            parameter == 'version':
        return False
    return True


# build the payload from the parameters which has value (not None), and they are parameter of checkpoint API as well
def get_payload_from_parameters(params):
    payload = {}
    for parameter in params:
        parameter_value = params[parameter]
        if parameter_value is not None and is_checkpoint_param(parameter):
            if isinstance(parameter_value, dict):
                payload[parameter.replace("_", "-")] = get_payload_from_parameters(parameter_value)
            elif isinstance(parameter_value, list) and len(parameter_value) != 0 and isinstance(parameter_value[0], dict):
                payload_list = []
                for element_dict in parameter_value:
                    payload_list.append(get_payload_from_parameters(element_dict))
                payload[parameter.replace("_", "-")] = payload_list
            else:
                payload[parameter.replace("_", "-")] = parameter_value
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
    payload = get_payload_from_parameters(module.params)
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


# handle api call facts
def api_call_facts(module, api_call_object, api_call_object_plural_version):
    payload = get_payload_from_parameters(module.params)
    connection = Connection(module._socket_path)
    # if user insert a specific version, we add it to the url
    version = ('v' + module.params['version'] + '/') if module.params['version'] else ''

    # if there is neither name nor uid, the API command will be in plural version (e.g. show-hosts instead of show-host)
    if payload.get("name") is None and payload.get("uid") is None:
        api_call_object = api_call_object_plural_version

    code, response = send_request(connection, version, 'show-' + api_call_object, payload)
    if code != 200:
        module.fail_json(msg='Checkpoint device returned error {0} with message {1}'.format(code, response))

    result = {api_call_object: response}
    return result


# handle api call
def api_call(module, api_call_object):
    payload = get_payload_from_parameters(module.params)
    connection = Connection(module._socket_path)

    result = {'changed': False}
    if module.check_mode:
        return result

    # if user insert a specific version, we add it to the url
    version = ('v' + module.params['version'] + '/') if module.params.get('version') else ''

    payload_for_equals = {'type': api_call_object, 'params': payload}
    equals_code, equals_response = send_request(connection, version, 'equals', payload_for_equals)

    result['checkpoint_session_uid'] = connection.get_session_uid()

    # if code is 400 (bad request) or 500 (internal error) - fail
    if equals_code == 400 or equals_code == 500:
        module.fail_json(msg=equals_response)
    if equals_code == 404 and equals_response['code'] == 'generic_err_command_not_found':
        module.fail_json(msg='Relevant hotfix is not installed on Check Point server. See sk114661 on Check Point Support Center.')

    if module.params['state'] == 'present':
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
        if equals_code == 200:
            payload_for_delete = get_copy_payload_with_some_params(payload, delete_params)
            code, response = send_request(connection, version, 'delete-' + api_call_object, payload_for_delete)
            if code != 200:
                module.fail_json(msg=response)

            handle_publish(module, connection, version)

            result['changed'] = True
        elif equals_code == 404:
            # no need to delete because object dose not exist
            pass

    return result


# get the position in integer format
def get_number_from_position(payload, connection, version):
    if 'position' in payload:
        position = payload['position']
    else:
        return None

    # This code relevant if we will decide to support 'top' and 'bottom' in position

    # position_number = None
    # # if position is not int, convert it to int. There are several cases: "top"
    # if position == 'top':
    #     position_number = 1
    # elif position == 'bottom':
    #     payload_for_show_access_rulebase = {'name': payload['layer'], 'limit': 0}
    #     code, response = send_request(connection, version, 'show-access-rulebase', payload_for_show_access_rulebase)
    #     position_number = response['total']
    # elif isinstance(position, str):
    #     # here position is a number in format str (e.g. "5" and not 5)
    #     position_number = int(position)
    # else:
    #     # here position suppose to be int
    #     position_number = position
    #
    # return position_number

    return int(position)


# is the param position (if the user inserted it) equals between the object and the user input
def is_equals_with_position_param(payload, connection, version, api_call_object):
    position_number = get_number_from_position(payload, connection, version)

    # if there is no position param, then it's equals in vacuous truth
    if position_number is None:
        return True

    payload_for_show_access_rulebase = {'name': payload['layer'], 'offset': position_number - 1, 'limit': 1}
    rulebase_command = 'show-' + api_call_object.split('-')[0] + '-rulebase'

    # if it's threat-exception, we change a little the payload and the command
    if api_call_object == 'threat-exception':
        payload_for_show_access_rulebase['rule-name'] = payload['rule-name']
        rulebase_command = 'show-threat-rule-exception-rulebase'

    code, response = send_request(connection, version, rulebase_command, payload_for_show_access_rulebase)

    # if true, it means there is no rule in the position that the user inserted, so I return false, and when we will try to set
    # the rule, the API server will get throw relevant error
    if response['total'] < position_number:
        return False

    rule = response['rulebase'][0]
    while 'rulebase' in rule:
        rule = rule['rulebase'][0]

    # if the names of the exist rule and the user input rule are equals, then it's means that their positions are equals so I
    # return True. and there is no way that there is another rule with this name cause otherwise the 'equals' command would fail
    if rule['name'] == payload['name']:
        return True
    else:
        return False


# get copy of the payload without some of the params
def get_copy_payload_without_some_params(payload, params_to_remove):
    copy_payload = dict(payload)
    for param in params_to_remove:
        if param in copy_payload:
            del copy_payload[param]
    return copy_payload


# get copy of the payload with only some of the params
def get_copy_payload_with_some_params(payload, params_to_insert):
    copy_payload = {}
    for param in params_to_insert:
        if param in payload:
            copy_payload[param] = payload[param]
    return copy_payload


# is equals with all the params including action and position
def is_equals_with_all_params(payload, connection, version, api_call_object, is_access_rule):
    if is_access_rule and 'action' in payload:
        payload_for_show = get_copy_payload_with_some_params(payload, ['name', 'uid', 'layer'])
        code, response = send_request(connection, version, 'show-' + api_call_object, payload_for_show)
        exist_action = response['action']['name']
        if exist_action != payload['action']:
            return False
    if not is_equals_with_position_param(payload, connection, version, api_call_object):
        return False

    return True


# handle api call for rule
def api_call_for_rule(module, api_call_object):
    is_access_rule = True if 'access' in api_call_object else False
    payload = get_payload_from_parameters(module.params)
    connection = Connection(module._socket_path)

    result = {'changed': False}
    if module.check_mode:
        return result

    # if user insert a specific version, we add it to the url
    version = ('v' + module.params['version'] + '/') if module.params.get('version') else ''

    if is_access_rule:
        copy_payload_without_some_params = get_copy_payload_without_some_params(payload, ['action', 'position'])
    else:
        copy_payload_without_some_params = get_copy_payload_without_some_params(payload, ['position'])
    payload_for_equals = {'type': api_call_object, 'params': copy_payload_without_some_params}
    equals_code, equals_response = send_request(connection, version, 'equals', payload_for_equals)

    result['checkpoint_session_uid'] = connection.get_session_uid()

    # if code is 400 (bad request) or 500 (internal error) - fail
    if equals_code == 400 or equals_code == 500:
        module.fail_json(msg=equals_response)
    if equals_code == 404 and equals_response['code'] == 'generic_err_command_not_found':
        module.fail_json(msg='Relevant hotfix is not installed on Check Point server. See sk114661 on Check Point Support Center.')

    if module.params['state'] == 'present':
        if equals_code == 200:
            if equals_response['equals']:
                if not is_equals_with_all_params(payload, connection, version, api_call_object, is_access_rule):
                    equals_response['equals'] = False
            if not equals_response['equals']:
                # if user insert param 'position' and needed to use the 'set' command, change the param name to 'new-position'
                if 'position' in payload:
                    payload['new-position'] = payload['position']
                    del payload['position']
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
        if equals_code == 200:
            payload_for_delete = get_copy_payload_with_some_params(payload, delete_params)
            code, response = send_request(connection, version, 'delete-' + api_call_object, payload_for_delete)
            if code != 200:
                module.fail_json(msg=response)

            handle_publish(module, connection, version)

            result['changed'] = True
        elif equals_code == 404:
            # no need to delete because object dose not exist
            pass

    return result


# handle api call facts for rule
def api_call_facts_for_rule(module, api_call_object, api_call_object_plural_version):
    payload = get_payload_from_parameters(module.params)
    connection = Connection(module._socket_path)
    # if user insert a specific version, we add it to the url
    version = ('v' + module.params['version'] + '/') if module.params['version'] else ''

    # if there is neither name nor uid, the API command will be in plural version (e.g. show-hosts instead of show-host)
    if payload.get("layer") is None:
        api_call_object = api_call_object_plural_version

    code, response = send_request(connection, version, 'show-' + api_call_object, payload)
    if code != 200:
        module.fail_json(msg='Checkpoint device returned error {0} with message {1}'.format(code, response))

    result = {api_call_object: response}
    return result


# The code from here till EOF will be deprecated when Rikis' modules will be deprecated
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
