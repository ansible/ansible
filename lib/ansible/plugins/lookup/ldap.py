# (c) 2019, Knut Franke <knut.franke@gmx.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: ldap
    author: Knut Franke <knut.franke@gmx.de>
    short_description: query LDAP
    description:
      - The ldap lookup performs a search against an LDAP server using a specified filter.
      - Search results are returned as a list of dictionaries of
        attribute-value pairs.
      - Single-value attributes are returned directly as text, unless flat=no
        is specified, in which case all attribute values are returned as lists.
      - The distinguished name ("dn") is always returned as text.
    options:
      _terms:
        description:
          - Search filter and/or attributes to return.
          - The search filter should conform to the string representation for search filters as defined in RFC 4515,
          - and it must be enclosed in parentheses (so that it can be distinguished from requested attributes
          - and other plugin options).
        default: '(objectClass=*)'
      server_uri:
        description:
          - The URI(s) of one or more LDAP servers.
        default: (from the underlying LDAP client library's configuration)
      base:
        description: The base DN to use, as a Distinguished Name in LDAP format.
        default: (from the underlying LDAP client library's configuration)
      bind_dn:
        description: The user with which to bind to the LDAP server, as a Distinguished Name in LDAP format.
        default: None
      bind_pw:
        description: The password for the binddn user.
        default: None
      start_tls:
        description: If true, we'll use the START_TLS LDAP extension.
        default: no
      validate_certs:
        description: If 'no', SSL certificates will not be validated. This should only be used on sites using self-signed certificates.
        default: yes
      timeout:
        description: Block for at most timeout seconds (or indefinitely if timeout is negative).
        default: -1
      flat:
        description: If set to no/0, do not peel single-value attribute lists.
        default: yes
      binary:
        description: If true, do not attempt to convert attribute values to text.
        default: no
"""

EXAMPLES = """
- name: Dump all attributes of user1.
  debug: msg="{{ lookup('ldap', '(uid=user1)')}}"

- name: Get only cn and uid attributes of user1
  debug: msg="{{ lookup('ldap', '(uid=user1)', 'cn,uid')}}"

- name: Explicitly restrict search to given OU.
  debug: msg="{{ lookup('ldap', '(uid=user1)', 'base=ou=Users,dc=example,dc=com'}}"

- name: Get all entries below the given OU
  debug: msg="{{ q('ldap', 'base=ou=Users,dc=example,dc=com'}}"

- name: Get members of admin group, making sure the result is a list also for a single-member group.
  debug: msg={{ lookup("ldap", "(&(objectClass=groupOfNames)(cn=admins))", "flat=no").member }}'

- name: Get content of auto.home automounter map
  debug: msg="{{ q('ldap', '(&(objectClass=nisObject)(nisMapName=auto.home))', 'cn,nisMapEntry') }}"
"""

RETURN = """
  _list:
    description:
      - list of dictionaries with the attributes of the entries found.
"""

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_native

try:
    import ldap

    HAS_LDAP = True
except ImportError:
    HAS_LDAP = False


def to_bool(s):
    return s.lower() in ('yes', 'on', '1', 'true')


class LookupModule(LookupBase):
    server_uri = None
    base = None
    bind_dn = None
    bind_pw = None
    start_tls = False
    validate_certs = True
    timeout = -1
    flat = True
    binary = False

    __options = ['server_uri', 'base', 'bind_dn', 'bind_pw', 'start_tls',
                 'validate_certs', 'timeout', 'flat', 'binary']

    def run(self, terms, variables=None, **kwargs):
        if HAS_LDAP is False:
            raise AnsibleError("The ldap lookup requires the 'python-ldap' library and it is not installed")

        queries = []
        wanted_attrs = []

        for t in terms:
            if t.startswith('('):
                queries.append(t)
            elif '=' in t:
                opt, arg = t.split('=', 1)
                if opt not in self.__options:
                    raise AnsibleError("Unsupported option {0} (hint: search filters have to be enclosed in ())".format(opt))
                if opt in ('start_tls', 'validate_certs', 'flat', 'binary'):
                    setattr(self, opt, to_bool(arg))
                elif opt in ('timeout',):
                    setattr(self, opt, int(arg))
                else:
                    setattr(self, opt, arg)
            else:
                wanted_attrs.extend(t.split(','))

        if not self.base:
            self.base = ldap.get_option(ldap.OPT_DEFBASE)
        if not self.server_uri:
            self.server_uri = ldap.get_option(ldap.OPT_URI)

        connection = self._connect_to_ldap()

        if not queries:
            queries.append('(objectClass=*)')
        if not wanted_attrs:
            wanted_attrs = None

        if self.flat:
            if self.binary:
                def read_attr(values):
                    if len(values) == 1:
                        return values[0]
                    else:
                        return values
            else:
                def read_attr(values):
                    if len(values) == 1:
                        return to_native(values[0])
                    else:
                        return list(map(to_native, values))
        else:
            if self.binary:
                def read_attr(values):
                    return values
            else:
                def read_attr(values):
                    return list(map(to_native, values))

        result = []

        for query in queries:
            try:
                entries = connection.search_st(self.base, ldap.SCOPE_SUBTREE,
                                               query, attrlist=wanted_attrs,
                                               timeout=self.timeout)
                result.extend(dict(((k, read_attr(v)) for k, v in attrs.items()), dn=dn)
                              for dn, attrs in entries)
            except ldap.NO_SUCH_OBJECT:
                pass
            except ldap.TIMEOUT:
                raise AnsibleError("LDAP query timed out after {0:d} seconds.".format(self.timeout))

        return result

    def _connect_to_ldap(self):
        if not self.validate_certs:
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

        connection = ldap.initialize(self.server_uri)

        if self.start_tls:
            try:
                connection.start_tls_s()
            except ldap.LDAPError as e:
                raise AnsibleError("Cannot start TLS: " + str(e))

        try:
            connection.simple_bind_s(self.bind_dn, self.bind_pw)
        except ldap.LDAPError as e:
            raise AnsibleError("Cannot bind to the LDAP server: " + str(e))

        return connection
