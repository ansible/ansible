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
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection


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


def get_api_call_object(connection, api_call_object, unique_payload_for_get):
    code, response = connection.send_request('/web_api/show-' + api_call_object, unique_payload_for_get)

    return code, response


def create_api_call_object(connection, api_call_object, payload):
    code, response = connection.send_request('/web_api/add-' + api_call_object, payload)

    return code, response


def update_api_call_object(connection, api_call_object, payload):
    code, response = connection.send_request('/web_api/set-' + api_call_object, payload)

    return code, response


def delete_api_call_object(connection, api_call_object, payload):
    code, response = connection.send_request('/web_api/delete-' + api_call_object, payload)

    return code, response


def needs_update(payload, api_call_object):
    for key, value in payload.items():
        if value and isinstance(api_call_object[key], str) and value != api_call_object[key]:
            return True
    return False

    # if module.params['source'] and module.params['source'] != api_call_object['source'][0]['name']:
    #     res = True
    # if module.params['destination'] and module.params['destination'] != api_call_object['destination'][0]['name']:
    #     res = True
    # if module.params['action'] != api_call_object['action']['name']:
    #     res = True
    # if module.params['enabled'] != api_call_object['enabled']:
    #     res = True


def api_call_facts(module, api_call_object, payload):
    file_name_plural = "checkpoint_" + api_call_object.replace("_", "-") + "s"
    connection = Connection(module._socket_path)
    code, response = get_api_call_object(connection, api_call_object, payload)
    if code == 200:
        ansible_facts = {}
        ansible_facts.update({file_name_plural: response})
        module.exit_json(ansible_facts=ansible_facts)
    else:
        module.fail_json(msg='Checkpoint device returned error {0} with message {1}'.format(code, response))


def api_call(module, api_call_object, payload, unique_payload_for_get):
    file_name_plural = "checkpoint_" + api_call_object.replace("_", "-") + "s"
    connection = Connection(module._socket_path)
    code, response = get_api_call_object(connection, api_call_object, unique_payload_for_get)
    result = {'changed': False}

    if module.params['state'] == 'present':
        if code == 200:
            if needs_update(payload, response):
                code, response = update_api_call_object(connection, api_call_object, payload)
                if module.params['auto_publish_session']:
                    publish(connection)

                    if module.params['auto_install_policy']:
                        install_policy(connection, module.params['policy_package'], module.params['targets'])

                result['changed'] = True
                result[file_name_plural] = response
            else:
                pass
        elif code == 404:
            code, response = create_api_call_object(connection, api_call_object, payload)

            if module.params['auto_publish_session']:
                publish(connection)

                if module.params['auto_install_policy']:
                    install_policy(connection, module.params['policy_package'], module.params['targets'])

            result['changed'] = True
            result[file_name_plural] = response
    else:
        if code == 200:
            code, response = delete_api_call_object(connection, api_call_object, payload)

            if module.params['auto_publish_session']:
                publish(connection)

                if module.params['auto_install_policy']:
                    install_policy(connection, module.params['policy_package'], module.params['targets'])

            result['changed'] = True
        elif code == 404:
            pass

    result['checkpoint_session_uid'] = connection.get_session_uid()
    module.exit_json(**result)
