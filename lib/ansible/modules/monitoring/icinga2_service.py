#!/usr/bin/python
# -*- coding: utf-8 -*-

# This module is proudly sponsored by CGI (www.cgi.com) and
# KPN (www.kpn.com).
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: icinga2_service
short_description: Manage a service for a host in Icinga2
description:
   - "Add or remove a services to Icinga2 through the API"
   - "( see https://www.icinga.com/docs/icinga2/latest/doc/12-icinga2-api/ )"
version_added: "2.5"
author: "Jurgen Brand (@t794104)"
options:
  url:
    description:
      - HTTP, HTTPS, or FTP URL in the form (http|https|ftp)://[user[:pass]]@host.domain[:port]/path
    required: true
  use_proxy:
    description:
      - If C(no), it will not use a proxy, even if one is defined in
        an environment variable on the target hosts.
    default: 'yes'
    type: bool
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    default: 'yes'
    type: bool
  url_username:
    description:
      - The username for use in HTTP basic authentication.
      - This parameter can be used without C(url_password) for sites that allow empty passwords.
  url_password:
    description:
        - The password for use in HTTP basic authentication.
        - If the C(url_username) parameter is not specified, the C(url_password) parameter will not be used.
  force_basic_auth:
    description:
      - httplib2, the library used by the uri module only sends authentication information when a webservice
        responds to an initial request with a 401 status. Since some basic auth services do not properly
        send a 401, logins will fail. This option forces the sending of the Basic authentication header
        upon initial request.
    default: 'no'
    type: bool
  client_cert:
    description:
      - PEM formatted certificate chain file to be used for SSL client
        authentication. This file can also include the key as well, and if
        the key is included, C(client_key) is not required.
  client_key:
    description:
      - PEM formatted file that contains your private key to be used for SSL
        client authentication. If C(client_cert) contains both the certificate
        and key, this option is not required.
  state:
    description:
      - Apply feature state.
    required: false
    choices: [ "present", "absent" ]
    default: present
  name:
    description:
      - Name of the service in Icinga2 style; <host>!<service>. Where <host> is
        a existing host.
      - Mutually exclusive with host / service.
    required: true
  host:
    description:
      - The name of the host the service will be create for.
      - If used, must be paired with service.
      - Mutually exclusive with name.
  service:
    description:
      - The name of the service.
      - If used, must be paired with host.
      - Mutually exclusive with name.
  zone:
    description:
      - The zone from where this host should be polled.
  template:
    description:
      - the template used to define the host
    required: false
    default: None
  check_command:
    description:
      - the command used to check if the host is alive
    required: false
    default: "hostalive"
  display_name:
    description:
      - the name used to display the service
    required: false
    default: if none is give it is the value of the <name> parameter
  ip:
    description:
      - The IP address of the host.
    required: true
  force_check:
    description:
      - Force a (re)check when a service is created or modified
    required: false
    default: Yes
  variables:
    description:
      - List of variables.
    required: false
    default: None
'''

EXAMPLES = '''
- name: Add a service to a host to icinga
  icinga_host:
    icinga_server: "icinga.example.com"
    icinga_user: "anisble"
    icinga_pass: "mypassword"
    state: present
    name: "{{ ansible_fqdn }}!nrpe"
    display_name: "NRPE"
    check_command: "nrpe"
    variables:
        nrpe_port: "5667"

- name: Same service but with host/service
  icinga_host:
    icinga_server: "icinga.example.com"
    icinga_user: "anisble"
    icinga_pass: "mypassword"
    state: present
    host: "{{ ansible_fqdn }}"
    service: "nrpe"
    display_name: "NRPE"
    check_command: "nrpe"
    variables:
        nrpe_port: "5667"
'''

RETURN = '''
name:
    description: The name used to create, modify or delete the service
    type: string
    returned: always
data:
    description: The data structure used for create, modify or delete of the service
    type: dict
    returned: always
