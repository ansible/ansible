#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Guillaume Smaha <guillaume.smaha@gmail.com>
# https://github.com/GuillaumeSmaha/
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: ldap_get
short_description: Search for an LDAP entries.
description:
  - Search for an LDAP entries by dn or filter and return the result
notes:
  - The default authentication settings will attempt to use a SASL EXTERNAL
    bind over a UNIX domain socket. This works well with the default Ubuntu
    install for example, which includes a cn=peercred,cn=external,cn=auth ACL
    rule allowing root to modify the server configuration. If you need to use
    a simple bind to access your server, pass the credentials in I(bind_dn)
    and I(bind_pw).
version_added: '2.7'
author:
  - Guillaume Smaha
requirements:
  - ldap3
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
    required: false
    description:
      - The DN of the entry to add or update.
  search_base:
    required: false
    description:
      - The location in the directory information tree (DIT) where the search will start
  search_filter:
    required: false
    description:
      - The filter to search the entries to return.
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
    type: bool
    default: False
    description:
      - If true, we'll use the START_TLS LDAP extension.
  validate_certs:
    required: false
    type: bool
    default: True
    description:
      - If C(no), SSL certificates will not be validated. This should only be
        used on sites using self-signed certificates.
  first_only:
    required: false
    choices: ['yes', 'no', 'auto']
    default: 'auto'
    description:
      - Define if the first entry is only returned.
        WIth 'auto', it set to true when dn is defined else it set to 'no'
"""

EXAMPLES = """
- name: Get an user by dn entry
  ldap_get:
    dn: cn=admin,dc=example,dc=com
  register: ldap_result

- name: Look for all admin user
  ldap_get:
    search_base: dc=example,dc=com
    search_filter: (user_type=admin)
  register: ldap_result

- name: Look for the first admin user
  ldap_get:
    search_base: dc=example,dc=com
    search_filter: (user_type=admin)
    first_only: yes
  register: ldap_result

#
# The same as in the previous example but with the authentication details
# stored in the ldap_auth variable:
#
# ldap_auth:
#   server_uri: ldap://localhost/
#   bind_dn: cn=admin,dc=example,dc=com
#   bind_pw: password
- name: Make sure we have an admin user
  ldap_get:
    params: "{{ ldap_auth }}"
    search_base: dc=example,dc=com
    search_filter: (user_type=admin)
    first_only: yes
  register: ldap_result
"""

RETURN = """
entries:
  description: list of entries found first_only = 'no'
  returned: success
  type: list
  sample: '[
    {"dn": cn=root,dc=example,dc=com", "attributes": {"objectClass": ["person"]}},
    {"dn": "cn=admin,dc=example,dc=com", "attributes": {"objectClass": ["person"]}}
  ]'
entry:
  description: the first entry when first_only = 'yes'
  returned: success
  type: dict
  sample: '{"dn": "cn=admin,dc=example,dc=com", "attributes": {"objectClass": ["person"]}}'
"""

from ansible.module_utils.basic import AnsibleModule

try:
    import ldap3
    from ldap3.core.exceptions import LDAPException
    import ssl

    HAS_LDAP3 = True
except ImportError:
    HAS_LDAP3 = False


class LdapEntries(object):
    def __init__(self, module):
        # Shortcuts
        self.module = module
        self.server_uri = self.module.params['server_uri']
        self.bind_dn = self.module.params['bind_dn']
        self.bind_pw = self.module.params['bind_pw']
        self.start_tls = self.module.params['start_tls']
        self.validate_certs = self.module.params['validate_certs']
        self.dn = self.module.params['dn']
        self.search_base = self.module.params['search_base']
        self.search_filter = self.module.params['search_filter']

        # Establish connection
        self.connection = self._connect_to_ldap()

    def search_entries(self):
        """ Search with the serach_filter and return an array of entries """
        result = False
        if self.dn:
            result = self.connection.search(
                self.dn, '', search_scope=ldap3.SUBTREE, attributes=ldap3.ALL_ATTRIBUTES)
        else:
            result = self.connection.search(
                self.search_base, self.search_filter, search_scope=ldap3.SUBTREE, attributes=ldap3.ALL_ATTRIBUTES)

        if result:
            return self.connection.response

        return None

    def close(self):
        if self.connection:
            self.connection.unbind()

    def _connect_to_ldap(self):
        if self.start_tls or self.server_uri.lower().startswith('ldaps://'):
            self.start_tls = True

            tls = None
            if self.validate_certs:
                tls = ldap3.Tls(validate=ssl.CERT_OPTIONAL)
            else:
                tls = ldap3.Tls(validate=ssl.CERT_NONE)

            try:
                server = ldap3.Server(self.server_uri, tls=tls, use_ssl=True)

            except LDAPException as e:
                self.module.fail_json(
                    msg="Invalid parameter for LDAP server.", details=str(e))
        else:
            server = ldap3.Server(self.server_uri)

        try:
            if self.bind_dn is not None:
                connection = ldap3.Connection(server, auto_bind=False,
                                              user=self.bind_dn, password=self.bind_pw)
            else:
                connection = ldap3.Connection(server, auto_bind=False, authentication=ldap3.SASL,
                                              sasl_mechanism='EXTERNAL', sasl_credentials='')

            if self.start_tls:
                try:
                    connection.start_tls()
                except LDAPException as e:
                    self.module.fail_json(
                        msg="Cannot start TLS.", details=str(e))

            connection.bind()

        except LDAPException as e:
            self.module.fail_json(
                msg="Cannot bind to the server.", details=str(e))

        return connection


def get_clean_entry(entry):
    return {
        'dn': entry['dn'],
        'attributes': entry['attributes']
    }


def main():
    module = AnsibleModule(
        argument_spec={
            'server_uri': dict(default='ldapi:///'),
            'bind_dn': dict(),
            'bind_pw': dict(default='', no_log=True),
            'start_tls': dict(default=False, type='bool'),
            'validate_certs': dict(default=True, type='bool'),
            'dn': dict(),
            'search_base': dict(default=''),
            'search_filter': dict(),
            'first_only': dict(default='auto', choices=['yes', 'no', 'auto']),
            'params': dict(type='dict'),
        },
        required_one_of=[['dn', 'search_filter']],
        supports_check_mode=True,
    )

    first_only = module.params['first_only']
    if first_only == 'auto':
        if module.params['dn']:
            first_only = 'yes'
        else:
            first_only = 'no'

    if not HAS_LDAP3:
        module.fail_json(
            msg="Missing required 'ldap' module (pip install ldap3).")

    # Update module parameters with user's parameters if defined
    if 'params' in module.params and isinstance(module.params['params'], dict):
        for key, val in module.params['params'].items():
            if key in module.argument_spec:
                module.params[key] = val
            else:
                module.params['attributes'][key] = val

        # Remove the params
        module.params.pop('params', None)

    # Instantiate the LdapEntries object
    ldap_entries = LdapEntries(module)

    # Search for all entries
    entries = ldap_entries.search_entries()

    ldap_entries.close()

    if not entries:
        if module.params['dn']:
            module.fail_json(
                msg="No entry found for this dn %s" % module.params['dn'],
                dn=module.params['dn'])
        else:
            module.fail_json(
                msg="No entry found for this search_filter %s" % module.params['search_filter'],
                search_base=module.params['search_base'],
                search_filter=module.params['search_filter'])

    if first_only == 'yes':
        result = get_clean_entry(entries[0])
        module.exit_json(entry=result)
    else:
        result = []
        for entry in entries:
            result.append(get_clean_entry(entry))

        module.exit_json(entries=result)


if __name__ == '__main__':
    main()
