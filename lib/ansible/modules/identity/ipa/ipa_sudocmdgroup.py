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
module: ipa_sudocmdgroup
author: Thomas Krahn (@Nosmoht)
short_description: Manage FreeIPA sudo command group
description:
- Add, modify or delete sudo command group within IPA server using IPA API.
options:
  cn:
    description:
    - Sudo Command Group.
    aliases: ['name']
    required: true
  description:
    description:
    - Group description.
  state:
    description: State to ensure
    default: present
    choices: ['present', 'absent']
  sudocmd:
    description:
    - List of sudo commands to assign to the group.
    - If an empty list is passed all assigned commands will be removed from the group.
    - If option is omitted sudo commands will not be checked or changed.
extends_documentation_fragment: ipa.documentation
version_added: "2.3"
'''

EXAMPLES = '''
- name: Ensure sudo command group exists
  ipa_sudocmdgroup:
    name: group01
    description: Group of important commands
    sudocmd:
    - su
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

- name: Ensure sudo command group does not exist
  ipa_sudocmdgroup:
    name: group01
    state: absent
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
'''

RETURN = '''
sudocmdgroup:
  description: Sudo command group as returned by IPA API
  returned: always
  type: dict
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import IPAClient, ipa_argument_spec
from ansible.module_utils._text import to_native


class SudoCmdGroupIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(SudoCmdGroupIPAClient, self).__init__(module, host, port, protocol)

    def sudocmdgroup_find(self, name):
        return self._post_json(method='sudocmdgroup_find', name=None, item={'all': True, 'cn': name})

    def sudocmdgroup_add(self, name, item):
        return self._post_json(method='sudocmdgroup_add', name=name, item=item)

    def sudocmdgroup_mod(self, name, item):
        return self._post_json(method='sudocmdgroup_mod', name=name, item=item)

    def sudocmdgroup_del(self, name):
        return self._post_json(method='sudocmdgroup_del', name=name)

    def sudocmdgroup_add_member(self, name, item):
        return self._post_json(method='sudocmdgroup_add_member', name=name, item=item)

    def sudocmdgroup_add_member_sudocmd(self, name, item):
        return self.sudocmdgroup_add_member(name=name, item={'sudocmd': item})

    def sudocmdgroup_remove_member(self, name, item):
        return self._post_json(method='sudocmdgroup_remove_member', name=name, item=item)

    def sudocmdgroup_remove_member_sudocmd(self, name, item):
        return self.sudocmdgroup_remove_member(name=name, item={'sudocmd': item})


def get_sudocmdgroup_dict(description=None):
    data = {}
    if description is not None:
        data['description'] = description
    return data


def get_sudocmdgroup_diff(client, ipa_sudocmdgroup, module_sudocmdgroup):
    return client.get_diff(ipa_data=ipa_sudocmdgroup, module_data=module_sudocmdgroup)


def ensure(module, client):
    name = module.params['cn']
    state = module.params['state']
    sudocmd = module.params['sudocmd']

    module_sudocmdgroup = get_sudocmdgroup_dict(description=module.params['description'])
    ipa_sudocmdgroup = client.sudocmdgroup_find(name=name)

    changed = False
    if state == 'present':
        if not ipa_sudocmdgroup:
            changed = True
            if not module.check_mode:
                ipa_sudocmdgroup = client.sudocmdgroup_add(name=name, item=module_sudocmdgroup)
        else:
            diff = get_sudocmdgroup_diff(client, ipa_sudocmdgroup, module_sudocmdgroup)
            if len(diff) > 0:
                changed = True
                if not module.check_mode:
                    data = {}
                    for key in diff:
                        data[key] = module_sudocmdgroup.get(key)
                    client.sudocmdgroup_mod(name=name, item=data)

        if sudocmd is not None:
            changed = client.modify_if_diff(name, ipa_sudocmdgroup.get('member_sudocmd', []), sudocmd,
                                            client.sudocmdgroup_add_member_sudocmd,
                                            client.sudocmdgroup_remove_member_sudocmd)
    else:
        if ipa_sudocmdgroup:
            changed = True
            if not module.check_mode:
                client.sudocmdgroup_del(name=name)

    return changed, client.sudocmdgroup_find(name=name)


def main():
    argument_spec = ipa_argument_spec()
    argument_spec.update(cn=dict(type='str', required=True, aliases=['name']),
                         description=dict(type='str'),
                         state=dict(type='str', default='present', choices=['present', 'absent', 'enabled', 'disabled']),
                         sudocmd=dict(type='list'))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    client = SudoCmdGroupIPAClient(module=module,
                                   host=module.params['ipa_host'],
                                   port=module.params['ipa_port'],
                                   protocol=module.params['ipa_prot'])
    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, sudocmdgroup = ensure(module, client)
        module.exit_json(changed=changed, sudorule=sudocmdgroup)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

if __name__ == '__main__':
    main()
