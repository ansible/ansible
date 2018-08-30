# -*- coding: utf-8 -*-
# (c) 2018, Scott Buchanan <sbuchanan@ri.pn>
# (c) 2016, Andrew Zenk <azenk@umn.edu> (lastpass.py used as starting point)
# (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
    lookup: onepassword
    author:
      - Scott Buchanan <sbuchanan@ri.pn>
      - Andrew Zenk <azenk@umn.edu>
      - Sam Doran<sdoran@redhat.com>
    version_added: "2.6"
    requirements:
      - C(op) 1Password command line utility. See U(https://support.1password.com/command-line/)
      - must have already logged into 1Password using C(op) CLI
    short_description: fetch field values from 1Password
    description:
      - onepassword wraps the C(op) command line utility to fetch specific field values from 1Password
    options:
      _terms:
        description: identifier(s) (UUID, name, or subdomain; case-insensitive) of item(s) to retrieve
        required: True
      field:
        description: field to return from each matching item (case-insensitive)
        default: 'password'
      section:
        description: item section containing the field to retrieve (case-insensitive); if absent will return first match from any section
        default: None
      subdomain:
        description: The 1Password subdomain to authenticate against.
        default: None
        version_added: '2.7'
      vault:
        description: vault containing the item to retrieve (case-insensitive); if absent will search all vaults
        default: None
      vault_password:
        description: The password used to unlock the specified vault.
        default: None
        version_added: '2.7'
"""

EXAMPLES = """
- name: Retrieve password for KITT
  debug:
    var: lookup('onepassword', 'KITT')

- name: Retrieve password for Wintermute
  debug:
    var: lookup('onepassword', 'Tessier-Ashpool', section='Wintermute')

- name: Retrieve username for HAL
  debug:
    var: lookup('onepassword', 'HAL 9000', field='username', vault='Discovery')

- name: Retrieve password for HAL when not signed in to 1Password
  debug:
    var: lookup('onepassword', 'HAL 9000', subdomain='Discovery', vault_password='DmbslfLvasjdl')
"""

RETURN = """
  _raw:
    description: field data requested
"""

import json
import errno

from subprocess import Popen, PIPE

from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleLookupError
from ansible.module_utils._text import to_bytes


class OnePass(object):

    def __init__(self, path='op'):
        self._cli_path = path
        self._logged_in = False
        self._token = None
        self._subdomain = None
        self._vault_password = None

    @property
    def cli_path(self):
        return self._cli_path

    def get_token(self):
        if not self._subdomain and not self._vault_password:
            raise AnsibleLookupError('Both subdomain and password are required when logging in.')
        args = ['signin', self._subdomain, '--output=raw']
        rc, out, err = self._run(args, command_input=to_bytes(self._vault_password))
        self._token = out.strip()

    def assert_logged_in(self):
        try:
            rc, out, err = self._run(['get', 'account'], ignore_errors=True)
            if rc != 1:
                self._logged_in = True
            if not self._logged_in:
                self.get_token()
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise AnsibleLookupError("1Password CLI tool not installed in path on control machine")
            raise e
        except AnsibleLookupError:
            raise AnsibleLookupError("Not logged into 1Password: please run 'op signin' first, or provide both subdomain and vault_password.")

    def get_raw(self, item_id, vault=None):
        args = ["get", "item", item_id]
        if vault is not None:
            args += ['--vault={0}'.format(vault)]
        if not self._logged_in:
            args += [to_bytes('--session=') + self._token]
        rc, output, dummy = self._run(args)
        return output

    def get_field(self, item_id, field, section=None, vault=None):
        output = self.get_raw(item_id, vault)
        return self._parse_field(output, field, section) if output != '' else ''

    def _run(self, args, expected_rc=0, command_input=None, ignore_errors=False):
        command = [self.cli_path] + args
        p = Popen(command, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        out, err = p.communicate(input=command_input)
        rc = p.wait()
        if not ignore_errors and rc != expected_rc:
            raise AnsibleLookupError(err)
        return rc, out, err

    def _parse_field(self, data_json, field_name, section_title=None):
        data = json.loads(data_json)
        if section_title is None:
            for field_data in data['details'].get('fields', []):
                if field_data.get('name').lower() == field_name.lower():
                    return field_data.get('value', '')
        for section_data in data['details'].get('sections', []):
            if section_title is not None and section_title.lower() != section_data['title'].lower():
                continue
            for field_data in section_data.get('fields', []):
                if field_data.get('t').lower() == field_name.lower():
                    return field_data.get('v', '')
        return ''


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        op = OnePass()

        field = kwargs.get('field', 'password')
        section = kwargs.get('section')
        vault = kwargs.get('vault')
        op._subdomain = kwargs.get('subdomain')
        op._vault_password = kwargs.get('vault_password')

        op.assert_logged_in()

        values = []
        for term in terms:
            values.append(op.get_field(term, field, section, vault))
        return values
