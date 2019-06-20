#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: ipa_role
author: Thomas Krahn (@Nosmoht)
short_description: Manage FreeIPA role
description:
- Add, modify and delete a role within FreeIPA server using FreeIPA API.
options:
  cn:
    description:
    - Role name.
    - Can not be changed as it is the unique identifier.
    required: true
    aliases: ['name']
    type: str
  description:
    description:
    - A description of this role-group.
    type: str
  group:
    description:
    - Accepts a list of member groups.  The action taken will depend on the value of "member_action."
    type: list
    elements: str
  host:
    description:
    - Accepts a list of member hosts.  The action taken will depend on the value of "member_action."
    type: list
    elements: str
  hostgroup:
    description:
    - Accepts a list of member host-groups.  The action taken will depend on the value of "member_action."
    type: list
    elements: str
  member_action:
    description:
    - Action to take for parameters accepting a list of member objects, such as host or hostgroup.
    - Setting the members will add and/or remove members so that the members are exactly those specified.
    - Adding members will add the specified members if required; existing members will not otherwise be affected.
    - Removing members will remove the specified members if they are present.  Nonexistent members will be ignored.
    default: "set"
    choices: ["add", "remove", "set"]
    version_added: "2.9"
  privilege:
    description:
    - Accepts a list of member privileges.  The action taken will depend on the value of "member_action."
    version_added: "2.4"
    type: list
    elements: str
  service:
    description:
    - Accepts a list of member services.  The action taken will depend on the value of "member_action."
    type: list
    elements: str
  state:
    description: State to ensure.
    default: "present"
    choices: ["present", "absent"]
    type: str
  user:
    description:
    - Accepts a list of member users.  The action taken will depend on the value of "member_action."
    type: list
    elements: str
extends_documentation_fragment: ipa.documentation
version_added: "2.3"
'''

EXAMPLES = r'''
- name: Ensure role is present
  ipa_role:
    name: dba
    description: Database Administrators
    state: present
    user:
    - pinky
    - brain
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

- name: Ensure role with certain details
  ipa_role:
    name: another-role
    description: Just another role
    group:
    - editors
    host:
    - host01.example.com
    hostgroup:
    - hostgroup01
    privilege:
    - Group Administrators
    - User Administrators
    service:
    - service01

- name: Ensure role is absent
  ipa_role:
    name: dba
    state: absent
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
'''

RETURN = r'''
role:
  description: Role as returned by IPA API.
  returned: always
  type: dict
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import IPAClient, ipa_argument_spec
from ansible.module_utils._text import to_native


class RoleIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(RoleIPAClient, self).__init__(module, host, port, protocol)

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

    def role_add_privilege(self, name, item):
        return self._post_json(method='role_add_privilege', name=name, item={'privilege': item})

    def role_remove_privilege(self, name, item):
        return self._post_json(method='role_remove_privilege', name=name, item={'privilege': item})


def get_role_dict(description=None):
    data = {}
    if description is not None:
        data['description'] = description
    return data


def get_role_diff(client, ipa_role, module_role):
    return client.get_diff(ipa_data=ipa_role, module_data=module_role)


