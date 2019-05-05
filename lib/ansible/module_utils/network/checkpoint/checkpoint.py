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
from ansible.module_utils.connection import Connection


checkpoint_argument_spec = dict(
    name=dict(type='str'),
    uid=dict(type='str'),
    tags=dict(type='list'),
    color=dict(type='str', choices=['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green',
                                    'khaki', 'orchid', 'dark orange', 'dark sea green', 'pink', 'turquoise',
                                    'dark blue', 'firebrick', 'brown', 'forest green', 'gold', 'dark gold', 'gray',
                                    'dark gray', 'light green', 'lemon chiffon', 'coral', 'sea green', 'sky blue',
                                    'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange',
                                    'red', 'sienna', 'yellow']),
    comments=dict(type='str'),
    details_level=dict(type='str', choices=['uid', 'standard', 'full']),
    groups=dict(type='list'),
    ignore_warnings=dict(type='bool'),
    ignore_errors=dict(type='bool'),
    new_name=dict(type='str'),
    auto_publish_session=dict(type='bool'),
    state=dict(type='str', required=True, choices=['present', 'absent'])
)

checkpoint_argument_spec_for_facts = dict(
    name=dict(type='str'),
    uid=dict(type='str'),
    details_level=dict(type='str', choices=['uid', 'standard', 'full']),
    limit=dict(type='int'),
    offset=dict(type='int'),
    order=dict(type='list'),
    show_membership=dict(type='bool')
)


# publish the session
def publish(connection, uid=None):
    payload = None

    if uid:
        payload = {'uid': uid}

    connection.send_request('/web_api/publish', payload)


# discard changes of session
def discard(connection, uid=None):
    payload = None

    if uid:
        payload = {'uid': uid}

    connection.send_request('/web_api/discard', payload)


# get the object from checkpoint DB, if exist
def get_api_call_object(connection, api_call_object, payload):
    code, response = connection.send_request('/web_api/show-' + api_call_object, payload)

    return code, response


# add object to checkpoint DB
def add_api_call_object(connection, api_call_object, payload):
    code, response = connection.send_request('/web_api/add-' + api_call_object, payload)

    return code, response


# set object in checkpoint DB
def set_api_call_object(connection, api_call_object, payload):
    code, response = connection.send_request('/web_api/set-' + api_call_object, payload)

    return code, response


# delete object from checkpoint DB
def delete_api_call_object(connection, api_call_object, payload):
    code, response = connection.send_request('/web_api/delete-' + api_call_object, payload)

    return code, response


# check if the object the user inserted is equals to the object in the checkpoint DB
def equals(connection, api_call_object, payload):
    payloadForEquals = {'type': api_call_object, 'params': payload}
    code, response = connection.send_request('/web_api/equals', payloadForEquals)

    return code, response


# run the api command
def run_api_command(connection, command, payload):
    code, response = connection.send_request('/web_api/' + command, payload)

    return code, response


# get the payload from the user parameters
def get_payload_from_user_parameters(module, user_parameters):
    payload = {}
    for parameter in user_parameters:
        if module.params[parameter]:
            payload[parameter.replace("_", "-")] = module.params[parameter]
    return payload


# handle a command
def api_command(module, command, user_parameters):
    payload = get_payload_from_user_parameters(module, user_parameters)
    connection = Connection(module._socket_path)
    code, response = run_api_command(connection, command, payload)
    result = {'changed': True}

    if code == 200:
        result['checkpoint_' + command.replace("-", "_")] = response
    else:
        module.fail_json(msg='Checkpoint device returned error {0} with message {1}'.format(code, response))

    module.exit_json(**result)


# handle api call facts
def api_call_facts(module, api_call_object, user_parameters):
    payload = get_payload_from_user_parameters(module, user_parameters)

    # if there is neither name nor uid, the API command will be in plural version (e.g. show-hosts instead of show-host)
    if payload.get("name") is None and payload.get("uid") is None:
        api_call_object += "s"
    connection = Connection(module._socket_path)
    code, response = get_api_call_object(connection, api_call_object, payload)
    if code == 200:
        module.exit_json(ansible_facts={api_call_object: response})
    else:
        module.fail_json(msg='Checkpoint device returned error {0} with message {1}'.format(code, response))


# handle api call
def api_call(module, api_call_object, user_parameters):
    payload = get_payload_from_user_parameters(module, user_parameters)
    connection = Connection(module._socket_path)
    code, response = equals(connection, api_call_object, payload)
    # if code is 400 (bad request) or 500 (internal error) - fail
    if code == 400 or code == 500:
        module.fail_json(msg=response)
    result = {'changed': False}

    if module.params['state'] == 'present':
        if code == 200:
            if not response['equals']:
                code, response = set_api_call_object(connection, api_call_object, payload)
                if code != 200:
                    module.fail_json(msg=response)

                if module.params['auto_publish_session']:
                    publish(connection)

                result['changed'] = True
                result[api_call_object] = response
            else:
                # objects are equals and there is no need for set request
                pass
        elif code == 404:
            code, response = add_api_call_object(connection, api_call_object, payload)
            if code != 200:
                module.fail_json(msg=response)

            if module.params['auto_publish_session']:
                publish(connection)

            result['changed'] = True
            result[api_call_object] = response
    else:
        if code == 200:
            code, response = delete_api_call_object(connection, api_call_object, payload)
            if code != 200:
                module.fail_json(msg=response)

            if module.params['auto_publish_session']:
                publish(connection)

            result['changed'] = True
        elif code == 404:
            # no need to delete because object dose not exist
            pass

    result['checkpoint_session_uid'] = connection.get_session_uid()
    module.exit_json(**result)
