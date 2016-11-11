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
module: ipa_sudocmd
author: Thomas Krahn (@Nosmoht)
short_description: Manage FreeIPA sudo command
description:
- Add, modify or delete sudo command within FreeIPA server using FreeIPA API.
options:
  sudocmd:
    description:
    - Sudo Command.
    aliases: ['name']
    required: true
  description:
    description:
    - A description of this command.
    required: false
  state:
    description: State to ensure
    required: false
    default: present
    choices: ['present', 'absent']
  ipa_port:
    description: Port of IPA server
    required: false
    default: 443
  ipa_host:
    description: IP or hostname of IPA server
    required: false
    default: "ipa.example.com"
  ipa_user:
    description: Administrative account used on IPA server
    required: false
    default: "admin"
  ipa_pass:
    description: Password of administrative user
    required: true
  ipa_prot:
    description: Protocol used by IPA server
    required: false
    default: "https"
    choices: ["http", "https"]
  validate_certs:
    description:
    - This only applies if C(ipa_prot) is I(https).
    - If set to C(no), the SSL certificates will not be validated.
    - This should only set to C(no) used on personally controlled sites using self-signed certificates.
    required: false
    default: true
version_added: "2.3"
requirements:
- json
'''

EXAMPLES = '''
# Ensure sudo command exists
- ipa_sudocmd:
    name: su
    description: Allow to run su via sudo
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Ensure sudo command does not exist
- ipa_sudocmd:
    name: su
    state: absent
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
'''

RETURN = '''
sudocmd:
  description: Sudo command as return from IPA API
  returned: always
  type: dict
'''

try:
    import json
except ImportError:
    import simplejson as json


class IPAClient:
    def __init__(self, module, host, port, protocol):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.module = module
        self.headers = None

    def get_base_url(self):
        return '%s://%s/ipa' % (self.protocol, self.host)

    def get_json_url(self):
        return '%s/session/json' % self.get_base_url()

    def login(self, username, password):
        url = '%s/session/login_password' % self.get_base_url()
        data = 'user=%s&password=%s' % (username, password)
        headers = {'referer': self.get_base_url(),
                   'Content-Type': 'application/x-www-form-urlencoded',
                   'Accept': 'text/plain'}
        try:
            resp, info = fetch_url(module=self.module, url=url, data=data, headers=headers)
            status_code = info['status']
            if status_code not in [200, 201, 204]:
                self._fail('login', info['body'])

            self.headers = {'referer': self.get_base_url(),
                            'Content-Type': 'application/json',
                            'Accept': 'application/json',
                            'Cookie': resp.info().getheader('Set-Cookie')}
        except Exception:
            e = get_exception()
            self._fail('login', str(e))

    def _fail(self, msg, e):
        if 'message' in e:
            err_string = e.get('message')
        else:
            err_string = e
        self.module.fail_json(msg='%s: %s' % (msg, err_string))

    def _post_json(self, method, name, item=None):
        if item is None:
            item = {}
        url = '%s/session/json' % self.get_base_url()
        data = {'method': method, 'params': [[name], item]}
        try:
            resp, info = fetch_url(module=self.module, url=url, data=json.dumps(data), headers=self.headers)
            status_code = info['status']
            if status_code not in [200, 201, 204]:
                self._fail(method, info['body'])
        except Exception:
            e = get_exception()
            self._fail('post %s' % method, str(e))

        resp = json.loads(resp.read())
        err = resp.get('error')
        if err is not None:
            self._fail('repsonse %s' % method, err)

        if 'result' in resp:
            result = resp.get('result')
            if 'result' in result:
                result = result.get('result')
                if isinstance(result, list):
                    if len(result) > 0:
                        return result[0]
                    else:
                        return {}
            return result
        return None

    def sudocmd_find(self, name):
        return self._post_json(method='sudocmd_find', name=None, item={'all': True, 'sudocmd': name})

    def sudocmd_add(self, name, item):
        return self._post_json(method='sudocmd_add', name=name, item=item)

    def sudocmd_mod(self, name, item):
        return self._post_json(method='sudocmd_mod', name=name, item=item)

    def sudocmd_del(self, name):
        return self._post_json(method='sudocmd_del', name=name)


def get_sudocmd_dict(description=None):
    data = {}
    if description is not None:
        data['description'] = description
    return data


def get_sudocmd_diff(ipa_sudocmd, module_sudocmd):
    data = []
    for key in module_sudocmd.keys():
        module_value = module_sudocmd.get(key, None)
        ipa_value = ipa_sudocmd.get(key, None)
        if isinstance(ipa_value, list) and not isinstance(module_value, list):
            module_value = [module_value]
        if isinstance(ipa_value, list) and isinstance(module_value, list):
            ipa_value = sorted(ipa_value)
            module_value = sorted(module_value)
        if ipa_value != module_value:
            data.append(key)
    return data


def ensure(module, client):
    name = module.params['sudocmd']
    state = module.params['state']

    module_sudocmd = get_sudocmd_dict(description=module.params['description'])
    ipa_sudocmd = client.sudocmd_find(name=name)

    changed = False
    if state == 'present':
        if not ipa_sudocmd:
            changed = True
            if not module.check_mode:
                client.sudocmd_add(name=name, item=module_sudocmd)
        else:
            diff = get_sudocmd_diff(ipa_sudocmd, module_sudocmd)
            if len(diff) > 0:
                changed = True
                if not module.check_mode:
                    data = {}
                    for key in diff:
                        data[key] = module_sudocmd.get(key)
                    client.sudocmd_mod(name=name, item=data)
    else:
        if ipa_sudocmd:
            changed = True
            if not module.check_mode:
                client.sudocmd_del(name=name)

    return changed, client.sudocmd_find(name=name)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            description=dict(type='str', required=False),
            state=dict(type='str', required=False, default='present',
                       choices=['present', 'absent', 'enabled', 'disabled']),
            sudocmd=dict(type='str', required=True, aliases=['name']),
            ipa_prot=dict(type='str', required=False, default='https', choices=['http', 'https']),
            ipa_host=dict(type='str', required=False, default='ipa.example.com'),
            ipa_port=dict(type='int', required=False, default=443),
            ipa_user=dict(type='str', required=False, default='admin'),
            ipa_pass=dict(type='str', required=True, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
        ),
        supports_check_mode=True,
    )

    client = IPAClient(module=module,
                       host=module.params['ipa_host'],
                       port=module.params['ipa_port'],
                       protocol=module.params['ipa_prot'])
    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, sudocmd = ensure(module, client)
        module.exit_json(changed=changed, sudocmd=sudocmd)
    except Exception:
        e = get_exception()
        module.fail_json(msg=str(e))


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.urls import fetch_url

if __name__ == '__main__':
    main()
