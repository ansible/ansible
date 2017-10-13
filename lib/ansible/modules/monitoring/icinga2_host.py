#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: icinga2_hosts

short_description: Manage a host in Icinga2
description:
   - Add or remove a host to Icinga2 through the API
   - ( see https://www.icinga.com/docs/icinga2/latest/doc/12-icinga2-api/ )
version_added: "2.5"
author: "Jurgen Brand"
options:
            server=dict(required=True),
            port=dict(default=5665, type='int'),
            user=dict(default=None),
            password=dict(default=None, no_log=True),
            ssl_ca=dict(default=None, type='path'),
            state=dict(default="present", choices=["absent", "present"]),
            name=dict(required=True, aliases=['host']),
            zone=dict(default=None),
            template=dict(default=None),
            check_command=dict(default="hostalive"),
            display_name=dict(default=None),
            ip=dict(required=True),
            variables=dict(type='dict', default=None),

  server:
    description:
      - the host name or ip-address of the Icinga2 host
    required: true
  port:
    description:
      - port used to connect too the Icinga2
    required: false
    default: 5665
  user:
    description:
      - the username used to authenticate with
    required: true
  password:
    description:
      - The password used to authenticate with.
    required: true
  ssl_ca:
    description:
      - the CA used for authenticaton
    required: false
    default: None
  state:
    description:
      - Apply feature state.
    required: false
    choices: [ "present", "absent" ]
    default: present
  name:
    description:
      - name used to create / delete the host
      - this does not need to be the FQDN, but does needs to be uniuqe
    required: true
    default: null
  zone:
    description:
      - ??
    required: false
    default: None
  template:
    description:
      - the template used to define the host
    required: false
    default: None
  check_command:
    description:
      - the command used to check if the host is alive
    required: false
    default "hostalive"
  display_name:
    description:
      - the name used to display the host
    required: false
    default: <name>
  ip:
    description:
      - the ip-addres of the host
    required: true
  variables:
    description:
      - list of variables
    required: false
    default: None

'''

EXAMPLES = '''
- name: Add host to icinga
  icinga_host:
    icinga_server: "icinga.example.com"
    icinga_user: "anisble
    icinga_pass: ""mypassword"
    state: present
    name: "{{ansible_fqdn }}"
    ip_address: "{{ ansible_default_ipv4.address }}"

'''

import requests
import json
import warnings
warnings.simplefilter('ignore', requests.packages.urllib3.exceptions.SecurityWarning)

# ===========================================
# Icinga2 API class
#
class icinga2_api:
    server = None
    port = None
    user = None
    password = None
    ssl_ca = None

    def call_url (self, url, data = {}, methode = 'GET' ):
        full_url = "https://" + self.server + ":" + str(self.port) + "/" + url
        headers = {
                'Accept': 'application/json',
                'X-HTTP-Method-Override': methode,
                }
        r = requests.post(
            full_url,
            headers=headers,
            auth=(self.user, self.password),
            data=json.dumps(data),
            verify=self.ssl_ca
        )
        return { 'code': r.status_code, 'data': r.json() }

    def check_connection(self):
        ret = self.call_url('v1/status')
        if ret['code'] == 200:
           return True
        return False

    def exists (self, hostname):
        data = {
          "filter":  "match(\"" + hostname + "\", host.name)",
        }
        ret = self.call_url ("v1/objects/hosts", data)
        if ret['code'] == 200:
           if len(ret['data']['results']) == 1:
             return True
        return False

    def create (self, hostname, data):
        ret = self.call_url (
            url="v1/objects/hosts/"+ hostname,
            data=data,
            methode="PUT"
        )
        return ret

    def delete (self, hostname):
        data = { "cascade": 1 }
        ret = self.call_url (
            url="v1/objects/hosts/"+ hostname,
            data=data,
            methode="DELETE"
        )
        return ret

    def modify (self, hostname, data):
        ret = self.call_url (
            url="v1/objects/hosts/"+ hostname,
            data=data,
            methode="POST"
        )
        return ret

    def diff (self, hostname, data):
        ret = self.call_url (
            url="v1/objects/hosts/"+ hostname,
            data={},
            methode="GET"
        )
        changed = False
        ic_data = ret['data']['results'][0]
        for key in data['attrs']:
            if key not in ic_data['attrs'].keys():
                changed = True
            elif data['attrs'][key] != ic_data['attrs'][key]:
                changed = True
        return changed

# ===========================================
# Module execution.
#
def main():
    module = AnsibleModule(
        argument_spec = dict(
            server=dict(required=True),
            port=dict(default=5665, type='int'),
            user=dict(default=None),
            password=dict(default=None, no_log=True),
            ssl_ca=dict(default=None, type='path'),
            state=dict(default="present", choices=["absent", "present"]),
            name=dict(required=True, aliases=['host']),
            zone=dict(default=None),
            template=dict(default=None),
            check_command=dict(default="hostalive"),
            display_name=dict(default=None),
            ip=dict(required=True),
            variables=dict(type='dict', default=None),
        ),
        supports_check_mode=True
    )

    server = module.params["server"]
    port = module.params["port"]
    if port < 0 or port > 65535:
        module.fail_json(msg="port must be a valid unix port number (0-65535)")
    user = module.params["user"]
    password = module.params["password"]
    ssl_ca = module.params["ssl_ca"]
    state = module.params["state"]
    name = module.params["name"]
    zone = module.params["zone"]
    template=[]
    template.append (name)
    if module.params["template"]:
        template.append(module.params["template"])
    check_command = module.params["check_command"]
    ip = module.params["ip"]
    display_name = module.params["display_name"]
    if not display_name:
      display_name = name
    variables = module.params["variables"]

    if not os.path.exists(ssl_ca):
        module.fail_json(msg="SSL ca cert can not be found")

    try:
        icinga = icinga2_api()
        icinga.server = server
        icinga.port = port
        icinga.user = user
        icinga.password = password
        icinga.ssl_ca = ssl_ca
        icinga.check_connection()
    except Exception as e:
        module.fail_json(msg="unable to connect to Icinga. Exception message: %s" % (e))

    data = {
        'attrs': {
            'address': ip,
            'check_command': check_command,
            'zone': zone,
            'vars': {
                'made_by': "ansible",
            },
            'templates': template,
        }
    }

    if variables:
        data['attrs']['vars'].upatde(variables)

    changed = False
    if icinga.exists(name):
        if state == "absent":
            if module.check_mode:
                module.exit_json(changed=True, name=name, data=data)
            else:
                try:
                    ret = icinga.delete(name)
                    if ret['code'] == 200:
                        changed = True
                    else:
                        module.fail_json(msg="bad return code deleting host: %s" % (ret['data']))
                except Exception as e:
                    module.fail_json(msg="exception deleting host: " + str(e))
                module.exit_json(changed=changed, name=name, data=data)

        elif icinga.diff(name, data):
            if module.check_mode:
                module.exit_json(changed=False, name=name, data=data)
            ret = icinga.modify(name,data)
            if ret['code'] == 200:
                changed = True
            else:
                module.fail_json(msg="bad return code modifying host: %s" % (ret['data']))

        module.exit_json(changed=changed, name=name, data=data)

    else:
        if state == "present":
            if module.check_mode:
                changed = True
            else:
                try:
                    ret = icinga.create(name, data)
                    if ret['code'] == 200:
                        changed = True
                    else:
                        module.fail_json(msg="bad return code creating host: %s" % (ret['data']))
                except Exception:
                    e = get_exception()
                    module.fail_json(msg="exception creating host: " + str(e))
        elif icinga.diff(name, data):
            if module.check_mode:
                module.exit_json(changed=False, name=name, data=data)
            ret = icinga.modify(name,data)
            if ret['code'] == 200:
                changed = True
            else:
                module.fail_json(msg="bad return code modifying host: %s" % (ret['data']))

        module.exit_json(changed=changed, name=name, data=data)


# import module snippets
if __name__ == '__main__':
    main()