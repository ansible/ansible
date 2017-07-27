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
lookup: ldap
author: 'Guillaume Smaha <guillaume.smaha (at) gmail.com>'
version_added: "2.7"
short_description: lookup info from ldap
description:
  - Search for an LDAP entries by dn or filter and return the result
notes:
  - The default authentication settings will attempt to use a SASL EXTERNAL
    bind over a UNIX domain socket. This works well with the default Ubuntu
    install for example, which includes a cn=peercred,cn=external,cn=auth ACL
    rule allowing root to modify the server configuration. If you need to use
    a simple bind to access your server, pass the credentials in I(bind_dn)
    and I(bind_pw).
requirements:
  - ldap3
options:
    server_uri:
        required: False
        default: ldapi:///
        description:
          - A URI to the LDAP server. The default value lets the underlying
            LDAP client library look for a UNIX domain socket in its default
            location.
    bind_dn:
        required: False
        default: null
        description:
          - A DN to bind with. If this is omitted, we'll try a SASL bind with
            the EXTERNAL mechanism. If this is blank, we'll use an anonymous
            bind.
    bind_pw:
        required: False
        default: null
        description:
          - The password to use with I(bind_dn).
    start_tls:
        required: False
        type: bool
        default: False
        description:
          - If True, we'll use the START_TLS LDAP extension.
    validate_certs:
        required: False
        type: bool
        default: True
        description:
          - If C(no), SSL certificates will not be validated. This should only be
            used on sites using self-signed certificates.
    dn:
        required: False
        description:
          - The DN of the entry to return.
    search_base:
        required: False
        description:
          - The location in the directory information tree (DIT) where the search will start
    search_filter:
        required: False
        description:
          - The filter to search the entries to return.
"""

EXAMPLES = """
- hosts: all
  gather_facts: False
  vars:
    ldap_user_admin:
        server_uri: ldap://localhost/
        bind_dn: cn=admin,dc=example,dc=com
        bind_pw: password
        dn: cn=admin,dc=example,dc=com

    ldap_users_admin:
        server_uri: ldap://localhost/
        bind_dn: cn=admin,dc=example,dc=com
        bind_pw: password
        search_base: dc=example,dc=com
        search_filter: (user_type=admin)

  tasks:
   - name: Get an user by dn entry
     debug: msg="Admin User= [{{ item.attributes.display_name }}]"
     with_items:
      - "{{ lookup('ldap', ldap_user_admin) }}"

   - name: Look for all admin user
     debug: msg="Admin User DN= [{{ item.dn }}]"
     with_items:
      - "{{ lookup('ldap', ldap_users_admin) }}"

   - name: Look for all admin user by calling with_ldap
     debug: msg="Admin User DN= [{{ item.dn }}]"
     with_ldap: "{{ldap_users_admin}}"
"""

RETURN = """
entries:
  description: list of entries
  returned: success
  type: list
  sample: '[
    {"dn": cn=root,dc=example,dc=com", "attributes": {"objectClass": ["person"]}},
    {"dn": "cn=admin,dc=example,dc=com", "attributes": {"objectClass": ["person"]}}
  ]'
"""

import os

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.six import string_types, integer_types

try:
    import ldap3
    from ldap3.core.exceptions import LDAPException
    import ssl

    HAS_LDAP3 = True
except ImportError:
    HAS_LDAP3 = False


class LdapEntries(object):
    def __init__(self, **kwargs):

        self.server_uri = kwargs.get('server_uri', 'ldapi:///')
        self.bind_dn = kwargs.get('bind_dn')
        self.bind_pw = kwargs.get('bind_pw')
        self.start_tls = bool(kwargs.get('start_tls', False))
        self.validate_certs = bool(kwargs.get('validate_certs', True))
        self.dn = kwargs.get('dn')
        self.search_base = kwargs.get('search_base', '')
        self.search_filter = kwargs.get('search_filter')

        if not self.dn and not self.search_filter:
            raise AnsibleError(
                "dn or search_filter is required for ldap lookup plugin")

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
                raise AnsibleError(
                    "Invalid parameter for LDAP server: %s" % str(e))
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
                    raise AnsibleError("Cannot start TLS: %s" % str(e))

            connection.bind()

        except LDAPException as e:
            raise AnsibleError("Cannot bind to the server: %s" % str(e))

        return connection


class LookupModule(LookupBase):

    def convert_ldap_entry_to_valid_json(self, attribute):
        if attribute is None:
            return attribute
        if isinstance(attribute, integer_types + (float, bool)):
            return attribute
        if isinstance(attribute, string_types):
            return attribute
        elif isinstance(attribute, list):
            new_list = []
            for elem in attribute:
                new_list.append(self.convert_ldap_entry_to_valid_json(elem))
            return new_list
        else:
            # failsafe
            return str(attribute)

    def get_clean_entry(self, entry):
        attributes = {}
        for (key, value) in entry['attributes'].items():
            attributes[key] = self.convert_ldap_entry_to_valid_json(value)

        return {
            'dn': entry['dn'],
            'attributes': attributes
        }

    def run(self, terms, variables=None, **kwargs):
        if not HAS_LDAP3:
            raise AnsibleError(
                "Please pip install ldap3 to use the ldap lookup module.")

        if isinstance(terms, dict):
            terms = [terms]

        ret = []
        for term in terms:
            # Instantiate the LdapEntries object
            ldap_entries = LdapEntries(**term)

            # Search for entries
            entries = ldap_entries.search_entries()

            for entry in entries:
                ret.append(self.get_clean_entry(entry))

            # Unbind connection
            ldap_entries.close()

        return ret
