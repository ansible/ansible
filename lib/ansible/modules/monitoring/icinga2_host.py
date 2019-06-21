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
module: icinga2_host
short_description: Manage a host in Icinga2
description:
   - "Add or remove a host to Icinga2 through the API."
   - "See U(https://www.icinga.com/docs/icinga2/latest/doc/12-icinga2-api/)"
   - "Many option defaults are controlled by the Icinga2 configuration."
version_added: "2.5"
author: "Jurgen Brand (@t794104)"
options:
  cascade:
    description:
      - This option controls behaviour when I(state) is C(absent) and the object is present. When set to C(true)
        the object and all objects that depend on it are removed. When set to C(false), the icinga API will let
        you know that the object cannot be removed, while there are dependent objects.
    default: true
    type: bool
    version_added: 2.8
  check_command:
    description:
      - The command used to check if the host is alive.
    default: hostalive
  client_cert:
    description:
      - PEM formatted certificate chain file to be used for SSL client
        authentication. This file can also include the key as well, and if
        the key is included, I(client_key) is not required.
  client_key:
    description:
      - PEM formatted file that contains your private key to be used for SSL
        client authentication. If I(client_cert) contains both the certificate
        and key, this option is not required.
  display_name:
    description:
      - The name used to display the host. If not set, then Icinga will use the value of I(name).
  force_basic_auth:
    description:
      - Httplib2, the library used by the uri module only sends authentication information when a webservice
        responds to an initial request with a C(401) status. Since some basic auth services do not properly
        send a C(401), logins will fail. This option forces the sending of the Basic authentication header
        upon initial request.
    default: no
    type: bool
  force_check:
    description:
      - Force a check when a host is created or modified
    type: bool
    default: yes
    version_added: 2.8
  ip:
    description:
      - The IP address of the host.
    required: true
  name:
    description:
      - Name used to create / delete the host. This does not need to be the FQDN, but does needs to be unique.
    required: true
  state:
    description:
      - Apply feature state.
    choices: [ "present", "absent" ]
    default: present
  template:
    description:
      - The template used to define the host.
  url:
    description:
      - HTTP, HTTPS, or FTP URL in the form (http|https|ftp)://[user[:pass]]@host.domain[:port]/path
    required: true
  url_password:
    description:
        - The password for use in HTTP basic authentication.
        - If the I(url_username) option is not specified, the I(url_password) option will not be used.
  url_username:
    description:
      - The username for use in HTTP basic authentication.
      - This parameter can be used without I(url_password) for sites that allow empty passwords.
  use_proxy:
    description:
      - If C(no), it will not use a proxy, even if one is defined in
        an environment variable on the target hosts.
    default: yes
    type: bool
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    default: yes
    type: bool
  max_check_attempts:
    description:
      - The number of times a service is checked before changing into a hard state.
    type: int
    version_added: 2.8
  check_period:
    description:
      - The name of a time period which determines when this service should be checked.
    version_added: 2.8
  check_timeout:
    description:
      - Check command timeout in seconds. Overrides the CheckCommand's timeout attribute.
    type: int
    version_added: 2.8
  check_interval:
    description:
      - The check interval (in seconds). This interval is used for checks when the service is in a HARD state.
    type: int
    version_added: 2.8
  retry_interval:
    description:
      - The retry interval (in seconds). This interval is used for checks when the service is in a SOFT state.
    type: int
    version_added: 2.8
  enable_notifications:
    description:
      - Whether notifications are enabled.
    type: bool
    version_added: 2.8
  enable_active_checks:
    description:
      - Whether active checks are enabled.
    type: bool
    version_added: 2.8
  enable_passive_checks:
    description:
      - Whether passive checks are enabled.
    type: bool
    version_added: 2.8
  enable_event_handler:
    description:
       - Enables event handlers for this host.
    type: bool
    version_added: 2.8
  enable_flapping:
    description:
      - Enables Whether flap detection is enabled.
    type: bool
    version_added: 2.8
  enable_perfdata:
    description:
      - Enables event handlers for this host.
    type: bool
    version_added: 2.8
  event_command:
    description:
      - The name of an event command that should be executed every time the service's state changes or the service is in a SOFT state.
    version_added: 2.8
  volatile:
    description:
      - The volatile setting enables always HARD state types if NOT-OK state changes occur.
    default: False
    type: bool
    version_added: 2.8
  command_endpoint:
    description:
      - The endpoint where commands are executed on.
    version_added: 2.8
  notes:
    description:
      - Notes for the host.
    version_added: 2.8
  notes_url:
    description:
      - URL for notes for the host (for example, in notification commands).
    version_added: 2.8
  action_url:
    description:
      - URL for actions for the host (for example, an external graphing tool).
    version_added: 2.8
  image_icon:
    description:
      -  Icon image for the host. Used by external interfaces only.
    version_added: 2.8
  image_icon_alt:
    description:
      - Icon image description for the host. Used by external interface only.
    version_added: 2.8
  variables:
    description:
      - List of variables.
  zone:
    description:
      - The zone from where this host should be polled. If I(zone) is omitted, during creation of the object,
        then the zone will be inherited from the engine that processes the API call.
