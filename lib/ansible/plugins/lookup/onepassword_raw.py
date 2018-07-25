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
    lookup: onepassword_raw
    author:
      - Scott Buchanan <sbuchanan@ri.pn>
      - Andrew Zenk <azenk@umn.edu>
    version_added: "2.6"
    requirements:
      - C(op) 1Password command line utility. See U(https://support.1password.com/command-line/)
      - must have already logged into 1Password using op CLI
    short_description: fetch raw json data from 1Password
    description:
      - onepassword_raw wraps C(op) command line utility to fetch an entire item from 1Password
    options:
      _terms:
        description: identifier(s) (UUID, name, or domain; case-insensitive) of item(s) to retrieve
        required: True
      vault:
        description: vault containing the item to retrieve (case-insensitive); if absent will search all vaults
        default: None
"""

EXAMPLES = """
- name: "retrieve all data about Wintermute"
  debug:
    msg: "{{ lookup('onepassword_raw', 'Wintermute') }}"
"""

RETURN = """
  _raw:
    description: field data requested
"""

import json

from ansible.plugins.lookup.onepassword import OnePass
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        op = OnePass()

        op.assert_logged_in()

        vault = kwargs.get('vault')

        values = []
        for term in terms:
            data = json.loads(op.get_raw(term, vault))
            values.append(data)
        return values
