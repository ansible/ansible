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
module: ipa_group
author: Thomas Krahn (@Nosmoht)
short_description: Manage FreeIPA group
description:
- Add, modify and delete group within IPA server
options:
  cn:
    description:
    - Canonical name.
    - Can not be changed as it is the unique identifier.
    required: true
    aliases: ['name']
  description:
    description:
    - Description of the group.
  external:
    description:
    - Allow adding external non-IPA members from trusted domains.
    type: bool
  gidnumber:
    description:
    - GID (use this option to set it manually).
    aliases: ['gid']
  group:
    description:
    - List of group names assigned to this group.
    - If an empty list is passed all groups will be removed from this group.
    - If option is omitted assigned groups will not be checked or changed.
    - Groups that are already assigned but not passed will be removed.
  nonposix:
    description:
    - Create as a non-POSIX group.
    type: bool
  user:
    description:
    - List of user names assigned to this group.
    - If an empty list is passed all users will be removed from this group.
    - If option is omitted assigned users will not be checked or changed.
    - Users that are already assigned but not passed will be removed.
  state:
    description:
    - State to ensure
    default: "present"
    choices: ["present", "absent"]
extends_documentation_fragment: ipa.documentation
version_added: "2.3"
'''

EXAMPLES = '''
# Ensure group is present
- ipa_group:
    name: oinstall
    gidnumber: 54321
    state: present
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Ensure that groups sysops and appops are assigned to ops but no other group
- ipa_group:
    name: ops
    group:
    - sysops
    - appops
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Ensure that users linus and larry are assign to the group, but no other user
- ipa_group:
    name: sysops
    user:
    - linus
    - larry
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Ensure group is absent
- ipa_group:
    name: sysops
    state: absent
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
'''

RETURN = '''
group:
  description: Group as returned by IPA API
  returned: always
  type: dict
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import IPAClient, ipa_argument_spec
from ansible.module_utils._text import to_native


class GroupIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(GroupIPAClient, self).__init__(module, host, port, protocol)

    def group_find(self, name):
        return self._post_json(method='group_find', name=None, item={'all': True, 'cn': name})

    def group_add(self, name, item):
        return self._post_json(method='group_add', name=name, item=item)

    def group_mod(self, name, item):
        return self._post_json(method='group_mod', name=name, item=item)

    def group_del(self, name):
        return self._post_json(method='group_del', name=name)

    def group_add_member(self, name, item):
        return self._post_json(method='group_add_member', name=name, item=item)

    def group_add_member_group(self, name, item):
        return self.group_add_member(name=name, item={'group': item})

    def group_add_member_user(self, name, item):
        return self.group_add_member(name=name, item={'user': item})

    def group_remove_member(self, name, item):
        return self._post_json(method='group_remove_member', name=name, item=item)

    def group_remove_member_group(self, name, item):
        return self.group_remove_member(name=name, item={'group': item})

    def group_remove_member_user(self, name, item):
        return self.group_remove_member(name=name, item={'user': item})


def get_group_dict(description=None, external=None, gid=None, nonposix=None):
    group = {}
    if description is not None:
        group['description'] = description
    if external is not None:
        group['external'] = external
    if gid is not None:
        group['gidnumber'] = gid
    if nonposix is not None:
        group['nonposix'] = nonposix
    return group


def get_group_diff(client, ipa_group, module_group):
    data = []
    # With group_add attribute nonposix is passed, whereas with group_mod only posix can be passed.
    if 'nonposix' in module_group:
        # Only non-posix groups can be changed to posix
        if not module_group['nonposix'] and ipa_group.get('nonposix'):
            module_group['posix'] = True
        del module_group['nonposix']

    if 'external' in module_group:
        if module_group['external'] and 'ipaexternalgroup' in ipa_group.get('objectclass'):
            del module_group['external']

    return client.get_diff(ipa_data=ipa_group, module_data=module_group)


def ensure(module, client):
    state = module.params['state']
    name = module.params['cn']
    group = module.params['group']
    user = module.params['user']

    module_group = get_group_dict(description=module.params['description'], external=module.params['external'],
                                  gid=module.params['gidnumber'], nonposix=module.params['nonposix'])
    ipa_group = client.group_find(name=name)

    changed = False
    if state == 'present':
        if not ipa_group:
            changed = True
            if not module.check_mode:
                ipa_group = client.group_add(name, item=module_group)
        else:
            diff = get_group_diff(client, ipa_group, module_group)
            if len(diff) > 0:
                changed = True
                if not module.check_mode:
                    data = {}
                    for key in diff:
                        data[key] = module_group.get(key)
                    client.group_mod(name=name, item=data)

        if group is not None:
            changed = client.modify_if_diff(name, ipa_group.get('member_group', []), group,
                                            client.group_add_member_group,
                                            client.group_remove_member_group) or changed

        if user is not None:
            changed = client.modify_if_diff(name, ipa_group.get('member_user', []), user,
                                            client.group_add_member_user,
                                            client.group_remove_member_user) or changed

    else:
        if ipa_group:
            changed = True
            if not module.check_mode:
                client.group_del(name)

    return changed, client.group_find(name=name)


def main():
    argument_spec = ipa_argument_spec()
    argument_spec.update(cn=dict(type='str', required=True, aliases=['name']),
                         description=dict(type='str'),
                         external=dict(type='bool'),
                         gidnumber=dict(type='str', aliases=['gid']),
                         group=dict(type='list'),
                         nonposix=dict(type='bool'),
                         state=dict(type='str', default='present', choices=['present', 'absent']),
                         user=dict(type='list'))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           )

    client = GroupIPAClient(module=module,
                            host=module.params['ipa_host'],
                            port=module.params['ipa_port'],
                            protocol=module.params['ipa_prot'])
    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, group = ensure(module, client)
        module.exit_json(changed=changed, group=group)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