'''

EXAMPLES = '''
- name: Add host to icinga
  icinga2_host:
    url: "https://icinga2.example.com"
    url_username: "ansible"
    url_password: "a_secret"
    state: present
    name: "{{ ansible_fqdn }}"
    ip: "{{ ansible_default_ipv4.address }}"
  delegate_to: 127.0.0.1
'''

RETURN = '''
name:
    description: The name used to create, modify or delete the host
    type: str
    returned: always
data:
    description: The data structure used for create, modify or delete of the host
    type: dict
    returned: always
'''


import json
import os
import types

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url, url_argument_spec


# ===========================================
# Return a dict that is flat (no dict as values)
#
def flat_dict(aDict):
    if isinstance(aDict, dict):
        flat = {}
        for key, value in aDict.items():
            if isinstance(value, dict):
                ret = flat_dict(value)
                for k, v in ret.items():
                    flat[key + '.' + k] = v
            else:
                flat[key] = value
        return flat
    else:
        return aDict


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
        rsp, info = fetch_url(module=self.module, url=url, data=data, headers=headers, method=method, use_proxy=self.module.params['use_proxy'])
        # catching transport level code and body first
        body = info['msg']
        code = info['status']
        if info['status'] <= 400:
            # approved of transport level responses
            body = json.loads(rsp.read())
            if method != 'GET':
                # for POST and PUT there is a json code available for usage
                code = body['results'][0]['code']
        return {'code': int(code), 'data': body}

    def check_connection(self):
        ret = self.call_url('v1/status')
        if ret['code'] == 200:
            return True
        return False

    def exists(self, hostname):
        ret = self.call_url(
            path="v1/objects/hosts?host=" + hostname,
        )
        if ret['code'] == 200:
            if len(ret['data']['results']) == 1:
                return True
        return False

    def create(self, hostname, data):
        ret = self.call_url(
            path="v1/objects/hosts/" + hostname,
            data=self.module.jsonify(data),
            method="PUT"
        )
        return ret

    def delete(self, hostname, cascade):
        if cascade:
            data = {"cascade": 1}
        else:
            data = {"cascade": 0}
        ret = self.call_url(
            path="v1/objects/hosts/" + hostname,
            data=self.module.jsonify(data),
            method="DELETE"
        )
        return ret

    def modify(self, hostname, data):
        ret = self.call_url(
            path="v1/objects/hosts/" + hostname,
            data=self.module.jsonify(data),
            method="POST"
        )
        return ret

    def check(self, hostname):
        data = {
            "type": "Host",
            "filter": "host.__name==\"" + hostname + "\"",
            "force_check": True,
        }
        ret = self.call_url(
            path="v1/actions/reschedule-check",
            data=self.module.jsonify(data),
            method="POST"
        )
        return ret

    def diff(self, hostname, data):
        ret = self.call_url(
            path="v1/objects/hosts/" + hostname,
            method="GET"
        )
        changed = False
        ch_data = {
            'attrs': {}
        }
        ic_attr = flat_dict(ret['data']['results'][0]['attrs'])
        an_attr = flat_dict(data['attrs'])
        for key in an_attr:
            if key not in ic_attr.keys():
                changed = True
                ch_data['attrs'][key] = an_attr[key]
            elif an_attr[key] != ic_attr[key]:
                changed = True
                ch_data['attrs'][key] = an_attr[key]
        return (changed, ch_data)


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
        name=dict(required=True, aliases=['host']),
        zone=dict(default=None),
        template=dict(default=None),
        check_command=dict(default="hostalive"),
        cascade=dict(default=True, type='bool'),
        display_name=dict(default=None),
        ip=dict(required=True),
        force_check=dict(default=True, type='bool'),
        variables=dict(type='dict', default=None),
        max_check_attempts=dict(default=None, type='int'),
        check_period=dict(default=None),
        check_timeout=dict(default=None, type='int'),
        check_interval=dict(default=None, type='int'),
        retry_interval=dict(default=None, type='int'),
        enable_notifications=dict(default=None, type='bool'),
        enable_active_checks=dict(default=None, type='bool'),
        enable_passive_checks=dict(default=None, type='bool'),
        enable_event_handler=dict(default=None, type='bool'),
        enable_flapping=dict(default=None, type='bool'),
        enable_perfdata=dict(default=None, type='bool'),
        event_command=dict(default=None),
        flapping_threshold=dict(default=None),
        volatile=dict(default=False, type='bool'),
        command_endpoint=dict(default=None),
        notes=dict(default=None),
        notes_url=dict(default=None),
        action_url=dict(default=None),
        image_icon=dict(default=None),
        image_icon_alt=dict(default=None),
    )

    # Define the main module
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    state = module.params["state"]
    name = module.params["name"]
    template = []
    if module.params["template"]:
        template.append(module.params["template"])
    check_command = module.params["check_command"]
    cascade = module.params["cascade"]
    ip = module.params["ip"]
    force_check = module.params["force_check"]
    display_name = module.params["display_name"]
    if not display_name:
        display_name = name
    variables = module.params["variables"]

    try:
        icinga = icinga2_api(module=module)
        icinga.check_connection()
    except Exception as e:
        module.fail_json(msg="unable to connect to Icinga. Exception message: %s" % (e))

    # Add attributes
    data = {
        'templates': template,
        'attrs': {
            'check_command': check_command,
            'address': ip,
            'display_name': display_name,
            'vars': {
                'made_by': 'Ansible'
            },
        }
    }
    # Loop through list of setable objects.
    obj_attrs = [
        'max_check_attempts', 'check_period', 'check_timeout', 'check_interval', 'retry_interval', 'enable_notifications', 'enable_active_checks',
        'enable_passive_checks', 'enable_event_handler', 'enable_flapping', 'enable_perfdata', 'event_command', 'flapping_threshold',
        'volatile', 'command_endpoint', 'notes', 'notes_url', 'action_url', 'image_icon', 'image_icon_alt', 'zone'
    ]
    for x in obj_attrs:
        if module.params[x]:
            data['attrs'][x] = module.params[x]

    if variables:
        data['attrs']['vars'].update(variables)

    data['attrs'] = flat_dict(data['attrs'])
    changed = False
    if icinga.exists(name):
        diff, ch_data = icinga.diff(name, data)
        if state == "absent":
            if module.check_mode:
                module.exit_json(changed=True, name=name, data=data)
            else:
                try:
                    ret = icinga.delete(name, cascade)
                    if ret['code'] == 200:
                        changed = True
                    else:
                        module.fail_json(msg="Caught return code [%i] deleting host: %s" % (ret['code'], ret['data']))
                except Exception as e:
                    module.fail_json(msg="exception deleting host: " + str(e))
        elif diff:
            if module.check_mode:
                module.exit_json(changed=False, name=name, data=ch_data)
            else:
                try:
                    ret = icinga.modify(name, ch_data)
                    if ret['code'] == 200:
                        changed = True
                        data = ch_data
                        if force_check:
                            ret = icinga.check(name)
                            if ret['code'] != 200:
                                module.fail_json(msg="Caught return code [%i] forcing host check: %s" % (ret['code'], ret['data']))
                    else:
                        module.fail_json(msg="Caught return code [%i] modifying host: %s" % (ret['code'], ret['data']))
                except Exception as e:
                    module.fail_json(msg="exception modifying host: " + str(e))
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
                                module.fail_json(msg="Caught return code [%i] forcing host check: %s" % (ret['code'], ret['data']))
                    else:
                        module.fail_json(msg="Caught return code [%i] creating host: %s" % (ret['code'], ret['data']))
                except Exception as e:
                    module.fail_json(msg="exception creating host: " + str(e))

    module.exit_json(changed=changed, name=name, data=data)


# import module snippets
if __name__ == '__main__':
    main()