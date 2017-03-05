#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Aditya Cheelangi Sreedharamurthy <aditya.gnu@gmail.com>
#
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
ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.0'
}

DOCUMENTATION = """
module: wildfly
version_added: "2.4"
short_description: Deploy applications to Wildfly.
description:
  - Deploy applications to Wildfly domain and standalone mode.
options:
  deployment:
    required: true
    description:
      - The name of the deployment.
  src:
    required: false
    description:
      - The remote path of the application ear or war to deploy.
  controller_address:
    required: true
    default: http://localhost:9990
    description:
      - The HTTP API management address.
  state:
    required: false
    choices: [ present, absent ]
    default: present
    description:
      - Whether the application should be deployed or undeployed.
  username:
    required: true
    description:
      - The HTTP API management username.
  password:
    required: true
    description:
      - The HTTP API management password.
  mode:
    required: false
    default: domain
    description:
      - Domain mode or standalone mode.
  server_groups:
    required: false
    default: all-relevant-server-groups
    description:
      - Server groups to deploy the war.
author: Aditya Cheelangi Sreedharamurthy
"""

EXAMPLES = """
- name: Deploy an application in domain mode
  wildfly:
    src: /tmp/hello-1.0-SNAPSHOT.war
    deployment: hello.war
    state: present
    controller_address: http://localhost:9990
    username: username
    password: password
    mode: domain
    server_groups: all-relevant-server-groups

- name: Undeploy an application in domain mode
  wildfly:
    deployment: hello.war
    state: absent
    controller_address: http://localhost:9990
    username: username
    password: password
    mode: domain
    server_groups: main-server-group

- name: Deploy an application in standalone mode
  wildfly:
    src: /tmp/hello-1.0-SNAPSHOT.war
    deployment: hello.war
    state: present
    controller_address: http://localhost:9990
    username: username
    password: password
    mode: standalone
"""

RETURN = """
---
state:
  description: State of deployment.
  returned: success
  type: string
  sample: present
name:
  description: Name of the deployed content.
  returned: success
  type: string
  sample: hello.war
"""

HAS_JSON = True

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        HAS_JSON = False

import ansible.module_utils.six.moves.urllib.error as urllib_error
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url, url_argument_spec
from ansible.module_utils.pycompat24 import get_exception


def undeploy(module):
    deployment = module.params['deployment']
    remove_content = {
        'operation': 'remove',
        'address': [
            {'deployment': deployment}
        ],
        'json.pretty': 1,
    }
    mode = module.params['mode']

    if mode == 'domain':
        deployed_domain, info = is_deployed_domain(module)
        if info['status'] == 200:
            server_groups = module.params['server_groups']
            remove_from_server = {
                'operation': 'remove',
                'address': [
                    {'server-group': server_groups},
                    {'deployment': deployment}
                ],
                'json.pretty': 1,
            }
            removed, info = get_response(module, remove_from_server)
            if info['status'] != 200:
                module.fail_json(msg='Undeploy failed.', details=info['msg'])
    return get_response(module, remove_content)


def deploy(module):
    deployment = module.params['deployment']
    server_groups = module.params['server_groups']
    add_content = {
        'operation': 'add',
        'address': [
            {'deployment': deployment}
        ],
        'content': [
            {'url': 'file:' + module.params['src'] + ''}
        ],
        'json.pretty': 1,
    }
    mode = module.params['mode']

    response_add_content, info = get_response(module, add_content)

    if info['status'] == 200:
        if mode == 'domain':
            add_content_server_group = {
                'operation': 'add',
                'address': [
                    {'server-group': server_groups},
                    {'deployment': deployment}
                ],
                'content': [
                    {'url': 'file:' + module.params['src'] + ''}
                ],
                'json.pretty': 1,
            }
            deploy_content_domain = {
                'operation': 'deploy',
                'address': [
                    {'server-group': server_groups},
                    {'deployment': deployment}
                ],
                'json.pretty': 1
            }
            response_add_content_server_group, info = get_response(
                module, add_content_server_group)
            if info['status'] == 200:
                return get_response(module, deploy_content_domain)
            else:
                return response_add_content_server_group, info
        else:
            deploy_content_standalone = {
                'operation': 'deploy',
                'address': [
                    {'deployment': deployment}
                ],
                'json.pretty': 1
            }
            return get_response(module, deploy_content_standalone)
    else:
        module.fail_json(
            msg='Error in wildfly operation.', details=info['msg'])


