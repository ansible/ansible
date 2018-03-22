# Copyright (c) 2018, Scott Buchanan <sbuchanan@ri.pn>
# Copyright (c) 2016, Andrew Zenk <azenk@umn.edu> (lastpass.py used as starting point)
# Copyright (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
    lookup: onepassword
    author:
      -  Scott Buchanan <sbuchanan@ri.pn>
      -  Andrew Zenk <azenk@umn.edu>
    version_added: "2.6"
    requirements:
      - op (1Password command line utility: https://support.1password.com/command-line/)
      - must have already logged into 1Password using op CLI
    short_description: fetch data from 1Password
    description:
      - use the op command line utility to fetch specific fields from 1Password
    options:
      _terms:
        description: identifier(s) of object(s) from which you want to retrieve the field (UUID, name or domain)
        required: True
      field:
        description: field to return from 1Password
        default: 'password'
      vault:
        description: vault to retrieve from (if absent will search all available vaults)
        default: None
"""

EXAMPLES = """
- name: "retrieve password from entry named KITT in any vault"
  debug: password="{{ lookup('onepassword', 'KITT') }}"

- name: "retrieve username from entry named HAL 9000 in vault Discovery"
  debug: password="{{ lookup('onepassword', 'HAL 9000', field='username', vault='Discovery') }}"
"""

RETURN = """
  _raw:
    description: field data requested
"""

import json
from subprocess import Popen, PIPE

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


class OnePass(object):

    def __init__(self, path='op'):
        self._cli_path = path

    @property
    def cli_path(self):
        return self._cli_path

    def assert_logged_in(self):
        try:
            self._run(["get", "account"])
        except:
            raise AnsibleError("Not logged into 1Password: please run 'op signin' first")

    def get_field(self, item_id, field, vault=None):
        args = ["get", "item", item_id]
        if vault is not None:
            args += ['--vault={0}'.format(vault)]
        output, dummy = self._run(args)
        return self._parse_field(field, output) if output != '' else ''

    def _run(self, args, expected_rc=0):
        p = Popen([self.cli_path] + args, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        out, err = p.communicate()
        rc = p.wait()
        if rc != expected_rc:
            raise AnsibleError(err)
        return out, err

    def _parse_field(self, field_name, data_json):
        data = json.loads(data_json)
        for section_data in data['details']['sections']:
            for field_data in section_data.get('fields', {}):
                if field_data.get('t') == field_name:
                    return field_data.get('v', '')
        return ''


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        op = OnePass()

        op.assert_logged_in()

        field = kwargs.get('field', 'password')
        vault = kwargs.get('vault')

        values = []
        for term in terms:
            values.append(op.get_field(term, field, vault))
        return values
