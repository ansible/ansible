import traceback
from ansible.module_utils._text import to_native

try:
    import ldap
    import ldap.sasl
    HAS_LDAP = True

except ImportError:
    HAS_LDAP = False


def gen_specs(**specs):
    specs.update({
        'bind_dn': dict(),
        'bind_pw': dict(default='', no_log=True),
        'dn': dict(required=True),
        'server_uri': dict(default='ldapi:///'),
        'start_tls': dict(default=False, type='bool'),
        'validate_certs': dict(default=True, type='bool'),
    })

    return specs


class LdapGeneric(object):
    def __init__(self, module):
        # Shortcuts
        self.module = module
        self.bind_dn = self.module.params['bind_dn']
        self.bind_pw = self.module.params['bind_pw']
        self.dn = self.module.params['dn']
        self.server_uri = self.module.params['server_uri']
        self.start_tls = self.module.params['start_tls']
        self.verify_cert = self.module.params['validate_certs']

        # Establish connection
        self.connection = self._connect_to_ldap()

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
