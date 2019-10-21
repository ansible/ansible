# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
lookup: laps_password
author: Jordan Borean (@jborean93)
version_added: "2.8"
short_description: Retrieves the LAPS password for a server.
description:
- This lookup returns the LAPS password set for a server from the Active Directory database.
- See U(https://github.com/jborean93/ansible-lookup-laps_password) for more information around installing
  pre-requisites and testing.
options:
  _terms:
    description:
    - The host name to retrieve the LAPS password for.
    - This is the C(Common Name (CN)) of the host.
    required: True
    type: str
  allow_plaintext:
    description:
    - When set to C(yes), will allow traffic to be sent unencrypted.
    - It is highly recommended to not touch this to avoid any credentials being exposed over the network.
    - Use C(scheme=ldaps), C(auth=gssapi), or C(start_tls=yes) to ensure the traffic is encrypted.
    default: no
    type: bool
  auth:
    description:
    - The type of authentication to use when connecting to the Active Directory server
    - When using C(simple), the I(username) and I(password) options must be set. If not using C(scheme=ldaps) or
      C(start_tls=True) then these credentials are exposed in plaintext in the network traffic.
    - It is recommended ot use C(gssapi) as it will encrypt the traffic automatically.
    - When using C(gssapi), run C(kinit) before running Ansible to get a valid Kerberos ticket.
    - You cannot use C(gssapi) when either C(scheme=ldaps) or C(start_tls=True) is set.
    choices:
    - simple
    - gssapi
    default: gssapi
    type: str
  ca_cert:
    description:
    - The path to a CA certificate PEM file to use for certificate validation.
    - Certificate validation is used when C(scheme=ldaps) or C(start_tls=yes).
    - This may fail on hosts with an older OpenLDAP install like MacOS, this will have to be updated before
      reinstalling python-ldap to get working again.
    type: str
    aliases: [ cacert_file ]
  domain:
    description:
    - The domain to search in to retrieve the LAPS password.
    - This could either be a Windows domain name visible to the Ansible controller from DNS or a specific domain
      controller FQDN.
    - Supports either just the domain/host name or an explicit LDAP URI with the domain/host already filled in.
    - If the URI is set, I(port) and I(scheme) are ignored.
    required: True
    type: str
  password:
    description:
    - The password for C(username).
    - Required when C(username) is set.
    type: str
  port:
    description:
    - The LDAP port to communicate over.
    - If I(kdc) is already an LDAP URI then this is ignored.
    type: int
  scheme:
    description:
    - The LDAP scheme to use.
    - When using C(ldap), it is recommended to set C(auth=gssapi), or C(start_tls=yes), otherwise traffic will be in
      plaintext.
    - The Active Directory host must be configured for C(ldaps) with a certificate before it can be used.
    - If I(kdc) is already an LDAP URI then this is ignored.
    choices:
    - ldap
    - ldaps
    default: ldap
  search_base:
    description:
    - Changes the search base used when searching for the host in Active Directory.
    - Will default to search in the C(defaultNamingContext) of the Active Directory server.
    - If multiple matches are found then a more explicit search_base is required so only 1 host is found.
    - If searching a larger Active Directory database, it is recommended to narrow the search_base for performance
      reasons.
    type: str
  start_tls:
    description:
    - When C(scheme=ldap), will use the StartTLS extension to encrypt traffic sent over the wire.
    - This requires the Active Directory to be set up with a certificate that supports StartTLS.
    - This is ignored when C(scheme=ldaps) as the traffic is already encrypted.
    type: bool
    default: no
  username:
    description:
    - Required when using C(auth=simple).
    - The username to authenticate with.
    - Recommended to use the username in the UPN format, e.g. C(username@DOMAIN.COM).
    - This is required when C(auth=simple) and is not supported when C(auth=gssapi).
    - Call C(kinit) outside of Ansible if C(auth=gssapi) is required.
    type: str
  validate_certs:
    description:
    - When using C(scheme=ldaps) or C(start_tls=yes), this controls the certificate validation behaviour.
    - C(demand) will fail if no certificate or an invalid certificate is provided.
    - C(try) will fail for invalid certificates but will continue if no certificate is provided.
    - C(allow) will request and check a certificate but will continue even if it is invalid.
    - C(never) will not request a certificate from the server so no validation occurs.
    default: demand
    choices:
    - never
    - allow
    - try
    - demand
    type: str
requirements:
- python-ldap
notes:
- If a host was found but had no LAPS password attribute C(ms-Mcs-AdmPwd), the lookup will fail.
- Due to the sensitive nature of the data travelling across the network, it is highly recommended to run with either
  C(auth=gssapi), C(scheme=ldaps), or C(start_tls=yes).
- Failing to run with one of the above settings will result in the account credentials as well as the LAPS password to
  be sent in plaintext.
- Some scenarios may not work when running on a host with an older OpenLDAP install like MacOS. It is recommended to
  install the latest OpenLDAP version and build python-ldap against this, see
  U(https://keathmilligan.net/python-ldap-and-macos/) for more information.
"""

EXAMPLES = """
# This isn't mandatory but it is a way to call kinit from within Ansible before calling the lookup
- name: call kinit to retrieve Kerberos token
  expect:
    command: kinit username@ANSIBLE.COM
    responses:
      (?i)password: SecretPass1
  no_log: True

- name: Get the LAPS password using Kerberos auth, relies on kinit already being called
  set_fact:
    ansible_password: "{{ lookup('laps_password', 'SERVER', domain='dc01.ansible.com') }}"

- name: Specific the domain host using an explicit LDAP URI
  set_fact:
    ansible_password: "{{ lookup('laps_password', 'SERVER', domain='ldap://ansible.com:389') }}"

- name: Use Simple auth over LDAPS
  set_fact:
    ansible_password: "{{ lookup('laps_password', 'server',
                                 domain='dc01.ansible.com',
                                 auth='simple',
                                 scheme='ldaps',
                                 username='username@ANSIBLE.COM',
                                 password='SuperSecret123') }}"

