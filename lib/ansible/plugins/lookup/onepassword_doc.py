# -*- coding: utf-8 -*-
# (c) 2019, David Taylor <djtaylor13@gmail.com> (onepassword.py used as a starting point)
# (c) 2018, Scott Buchanan <sbuchanan@ri.pn>
# (c) 2016, Andrew Zenk <azenk@umn.edu> (lastpass.py used as starting point)
# (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
    lookup: onepassword_doc
    author:
      - David Taylor <djtaylor13@gmail.com>
      - Scott Buchanan <sbuchanan@ri.pn>
      - Andrew Zenk <azenk@umn.edu>
      - Sam Doran<sdoran@redhat.com>
    version_added: "2.7"
    requirements:
      - C(op) 1Password command line utility. See U(https://support.1password.com/command-line/)
    short_description: fetch documents from 1Password
    description:
      - C(onepassword_doc) wraps the C(op) command line utility to fetch documents from 1Password.
    options:
      _terms:
        description: identifier(s) (UUID, name, or subdomain; case-insensitive) of item(s) to retrieve
        required: True
      master_password:
        description: The password used to unlock the specified vault.
        default: None
        version_added: '2.7'
        aliases: ['vault_password']
      subdomain:
        description: The 1Password subdomain to authenticate against.
        default: None
        version_added: '2.7'
      username:
        description: The username used to sign in.
        version_added: '2.7'
      secret_key:
        description: The secret key used when performing an initial sign in.
        version_added: '2.7'
      vault:
        description: Vault containing the item to retrieve (case-insensitive). If absent will search all vaults
        default: None
    notes:
      - This lookup will use an existing 1Password session if one exists. If not, and you have already
        performed an initial sign in (meaning C(~/.op/config exists)), then only the C(master_password) is required.
        You may optionally specify C(subdomain) in this scenario, otherwise the last used subdomain will be used by C(op).
      - This lookup can perform an initial login by providing C(subdomain), C(username), C(secret_key), and C(master_password).
      - Due to the B(very) sensitive nature of these credentials, it is B(highly) recommeneded that you only pass in the minial credentials
        needed at any given time. Also, store these credentials in an Ansible Vault using a key that is equal to or greater in strength
        to the 1Password master password.
      - This lookup stores potentially sensitive data from 1Password as Ansible facts.
        Facts are subject to caching if enabled, which means this data could be stored in clear text
        on disk or in a database.
      - Tested with C(op) version 0.5.3
"""

EXAMPLES = """
# These examples only work when already signed in to 1Password
- name: Retrieve document contents for MyAwesomeDocument when already signed in to 1Password
  debug:
    var: lookup('onepassword_doc', 'MyAwesomeDocument')

- name: Retrieve document contents for MySecureTLSCert from a specific vault
  debug:
    var: lookup('onepassword_doc', 'MySecureTLSCert', vault='MyVault')

- name: Retrieve MySecureTLSCert document when not signed in to 1Password
  debug:
    var: lookup('onepassword_doc'
                'MySecureTLSCert'
                subdomain='MySubdomain'
                master_password=vault_master_password)

- name: Retrieve MySecureTLSCert document when never signed in to 1Password
  debug:
    var: lookup('onepassword_doc'
                'MySecureTLSCert'
                subdomain='MySubdomain'
                master_password=vault_master_password
                username='tweety@acme.com'
                secret_key=vault_secret_key)
"""

RETURN = """
  _raw:
    description: document contents requested
"""

from ansible.plugins.lookup.onepassword import OnePass
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_bytes


class OnePassDoc(OnePass):

    def get_document_raw(self, item_id, vault=None):
        args = ["get", "document", item_id]
        if vault is not None:
            args += ['--vault={0}'.format(vault)]
        if not self.logged_in:
            args += [to_bytes('--session=') + self.token]
        rc, output, dummy = self._run(args)
        return output

    def get_document(self, item_id, vault=None):
        output = self.get_document_raw(item_id, vault)
        return self._parse_document_output(output)

    def _parse_document_output(self, doc_data):
        return doc_data

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        op = OnePassDoc()

        vault = kwargs.get('vault')
        op.subdomain = kwargs.get('subdomain')
        op.username = kwargs.get('username')
        op.secret_key = kwargs.get('secret_key')
        op.master_password = kwargs.get('master_password', kwargs.get('vault_password'))

        op.assert_logged_in()

        values = []
        for term in terms:
            values.append(op.get_document(term, vault))
        return values
