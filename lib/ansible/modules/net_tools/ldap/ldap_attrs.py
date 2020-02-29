#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Maciej Delmanowski <drybjed@gmail.com>
# Copyright: (c) 2017, Alexander Korinek <noles@a3k.net>
# Copyright: (c) 2016, Peter Sagerson <psagers@ignorare.net>
# Copyright: (c) 2016, Jiri Tyr <jiri.tyr@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = r'''
---
module: ldap_attrs
short_description: Add or remove multiple LDAP attribute values
description:
  - Add or remove multiple LDAP attribute values.
notes:
  - This only deals with attributes on existing entries. To add or remove
    whole entries, see M(ldap_entry).
  - The default authentication settings will attempt to use a SASL EXTERNAL
    bind over a UNIX domain socket. This works well with the default Ubuntu
    install for example, which includes a cn=peercred,cn=external,cn=auth ACL
    rule allowing root to modify the server configuration. If you need to use
    a simple bind to access your server, pass the credentials in I(bind_dn)
    and I(bind_pw).
  - For I(state=present) and I(state=absent), all value comparisons are
    performed on the server for maximum accuracy. For I(state=exact), values
    have to be compared in Python, which obviously ignores LDAP matching
    rules. This should work out in most cases, but it is theoretically
    possible to see spurious changes when target and actual values are
    semantically identical but lexically distinct.
version_added: '2.10'
author:
  - Jiri Tyr (@jtyr)
  - Alexander Korinek (@noles)
  - Maciej Delmanowski (@drybjed)
requirements:
  - python-ldap
options:
  state:
    required: false
    type: str
    choices: [present, absent, exact]
    default: present
    description:
      - The state of the attribute values. If C(present), all given attribute
        values will be added if they're missing. If C(absent), all given
        attribute values will be removed if present. If C(exact), the set of
        attribute values will be forced to exactly those provided and no others.
        If I(state=exact) and the attribute I(value) is empty, all values for
        this attribute will be removed.
  attributes:
    required: true
    type: dict
    description:
      - The attribute(s) and value(s) to add or remove. The complex argument format is required in order to pass
        a list of strings (see examples).
  ordered:
    required: false
    type: bool
    default: 'no'
    description:
      - If C(yes), prepend list values with X-ORDERED index numbers in all
        attributes specified in the current task. This is useful mostly with
        I(olcAccess) attribute to easily manage LDAP Access Control Lists.
extends_documentation_fragment:
- ldap.documentation
'''


EXAMPLES = r'''
- name: Configure directory number 1 for example.com
  ldap_attrs:
    dn: olcDatabase={1}hdb,cn=config
    attributes:
        olcSuffix: dc=example,dc=com
    state: exact

# The complex argument format is required here to pass a list of ACL strings.
- name: Set up the ACL
  ldap_attrs:
    dn: olcDatabase={1}hdb,cn=config
    attributes:
        olcAccess:
          - >-
            {0}to attrs=userPassword,shadowLastChange
            by self write
            by anonymous auth
            by dn="cn=admin,dc=example,dc=com" write
            by * none'
          - >-
            {1}to dn.base="dc=example,dc=com"
            by dn="cn=admin,dc=example,dc=com" write
            by * read
    state: exact

# An alternative approach with automatic X-ORDERED numbering
- name: Set up the ACL
  ldap_attrs:
    dn: olcDatabase={1}hdb,cn=config
    attributes:
        olcAccess:
          - >-
            to attrs=userPassword,shadowLastChange
            by self write
            by anonymous auth
            by dn="cn=admin,dc=example,dc=com" write
            by * none'
          - >-
            to dn.base="dc=example,dc=com"
            by dn="cn=admin,dc=example,dc=com" write
            by * read
    ordered: yes
    state: exact

- name: Declare some indexes
  ldap_attrs:
    dn: olcDatabase={1}hdb,cn=config
    attributes:
        olcDbIndex:
            - objectClass eq
            - uid eq

- name: Set up a root user, which we can use later to bootstrap the directory
  ldap_attrs:
    dn: olcDatabase={1}hdb,cn=config
    attributes:
        olcRootDN: cn=root,dc=example,dc=com
        olcRootPW: "{SSHA}tabyipcHzhwESzRaGA7oQ/SDoBZQOGND"
    state: exact

- name: Remove an attribute with a specific value
  ldap_attrs:
    dn: uid=jdoe,ou=people,dc=example,dc=com
    attributes:
        description: "An example user account"
    state: absent
    server_uri: ldap://localhost/
    bind_dn: cn=admin,dc=example,dc=com
    bind_pw: password