'''

import json
import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url, url_argument_spec


# ===========================================
# Icinga2 API class
#
class icinga2_api:
    module = None

    def call_url(self, path, data='', method='GET'):
        headers = {
            'Accept': 'application/json',
            'X-HTTP-Method-Override': method,
        }
        url = self.module.params.get("url") + "/" + path
        rsp, info = fetch_url(module=self.module, url=url, data=data, headers=headers, method=method)
        body = ''
        if rsp:
            body = json.loads(rsp.read())
        if info['status'] >= 400:
            body = info['body']
        return {'code': info['status'], 'data': body}

    def check_connection(self):
        ret = self.call_url('v1/status')
        if ret['code'] == 200:
            return True
        return False

    def exists(self, service):
        ret = self.call_url(
            path="v1/objects/services?service=" + service,
        )
        if ret['code'] == 200:
            if len(ret['data']['results']) == 1:
                return True
        return False

    def create(self, service, data):
        ret = self.call_url(
            path="v1/objects/services/" + service,
            data=self.module.jsonify(data),
            method="PUT"
        )
        return ret

    def delete(self, service):
        data = {"cascade": 1}
        ret = self.call_url(
            path="v1/objects/services/" + service,
            data=self.module.jsonify(data),
            method="DELETE"
        )
        return ret

    def modify(self, service, data):
        ret = self.call_url(
            path="v1/objects/services/" + service,
            data=self.module.jsonify(data),
            method="POST"
        )
        return ret

    def check(self, service):
        data = {
            "type": "Service",
            "filter": "service.__name==\"" + service + "\"",
            "force_check": True,
        }
        ret = self.call_url(
            path="v1/actions/reschedule-check",
            data=self.module.jsonify(data),
            method="POST"
        )
        return ret

    def diff(self, service, data):
        ret = self.call_url(
            path="v1/objects/services/" + service,
            method="GET"
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
    # use the predefined argument spec for url
    argument_spec = url_argument_spec()
    # remove unnecessary argument 'force'
    del argument_spec['force']
    # add our own arguments
    argument_spec.update(
        state=dict(default="present", choices=["absent", "present"]),
        name=dict(),
        host=dict(),
        service=dict(),
        zone=dict(),
        template=dict(default=None),
        check_command=dict(default="hostalive"),
        display_name=dict(default=None),
        command_endpoint=dict(default=""),
        force_check=dict(default=True, type='bool'),
        variables=dict(type='dict', default=None),
    )

    # Define the main module
    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['name', 'host'],
                            ['name', 'service'],
                            ],
        required_together=[['host', 'service'],
                           ],
        supports_check_mode=True
    )

    state = module.params["state"]
    if module.params["host"]:
        name = module.params["host"] + "!" + module.params["service"]
    else:
        name = module.params["name"]
    zone = module.params["zone"]
    template = []
    template.append(name)
    if module.params["template"]:
        template.append(module.params["template"])
    check_command = module.params["check_command"]
    command_endpoint = module.params["command_endpoint"]
    display_name = module.params["display_name"]
    force_check = module.params["force_check"]
    if not display_name:
        display_name = name
    variables = module.params["variables"]

    try:
        icinga = icinga2_api()
        icinga.module = module
        icinga.check_connection()
    except Exception as e:
        module.fail_json(msg="unable to connect to Icinga. Exception message: %s" % (e))

    data = {
        'attrs': {
            'check_command': check_command,
            'command_endpoint': command_endpoint,
            'display_name': display_name,
            'zone': zone,
            'vars': {
                'made_by': "ansible",
            },
            'templates': template,
        }
    }

    if variables:
        data['attrs']['vars'].update(variables)

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
                        module.fail_json(msg="bad return code deleting service: %s" % (ret['data']))
                except Exception as e:
                    module.fail_json(msg="exception deleting service: " + str(e))

        elif icinga.diff(name, data):
            if module.check_mode:
                module.exit_json(changed=False, name=name, data=data)
            # ret = icinga.modify(name,data)
            ret = icinga.delete(name)
            ret = icinga.create(name, data)
            if ret['code'] == 200:
                changed = True
                if force_check:
                    ret = icinga.check(name)
                    if ret['code'] != 200:
                        module.fail_json(msg="bad return code checking service: %s" % (ret['data']))
            else:
                module.fail_json(msg="bad return code modifying service: %s" % (ret['data']))

    else:
        if state == "present":
            if module.check_mode:
                changed = True
            else:
                try:
                    ret = icinga.create(name, data)
                    if ret['code'] == 200:
                        changed = True
                        if force_check:
                            ret = icinga.check(name)
                            if ret['code'] != 200:
                                module.fail_json(msg="bad return code checking service: %s" % (ret['data']))
                    else:
                        module.fail_json(msg="bad return code creating service: %s" % (ret['data']))
                except Exception as e:
                    module.fail_json(msg="exception creating service: " + str(e))

    module.exit_json(changed=changed, name=name, data=data)


# import module snippets
if __name__ == '__main__':
    main()