def ensure(module, client):
    state = module.params['state']
    name = module.params['cn']
    group = module.params['group']
    host = module.params['host']
    hostgroup = module.params['hostgroup']
    member_action = module.params['member_action']
    privilege = module.params['privilege']
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
            diff = get_role_diff(client, ipa_role, module_role)
            if len(diff) > 0:
                changed = True
                if not module.check_mode:
                    data = {}
                    for key in diff:
                        data[key] = module_role.get(key)
                    client.role_mod(name=name, item=data)

        if member_action == 'set':
            if group is not None:
                changed = client.modify_if_diff(name, ipa_role.get('member_group', []), group,
                                                client.role_add_group,
                                                client.role_remove_group) or changed
            if host is not None:
                changed = client.modify_if_diff(name, ipa_role.get('member_host', []), host,
                                                client.role_add_host,
                                                client.role_remove_host) or changed
            if hostgroup is not None:
                changed = client.modify_if_diff(name, ipa_role.get('member_hostgroup', []), hostgroup,
                                                client.role_add_hostgroup,
                                                client.role_remove_hostgroup) or changed
            if privilege is not None:
                changed = client.modify_if_diff(name, ipa_role.get('memberof_privilege', []), privilege,
                                                client.role_add_privilege,
                                                client.role_remove_privilege) or changed
            if service is not None:
                changed = client.modify_if_diff(name, ipa_role.get('member_service', []), service,
                                                client.role_add_service,
                                                client.role_remove_service) or changed
            if user is not None:
                changed = client.modify_if_diff(name, ipa_role.get('member_user', []), user,
                                                client.role_add_user,
                                                client.role_remove_user) or changed

        elif member_action == "add":
            if group is not None:
                changed = client.add_if_missing(name, ipa_role.get('member_group', []), group,
                                                client.role_add_group) or changed
            if host is not None:
                changed = client.add_if_missing(name, ipa_role.get('member_host', []), host,
                                                client.role_add_host) or changed
            if hostgroup is not None:
                changed = client.add_if_missing(name, ipa_role.get('member_hostgroup', []), hostgroup,
                                                client.role_add_hostgroup) or changed
            if privilege is not None:
                changed = client.add_if_missing(name, ipa_role.get('memberof_privilege', []), privilege,
                                                client.role_add_privilege) or changed
            if service is not None:
                changed = client.add_if_missing(name, ipa_role.get('member_service', []), service,
                                                client.role_add_service) or changed
            if user is not None:
                changed = client.add_if_missing(name, ipa_role.get('member_user', []), user,
                                                client.role_add_user) or changed

        elif member_action == 'remove':
            if group is not None:
                changed = client.remove_if_present(name, ipa_role.get('member_group', []), group,
                                                   client.role_remove_group) or changed
            if host is not None:
                changed = client.remove_if_present(name, ipa_role.get('member_host', []), host,
                                                   client.role_remove_host) or changed
            if hostgroup is not None:
                changed = client.remove_if_present(name, ipa_role.get('member_hostgroup', []), hostgroup,
                                                   client.role_remove_hostgroup) or changed
            if privilege is not None:
                changed = client.remove_if_present(name, ipa_role.get('memberof_privilege', []), privilege,
                                                   client.role_remove_privilege) or changed
            if service is not None:
                changed = client.remove_if_present(name, ipa_role.get('member_service', []), service,
                                                   client.role_remove_service) or changed
            if user is not None:
                changed = client.remove_if_present(name, ipa_role.get('member_user', []), user,
                                                   client.role_remove_user) or changed

    elif state == 'absent':
        if ipa_role:
            changed = True
            if not module.check_mode:
                client.role_del(name)

    else:
        raise NotImplementedError("Support for state '%s' has not yet been implemented." % state)

    return changed, client.role_find(name=name)


def main():
    argument_spec = ipa_argument_spec()
    argument_spec.update(
        cn=dict(type='str', required=True, aliases=['name']),
        description=dict(type='str'),
        group=dict(type='list', elements='str'),
        host=dict(type='list', elements='str'),
        hostgroup=dict(type='list', elements='str'),
        member_action=dict(
            type='str', default='set',
            choices=[
                'add',
                'remove',
                'set',
            ],
        ),
        privilege=dict(type='list', elements='str'),
        service=dict(type='list', elements='str'),
        state=dict(
            type='str', default='present',
            choices=[
                'absent',
                'present',
            ]),
        user=dict(type='list', elements='str')
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    client = RoleIPAClient(module=module,
                           host=module.params['ipa_host'],
                           port=module.params['ipa_port'],
                           protocol=module.params['ipa_prot'])

    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, role = ensure(module, client)
        module.exit_json(changed=changed, role=role)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
