#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ipa_service
author: Cédric Parent
short_description: Manage FreeIPA service
description:
- Add and delete an IPA service using IPA API
options:
  krbcanonicalname:
    description:
    - principal of the service
    - Can not be changed as it is the unique identifier.
    required: true
    aliases: ["name"]
  hosts:
    description:
    - defines the list of 'ManagedBy' hosts
    required: false
  force:
    description:
    - Force principal name even if host is not in DNS.
    required: false
    type: bool
  state:
    description: State to ensure
    required: false
    default: present
    choices: ["present", "absent"]
extends_documentation_fragment: ipa.documentation
version_added: "2.5"
'''

EXAMPLES = '''
# Ensure service is present
- ipa_service:
    name: http/host01.example.com
    state: present
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Ensure service is absent
- ipa_service:
    name: http/host01.example.com
    state: absent
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Changing Managing hosts list
- ipa_service:
    name: http/host01.example.com
    host:
       - host01.example.com
       - host02.example.com
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
'''

RETURN = '''
service:
  description: Service as returned by IPA API.
  returned: always
  type: dict
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import IPAClient, ipa_argument_spec
from ansible.module_utils._text import to_native


class ServiceIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(ServiceIPAClient, self).__init__(module, host, port, protocol)

    def service_find(self, name):
        return self._post_json(method='service_find', name=None, item={'all': True, 'krbcanonicalname': name})

    def service_add(self, name, service):
        return self._post_json(method='service_add', name=name, item=service)

    def service_mod(self, name, service):
        return self._post_json(method='service_mod', name=name, item=service)

    def service_del(self, name):
        return self._post_json(method='service_del', name=name)

    def service_disable(self, name):
        return self._post_json(method='service_disable', name=name)

    def service_add_host(self, name, item):
        return self._post_json(method='service_add_host', name=name, item={'host': item})

    def service_remove_host(self, name, item):
        return self._post_json(method='service_remove_host', name=name, item={'host': item})


def get_service_dict(force=None, krbcanonicalname=None):
    data = {}
    if force is not None:
        data['force'] = force
    if krbcanonicalname is not None:
        data['krbcanonicalname'] = krbcanonicalname
    return data


def get_service_diff(client, ipa_host, module_service):
    non_updateable_keys = ['force', 'krbcanonicalname']
    for key in non_updateable_keys:
        if key in module_service:
            del module_service[key]

    return client.get_diff(ipa_data=ipa_host, module_data=module_service)


def ensure(module, client):
    name = module.params['krbcanonicalname']
    state = module.params['state']
    hosts = module.params['hosts']

    ipa_service = client.service_find(name=name)
    module_service = get_service_dict(force=module.params['force'])
    changed = False
    if state in ['present', 'enabled', 'disabled']:
        if not ipa_service:
            changed = True
            if not module.check_mode:
                client.service_add(name=name, service=module_service)
        else:
            diff = get_service_diff(client, ipa_service, module_service)
            if len(diff) > 0:
                changed = True
                if not module.check_mode:
                    data = {}
                    for key in diff:
                        data[key] = module_service.get(key)
                    client.service_mod(name=name, service=data)
        if hosts is not None:
            if 'managedby_host' in ipa_service:
                for host in ipa_service['managedby_host']:
                    if host not in hosts:
                        if not module.check_mode:
                            client.service_remove_host(name=name, item=host)
                        changed = True
                for host in hosts:
                    if host not in ipa_service['managedby_host']:
                        if not module.check_mode:
                            client.service_add_host(name=name, item=host)
                        changed = True
            else:
                for host in hosts:
                    if not module.check_mode:
                        client.service_add_host(name=name, item=host)
                    changed = True

    else:
        if ipa_service:
            changed = True
            if not module.check_mode:
                client.service_del(name=name)

    return changed, client.service_find(name=name)


def main():
    argument_spec = ipa_argument_spec()
    argument_spec.update(
        krbcanonicalname=dict(type='str', required=True, aliases=['name']),
        force=dict(type='bool', required=False),
        hosts=dict(type='list', required=False),
        state=dict(type='str', required=False, default='present',
                   choices=['present', 'absent']))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    client = ServiceIPAClient(module=module,
                              host=module.params['ipa_host'],
                              port=module.params['ipa_port'],
                              protocol=module.params['ipa_prot'])

    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, host = ensure(module, client)
        module.exit_json(changed=changed, host=host)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

if __name__ == '__main__':
    main()
