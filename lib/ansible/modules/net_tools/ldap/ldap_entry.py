#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Peter Sagerson <psagers@ignorare.net>
# (c) 2016, Jiri Tyr <jiri.tyr@gmail.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: ldap_entry
short_description: Add or remove LDAP entries.
description:
  - Add or remove LDAP entries. This module only asserts the existence or
    non-existence of an LDAP entry, not its attributes. To assert the
    attribute values of an entry, see M(ldap_attr).
notes:
  - The default authentication settings will attempt to use a SASL EXTERNAL
    bind over a UNIX domain socket. This works well with the default Ubuntu
    install for example, which includes a cn=peercred,cn=external,cn=auth ACL
    rule allowing root to modify the server configuration. If you need to use
    a simple bind to access your server, pass the credentials in I(bind_dn)
    and I(bind_pw).
version_added: '2.3'
author:
  - Jiri Tyr (@jtyr)
requirements:
  - python-ldap
options:
  bind_dn:
    required: false
    default: null
    description:
      - A DN to bind with. If this is omitted, we'll try a SASL bind with
        the EXTERNAL mechanism. If this is blank, we'll use an anonymous
        bind.
  bind_pw:
    required: false
    default: null
    description:
      - The password to use with I(bind_dn).
  dn:
    required: true
    description:
      - The DN of the entry to add or remove.
  attributes:
    required: false
    default: null
    description:
      - If I(state=present), attributes necessary to create an entry. Existing
        entries are never modified. To assert specific attribute values on an
        existing entry, use M(ldap_attr) module instead.
  objectClass:
    required: false
    default: null
    description:
      - If I(state=present), value or list of values to use when creating
        the entry. It can either be a string or an actual list of
        strings.
  params:
    required: false
    default: null
    description:
      - List of options which allows to overwrite any of the task or the
        I(attributes) options. To remove an option, set the value of the option
        to C(null).
  server_uri:
    required: false
    default: ldapi:///
    description:
      - A URI to the LDAP server. The default value lets the underlying
        LDAP client library look for a UNIX domain socket in its default
        location.
  start_tls:
    required: false
    choices: ['yes', 'no']
    default: 'no'
    description:
      - If true, we'll use the START_TLS LDAP extension.
  state:
    required: false
    choices: [present, absent]
    default: present
    description:
      - The target state of the entry.
  validate_certs:
    required: false
    choices: ['yes', 'no']
    default: 'yes'
    description:
      - If C(no), SSL certificates will not be validated. This should only be
        used on sites using self-signed certificates.
    version_added: "2.4"
"""


EXAMPLES = """
- name: Make sure we have a parent entry for users
  ldap_entry:
    dn: ou=users,dc=example,dc=com
    objectClass: organizationalUnit

- name: Make sure we have an admin user
  ldap_entry:
    dn: cn=admin,dc=example,dc=com
    objectClass:
      - simpleSecurityObject
      - organizationalRole
    attributes:
      description: An LDAP administrator
      userPassword: "{SSHA}tabyipcHzhwESzRaGA7oQ/SDoBZQOGND"

- name: Get rid of an old entry
  ldap_entry:
    dn: ou=stuff,dc=example,dc=com
    state: absent
    server_uri: ldap://localhost/
    bind_dn: cn=admin,dc=example,dc=com
    bind_pw: password

#
# The same as in the previous example but with the authentication details
# stored in the ldap_auth variable:
#
# ldap_auth:
#   server_uri: ldap://localhost/
#   bind_dn: cn=admin,dc=example,dc=com
#   bind_pw: password
- name: Get rid of an old entry
  ldap_entry:
    dn: ou=stuff,dc=example,dc=com
    state: absent
    params: "{{ ldap_auth }}"
