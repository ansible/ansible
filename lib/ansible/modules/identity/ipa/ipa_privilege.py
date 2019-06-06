#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: ipa_privilege
author: Lek (@HaloGithub)
short_description: Manage FreeIPA RBAC privilege. Tested on FreeIPA v4.6.4.
description:
- Add, modify and delete a privilege within FreeIPA server using FreeIPA API.
options:
  cn:
    description: Privilege name.
    required: true
    aliases: ['name']
  description:
    description: A description of this privilege.
  permission:
    description: |
      List of permission assig to this privilege.
      If an empty list is passed all assigned permissions will be unassigned from the privilege.
      If option is omitted permissions will not be checked or changed.
      If option is passed all assigned permissions that are not passed will be unassigned from the privilege.
  rename:
    description: |
      A new name to apply to a privilege object.
      Origin privilege must be exist.
  state:
    description: State to ensure.
    default: "present"
    choices: ["present", "absent"]
extends_documentation_fragment: ipa.documentation
version_added: "2.9"
'''

EXAMPLES = '''
# Ensure privilege is present.
- ipa_privilege:
    cn: Database Administrators
    description: Database Administrators
    permission:
      - Read User Membership
    state: present
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: secret

# Rename privilege.
- ipa_privilege:
    cn: Database Administrators
    rename: MySQL Database Administrators
    state: present
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: secret

# Ensure privilege is absent.
- ipa_privilege:
    cn: MySQL Database Administrators
    state: absent
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: secret
'''

RETURN = '''
privilege:
  description: Privilege as returned by IPA API.
  returned: always
  type: dict
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import IPAClient, ipa_argument_spec
from ansible.module_utils._text import to_native


class PrivilegeAttrs:
    NAME = 'cn'
    DESCRIPTION = 'description'
    PERMISSION = 'permission'
    RENAME = 'rename'


class PrivilegeIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(PrivilegeIPAClient, self).__init__(module, host, port, protocol)

    def check_permissions(self, items):
        for item in items:
            body = {'cn': item}
            result = self._post_json(method='permission_find', name=None, item=body)
            if not result:
                raise Exception('Permission not found: {perm}.'.format(perm=item))

    def privilege_add(self, name, item):
        # Remove `cn` property, or it will show error:
        #   response privilege_add: overlapping arguments and options: ['cn']
        if PrivilegeAttrs.NAME in item:
            del item[PrivilegeAttrs.NAME]

        # Create privilege should not include `rename` attr.
        if PrivilegeAttrs.RENAME in item:
            del item[PrivilegeAttrs.RENAME]

        return self._post_json(method='privilege_add', name=name, item=item)

    def privilege_del(self, name):
        return self._post_json(method='privilege_del', name=name)

    def privilege_find(self, name):
        body = {'all': True, 'cn': name}
        return self._post_json(method='privilege_find', name=None, item=body)

    def privilege_mod(self, name, item):
        return self._post_json(method='privilege_mod', name=name, item=item)

    def privilege_add_permission(self, name, item):
        body = {'permission': item}
        return self._post_json(method='privilege_add_permission', name=name, item=body)

    def privilege_remove_permission(self, name, item):
        body = {'permission': item}
        return self._post_json(method='privilege_remove_permission', name=name, item=body)


def get_privilege_dict(module_params):
    data = dict()
    properties = [
        PrivilegeAttrs.NAME,
        PrivilegeAttrs.DESCRIPTION,
        PrivilegeAttrs.RENAME,
    ]

    for _property in properties:
        if _property in module_params and module_params[_property] is not None:
            data[_property] = module_params[_property]

    return data


def get_privilege_diff(client, ipa_privilege, module_privilege):
    return client.get_diff(ipa_privilege, module_privilege)


def ensure(module, client):
    name = module.params[PrivilegeAttrs.NAME]
    permission = module.params[PrivilegeAttrs.PERMISSION]
    rename = module.params[PrivilegeAttrs.RENAME]
    state = module.params['state']

    changed = False
    renamed = False

    # New privilege going to apply.
    module_priv = get_privilege_dict(module.params)
    # Original privilege.
    ipa_priv = client.privilege_find(name)
    if rename is not None and not ipa_priv:
        raise Exception('Privilege "{name}" not found, cannot rename.'.format(name=name))

    if state == 'present':

        # Check permissions exist first.
        if permission is not None:
            client.check_permissions(permission)

        if not ipa_priv:
            changed = True
            if not module.check_mode:
                client.privilege_add(name=name, item=module_priv)
        else:
            diff = get_privilege_diff(client, ipa_priv, module_priv)
            if len(diff) > 0:
                changed = True
                if not module.check_mode:
                    renamed = PrivilegeAttrs.RENAME in diff
                    data = {}
                    for key in diff:
                        origin_value = ipa_priv.get(key)
                        new_value = module_priv.get(key)
                        data[key] = new_value
                    client.privilege_mod(name=name, item=data)

        if permission is not None:
            # If renamed above, then search with new privilege name.
            # otherwise, use origin privilege new.
            priv_name = rename if renamed else name
            changed = client.modify_if_diff(priv_name, ipa_priv.get('memberof_permission', []), permission,
                                            client.privilege_add_permission,
                                            client.privilege_remove_permission) or changed
    else:
        if ipa_priv:
            changed = True
            if not module.check_mode:
                client.privilege_del(name)

    if not renamed:
        new_priv = client.privilege_find(name)
    else:
        new_priv = client.privilege_find(rename)

    return changed, new_priv


def main():
    argument_spec = ipa_argument_spec()
    argument_spec.update(
        cn=dict(type='str', required=True, aliases=['name']),
        description=dict(type='str'),
        permission=dict(type='list'),
        rename=dict(type='str'),
        state=dict(type='str', default='present', choices=['present', 'absent'])
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    client = PrivilegeIPAClient(module=module,
                                host=module.params['ipa_host'],
                                port=module.params['ipa_port'],
                                protocol=module.params['ipa_prot'])

    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, privilege = ensure(module, client)
        module.exit_json(changed=changed, privilege=privilege)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
