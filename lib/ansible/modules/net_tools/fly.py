#!/usr/bin/python
# Copyright (c) 2017 AndyPi.co.uk
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fly

short_description: Fly.io API integration

description:
    - "Create hostnames, link backends and add rules using Fly.io API"
    
version_added: "1.0"

author:
    - Andy Wilson (@andypitech)
'''

EXAMPLES = '''
# Add new hostname
- name: Create a fly hostname
  fly:
    command: create_hostname
    fly_auth_key: "{{ fly_auth_key }}"
    site: "example-com"
    hostname: "example.com"
# View hostname information
- name: View a fly hostname
  fly:
    command: view_hostname
    fly_auth_key: "{{ fly_auth_key }}"
    site: "example-com"
    hostname: "example.com"
  register: results
- name: Show fly hostname info
  debug:
    msg: '{{ results.attributes }}'
# Add new backend
  - name: Add a fly backend (s3 bucket)
    fly:
      command: add_backend
      fly_auth_key: "{{ fly_auth_key }}"
      site: "example-com"
      backend_name: "s3-1"
      backend_type: "aws_s3"
      backend_settings: 
        bucket: "my_bucket"
        region: "eu-west-1"
      register: result
  - name: Show backend info
    debug:
      msg: '{{ result.id }}'
# Add new rule
  - name: Add a fly rule
    fly:
      command: add_rule
      fly_auth_key: "{{ fly_auth_key }}"
      site: "example-com"
      hostname: "example.com"
      backend_id: '{{ result.id }}'
      action_type: "rewrite"
      path: "/" # incoming path
      priority: "10"
      path_replacement: "/index.html" # rewrite to this path on the backend

