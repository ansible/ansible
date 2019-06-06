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
module: ipa_permission
author: Lek (@HaloGithub)
short_description: Manage FreeIPA RBAC permission. Tested on FreeIPA v4.6.4.
description:
- Add, modify and delete a permission within FreeIPA server using FreeIPA API.
options:
  cn:
    description: Permission name.
    required: true
    aliases: ['name']
  ipapermbindruletype:
    description: Bind rule type.
    required: true
    choices: ["permission", "all", "anonymous"]
  ipapermright:
    description: |
      Permission rights.
      Valid options: read, search, compare, write, add, delete, all.
  type:
    description: |
      Type of IPA object (sets subtree and objectClass targetfilter).
      `type` & `ipapermlocation` are mutually exclusive.
      `type` & `ipapermtarget` are mutually exclusive.
  ipapermlocation:
    description: Subtree to apply permissions to.
  extratargetfilter:
    description: Extra target filter.
  ipapermtarget:
    description: Optional DN to apply the permission to (must be in the subtree, but may not yet exist).
  memberof:
    description: Target members of a group (sets memberOf targetfilter).
  attrs:
    description: All attributes to which the permission applies.
  rename:
    description: A new name to apply to a permission object. Origin permission must be exist.
  state:
    description: State to ensure.
    default: "present"
    choices: ["present", "absent"]
extends_documentation_fragment: ipa.documentation
version_added: "2.9"
'''

EXAMPLES = '''
# Ensure permission is present.
- ipa_permission:
    cn: Read User OU Attribute
    ipapermbindruletype: permission
    ipapermright:
      - read
    type: user
    attrs:
      - ou
    state: present
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: secret

# Rename permission.
- ipa_permission:
    cn: Read User OU Attribute
    ipapermbindruletype: permission
    rename: "System: Read User OU Attribute"
    state: present
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: secret

# Ensure permission is absent.
- ipa_permission:
    cn: Read User OU Attribute
    ipapermbindruletype: permission
    state: absent
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: secret
'''

RETURN = '''
permission:
  description: Permission as returned by IPA API.
  returned: always
  type: dict
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import IPAClient, ipa_argument_spec
from ansible.module_utils._text import to_native


class PermissionAttrs:
    NAME = 'cn'
    IPA_PERM_BIND_RULE_TYPE = 'ipapermbindruletype'
    IPA_PERM_RIGHT = 'ipapermright'
    TYPE = 'type'
    IPA_PERM_LOCATION = 'ipapermlocation'
    EXTRA_TARGET_FILTER = 'extratargetfilter'
    IPA_PERM_TARGET = 'ipapermtarget'
    MEMBER_OF = 'memberof'
    ATTRS = 'attrs'
    RENAME = 'rename'
    # Is below properties obsolete?
    #
    # IPA_PERM_INCLUDED_ATTR = 'ipapermincludedattr'
    # IPA_PERM_EXCLUDED_ATTR = 'ipapermexcludedattr'
    # IPA_PERM_TARGET_FILTER = 'ipapermtargetfilter'
    # IPA_PERM_TARGET_TO     = 'ipapermtargetto'
    # IPA_PERM_TARGET_FROM   = 'ipapermtargetfrom'
    # TARGET_GROUP           = 'targetgroup'
    # NO_MEMBERS             = 'no_members'


class PermissionIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(PermissionIPAClient, self).__init__(module, host, port, protocol)

    def permission_add(self, name, item):
        # Remove `cn` property, or it will show error:
        #   response permission_add: overlapping arguments and options: ['cn']
        if PermissionAttrs.NAME in item:
            del item[PermissionAttrs.NAME]

        # Create permission should not include `rename` attr.
        if PermissionAttrs.RENAME in item:
            del item[PermissionAttrs.RENAME]

        return self._post_json(method='permission_add', name=name, item=item)

    def permission_del(self, name):
        return self._post_json(method='permission_del', name=name)

    def permission_find(self, name):
        body = {'all': True, 'cn': name}
        return self._post_json(method='permission_find', name=None, item=body)

    def permission_mod(self, name, item):
        return self._post_json(method='permission_mod', name=name, item=item)


