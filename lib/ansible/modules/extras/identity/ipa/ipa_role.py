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
module: ipa_role
short_description: Manage FreeIPA role
description:
- Add, modify and delete a role within FreeIPA server using FreeIPA API
options:
  cn:
    description:
    - Role name.
    - Can not be changed as it is the unique identifier.
    required: true
    aliases: ['name']
  description:
    description:
    - A description of this role-group.
    required: false
  group:
    description:
    - List of group names assign to this role.
    - If an empty list is passed all assigned groups will be unassigned from the role.
    - If option is omitted groups will not be checked or changed.
    - If option is passed all assigned groups that are not passed will be unassigned from the role.
  host:
    description:
    - List of host names to assign.
    - If an empty list is passed all assigned hosts will be unassigned from the role.
    - If option is omitted hosts will not be checked or changed.
    - If option is passed all assigned hosts that are not passed will be unassigned from the role.
    required: false
  hostgroup:
    description:
    - List of host group names to assign.
    - If an empty list is passed all assigned host groups will be removed from the role.
    - If option is omitted host groups will not be checked or changed.
    - If option is passed all assigned hostgroups that are not passed will be unassigned from the role.
    required: false
  service:
    description:
    - List of service names to assign.
    - If an empty list is passed all assigned services will be removed from the role.
    - If option is omitted services will not be checked or changed.
    - If option is passed all assigned services that are not passed will be removed from the role.
    required: false
  state:
    description: State to ensure
    required: false
    default: "present"
    choices: ["present", "absent"]
  user:
    description:
    - List of user names to assign.
    - If an empty list is passed all assigned users will be removed from the role.
    - If option is omitted users will not be checked or changed.
    required: false
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
# Ensure role is present
- ipa_role:
    name: dba
    description: Database Administrators
    state: present
    user:
    - pinky
    - brain
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Ensure role with certain details
- ipa_role:
    name: another-role
    description: Just another role
    group:
    - editors
    host:
    - host01.example.com
    hostgroup:
    - hostgroup01
    service:
    - service01

# Ensure role is absent
- ipa_role:
    name: dba
    state: absent
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
'''

RETURN = '''
role:
  description: Role as returned by IPA API.
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

    def role_find(self, name):
        return self._post_json(method='role_find', name=None, item={'all': True, 'cn': name})

    def role_add(self, name, item):
        return self._post_json(method='role_add', name=name, item=item)

    def role_mod(self, name, item):
        return self._post_json(method='role_mod', name=name, item=item)

    def role_del(self, name):
        return self._post_json(method='role_del', name=name)

    def role_add_member(self, name, item):
        return self._post_json(method='role_add_member', name=name, item=item)

    def role_add_group(self, name, item):
        return self.role_add_member(name=name, item={'group': item})

    def role_add_host(self, name, item):
        return self.role_add_member(name=name, item={'host': item})

    def role_add_hostgroup(self, name, item):
        return self.role_add_member(name=name, item={'hostgroup': item})

    def role_add_service(self, name, item):
        return self.role_add_member(name=name, item={'service': item})

    def role_add_user(self, name, item):
        return self.role_add_member(name=name, item={'user': item})

    def role_remove_member(self, name, item):
        return self._post_json(method='role_remove_member', name=name, item=item)

    def role_remove_group(self, name, item):
        return self.role_remove_member(name=name, item={'group': item})

    def role_remove_host(self, name, item):
        return self.role_remove_member(name=name, item={'host': item})

    def role_remove_hostgroup(self, name, item):
        return self.role_remove_member(name=name, item={'hostgroup': item})

    def role_remove_service(self, name, item):
        return self.role_remove_member(name=name, item={'service': item})

    def role_remove_user(self, name, item):
        return self.role_remove_member(name=name, item={'user': item})


def get_role_dict(description=None):
    data = {}
    if description is not None:
        data['description'] = description
    return data


def get_role_diff(ipa_role, module_role):
    data = []
    for key in module_role.keys():
        module_value = module_role.get(key, None)
        ipa_value = ipa_role.get(key, None)
        if isinstance(ipa_value, list) and not isinstance(module_value, list):
            module_value = [module_value]
        if isinstance(ipa_value, list) and isinstance(module_value, list):
            ipa_value = sorted(ipa_value)
            module_value = sorted(module_value)
        if ipa_value != module_value:
            data.append(key)
    return data


def modify_if_diff(module, name, ipa_list, module_list, add_method, remove_method):
    changed = False
    diff = list(set(ipa_list) - set(module_list))
    if len(diff) > 0:
        changed = True
        if not module.check_mode:
            remove_method(name=name, item=diff)

    diff = list(set(module_list) - set(ipa_list))
    if len(diff) > 0:
        changed = True
        if not module.check_mode:
            add_method(name=name, item=diff)
    return changed


def ensure(module, client):
    state = module.params['state']
    name = module.params['name']
    group = module.params['group']
    host = module.params['host']
    hostgroup = module.params['hostgroup']
    service = module.params['service']
    user = module.params['user']

    module_role = get_role_dict(description=module.params['description'])
    ipa_role = client.role_find(name=name)

    changed = False
    if state == 'present':
        if not ipa_role:
            changed = True
            if not module.check_mode:
                ipa_role = client.role_add(name=name, item=module_role)
        else:
            diff = get_role_diff(ipa_role=ipa_role, module_role=module_role)
            if len(diff) > 0:
                changed = True
                if not module.check_mode:
                    data = {}
                    for key in diff:
                        data[key] = module_role.get(key)
                    client.role_mod(name=name, item=data)

        if group is not None:
            changed = modify_if_diff(module, name, ipa_role.get('member_group', []), group,
                                     client.role_add_group,
                                     client.role_remove_group) or changed

        if host is not None:
            changed = modify_if_diff(module, name, ipa_role.get('member_host', []), host,
                                     client.role_add_host,
                                     client.role_remove_host) or changed

        if hostgroup is not None:
            changed = modify_if_diff(module, name, ipa_role.get('member_hostgroup', []), hostgroup,
                                     client.role_add_hostgroup,
                                     client.role_remove_hostgroup) or changed

        if service is not None:
            changed = modify_if_diff(module, name, ipa_role.get('member_service', []), service,
                                     client.role_add_service,
                                     client.role_remove_service) or changed
        if user is not None:
            changed = modify_if_diff(module, name, ipa_role.get('member_user', []), user,
                                     client.role_add_user,
                                     client.role_remove_user) or changed
    else:
        if ipa_role:
            changed = True
            if not module.check_mode:
                client.role_del(name)

    return changed, client.role_find(name=name)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            cn=dict(type='str', required=True, aliases=['name']),
            description=dict(type='str', required=False),
            group=dict(type='list', required=False),
            host=dict(type='list', required=False),
            hostgroup=dict(type='list', required=False),
            service=dict(type='list', required=False),
            state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
            user=dict(type='list', required=False),
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
        changed, role = ensure(module, client)
        module.exit_json(changed=changed, role=role)
    except Exception:
        e = get_exception()
        module.fail_json(msg=str(e))


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.urls import fetch_url

if __name__ == '__main__':
    main()