def get_response(module, request_data):
    headers = {'Content-Type': 'application/json'}
    response = {}
    info = {}
    controller_address = module.params['controller_address']
    try:
        response, info = fetch_url(
            module,
            controller_address + '/management',
            data=json.dumps(request_data),
            headers=headers,
            method='POST',
        )
    except urllib_error.HTTPError:
        e = get_exception()
        module.fail_json(
            msg='Error while performing wildfly operation.', details=e.message)

    return response, info


def is_deployed(module):
    deployment = module.params['deployment']
    request_data = {
        'operation': 'read-resource',
        'address': [
            'deployment', deployment
        ],
        'json.pretty': 1
    }
    return get_response(module, request_data)


def is_deployed_domain(module):
    deployment = module.params['deployment']
    server_groups = module.params['server_groups']
    request_data = {
        'operation': 'read-resource',
        'address': [
            {'server-group': server_groups},
            {'deployment': deployment}
        ],
        'json.pretty': 1
    }
    return get_response(module, request_data)


def deploy_disable(result, module):
    if result.get('outcome') == 'failed':
        return False
    elif result.get('outcome') == 'success':
        if not module.check_mode:
            undeploy_result, info = undeploy(module)
            if info['status'] == 200:
                return True
            else:
                module.fail_json(msg='Undeploy failed.', details=info['msg'])
        else:
            return True


def deploy_enable(result, module):
    if result.get('outcome') == 'failed':
        if not module.check_mode:
            deployment_result, info = deploy(module)
            if info['status'] == 200:
                return True
            else:
                module.fail_json(msg='Deployment failed.', details=info['msg'])
        else:
            return True
    elif result.get('outcome') == 'success':
        if not module.check_mode:
            undeploy_result, info = undeploy(module)
            if info['status'] == 200:
                deployment_result, info = deploy(module)
                if info['status'] == 200:
                    return True
                else:
                    module.fail_json(
                        msg='Deployment failed.', details=info['msg'])
        else:
            return True
    else:
        module.fail_json(msg='Deployment failed.', details=info['msg'])


def main():
    module = AnsibleModule(
        argument_spec=dict(
            src=dict(type='str', required=False),
            deployment=dict(type='str', required=True),
            url_username=dict(required=True, aliases=['username']),
            url_password=dict(
                required=True, aliases=['password'], no_log=True),
            state=dict(choices=['absent', 'present'], default='present'),
            mode=dict(choices=['domain', 'standalone'], default='domain'),
            controller_address=dict(default='localhost:9990'),
            server_groups=dict(
                type='str', default='all-relevant-server-groups'),
        ),
        supports_check_mode=True
    )

    changed = False

    state = module.params['state']
    deployment = module.params['deployment']

    if not HAS_JSON:
        module.fail_json(msg='Cannot import JSON package.')

    deployed, info = is_deployed(module)

    if info['status'] == 200:
        result = json.loads(deployed.read())
    elif info['status'] == 500:
        result = json.loads(info['body'])
    else:
        module.fail_json(msg=info['status'], details=info['msg'])

    if 'outcome' in result:
        if state == 'absent':
            changed = deploy_disable(result, module)
            if changed:
                module.exit_json(
                    changed=changed, state=state, name=deployment)
            else:
                module.exit_json(
                    changed=changed, state=state, name=deployment)
        else:
            changed = deploy_enable(result, module)
            module.exit_json(
                changed=changed, state=state, name=deployment)
    else:
        module.fail_json(msg='Wildfly operation failed.', details=info['body'])

if __name__ == '__main__':
    main()
