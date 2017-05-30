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


def undeploy(deployment, server_groups):
    deployment = "{}".format(deployment)
    server_groups = "{}".format(server_groups)
    remove_from_server = {'operation':'remove', 'address': [{'server-group': server_groups}, {'deployment': deployment}], 'json.pretty':1}
    remove_content = {'operation':'remove', 'address': [{'deployment': deployment}]}
    response = get_response(remove_from_server)
    if response.code is 200:
        return get_response(remove_content)
    else:
        return response

def deploy(deployment, server_groups, src):
    deployment = "{}".format(deployment)
    server_groups = "{}".format(server_groups)
    add_content = {'operation' : 'add', 'address' : [{'deployment': deployment}], 'content' : [{'url' : 'file:'+src+''}], 'json.pretty':1}
    response_add_content = get_response(add_content)
    if response_add_content.code is 200: 
        add_content_server_group = {'operation' : 'add', 'address' : [{'server-group': server_groups}, {'deployment': deployment}], 'content' : [{'url' : 'file:'+src+''}], 'json.pretty':1}
        response_add_content_server_group = get_response(add_content_server_group)
        if response_add_content_server_group.code is 200:
            request_data = {'operation' : 'deploy', 'address' : [{'server-group': server_groups}, {'deployment': deployment}],'json.pretty':1}
            return get_response(request_data)
        else:
            return response_add_content_server_group
    else:
        return response_add_content



def get_response(request_data):
    headers = {'Content-Type':'application/json'}
    response = ""
    try:
        response = open_url(controller_address+'/management',follow_redirects=None, method="POST",headers=headers,url_username=username,url_password=password,force_basic_auth=False, data=json.dumps(request_data))
    except urllib_error.HTTPError as e:
        return e

    return response


def is_deployed(deployment):
    deployment = "{}".format(deployment)
    request_data = {"operation":"read-resource", "address":["deployment", deployment], "json.pretty":1}
    return get_response(request_data)

def deploy_disable(result):
    if result.get('outcome') == 'failed':
        module.exit_json(changed=False, stdout="", stderr="") 
    elif result.get('outcome') == 'success':
        undeploy_result = undeploy(deployment, server_groups)
        if undeploy_result.code is 200:
            module.exit_json(changed=True, stdout="undeployed", stderr="") 
        else:
            module.fail_json(msg="Failed to undeploy", stdout=undeploy_result.read(), stderr=undeploy_result.read())

def deploy_enable(result):
    if result.get('outcome') == 'failed':
        deployment_result = deploy(deployment, server_groups, src)
        if deployment_result.code is 200:
            module.exit_json(changed=True, stdout="deployed", stderr="") 
        else:
            module.fail_json(msg="Failed to deploy", stdout=deployment_result.read(), stderr=deployment_result.read())
    elif result.get('outcome') == 'success':
        undeploy_result = undeploy(deployment, server_groups)
        if undeploy_result.code is 200:
            deployment_result = deploy(deployment, server_groups, src)
            if deployment_result.code is 200:
                module.exit_json(changed=True, stdout="deployed", stderr="") 
            else:
                module.fail_json(msg="Failed to deploy", stdout=deployment_result.read(), stderr=deployment_result.read())
        else:
            module.fail_json(msg="Failed to undeploy", stdout=undeploy_result.read(), stderr=undeploy_result.read())


def main():

    global module, changed, username, password, controller_address, deployment, src, server_groups

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
    
    changed = False

    src = module.params['src']
    deployment = module.params['deployment']
    username = module.params['username']
    password = module.params['password']
    state = module.params['state']
    mode = module.params['mode']
    controller_address = module.params['controller_address']
    server_groups = module.params['server_groups']

    deployed = is_deployed(deployment)
    result = json.loads(deployed.read())

    if state == 'present':
        if 'outcome' in result:
            deploy_enable(result)
    elif state == 'absent':
        if 'outcome' in result:
            deploy_disable(result)      
    else:
        module.fail_json(msg="Missing Configurations", stdout="", stderr="Missing Configurations")
       

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.pycompat24 import get_exception
import json
main()
