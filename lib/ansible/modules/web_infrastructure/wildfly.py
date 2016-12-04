#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Aditya C S <aditya.gnu@gmail.com>
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

DOCUMENTATION = """
module: wildfly
version_added: "1.4"
short_description: deploy applications to Wildfly
description:
  - Deploy applications to Wildfly domain and standalone mode
options:
  deployment:
    required: true
    description:
      - The name of the deployment
  src:
    required: false
    description:
      - The remote path of the application ear or war to deploy
  controller_address:
    required: true
    default: http://localhost:9990
    description:
      - The http api management address
  state:
    required: false
    choices: [ present, absent ]
    default: "present"
    description:
      - Whether the application should be deployed or undeployed
  username:
    required: true
    description:
      - The http api management username
  password:
    required: true
    description:
      - The http api management password
  mode:
    required: false
    default: domain
    description: Domain mode or standalone mode
  server_groups:
    required: false
    default: all-relevant-server-groups
    description: Server groups to deploy the war

notes:
author: "Aditya C S"
"""

EXAMPLES = """
# Deploy a hello world application
- wildfly:
    src: /tmp/hello-1.0-SNAPSHOT.war
    deployment: hello.war
    state: present
    controller_address: http://localhost:9990
    username: username
    password: password
    mode: domain
    server_groups: all-relevant-server-groups
# Undeploy the hello world application
- wildfly:
    deployment: hello.war
    state: absent
    controller_address: http://localhost:9990
    username: username
    password: password
    mode: domain
    server_groups: all-relevant-server-groups
"""

import requests


def undeploy(deployment, server_groups):
    deployment = '"'+deployment+'"'
    server_groups = '"'+server_groups+'"'
    address_remove_from_server = '[{"server-group": ' + server_groups+'}, {"deployment": ' + deployment + '}]'
    address = '[{"deployment": ' + deployment + '}]'
    request_data = '{"operation" : "composite", "address" : [], "steps": [{"operation":"remove", "address": '+address_remove_from_server+'}, {"operation":"remove", "address": '+address+'}], "json.pretty":1}'
    return get_response(request_data)

def deploy(deployment, server_groups, src):
    deployment = '"'+deployment+'"'
    server_groups = '"'+server_groups+'"'
    address_add_content = '[{"deployment": ' + deployment + '}]'
    request_data_add_content = '{"operation" : "add", "address" :'+ address_add_content +', "content" : [{"url" : "file:'+src+'"}], "json.pretty":1}'
    response_add_content = get_response(request_data_add_content)
    if response_add_content.status_code is 200: 
        address = '[{"server-group": ' + server_groups+'}, {"deployment": ' + deployment + '}]'
        request_data_add_content_server_group = '{"operation" : "add", "address" :'+ address +', "content" : [{"url" : "file:'+src+'"}], "json.pretty":1}'
        response_add_content_server_group = get_response(request_data_add_content_server_group)
        if response_add_content_server_group.status_code is 200:
            request_data = '{"operation" : "deploy", "address" :'+ address +',"json.pretty":1}'
            return get_response(request_data)
        else:
            return response_add_content_server_group
    else:
        return response_add_content

def get_response(request_data):
    return requests.post(controller_address+'/management',data=request_data, auth=requests.auth.HTTPDigestAuth(username, password), headers={'Content-Type':'application/json'})

def is_deployed(deployment):
    deployment = '"'+deployment+'"'
    request_data ='{"operation":"read-resource", "address":["deployment",'+deployment+'], "json.pretty":1}'
    return get_response(request_data).json()


def main():
    module = AnsibleModule(
        argument_spec = dict(
            src=dict(),
            deployment=dict(required=True),
            username=dict(required=True),
            password=dict(required=True),
            state=dict(choices=['absent', 'present'], default='present'),
            mode=dict(choices=['domain', 'standalone'], default='domain'),
            controller_address=dict(default='localhost:9990'),
            server_groups=dict(required=True)
        ),
    )
    global username, password, controller_address, deploy_response
    changed = False

    src = module.params['src']
    deployment = module.params['deployment']
    username = module.params['username']
    password = module.params['password']
    state = module.params['state']
    mode = module.params['mode']
    controller_address = module.params['controller_address']
    server_groups = module.params['server_groups']


    if state == 'present' and not src:
        module.fail_json(msg="Argument 'src' required.")

    deployed = is_deployed(deployment)
    
    if state == 'present':
        if deployed.get('outcome') == 'success':
            response = undeploy(deployment, server_groups)
            if response.status_code is 200:
                deploy_response = deploy(deployment, server_groups, src)
                if deploy_response.status_code is 200:
                    changed = True
                else:
                    module.fail_json(msg="Failed to deploy", stdout="", stderr=deploy_response.reason)
        else:
            deploy_response = deploy(deployment, server_groups, src)
            if deploy_response.status_code is 200:
                changed = True
            else:
                module.fail_json(msg="Failed to deploy", stdout="", stderr=deploy_response.reason)

    if state == 'absent':
        if deployed.get('outcome') == 'success':
            response = undeploy(deployment, server_groups)
            changed = True

        module.exit_json(changed=changed, stdout="Undeployed", stderr="") 
       

    module.exit_json(changed=changed, stdout="Deployed", stderr="")

# import module snippets
from ansible.module_utils.basic import *
main()