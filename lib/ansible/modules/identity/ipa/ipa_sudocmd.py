#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


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
  state:
    description: State to ensure
    default: present
    choices: ['present', 'absent']
extends_documentation_fragment: ipa.documentation
version_added: "2.3"
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

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import IPAClient, ipa_argument_spec
from ansible.module_utils._text import to_native


class SudoCmdIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(SudoCmdIPAClient, self).__init__(module, host, port, protocol)

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


def get_sudocmd_diff(client, ipa_sudocmd, module_sudocmd):
    return client.get_diff(ipa_data=ipa_sudocmd, module_data=module_sudocmd)


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
            diff = get_sudocmd_diff(client, ipa_sudocmd, module_sudocmd)
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
    argument_spec = ipa_argument_spec()
    argument_spec.update(description=dict(type='str'),
                         state=dict(type='str', default='present', choices=['present', 'absent', 'enabled', 'disabled']),
                         sudocmd=dict(type='str', required=True, aliases=['name']))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    client = SudoCmdIPAClient(module=module,
                              host=module.params['ipa_host'],
                              port=module.params['ipa_port'],
                              protocol=module.params['ipa_prot'])
    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, sudocmd = ensure(module, client)
        module.exit_json(changed=changed, sudocmd=sudocmd)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
