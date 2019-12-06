# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Scott Buchanan <sbuchanan@ri.pn>
# Copyright: (c) 2016, Andrew Zenk <azenk@umn.edu> (lastpass.py used as starting point)
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
    lookup: onepassword
    author:
      - Scott Buchanan (@scottsb)
      - Andrew Zenk (@azenk)
      - Sam Doran (@samdoran)
    version_added: "2.6"
    requirements:
      - C(op) 1Password command line utility. See U(https://support.1password.com/command-line/)
    short_description: fetch field values from 1Password
    description:
      - C(onepassword) wraps the C(op) command line utility to fetch specific field values from 1Password.
    options:
      _terms:
        description: identifier(s) (UUID, name, or subdomain; case-insensitive) of item(s) to retrieve.
        required: True
      field:
        description: field to return from each matching item (case-insensitive).
        default: 'password'
      master_password:
        description: The password used to unlock the specified vault.
        version_added: '2.7'
        aliases: ['vault_password']
      section:
        description: Item section containing the field to retrieve (case-insensitive). If absent will return first match from any section.
      subdomain:
        description: The 1Password subdomain to authenticate against.
        version_added: '2.7'
      username:
        description: The username used to sign in.
        version_added: '2.7'
      secret_key:
        description: The secret key used when performing an initial sign in.
        version_added: '2.7'
      vault:
        description: Vault containing the item to retrieve (case-insensitive). If absent will search all vaults.
    notes:
      - This lookup will use an existing 1Password session if one exists. If not, and you have already
        performed an initial sign in (meaning C(~/.op/config exists)), then only the C(master_password) is required.
        You may optionally specify C(subdomain) in this scenario, otherwise the last used subdomain will be used by C(op).
      - This lookup can perform an initial login by providing C(subdomain), C(username), C(secret_key), and C(master_password).
      - Due to the B(very) sensitive nature of these credentials, it is B(highly) recommended that you only pass in the minimal credentials
        needed at any given time. Also, store these credentials in an Ansible Vault using a key that is equal to or greater in strength
        to the 1Password master password.
      - This lookup stores potentially sensitive data from 1Password as Ansible facts.
        Facts are subject to caching if enabled, which means this data could be stored in clear text
        on disk or in a database.
      - Tested with C(op) version 0.5.3
"""

EXAMPLES = """
# These examples only work when already signed in to 1Password
- name: Retrieve password for KITT when already signed in to 1Password
  debug:
    var: lookup('onepassword', 'KITT')

- name: Retrieve password for Wintermute when already signed in to 1Password
  debug:
    var: lookup('onepassword', 'Tessier-Ashpool', section='Wintermute')

- name: Retrieve username for HAL when already signed in to 1Password
  debug:
    var: lookup('onepassword', 'HAL 9000', field='username', vault='Discovery')

- name: Retrieve password for HAL when not signed in to 1Password
  debug:
    var: lookup('onepassword'
                'HAL 9000'
                subdomain='Discovery'
                master_password=vault_master_password)

- name: Retrieve password for HAL when never signed in to 1Password
  debug:
    var: lookup('onepassword'
                'HAL 9000'
                subdomain='Discovery'
                master_password=vault_master_password
                username='tweety@acme.com'
                secret_key=vault_secret_key)
"""

RETURN = """
  _raw:
    description: field data requested
"""

import errno
import json
import os

from subprocess import Popen, PIPE

from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleLookupError
from ansible.module_utils._text import to_bytes, to_text


class OnePass(object):

    def __init__(self, path='op'):
        self.cli_path = path
        self.config_file_path = os.path.expanduser('~/.op/config')
        self.logged_in = False
        self.token = None
        self.subdomain = None
        self.username = None
        self.secret_key = None
        self.master_password = None

    def get_token(self):
        # If the config file exists, assume an initial signin has taken place and try basic sign in
        if os.path.isfile(self.config_file_path):

            if not self.master_password:
                raise AnsibleLookupError('Unable to sign in to 1Password. master_password is required.')

            try:
                args = ['signin', '--output=raw']

                if self.subdomain:
                    args = ['signin', self.subdomain, '--output=raw']

                rc, out, err = self._run(args, command_input=to_bytes(self.master_password))
                self.token = out.strip()

            except AnsibleLookupError:
                self.full_login()

        else:
            # Attempt a full sign in since there appears to be no existing sign in
            self.full_login()

    def assert_logged_in(self):
        try:
            rc, out, err = self._run(['get', 'account'], ignore_errors=True)
            if rc == 0:
                self.logged_in = True
            if not self.logged_in:
                self.get_token()
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise AnsibleLookupError("1Password CLI tool '%s' not installed in path on control machine" % self.cli_path)
            raise e

    def get_raw(self, item_id, vault=None):
        args = ["get", "item", item_id]
        if vault is not None:
            args += ['--vault={0}'.format(vault)]
        if not self.logged_in:
            args += [to_bytes('--session=') + self.token]
        rc, output, dummy = self._run(args)
        return output

    def get_field(self, item_id, field, section=None, vault=None):
        output = self.get_raw(item_id, vault)
        return self._parse_field(output, field, section) if output != '' else ''

    def full_login(self):
        if None in [self.subdomain, self.username, self.secret_key, self.master_password]:
            raise AnsibleLookupError('Unable to perform initial sign in to 1Password. '
                                     'subdomain, username, secret_key, and master_password are required to perform initial sign in.')

        args = [
            'signin',
            '{0}.1password.com'.format(self.subdomain),
            to_bytes(self.username),
            to_bytes(self.secret_key),
            '--output=raw',
        ]

        rc, out, err = self._run(args, command_input=to_bytes(self.master_password))
        self.token = out.strip()

    def _run(self, args, expected_rc=0, command_input=None, ignore_errors=False):
        command = [self.cli_path] + args
        p = Popen(command, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        out, err = p.communicate(input=command_input)
        rc = p.wait()
        if not ignore_errors and rc != expected_rc:
            raise AnsibleLookupError(to_text(err))
        return rc, out, err

    def _parse_field(self, data_json, field_name, section_title=None):
        data = json.loads(data_json)
        if section_title is None:
            for field_data in data['details'].get('fields', []):
                if field_data.get('name', '').lower() == field_name.lower():
                    return field_data.get('value', '')
        for section_data in data['details'].get('sections', []):
            if section_title is not None and section_title.lower() != section_data['title'].lower():
                continue
            for field_data in section_data.get('fields', []):
                if field_data.get('t', '').lower() == field_name.lower():
                    return field_data.get('v', '')
        return ''


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        op = OnePass()

        field = kwargs.get('field', 'password')
        section = kwargs.get('section')
        vault = kwargs.get('vault')
        op.subdomain = kwargs.get('subdomain')
        op.username = kwargs.get('username')
        op.secret_key = kwargs.get('secret_key')
        op.master_password = kwargs.get('master_password', kwargs.get('vault_password'))

        op.assert_logged_in()

        values = []
        for term in terms:
            values.append(op.get_field(term, field, section, vault))
        return values
