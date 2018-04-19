#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017-2018, Keller Fuchs <kellerfuchs@hashbang.sh>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


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
  - Keller Fuchs (@kellerfuchs)
requirements:
  - python-ldap
options:
  passwd:
    required: true
    default: null
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
    alice: "alice123123"
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ldap import LdapGeneric, gen_specs, HAS_LDAP
from ansible.module_utils._text import to_native

try:
    import ldap
except ImportError:
    HAS_LDAP = False


class LdapPasswd(LdapGeneric):
    def __init__(self, module):
        LdapGeneric.__init__(self, module)

        # Shortcuts
        self.passwd = self.module.params['passwd']

    def passwd_check(self):
        u_con = ldap.initialize(self.server_uri)

        if self.start_tls:
            try:
                u_con.start_tls_s()
            except ldap.LDAPError as e:
                self.fail("Cannot start TLS.", e)

        try:
            u_con.simple_bind_s(self.dn, self.passwd)
        except ldap.INVALID_CREDENTIALS:
            return True
        except ldap.LDAPError as e:
            self.fail("Cannot bind to the server.", e)
        else:
            return False
        finally:
            u_con.unbind()

    def passwd_set(self):
        # Exit early if the password is already valid
        if not self.passwd_check():
            return False

        # Change the password (or throw an exception)
        self.connection.passwd_set(self.dn, None, self.passwd)

        # We successfully changed the password  \o/
        return True


def main():
    module = AnsibleModule(
        argument_spec=gen_specs(passwd=dict(no_log=True)),
        supports_check_mode=True,
    )

    if not HAS_LDAP:
        module.fail_json(
            msg="Missing required 'ldap' module (pip install python-ldap).")

    ldap = LdapPasswd(module)

    try:
        if module.check_mode:
            module.exit_json(changed=ldap.passwd_check())
        else:
            module.exit_json(changed=ldap.passwd_set())
    except Exception as e:
        ldap.fail("Passwd action failed.", e)


if __name__ == '__main__':
    main()