"""


RETURN = """
# Default return values
"""

import traceback

try:
    import ldap
    import ldap.modlist
    import ldap.sasl

    HAS_LDAP = True
except ImportError:
    HAS_LDAP = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native


class LdapEntry(object):
    def __init__(self, module):
        # Shortcuts
        self.module = module
        self.bind_dn = self.module.params['bind_dn']
        self.bind_pw = self.module.params['bind_pw']
        self.dn = self.module.params['dn']
        self.server_uri = self.module.params['server_uri']
        self.start_tls = self.module.params['start_tls']
        self.state = self.module.params['state']
        self.verify_cert = self.module.params['validate_certs']

        # Add the objectClass into the list of attributes
        self.module.params['attributes']['objectClass'] = (
            self.module.params['objectClass'])

        # Load attributes
        if self.state == 'present':
            self.attrs = self._load_attrs()

        # Establish connection
        self.connection = self._connect_to_ldap()

    def _load_attrs(self):
        """ Turn attribute's value to array. """
        attrs = {}

        for name, value in self.module.params['attributes'].items():
            if name not in attrs:
                attrs[name] = []

            if isinstance(value, list):
                attrs[name] = value
            else:
                attrs[name].append(str(value))

        return attrs

    def add(self):
        """ If self.dn does not exist, returns a callable that will add it. """
        def _add():
            self.connection.add_s(self.dn, modlist)

        if not self._is_entry_present():
            modlist = ldap.modlist.addModlist(self.attrs)
            action = _add
        else:
            action = None

        return action

    def delete(self):
        """ If self.dn exists, returns a callable that will delete it. """
        def _delete():
            self.connection.delete_s(self.dn)

        if self._is_entry_present():
            action = _delete
        else:
            action = None

        return action

    def _is_entry_present(self):
        try:
            self.connection.search_s(self.dn, ldap.SCOPE_BASE)
        except ldap.NO_SUCH_OBJECT:
            is_present = False
        else:
            is_present = True

        return is_present

    def _connect_to_ldap(self):
        if not self.verify_cert:
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

        connection = ldap.initialize(self.server_uri)

        if self.start_tls:
            try:
                connection.start_tls_s()
            except ldap.LDAPError as e:
                self.module.fail_json(msg="Cannot start TLS.", details=to_native(e),
                                      exception=traceback.format_exc())

        try:
            if self.bind_dn is not None:
                connection.simple_bind_s(self.bind_dn, self.bind_pw)
            else:
                connection.sasl_interactive_bind_s('', ldap.sasl.external())
        except ldap.LDAPError as e:
            self.module.fail_json(
                msg="Cannot bind to the server.", details=to_native(e),
                exception=traceback.format_exc())

        return connection


def main():
    module = AnsibleModule(
        argument_spec={
            'attributes': dict(default={}, type='dict'),
            'bind_dn': dict(),
            'bind_pw': dict(default='', no_log=True),
            'dn': dict(required=True),
            'objectClass': dict(type='raw'),
            'params': dict(type='dict'),
            'server_uri': dict(default='ldapi:///'),
            'start_tls': dict(default=False, type='bool'),
            'state': dict(default='present', choices=['present', 'absent']),
            'validate_certs': dict(default=True, type='bool'),
        },
        supports_check_mode=True,
    )

    if not HAS_LDAP:
        module.fail_json(
            msg="Missing required 'ldap' module (pip install python-ldap).")

    state = module.params['state']

    # Check if objectClass is present when needed
    if state == 'present' and module.params['objectClass'] is None:
        module.fail_json(msg="At least one objectClass must be provided.")

    # Check if objectClass is of the correct type
    if (
            module.params['objectClass'] is not None and not (
                isinstance(module.params['objectClass'], string_types) or
                isinstance(module.params['objectClass'], list))):
        module.fail_json(msg="objectClass must be either a string or a list.")

    # Update module parameters with user's parameters if defined
    if 'params' in module.params and isinstance(module.params['params'], dict):
        for key, val in module.params['params'].items():
            if key in module.argument_spec:
                module.params[key] = val
            else:
                module.params['attributes'][key] = val

        # Remove the params
        module.params.pop('params', None)

    # Instantiate the LdapEntry object
    ldap = LdapEntry(module)

    # Get the action function
    if state == 'present':
        action = ldap.add()
    elif state == 'absent':
        action = ldap.delete()

    # Perform the action
    if action is not None and not module.check_mode:
        try:
            action()
        except Exception as e:
            module.fail_json(msg="Entry action failed.", details=to_native(e), exception=traceback.format_exc())

    module.exit_json(changed=(action is not None))


if __name__ == '__main__':
    main()
