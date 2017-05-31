#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: ldap
short_description: basic ldap entries management
description:
     - Manages ldap using standard python-ldap library.
version_added: "1.7"
options:
    uri:
        description:
            - C(URI) to connect LDAP server. If set I(protocol), I(host) and I(port) parameters are ignored
        required: false
        default: null
        aliases: ["url"]
    protocol:
        description:
            - LDAP server connection protocol
        required: false
        default: "ldap"
        aliases: []
        choices: ["ldap", "ldaps", "ldapi"]
    host:
        description:
            - LDAP host
        required: false
        default: "localhost"
        aliases: []
    port:
        description:
            - LDAP port
        required: false
        default: 389
        aliases: []
    bind_dn:
        description:
            - Directory bind user distinguished name (dn). Anonymous bind if not set
        required: false
        default: null
        aliases: []
    bind_pw:
        description:
            - Directory bind user password. For auth=simple
        required: false
        default: null
        aliases: []
    auth:
        description:
            - Authentication method. C(sasl_ext) is supported only on U(ldapi://) (unix socket connection)
        required: false
        aliases: []
        choices: ["simple", "sasl_ext"]
        default: "simple"
    dn:
        description:
            - Operation-specific distinguished name (dn)
        required: true
        default: null
        aliases: ["name"]
    state:
        description:
            - Whether the entry should be present.
              In case of I(present) C(data) is interpreted.
              In case of I(absent) ldap entry is just deleted.
        required: false
        choices: ["present", "absent"]
        default: "present"
    data:
        description:
            - Data for current operation in C(ldapmodify)-like format.
              Usually I(complex_args) is used to set this parameter.
              If you have to use command-line variant one-line ad-hoc format is supported.
              See definition in I(examples) section.
        required: false
        default: null
requirements:
  - python-ldap
author: Konstantin Gribov
'''

EXAMPLES = '''
# Simple args recommended for command line ad-hoc use.
# `ldapmodify` LDIF-like format in complex args for general-purpose use.
# Simple args grammar in BNF-like format is explained below.



# EXAMPLES


# Remove entry from ldap:

- ldap: uri=ldap:// bind_dn=cn=Manager,dc=my-domain,dc=com bind_pw=secret
        dn=ou=ou1,dc=my-domain,dc=com
        state=absent

# It's equal to `ldapmodify` LDIF:
dn: ou=ou1,dc=my-domain,dc=com
changetype: delete


# Add entry with `objectClass` and `ou` attrs

- ldap: uri=ldap:// bind_dn=cn=Manager,dc=my-domain,dc=com bind_pw=secret
        dn=ou=ou1,dc=my-domain,dc=com
        data=objectClass=organizationalUnit;ou=[ou1,ou1_alias];l=Moscow

- ldap: uri=ldap:// bind_dn=cn=Manager,dc=my-domain,dc=com bind_pw=secret
        dn=ou=ou1,dc=my-domain,dc=com
        data=add/objectClass=organizationalUnit;add/ou=[ou1,ou1_alias];a/l=Moscow

- ldap: uri=ldap:// bind_dn=cn=Manager,dc=my-domain,dc=com bind_pw=secret
  args:
    dn: ou=ou1,dc=my-domain,dc=com
    data:
      objectClass: organizationalUnit
      ou:
      - ou1
      - ou1_alias
      l: Moscow

# It's equal to such `ldapmodify` LDIF:
dn: ou=ou1,dc=my-domain,dc=com
changetype: modify
add: objectClass
objectClass: organizationalUnit
-
add: ou
ou: ou1
ou: ou1_alias
-
add: l
l: Moscow


# Add `dcObject` and replace `dc` to existing entry (because `dcObject` is auxiliary objectClass
# and `dc` is single-value field)

- ldap: uri=ldap:// bind_dn=cn=Manager,dc=my-domain,dc=com bind_pw=secret
        dn=ou=ou1,dc=my-domain,dc=com
        data=objectClass=dcObject;r/dc=ou1.my-domain.com

- ldap: uri=ldap:// bind_dn=cn=Manager,dc=my-domain,dc=com bind_pw=secret
        dn=ou=ou1,dc=my-domain,dc=com
        data=add/objectClass=dcObject;replace/dc=ou1.my-domain.com

- ldap: uri=ldap:// bind_dn=cn=Manager,dc=my-domain,dc=com bind_pw=secret
  args:
    dn: ou=ou1,dc=my-domain,dc=com
    data:
      - objectClass: dcObject
      - op: replace
        dc: ou1.my-domain.com

# It's equal to such `ldapmodify` LDIF:
dn: ou=ou1,dc=my-domain,dc=com
changetype: modify
# this add section only if `objectClass` not present in entry yet
add: objectClass
objectClass: dcObject
-
replace: dc
dc: ou1.my-domain.com


# Remove `dcObject` `objectClass` and `dc` attr from entry

- ldap: uri=ldap:// bind_dn=cn=Manager,dc=my-domain,dc=com bind_pw=secret
        dn=ou=ou1,dc=my-domain,dc=com
        data=d/objectClass=dcObject;d/dc

- ldap: uri=ldap:// bind_dn=cn=Manager,dc=my-domain,dc=com bind_pw=secret
        dn=ou=ou1,dc=my-domain,dc=com
        data=delete/objectClass=dcObject;delete/dc

- ldap: uri=ldap:// bind_dn=cn=Manager,dc=my-domain,dc=com bind_pw=secret
  args:
    dn: ou=ou1,dc=my-domain,dc=com
    data:
      op: delete
      objectClass: dcObject
      dc:

# It's equal to such `ldapmodify` LDIF:
dn: ou=ou1,dc=my-domain,dc=com
changetype: modify
delete: objectClass
objectClass: dcObject
-
delete: dc


# Use SASL EXTERNAL auth method on unix socket (ldapi://).
# It's often used on initial OpenLDAP 2.4+ configuration on cn=config tree.

- ldap: uri=ldapi:// auth=sasl_ext
        dn=ou=ou1,dc=my-domain,dc=com
        data=a/objectClass=organizationalUnit;a/ou=ou1


# `data` one-line format BNF-like grammar.

data ::= modification { ';' modification }
modification ::= [ operation '/' ] attr-def
attr-def ::= attr-type '=' attr-values
attr-values ::= attr-value | '[' attr-value { ',' attr-value } ']'
operation ::= 'add' | 'delete' | 'replace' | 'a' | 'd' | 'r'
attr-type ::= ALPHA { ALPHA | DIGIT | '-' }
attr-value ::= SAFE-STRING | safe-utf8-string

safe-utf8-string ::= safe-utf8-init-char { UTF8-CHAR }
safe-utf8-init-char ::= SAFE-INIT-CHAR | UTF8-2 | UTF8-3 | UTF8-4 | UTF8-5 | UTF8-6

# SAFE-STRING, SAFE-INIT-CHAR, UTF8-CHAR, UTF8-* are from
# RFC2849 "The LDAP Data Interchange Format (LDIF) - Technical Specification" http://tools.ietf.org/html/rfc2849

'''

try:
    import ldap
    import ldap.sasl
    import ldap.modlist
    import ldapurl

    HAVE_LDAP = True
except ImportError:
    HAVE_LDAP = False


if HAVE_LDAP:
    LDAP_OPERATION_MAP = {
        'add': ldap.MOD_ADD,
        'delete': ldap.MOD_DELETE,
        'replace': ldap.MOD_REPLACE
    }

    INVERSE_LDAP_OPERATION_MAP = {
        ldap.MOD_ADD: 'add',
        ldap.MOD_DELETE: 'delete',
        ldap.MOD_REPLACE: 'replace'
    }


class LdapModuleError(Exception):
    pass


class LdapManager(object):
    def __init__(self,
                 uri,
                 start_tls=False,
                 bind_dn=None,
                 bind_pw=None,
                 auth='simple',
                 dry_run=False):

        self._conn = ldap.initialize(uri)
        self._dry_run = dry_run

        if ldapurl.LDAPUrl(uri).urlscheme.lower() != 'ldap' and start_tls:
            raise LdapModuleError('Can not use STARTTLS on non-plain LDAP URL: ' + uri)

        if auth == 'sasl_ext' and ldapurl.LDAPUrl(uri).urlscheme.lower() != 'ldapi':
            raise LdapModuleError('SASL EXTERNAL auth mechanism is only supported on ldapi:// LDAP URL')

        if start_tls:
            self._conn.start_tls_s()

        if auth == 'simple':
            if bind_dn is None:
                self._conn.simple_bind_s()
            else:
                self._conn.simple_bind_s(bind_dn, bind_pw)
        elif auth == 'sasl_ext':
            self._conn.sasl_interactive_bind_s('', ldap.sasl.external())
        else:
            raise LdapModuleError('Unsupported auth method: ' + auth)

    def close(self):
        self._conn.unbind_s()

    def _entry_get(self, dn):
        """
        Internal function to get ldap entry by exact dn.
        It performs search with scope=base and limit=1.
        :param dn: entry distinguished name
        :return: None if entry not found or dict attr => [values]
        """
        try:
            result = self._conn.search_ext_s(dn, ldap.SCOPE_BASE, sizelimit=1)
        except ldap.NO_SUCH_OBJECT:
            return None
        except Exception as e:
            raise LdapModuleError('Generic error: ' + str(e))
        else:
            # get first result (0) entry field (1)
            # search_result contains [(dn1, entry1), (dn2, entry2), ...]
            return result[0][1]

    def _entry_exists(self, dn):
        if self._entry_get(dn):
            return True
        else:
            return False

    def _entry_remove(self, dn):
        if not self._dry_run:
            self._conn.delete_s(dn)

    def _entry_add(self, dn, mod_list):
        if not self._dry_run:
            self._conn.add_s(dn, mod_list)

    def _entry_modify(self, dn, mod_list):
        if not self._dry_run:
            self._conn.modify_ext_s(dn, mod_list)

    def ensure_entry(self, dn, operations, state):
        if state == 'absent':
            if self._entry_exists(dn):
                self._entry_remove(dn)
                return True, []
            else:
                return False, []

        elif state == 'present':
            if not operations:
                raise LdapModuleError('data should be not empty (or no-op) for state=present')

            old_entry = self._entry_get(dn)
            mod_list = self.build_mod_list(old_entry, operations)

            if old_entry is None:
                self._entry_add(dn, self.build_add_list(mod_list))
                return True, mod_list

            else:
                if not mod_list:
                    return False, mod_list

                self._entry_modify(dn, mod_list)
                return True, mod_list

        else:
            raise LdapModuleError('Unknown state: ' + state)

    @staticmethod
    def build_add_list(mod_list):
        """
        Build ldap add_list (list of modification tuples for LDAPObject.add methods).
        Input `mod_list` should have collapsed entries, as produced by build_mod_list method.
        Also `mod_list` should have only add operations (or behavior would be incorrect).
        :param mod_list: mod_list, built by `build_mod_list` method
        """
        entry = {}
        for operation, attr, values in mod_list:
            if operation == ldap.MOD_ADD:
                entry[attr] = values

        return ldap.modlist.addModlist(entry)

    @staticmethod
    def _mod_list_filter_by_attr(mod_list, attr):
        """
        Removes all modifications on `attr` in partial mod_list.
        Each modification is tuple (with 3 elements: `operation`, `attr`, `values`).
        """
        return filter(lambda x: x[1] != attr, mod_list)

    @staticmethod
    def _collapse_operations(old_values, partial_operations):
        """
        Collapses list of ordered ldap operations to one operation or no-op.
        All operations, passed to this method should be on one attribute.
        :param old_values: values in field before operations sequence
        :param partial_operations: list of operation tuples, at least one required.
        :return: None if operation sequence on old_values will be no-op or
                 one `add`, `replace` or `delete` operation with args.
        """
        assert partial_operations
        assert len(partial_operations) > 0
        assert len(set(map(lambda x: x[1], partial_operations))) == 1

        old_values = set(old_values or [])

        attr = partial_operations[0][1]
        result_values = set(old_values)

        for operation, _, values in partial_operations:
            if operation == 'delete':
                if values:
                    [result_values.discard(v) for v in values]
                else:
                    result_values.clear()
            elif operation == 'replace':
                if values:
                    result_values.clear()
                    [result_values.add(v) for v in values]
                else:
                    result_values.clear()
            elif operation == 'add':
                [result_values.add(v) for v in values]

        if result_values == old_values:
            return None
        elif result_values == set():
            return 'delete', attr, set()
        elif result_values.issuperset(old_values):
            return 'add', attr, result_values - old_values
        elif result_values.issubset(old_values):
            return 'delete', attr, old_values - result_values
        else:
            return 'replace', attr, result_values

    @staticmethod
    def build_mod_list(old_entry, operations):
        """
        Build ldap mod_list (list of modification tuples for LDAPObject.modify methods).
        It supposed to be optimal (have at most one operation per attribute).
        If operation sequence on one attribute will change nothing in ldap it will be suppressed.
        """
        if old_entry is None:
            old_entry = {}

        attrs = set([attr for (_, attr, _) in operations])
        result = []

        for attr in attrs:
            # at least one operation in partial_operations by its construction
            partial_operations = filter(lambda mod: mod[1] == attr, operations)
            old_values = []
            if attr in old_entry:
                old_values = old_entry[attr]

            collapsed_operation = LdapManager._collapse_operations(old_values, partial_operations)
            if collapsed_operation:
                result.append(collapsed_operation)

        return [(LDAP_OPERATION_MAP[operation], attr, list(values)) for (operation, attr, values) in result]


def encode_str(s):
    if isinstance(s, str):
        return s
    elif isinstance(s, unicode):
        return s.encode('utf-8')
    else:
        return str(s)


def parse_data_str(data):
    op_name_expansion = {'a': 'add', 'd': 'delete', 'r': 'replace'}

    result = []
    for s in data.split(';'):
        if s.find('/') != -1:
            (operation, attr_def) = s.split('/', 1)
        else:
            (operation, attr_def) = ('add', s)

        if operation in op_name_expansion:
            operation = op_name_expansion[operation]

        if attr_def.find('=') != -1:
            (attr, raw_values) = attr_def.split('=', 1)
        else:
            (attr, raw_values) = (attr_def, None)

        if raw_values is None:
            values = []
        elif raw_values[0] == '[' and raw_values[-1] == ']':
            values = raw_values[1:-1].split(',')
        else:
            values = [raw_values]

        result.append((operation, attr, [encode_str(x) for x in values]))

    return result


def parse_data_dict(data):
    result = []

    if 'op' in data:
        operation = data['op']
    else:
        operation = 'add'

    for attr, values in data.items():
        if attr == 'op':
            continue

        if isinstance(values, str) or isinstance(values, unicode):
            result.append((operation, attr, [encode_str(values)]))
        elif isinstance(values, list):
            result.append((operation, attr, [encode_str(x) for x in values]))
        elif values is None:
            result.append((operation, attr, []))
        else:
            raise LdapModuleError('Unexpected type for values %s: %s' % (repr(values), type(values)))

    return result


def parse_data(data):
    """
    Parse data in object format and plain string format.
    :return: list of ldap modifications
    """

    if isinstance(data, dict):
        return parse_data_dict(data)
    elif isinstance(data, list):
        return reduce(lambda x, y: x + y, map(parse_data_dict, data))
    elif isinstance(data, str):
        return parse_data_str(data)
    elif isinstance(data, types.NoneType):
        return None
    else:
        raise LdapModuleError('Data should be python `str` (in case of simple args) ' +
                              'or `dict` (in case of complex_args). Received: ' +
                              str(type(data)))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            uri=dict(default=None, required=False, aliases=['url']),
            starttls=dict(default=False, type='bool'),

            protocol=dict(default='ldap', choices=['ldap', 'ldaps', 'ldapi']),
            host=dict(default='localhost'),
            port=dict(default=389),

            auth=dict(default='simple', choises=['simple', 'sasl_ext']),

            bind_dn=dict(default=None),
            bind_pw=dict(default=None, aliases=['bind_pass', 'bind_password']),

            state=dict(required=True, choices=['present', 'absent']),

            dn=dict(required=True, aliases=['name']),

            data=dict(default=None)
        ),
        supports_check_mode=True
    )

    if not HAVE_LDAP:
        module.fail_json(msg='Failed loading some of python-ldap modules')

    uri = module.params['uri']
    protocol = module.params['protocol']
    host = module.params['host']
    port = module.params['port']
    start_tls = module.params['starttls']
    auth = module.params['auth']

    bind_dn = module.params['bind_dn']
    bind_pw = module.params['bind_pw']

    dn = module.params['dn']
    state = module.params['state']

    data = module.params['data']

    if uri is None:
        if protocol == 'ldapi':
            uri = protocol + '://'
        else:
            uri = protocol + '://' + host + ':' + str(port)

    try:
        lm = LdapManager(uri, start_tls, bind_dn, bind_pw, auth=auth, dry_run=module.check_mode)
    except LdapModuleError as e:
        module.fail_json(msg='Error connecting LDAP: ' + str(e), exitValue=1)
    except ldap.LDAPError as e:
        module.fail_json(msg='Error connecting LDAP: ' + str(e), exitValue=1)

    try:
        try:
            parsed_data = parse_data(data)
        except LdapModuleError as e:
            module.fail_json(msg='Error parsing data: ' + str(e), dn=dn, raw_data=data)

        try:
            (changed, applied_mod_list) = lm.ensure_entry(dn, operations=parsed_data, state=state)

            applied_operations = [(INVERSE_LDAP_OPERATION_MAP[op], attr, values) for (op, attr, values) in applied_mod_list]

            module.exit_json(changed=changed,
                             dn=dn,
                             target_state=state,
                             target_operations=parsed_data,
                             applied_operations=applied_operations)
        except LdapModuleError as e:
            module.fail_json(msg='Error: ' + str(e), exitValue=1, target_operations=parsed_data)
        except ldap.LDAPError as e:
            module.fail_json(msg='LDAP error: ' + str(e), exitValue=1, target_operations=parsed_data)
    finally:
        lm.close()


from ansible.module_utils.basic import *

main()
