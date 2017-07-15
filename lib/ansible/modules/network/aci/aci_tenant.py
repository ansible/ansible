#!/usr/bin/python
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
#

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---

module: aci_tenant
short_description: Direct access to the APIC API
description:
    - Offers direct access to the APIC API
author: Cisco
extends_documentation_fragment: aci
requirements:
    - ACI Fabric 1.0(3f)+
notes:
options:
    tenant_name:
        description:
            - Tenant Name
        required: true
        default: null
        choices: []
        aliases: []
    descr:
        description:
            - Description for the AEP
        required: false
        default: null
        choices: []
        aliases: []
'''

EXAMPLES = '''

    aci_tenant:
       action: "{{ action }}"
       tenant_name: "{{ tenant_name }}"
       descr: "{{ descr }}"
       host: "{{ host }}"
       username: "{{ user }}"
       password: "{{ pass }}"
       protocol: "{{ protocol }}"

'''
RETURN = """
status:
   description: The status code of the http request
   returned: upon making a successful GET, POST or DELETE request to the APIC
   type: int
   sample: 200
response:
   description: Rsponse text returned by APIC
   returned: when a HTTP request has been made to APIC
   type: string
   sample:  "{\"totalCount\":\"0\",\"imdata\":[]}"
changed:
   description: Returns true when changes are made on APIC successfully
   returned: when a HTTP request has been made to APIC and response is received
   type: boolean
   sample: true

"""

import socket
import json
try:
  import requests
  HAS_PYEZ = True
except ImportError:
  HAS_PYEZ = False

def main():

    ''' Ansible module to take all the parameter values from the playbook '''
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(choices=['post', 'get', 'delete']),
            host=dict(required=True),
            username=dict(type='str', default='admin'),
            password=dict(type='str'),
            protocol=dict(choices=['http', 'https'], default='https'),
            tenant_name=dict(type="str"),
            descr=dict(type="str", required=False),
        ),
        supports_check_mode=False
    )

    tenant_name=module.params['tenant_name']
    descr=module.params['descr']
    descr=str(descr)
    
    username = module.params['username']
    password = module.params['password']
    protocol = module.params['protocol']
    host = socket.gethostbyname(module.params['host'])
    action = module.params['action']
    
    post_uri ='api/mo/uni/tn-'+tenant_name+'.json'
    get_uri = 'api/node/class/fvTenant.json'

    ''' Config payload to enable the physical interface '''
    config_data = {"fvTenant":{"attributes":{"name":tenant_name, "descr":descr }}}
    payload_data = json.dumps(config_data)

    ''' authentication || || Throw an error otherwise'''
    apic = '{0}://{1}/'.format(protocol, host)
    auth = dict(aaaUser=dict(attributes=dict(name=username, pwd=password)))
    url=apic+'api/aaaLogin.json'
    authenticate = requests.post(url, data=json.dumps(auth), timeout=2, verify=False)

    if authenticate.status_code != 200:
        module.fail_json(msg='could not authenticate to apic', status=authenticate.status_code, response=authenticate.text)

    ''' Sending the request to APIC '''
    if post_uri.startswith('/'):
        post_uri = post_uri[1:]
    post_url = apic + post_uri

    if get_uri.startswith('/'):
        get_uri = get_uri[1:]
    get_url = apic + get_uri

    if action == 'post':
        req = requests.post(post_url, cookies=authenticate.cookies, data=payload_data, verify=False)
    
    elif action == 'delete':
        req = requests.delete(post_url, cookies=authenticate.cookies, data=payload_data, verify=False)

    elif action == 'get':
        req = requests.get(get_url, cookies=authenticate.cookies, data=payload_data, verify=False)

    ''' Check response status and parse it for status || Throw an error otherwise '''
    response = req.text
    status = req.status_code
    changed = False

    if req.status_code == 200:
        if action == 'post':
            changed = True
        else:
            changed = False

    else:
        module.fail_json(msg='error issuing api request',response=response, status=status)
    
    
    if not HAS_PYEZ:
         module.fail_json(msg='ACI requires you to install requests library')
         changed = False

    results = {}
    results['status'] = status
    results['response'] = response
    results['changed'] = changed
    module.exit_json(**results)


from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()
