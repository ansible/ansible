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
    version_added: "2.6"
    requirements:
      - C(op) 1Password command line utility. See U(https://support.1password.com/command-line/)
      - must have already logged into 1Password using C(op) CLI
    short_description: fetch field values from 1Password
    description:
      - onepassword wraps the C(op) command line utility to fetch specific field values from 1Password
    options:
      _terms:
        description: identifier(s) (UUID, name or domain; case-insensitive) of item(s) to retrieve
        required: True
      field:
        description: field to return from each matching item (case-insensitive)
        default: 'password'
      section:
        description: item section containing the field to retrieve (case-insensitive); if absent will return first match from any section
        default: None
      vault:
        description: vault containing the item to retrieve (case-insensitive); if absent will search all vaults
        default: None
"""

EXAMPLES = """
- name: "retrieve password for KITT"
  debug:
    msg: "{{ lookup('onepassword', 'KITT') }}"

- name: "retrieve password for Wintermute"
  debug:
    msg: "{{ lookup('onepassword', 'Tessier-Ashpool', section='Wintermute') }}"

- name: "retrieve username for HAL"
  debug:
    msg: "{{ lookup('onepassword', 'HAL 9000', field='username', vault='Discovery') }}"
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


class OnePass(object):

    def __init__(self, path='op'):
        self._cli_path = path

    @property
    def cli_path(self):
        return self._cli_path

    def assert_logged_in(self):
        try:
            self._run(["get", "account"])
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise AnsibleLookupError("1Password CLI tool not installed in path on control machine")
            raise e
        except AnsibleLookupError:
            raise AnsibleLookupError("Not logged into 1Password: please run 'op signin' first")

    def get_raw(self, item_id, vault=None):
        args = ["get", "item", item_id]
        if vault is not None:
            args += ['--vault={0}'.format(vault)]
        output, dummy = self._run(args)
        return output

    def get_field(self, item_id, field, section=None, vault=None):
        output = self.get_raw(item_id, vault)
        return self._parse_field(output, field, section) if output != '' else ''

    def _run(self, args, expected_rc=0):
        p = Popen([self.cli_path] + args, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        out, err = p.communicate()
        rc = p.wait()
        if rc != expected_rc:
            raise AnsibleLookupError(err)
        return out, err

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

        op.assert_logged_in()

        field = kwargs.get('field', 'password')
        section = kwargs.get('section')
        vault = kwargs.get('vault')

        values = []
        for term in terms:
            values.append(op.get_field(term, field, section, vault))
        return values