def get_permission_dict(module_params):
    data = dict()
    properties = [
        PermissionAttrs.NAME,
        PermissionAttrs.IPA_PERM_BIND_RULE_TYPE,
        PermissionAttrs.IPA_PERM_RIGHT,
        PermissionAttrs.TYPE,
        PermissionAttrs.IPA_PERM_LOCATION,
        PermissionAttrs.EXTRA_TARGET_FILTER,
        PermissionAttrs.IPA_PERM_TARGET,
        PermissionAttrs.MEMBER_OF,
        PermissionAttrs.ATTRS,
        PermissionAttrs.RENAME,
    ]

    for _property in properties:
        if _property in module_params and module_params[_property] is not None:
            data[_property] = module_params[_property]

    # NOTE: Base on https://www.redhat.com/archives/freeipa-devel/2013-December/msg00045.html
    #
    # - type & ipapermlocation are mutually exclusive
    # - type & ipapermtarget are mutually exclusive
    # - targetgroup & ipapermtarget are mutually exclusive
    # - memberof & ipapermtargetfilter are mutually exclusive

    return data


def get_permission_diff(client, ipa_permission, module_permission):
    return client.get_diff(ipa_permission, module_permission)


def ensure(module, client):
    name = module.params[PermissionAttrs.NAME]
    ipa_perm_bind_rule_type = module.params[PermissionAttrs.IPA_PERM_BIND_RULE_TYPE]
    ipa_perm_right = module.params[PermissionAttrs.IPA_PERM_RIGHT]
    ipa_object_type = module.params[PermissionAttrs.TYPE]
    ipa_perm_location = module.params[PermissionAttrs.IPA_PERM_LOCATION]
    extra_target_filter = module.params[PermissionAttrs.EXTRA_TARGET_FILTER]
    ipa_perm_target = module.params[PermissionAttrs.IPA_PERM_TARGET]
    member_of = module.params[PermissionAttrs.MEMBER_OF]
    attrs = module.params[PermissionAttrs.ATTRS]
    rename = module.params[PermissionAttrs.RENAME]
    state = module.params['state']

    changed = False
    renamed = False

    # New permission going to apply.
    module_perm = get_permission_dict(module.params)
    # Original permission.
    ipa_perm = client.permission_find(name)
    if rename is not None and not ipa_perm:
        raise Exception('Permission "{name}" not found, cannot rename.'.format(name=name))

    if state == 'present':
        if not ipa_perm:
            changed = True
            if not module.check_mode:
                client.permission_add(name=name, item=module_perm)
        else:
            diff = get_permission_diff(client, ipa_perm, module_perm)
            if len(diff) > 0:
                changed = True
                if not module.check_mode:
                    renamed = PermissionAttrs.RENAME in diff
                    data = {}
                    for key in diff:
                        origin_value = ipa_perm.get(key)
                        new_value = module_perm.get(key)
                        data[key] = new_value
                    client.permission_mod(name=name, item=data)
    else:
        if ipa_perm:
            changed = True
            if not module.check_mode:
                client.permission_del(name)

    if not renamed:
        new_perm = client.permission_find(name)
    else:
        new_perm = client.permission_find(rename)

    return changed, new_perm


def main():
    argument_spec = ipa_argument_spec()
    argument_spec.update(
        cn=dict(type='str', required=True, aliases=['name']),
        ipapermbindruletype=dict(type='str', required=True, choices=['permission', 'all', 'anonymous']),
        ipapermright=dict(type='list'),
        type=dict(type='str'),
        ipapermlocation=dict(type='str'),
        extratargetfilter=dict(type='list'),
        ipapermtarget=dict(type='str'),
        memberof=dict(type='list'),
        attrs=dict(type='list'),
        rename=dict(type='str'),
        # ipapermtargetfilter=dict(type='list'),
        # ipapermtargetto=dict(type='str'),
        # ipapermtargetfrom=dict(type='str'),
        # targetgroup=dict(type='str'),
        state=dict(type='str', default='present', choices=['present', 'absent'])
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    client = PermissionIPAClient(module=module,
                                 host=module.params['ipa_host'],
                                 port=module.params['ipa_port'],
                                 protocol=module.params['ipa_prot'])

    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, permission = ensure(module, client)
        module.exit_json(changed=changed, permission=permission)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
