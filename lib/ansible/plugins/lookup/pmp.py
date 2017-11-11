# (c) 2016, Andrew Zenk <azenk@umn.edu>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.modules.web_infrastructure.pmp import PasswordManagerPro

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display

    display = Display()
__metaclass__ = type

DOCUMENTATION = """
    lookup: pmp
    author:
      -  Bernat Mut <bernat.mut@aireuropa.com>
    version_added: "2.5"
    short_description: Recover password account from Password Manager Pro (PMP)
    description:
      - Use this module to  requests passwords from an specific account to PMP
    options:
      _terms:
        description: key from which you want to retrieve the field
        required: True
      field:
        description: field to return from lastpass
        default: 'password'
"""

EXAMPLES = """
  - name: passing options to the lookup
    debug: msg={{ lookup("pmp", { "uri":"{{ pmp_server }}", "token":"{{ pmp_token }}", "resource_name":"{{ server_name }}", "account_name":"{{ user }}" }) }}"""

RETURN = """
  _raw:
    password: requested password
"""


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):

        if isinstance(terms, list):
            return_values = []
            for term in terms:
                display.vvvv("Term: %s" % term)
                uri = term.get('uri', None)
                port = term.get('port', 7272)
                token = term.get('token', None)
                resource_name = term.get('resource_name', None)
                account_name = term.get('account_name', None)
                use_proxy = term.get('use_proxy', True)
                validate_certs = term.get('validate_certs', True)
                if uri is None or token is None or resource_name is None or account_name is None:
                    raise AnsibleError("Field: uri, token, resource_name and account_name  are mandatories")
                pmp = PasswordManagerPro(token, uri, port, use_proxy, validate_certs)
                password = pmp.get_password(resource_name, account_name)
                return_values.append(password)

            return return_values
        else:
            display.vvvv("Term: %s" % terms)
            uri = terms.get('uri', None)
            port = terms.get('port', 7272)
            token = terms.get('token', None)
            resource_name = terms.get('resource_name', None)
            account_name = terms.get('account_name', None)
            use_proxy = terms.get('use_proxy', True)
            validate_certs = terms.get('validate_certs', True)

            if uri is None or token is None or resource_name is None or account_name is None:
                raise AnsibleError("Field: uri, token, resource_name and account_name  are mandatories")

            pmp = PasswordManagerPro(token, uri, port, use_proxy, validate_certs)
            password = pmp.get_password(resource_name, account_name)
            return password
