#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017-2018, Keller Fuchs <kellerfuchs@hashbang.sh>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = """
---
module: ldap_passwd
short_description: Set passwords in LDAP.
description:
  - Set a password for an LDAP entry.  This module only asserts that
    a given password is valid for a given entry.  To assert the
    existence of an entry, see M(ldap_entry).
notes:
  - The default authentication settings will attempt to use a SASL EXTERNAL
    bind over a UNIX domain socket. This works well with the default Ubuntu
    install for example, which includes a cn=peercred,cn=external,cn=auth ACL
    rule allowing root to modify the server configuration. If you need to use
    a simple bind to access your server, pass the credentials in I(bind_dn)
    and I(bind_pw).
version_added: '2.6'
author:
  - Keller Fuchs (@KellerFuchs)
requirements:
  - python-ldap
options:
  passwd:
    required: true
    description:
      - The (plaintext) password to be set for I(dn).
extends_documentation_fragment: ldap.documentation
"""

EXAMPLES = """
- name: Set a password for the admin user
  ldap_passwd:
    dn: cn=admin,dc=example,dc=com
    passwd: "{{ vault_secret }}"

- name: Setting passwords in bulk
  ldap_passwd:
    dn: "{{ item.key }}"
    passwd: "{{ item.value }}"
  with_dict:
    alice: alice123123
    bob:   "|30b!"
    admin: "{{ vault_secret }}"
"""

RETURN = """
modlist:
  description: list of modified parameters
  returned: success
  type: list
  sample: '[[2, "olcRootDN", ["cn=root,dc=example,dc=com"]]]'
"""

import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.ldap import LdapGeneric, gen_specs

LDAP_IMP_ERR = None
try:
    import ldap

    HAS_LDAP = True
except ImportError:
    LDAP_IMP_ERR = traceback.format_exc()
    HAS_LDAP = False


class LdapPasswd(LdapGeneric):
    def __init__(self, module):
        LdapGeneric.__init__(self, module)

        # Shortcuts
        self.passwd = self.module.params['passwd']

    def passwd_check(self):
        try:
            tmp_con = ldap.initialize(self.server_uri)
        except ldap.LDAPError as e:
            self.fail("Cannot initialize LDAP connection", e)

        if self.start_tls:
            try:
                tmp_con.start_tls_s()
            except ldap.LDAPError as e:
                self.fail("Cannot start TLS.", e)

        try:
            tmp_con.simple_bind_s(self.dn, self.passwd)
        except ldap.INVALID_CREDENTIALS:
            return True
        except ldap.LDAPError as e:
            self.fail("Cannot bind to the server.", e)
        else:
            return False
        finally:
            tmp_con.unbind()

    def passwd_set(self):
        # Exit early if the password is already valid
        if not self.passwd_check():
            return False

        # Change the password (or throw an exception)
        try:
            self.connection.passwd_s(self.dn, None, self.passwd)
        except ldap.LDAPError as e:
            self.fail("Unable to set password", e)

        # Password successfully changed
        return True


def main():
    module = AnsibleModule(
        argument_spec=gen_specs(passwd=dict(no_log=True)),
        supports_check_mode=True,
    )

    if not HAS_LDAP:
        module.fail_json(msg=missing_required_lib('python-ldap'),
                         exception=LDAP_IMP_ERR)

    ldap = LdapPasswd(module)

    if module.check_mode:
        module.exit_json(changed=ldap.passwd_check())

    module.exit_json(changed=ldap.passwd_set())


if __name__ == '__main__':
    main()