- name: Remove specified attribute(s) from an entry
  ldap_attrs:
    dn: uid=jdoe,ou=people,dc=example,dc=com
    attributes:
        description: []
    state: exact
    server_uri: ldap://localhost/
    bind_dn: cn=admin,dc=example,dc=com
    bind_pw: password
'''


RETURN = r'''
modlist:
  description: list of modified parameters
  returned: success
  type: list
  sample: '[[2, "olcRootDN", ["cn=root,dc=example,dc=com"]]]'
'''

import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native, to_bytes
from ansible.module_utils.ldap import LdapGeneric, gen_specs
import re

LDAP_IMP_ERR = None
try:
    import ldap

    HAS_LDAP = True
except ImportError:
    LDAP_IMP_ERR = traceback.format_exc()
    HAS_LDAP = False


class LdapAttrs(LdapGeneric):
    def __init__(self, module):
        LdapGeneric.__init__(self, module)

        # Shortcuts
        self.attrs = self.module.params['attributes']
        self.state = self.module.params['state']
        self.ordered = self.module.params['ordered']

    def _order_values(self, values):
        """ Preprend X-ORDERED index numbers to attribute's values. """
        ordered_values = []

        if isinstance(values, list):
            for index, value in enumerate(values):
                cleaned_value = re.sub(r'^\{\d+\}', '', value)
                ordered_values.append('{' + str(index) + '}' + cleaned_value)

        return ordered_values

    def _normalize_values(self, values):
        """ Normalize attribute's values. """
        norm_values = []

        if isinstance(values, list):
            if self.ordered:
                norm_values = list(map(to_bytes,
                                   self._order_values(list(map(str,
                                                               values)))))
            else:
                norm_values = list(map(to_bytes, values))
        else:
            norm_values = [to_bytes(str(values))]

        return norm_values

    def add(self):
        modlist = []
        for name, values in self.module.params['attributes'].items():
            norm_values = self._normalize_values(values)
            for value in norm_values:
                if self._is_value_absent(name, value):
                    modlist.append((ldap.MOD_ADD, name, value))

        return modlist

    def delete(self):
        modlist = []
        for name, values in self.module.params['attributes'].items():
            norm_values = self._normalize_values(values)
            for value in norm_values:
                if self._is_value_present(name, value):
                    modlist.append((ldap.MOD_DELETE, name, value))

        return modlist

    def exact(self):
        modlist = []
        for name, values in self.module.params['attributes'].items():
            norm_values = self._normalize_values(values)
            try:
                results = self.connection.search_s(
                    self.dn, ldap.SCOPE_BASE, attrlist=[name])
            except ldap.LDAPError as e:
                self.fail("Cannot search for attribute %s" % name, e)

            current = results[0][1].get(name, [])

            if frozenset(norm_values) != frozenset(current):
                if len(current) == 0:
                    modlist.append((ldap.MOD_ADD, name, norm_values))
                elif len(norm_values) == 0:
                    modlist.append((ldap.MOD_DELETE, name, None))
                else:
                    modlist.append((ldap.MOD_REPLACE, name, norm_values))

        return modlist

    def _is_value_present(self, name, value):
        """ True if the target attribute has the given value. """
        try:
            is_present = bool(
                self.connection.compare_s(self.dn, name, value))
        except ldap.NO_SUCH_ATTRIBUTE:
            is_present = False

        return is_present

    def _is_value_absent(self, name, value):
        """ True if the target attribute doesn't have the given value. """
        return not self._is_value_present(name, value)


def main():
    module = AnsibleModule(
        argument_spec=gen_specs(
            attributes=dict(type='dict', required=True),
            ordered=dict(type='bool', default=False, required=False),
            state=dict(type='str', default='present', choices=['absent', 'exact', 'present']),
        ),
        supports_check_mode=True,
    )

    if not HAS_LDAP:
        module.fail_json(msg=missing_required_lib('python-ldap'),
                         exception=LDAP_IMP_ERR)

    # Instantiate the LdapAttr object
    ldap = LdapAttrs(module)

    state = module.params['state']

    # Perform action
    if state == 'present':
        modlist = ldap.add()
    elif state == 'absent':
        modlist = ldap.delete()
    elif state == 'exact':
        modlist = ldap.exact()

    changed = False

    if len(modlist) > 0:
        changed = True

        if not module.check_mode:
            try:
                ldap.connection.modify_s(ldap.dn, modlist)
            except Exception as e:
                module.fail_json(msg="Attribute action failed.", details=to_native(e))

    module.exit_json(changed=changed, modlist=modlist)


if __name__ == '__main__':
    main()