'''

RETURN = '''
create_hostname:
    description: create fly hostname
    returned: changed
    type: json
    sample: {"changed": true, "failed": false, "response": {"dns_configured": false, "hostname": "example.com", "preview_hostname": "xyz.shw.io"}
view_hostname:
    description: view a specific fly hostname
    returned: success
    type: json
    sample: {"changed": false, "failed": false, "response": {"dns_configured": false, "hostname": "example.com", "preview_hostname": "xyz.shw.io"}}
add_backend:
    description: add a fly backend
    returned: changed
    type: json
    sample: {"changed": true, "failed": false, "id": "123123123"}
add_rule:   
    description: add a fly rule
    returned: changed
    type: json
    sample: {"changed": true, "failed": false, "response": {"data": {"attributes": {"action_type": "rewrite", "backend_id": "123123123", "hostname": "example.com", "http_header_key": "", "http_header_value_regex": "", "match_scheme": null, "path": "/", "path_replacement": "/index.html", "priority": 10, "redirect_url": null}, "id": "456456456", "type": "rules"}}}
'''


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *


api_endpoint = 'https://fly.io/api/v1/sites/'

class Fly(object):
    def __init__(self, module):
        self.module = module

    def get_key_or_fail(self, k):
        v = self.module.params[k]
        if v is None:
            self.module.fail_json(msg='Unable to load %s' % k)
        return v
        
    def hostname_add(self):  
        fly_auth_key = self.get_key_or_fail('fly_auth_key')
        site = self.get_key_or_fail('site')
        hostname = self.get_key_or_fail('hostname')
        url = api_endpoint + site + '/hostnames'
        payload={"data": { "attributes": { "hostname": hostname } } }
        headers = {'Content-Type':'application/json', 'Authorization': 'Bearer %s' %fly_auth_key}
        resp = open_url(url,method="POST",headers=headers,validate_certs=False,data=json.dumps(payload))
        try:
            resp_json = json.loads(to_text(resp.read(), errors='surrogate_then_strict'))
            self.module.exit_json(changed=True, response = resp_json['data']['attributes'])
        except (json.JSONDecodeError, UnicodeError) as e:
            error_msg += "; Failed to parse API response with error {0}: {1}".format(to_native(e), content)
            self.module.fail_json(msg=error_msg)

        
    def hostname_view(self): 
        fly_auth_key = self.get_key_or_fail('fly_auth_key')
        site = self.get_key_or_fail('site')
        hostname = self.get_key_or_fail('hostname')
        url = api_endpoint + site + '/hostnames/' + hostname
        headers = {'Content-Type':'application/json', 'Authorization': 'Bearer %s' %fly_auth_key}
        try: 
            resp = open_url(url,method="GET",headers=headers,validate_certs=False)
            try:
                resp_json = json.loads(to_text(resp.read(), errors='surrogate_then_strict'))
                self.module.exit_json(changed=True, response = resp_json['data']['attributes'])
            except (json.JSONDecodeError, UnicodeError) as e:
                error_msg += "; Failed to parse API response with error {0}: {1}".format(to_native(e), content)
                self.module.fail_json(msg=error_msg)
        except:
            return False

    def backend_add(self):
        fly_auth_key = self.get_key_or_fail('fly_auth_key')
        site = self.get_key_or_fail('site')
        backend_name = self.get_key_or_fail('backend_name')
        backend_type = self.get_key_or_fail('backend_type')
        backend_settings = self.get_key_or_fail('backend_settings')
        
        url = api_endpoint + site + '/backends'
        headers = {'Content-Type':'application/json', 'Authorization': 'Bearer %s' %fly_auth_key}
        # is this correct way to add settings?
        payload = {"data": { "attributes": { "name": backend_name,
                                             "type": backend_type,
                                             "settings": backend_settings
                    } } }
                    
        resp = open_url(url,method="POST",headers=headers,validate_certs=False,data=json.dumps(payload))
        try:
            resp_json = json.loads(to_text(resp.read(), errors='surrogate_then_strict'))
            self.module.exit_json(changed=True, id = resp_json['data']['id'])
        except (json.JSONDecodeError, UnicodeError) as e:
            error_msg += "; Failed to parse API response with error {0}: {1}".format(to_native(e), content)
            self.module.fail_json(msg=error_msg)
        
    
    def rules_add(self):  
        fly_auth_key = self.get_key_or_fail('fly_auth_key')
        site = self.get_key_or_fail('site')
        hostname = self.get_key_or_fail('hostname')
        backend_id = self.get_key_or_fail('backend_id')
        action_type = self.get_key_or_fail('action_type') # an be "rewrite" or "redirect".
        path = self.get_key_or_fail('path') # Path to match. For example /blog/.
        if self.module.params['priority'] == None:
            priority = "null"
        else:
            priority=self.module.params['priority']
        if self.module.params['path_replacement'] == None:
            path_replacement = "null"
        else:
            path_replacement=self.module.params['path_replacement']
        url = api_endpoint + site + '/rules'
        headers = {'Content-Type':'application/json', 'Authorization': 'Bearer %s' %fly_auth_key}
        payload = {"data": { "attributes": {
                              "hostname": hostname,
                              "backend_id": backend_id,
                              "action_type": action_type,
                              "path": path,
                              "priority": priority, 
                              "path_replacement": path_replacement
                    } } }
                    
        resp = open_url(url,method="POST",headers=headers,validate_certs=False,data=json.dumps(payload))
        try:
            resp_json = json.loads(to_text(resp.read(), errors='surrogate_then_strict'))
            self.module.exit_json(changed=True, response = resp_json)
        except (json.JSONDecodeError, UnicodeError) as e:
            error_msg += "; Failed to parse API response with error {0}: {1}".format(to_native(e), content)
            self.module.fail_json(msg=error_msg)


def handle_request(module):
    fly = Fly(module)
    command = module.params['command']
    if command == 'create_hostname':
        preview_hostname=fly.hostname_view()
        if preview_hostname == False:
            fly.hostname_add()
        else:
            pass
    elif command == 'view_hostname':
        fly.hostname_view()
    elif command == 'add_backend':
        fly.backend_add()
    elif command == 'add_rule':
        fly.rules_add()


def main():

    module = AnsibleModule(
        argument_spec=dict(
            command=dict(choices=['create_hostname', 'view_hostname', 'add_backend', 'add_rule'], required=True),
            fly_auth_key=dict(aliases=['API_TOKEN'], no_log=True, required=True),
            site=dict(type='str', required=True),
            hostname=dict(type='str'),
            backend_name=dict(type='str'),
            backend_type=dict(type='str'),
            backend_settings=dict(type='dict'),
            backend_id=dict(type='str'),
            action_type=dict(type='str'),
            path =dict(type='str'),
            priority =dict(type='str'),
            path_replacement=dict(type='str')
        ),
    )
    
    handle_request(module)


if __name__ == '__main__':  
    main()
