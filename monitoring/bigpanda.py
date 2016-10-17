#!/usr/bin/python
# -*- coding: utf-8 -*-

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

DOCUMENTATION = '''
---
module: bigpanda
author: "Hagai Kariti (@hkariti)"
short_description: Notify BigPanda about deployments
version_added: "1.8"
description:
   - Notify BigPanda when deployments start and end (successfully or not). Returns a deployment object containing all the parameters for future module calls.
options:
  component:
    description:
      - "The name of the component being deployed. Ex: billing"
    required: true
    alias: name
  version:
    description:
      - The deployment version.
    required: true
  token:
    description:
      - API token.
    required: true
  state:
    description:
      - State of the deployment.
    required: true
    choices: ['started', 'finished', 'failed']
  hosts:
    description:
      - Name of affected host name. Can be a list.
    required: false
    default: machine's hostname
    alias: host
  env:
    description:
      - The environment name, typically 'production', 'staging', etc.
    required: false
  owner:
    description:
      - The person responsible for the deployment.
    required: false
  description:
    description:
      - Free text description of the deployment.
    required: false
  url:
    description:
      - Base URL of the API server.
    required: False
    default: https://api.bigpanda.io
  validate_certs:
    description:
      - If C(no), SSL certificates for the target url will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    required: false
    default: 'yes'
    choices: ['yes', 'no']

# informational: requirements for nodes
requirements: [ ]
'''

EXAMPLES = '''
- bigpanda: component=myapp version=1.3 token={{ bigpanda_token }} state=started
...
- bigpanda: component=myapp version=1.3 token={{ bigpanda_token }} state=finished

If outside servers aren't reachable from your machine, use local_action and override hosts:
- local_action: bigpanda component=myapp version=1.3 token={{ bigpanda_token }} hosts={{ansible_hostname}} state=started
  register: deployment
...
- local_action: bigpanda component=deployment.component version=deployment.version token=deployment.token state=finished
'''

# ===========================================
# Module execution.
#
import socket

def main():

    module = AnsibleModule(
        argument_spec=dict(
            component=dict(required=True, aliases=['name']),
            version=dict(required=True),
            token=dict(required=True, no_log=True),
            state=dict(required=True, choices=['started', 'finished', 'failed']),
            hosts=dict(required=False, default=[socket.gethostname()], aliases=['host']),
            env=dict(required=False),
            owner=dict(required=False),
            description=dict(required=False),
            message=dict(required=False),
            source_system=dict(required=False, default='ansible'),
            validate_certs=dict(default='yes', type='bool'),
            url=dict(required=False, default='https://api.bigpanda.io'),
        ),
        supports_check_mode=True,
        check_invalid_arguments=False,
    )

    token = module.params['token']
    state = module.params['state']
    url = module.params['url']

    # Build the common request body
    body = dict()
    for k in ('component', 'version', 'hosts'):
        v = module.params[k]
        if v is not None:
            body[k] = v

    if not isinstance(body['hosts'], list):
        body['hosts'] = [body['hosts']]

    # Insert state-specific attributes to body
    if state == 'started':
        for k in ('source_system', 'env', 'owner', 'description'):
            v = module.params[k]
            if v is not None:
                body[k] = v

        request_url = url + '/data/events/deployments/start'
    else:
        message = module.params['message']
        if message is not None:
            body['errorMessage'] = message

        if state == 'finished':
            body['status'] = 'success'
        else:
            body['status'] = 'failure'

        request_url = url + '/data/events/deployments/end'

    # Build the deployment object we return
    deployment = dict(token=token, url=url)
    deployment.update(body)
    if 'errorMessage' in deployment:
        message = deployment.pop('errorMessage')
        deployment['message'] = message

    # If we're in check mode, just exit pretending like we succeeded
    if module.check_mode:
        module.exit_json(changed=True, **deployment)

    # Send the data to bigpanda
    data = json.dumps(body)
    headers = {'Authorization':'Bearer %s' % token, 'Content-Type':'application/json'}
    try:
        response, info = fetch_url(module, request_url, data=data, headers=headers)
        if info['status'] == 200:
            module.exit_json(changed=True, **deployment)
        else:
            module.fail_json(msg=json.dumps(info))
    except Exception:
        e = get_exception()
        module.fail_json(msg=str(e))

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.pycompat24 import get_exception
if __name__ == '__main__':
    main()