- name: Use Simple auth with LDAP and StartTLS
  set_fact:
    ansible_password: "{{ lookup('laps_password', 'app01',
                                 domain='dc01.ansible.com',
                                 auth='simple',
                                 start_tls=True,
                                 username='username@ANSIBLE.COM',
                                 password='SuperSecret123') }}"

- name: Narrow down the search base to a an OU
  set_fact:
    ansible_password: "{{ lookup('laps_password', 'sql10',
                                 domain='dc01.ansible.com',
                                 search_base='OU=Databases,DC=ansible,DC=com') }}"

- name: Set certificate file to use when validating the TLS certificate
  set_fact:
    ansible_password: "{{ lookup('laps_password', 'windows-pc',
                                 domain='dc01.ansible.com',
                                 start_tls=True,
                                 ca_cert='/usr/local/share/certs/ad.pem') }}"
"""

RETURN = """
_raw:
  description:
  - The LAPS password(s) for the host(s) requested.
  type: str
"""

import os
import traceback

from ansible.errors import AnsibleLookupError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.basic import missing_required_lib
from ansible.plugins.lookup import LookupBase

LDAP_IMP_ERR = None
try:
    import ldap
    import ldapurl
    HAS_LDAP = True
except ImportError:
    LDAP_IMP_ERR = traceback.format_exc()
    HAS_LDAP = False


def get_laps_password(conn, cn, search_base):
    search_filter = u"(&(objectClass=computer)(CN=%s))" % to_text(cn)

    ldap_results = conn.search_s(to_text(search_base), ldap.SCOPE_SUBTREE, search_filter,
                                 attrlist=[u"distinguishedName", u"ms-Mcs-AdmPwd"])

    # Filter out non server hosts, search_s seems to return 3 extra entries
    # that are not computer classes, they do not have a distinguished name
    # set in the returned results
    valid_results = [attr for dn, attr in ldap_results if dn]

    if len(valid_results) == 0:
        raise AnsibleLookupError("Failed to find the server '%s' in the base '%s'" % (cn, search_base))
    elif len(valid_results) > 1:
        found_servers = [to_native(attr['distinguishedName'][0]) for attr in valid_results]
        raise AnsibleLookupError("Found too many results for the server '%s' in the base '%s'. Specify a more "
                                 "explicit search base for the server required. Found servers '%s'"
                                 % (cn, search_base, "', '".join(found_servers)))

    password = valid_results[0].get('ms-Mcs-AdmPwd', None)
    if not password:
        distinguished_name = to_native(valid_results[0]['distinguishedName'][0])
        raise AnsibleLookupError("The server '%s' did not have the LAPS attribute 'ms-Mcs-AdmPwd'" % distinguished_name)

    return to_native(password[0])


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        if not HAS_LDAP:
            msg = missing_required_lib("python-ldap", url="https://pypi.org/project/python-ldap/")
            msg += ". Import Error: %s" % LDAP_IMP_ERR
            raise AnsibleLookupError(msg)

        # Load the variables and direct args into the lookup options
        self.set_options(var_options=variables, direct=kwargs)
        domain = self.get_option('domain')
        port = self.get_option('port')
        scheme = self.get_option('scheme')
        start_tls = self.get_option('start_tls')
        validate_certs = self.get_option('validate_certs')
        cacert_file = self.get_option('ca_cert')
        search_base = self.get_option('search_base')
        username = self.get_option('username')
        password = self.get_option('password')
        auth = self.get_option('auth')
        allow_plaintext = self.get_option('allow_plaintext')

        # Validate and set input values
        # https://www.openldap.org/lists/openldap-software/200202/msg00456.html
        validate_certs_map = {
            'never': ldap.OPT_X_TLS_NEVER,
            'allow': ldap.OPT_X_TLS_ALLOW,
            'try': ldap.OPT_X_TLS_TRY,
            'demand': ldap.OPT_X_TLS_DEMAND,  # Same as OPT_X_TLS_HARD
        }
        validate_certs_value = validate_certs_map.get(validate_certs, None)
        if validate_certs_value is None:
            valid_keys = list(validate_certs_map.keys())
            valid_keys.sort()
            raise AnsibleLookupError("Invalid validate_certs value '%s': valid values are '%s'"
                                     % (validate_certs, "', '".join(valid_keys)))

        if auth not in ['gssapi', 'simple']:
            raise AnsibleLookupError("Invalid auth value '%s': expecting either 'gssapi', or 'simple'" % auth)
        elif auth == 'gssapi':
            if not ldap.SASL_AVAIL:
                raise AnsibleLookupError("Cannot use auth=gssapi when SASL is not configured with the local LDAP "
                                         "install")
            if username or password:
                raise AnsibleLookupError("Explicit credentials are not supported when auth='gssapi'. Call kinit "
                                         "outside of Ansible")
        elif auth == 'simple' and not (username and password):
            raise AnsibleLookupError("The username and password values are required when auth=simple")

        if ldapurl.isLDAPUrl(domain):
            ldap_url = ldapurl.LDAPUrl(ldapUrl=domain)
        else:
            port = port if port else 389 if scheme == 'ldap' else 636
            ldap_url = ldapurl.LDAPUrl(hostport="%s:%d" % (domain, port), urlscheme=scheme)

        # We have encryption if using LDAPS, or StartTLS is used, or we auth with SASL/GSSAPI
        encrypted = ldap_url.urlscheme == 'ldaps' or start_tls or auth == 'gssapi'
        if not encrypted and not allow_plaintext:
            raise AnsibleLookupError("Current configuration will result in plaintext traffic exposing credentials. "
                                     "Set auth=gssapi, scheme=ldaps, start_tls=True, or allow_plaintext=True to "
                                     "continue")

        if ldap_url.urlscheme == 'ldaps' or start_tls:
            # We cannot use conn.set_option as OPT_X_TLS_NEWCTX (required to use the new context) is not supported on
            # older distros like EL7. Setting it on the ldap object works instead
            if not ldap.TLS_AVAIL:
                raise AnsibleLookupError("Cannot use TLS as the local LDAP installed has not been configured to support it")

            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, validate_certs_value)
            if cacert_file:
                cacert_path = os.path.expanduser(os.path.expandvars(cacert_file))
                if not os.path.exists(to_bytes(cacert_path)):
                    raise AnsibleLookupError("The cacert_file specified '%s' does not exist" % to_native(cacert_path))

                try:
                    # While this is a path, python-ldap expects a str/unicode and not bytes
                    ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, to_text(cacert_path))
                except ValueError:
                    # https://keathmilligan.net/python-ldap-and-macos/
                    raise AnsibleLookupError("Failed to set path to cacert file, this is a known issue with older "
                                             "OpenLDAP libraries on the host. Update OpenLDAP and reinstall "
                                             "python-ldap to continue")

        conn_url = ldap_url.initializeUrl()
        conn = ldap.initialize(conn_url, bytes_mode=False)
        conn.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        conn.set_option(ldap.OPT_REFERRALS, 0)  # Allow us to search from the base

        # Make sure we run StartTLS before doing the bind to protect the credentials
        if start_tls:
            try:
                conn.start_tls_s()
            except ldap.LDAPError as err:
                raise AnsibleLookupError("Failed to send StartTLS to LDAP host '%s': %s"
                                         % (conn_url, to_native(err)))

        if auth == 'simple':
            try:
                conn.bind_s(to_text(username), to_text(password))
            except ldap.LDAPError as err:
                raise AnsibleLookupError("Failed to simple bind against LDAP host '%s': %s"
                                         % (conn_url, to_native(err)))
        else:
            try:
                conn.sasl_gssapi_bind_s()
            except ldap.AUTH_UNKNOWN as err:
                # The SASL GSSAPI binding is not installed, e.g. cyrus-sasl-gssapi. Give a better error message than
                # what python-ldap provides
                raise AnsibleLookupError("Failed to do a sasl bind against LDAP host '%s', the GSSAPI mech is not "
                                         "installed: %s" % (conn_url, to_native(err)))
            except ldap.LDAPError as err:
                raise AnsibleLookupError("Failed to do a sasl bind against LDAP host '%s': %s"
                                         % (conn_url, to_native(err)))

        try:
            if not search_base:
                root_dse = conn.read_rootdse_s()
                search_base = root_dse['defaultNamingContext'][0]

            ret = []
            # TODO: change method to search for all servers in 1 request instead of multiple requests
            for server in terms:
                ret.append(get_laps_password(conn, server, search_base))
        finally:
            conn.unbind_s()

        return ret
