#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Ryan Conway (@rylon)
# (c) 2018, Scott Buchanan <sbuchanan@ri.pn> (onepassword.py used as starting point)
# (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: onepassword_info
author:
    - Ryan Conway (@Rylon)
version_added: "2.7"
requirements:
    - C(op) 1Password command line utility. See U(https://support.1password.com/command-line/)
notes:
    - Tested with C(op) version 0.5.5
    - "Based on the C(onepassword) lookup plugin by Scott Buchanan <sbuchanan@ri.pn>."
    - When this module is called with the deprecated C(onepassword_facts) name, potentially sensitive data
      from 1Password is returned as Ansible facts. Facts are subject to caching if enabled, which means this
      data could be stored in clear text on disk or in a database.
short_description: Gather items from 1Password
description:
    - M(onepassword_info) wraps the C(op) command line utility to fetch data about one or more 1Password items.
    - A fatal error occurs if any of the items being searched for can not be found.
    - Recommend using with the C(no_log) option to avoid logging the values of the secrets being retrieved.
    - This module was called C(onepassword_facts) before Ansible 2.9, returning C(ansible_facts).
      Note that the M(onepassword_info) module no longer returns C(ansible_facts)!
      You must now use the C(register) option to use the facts in other tasks.
options:
    search_terms:
        type: list
        description:
            - A list of one or more search terms.
            - Each search term can either be a simple string or it can be a dictionary for more control.
            - When passing a simple string, I(field) is assumed to be C(password).
            - When passing a dictionary, the following fields are available.
        suboptions:
            name:
                type: str
                description:
                    - The name of the 1Password item to search for (required).
            field:
                type: str
                description:
                    - The name of the field to search for within this item (optional, defaults to "password" (or "document" if the item has an attachment).
            section:
                type: str
                description:
                    - The name of a section within this item containing the specified field (optional, will search all sections if not specified).
            vault:
                type: str
                description:
                    - The name of the particular 1Password vault to search, useful if your 1Password user has access to multiple vaults (optional).
        required: True
    auto_login:
        type: dict
        description:
            - A dictionary containing authentication details. If this is set, M(onepassword_info) will attempt to sign in to 1Password automatically.
            - Without this option, you must have already logged in via the 1Password CLI before running Ansible.
            - It is B(highly) recommended to store 1Password credentials in an Ansible Vault. Ensure that the key used to encrypt
              the Ansible Vault is equal to or greater in strength than the 1Password master password.
        suboptions:
            subdomain:
                type: str
                description:
                    - 1Password subdomain name (<subdomain>.1password.com).
                    - If this is not specified, the most recent subdomain will be used.
            username:
                type: str
                description:
                    - 1Password username.
                    - Only required for initial sign in.
            master_password:
                type: str
                description:
                    - The master password for your subdomain.
                    - This is always required when specifying C(auto_login).
                required: True
            secret_key:
                type: str
                description:
                    - The secret key for your subdomain.
                    - Only required for initial sign in.
        default: {}
        required: False
    cli_path:
        type: path
        description: Used to specify the exact path to the C(op) command line interface
        required: False
        default: 'op'
'''

EXAMPLES = '''
# Gather secrets from 1Password, assuming there is a 'password' field:
- name: Get a password
  onepassword_info:
    search_terms: My 1Password item
  delegate_to: localhost
  register: my_1password_item
  no_log: true         # Don't want to log the secrets to the console!

# Gather secrets from 1Password, with more advanced search terms:
- name: Get a password
  onepassword_info:
    search_terms:
      - name:    My 1Password item
        field:   Custom field name       # optional, defaults to 'password'
        section: Custom section name     # optional, defaults to 'None'
        vault:   Name of the vault       # optional, only necessary if there is more than 1 Vault available
  delegate_to: localhost
  register: my_1password_item
  no_log: True                           # Don't want to log the secrets to the console!

# Gather secrets combining simple and advanced search terms to retrieve two items, one of which we fetch two
# fields. In the first 'password' is fetched, as a field name is not specified (default behaviour) and in the
# second, 'Custom field name' is fetched, as that is specified explicitly.
- name: Get a password
  onepassword_info:
    search_terms:
      - My 1Password item                # 'name' is optional when passing a simple string...
      - name: My Other 1Password item    # ...but it can also be set for consistency
      - name:    My 1Password item
        field:   Custom field name       # optional, defaults to 'password'
        section: Custom section name     # optional, defaults to 'None'
        vault:   Name of the vault       # optional, only necessary if there is more than 1 Vault available
      - name: A 1Password item with document attachment
  delegate_to: localhost
  register: my_1password_item
  no_log: true                           # Don't want to log the secrets to the console!

- name: Debug a password (for example)
  debug:
    msg: "{{ my_1password_item['onepassword']['My 1Password item'] }}"
'''

RETURN = '''
---
# One or more dictionaries for each matching item from 1Password, along with the appropriate fields.
# This shows the response you would expect to receive from the third example documented above.
onepassword:
    description: Dictionary of each 1password item matching the given search terms, shows what would be returned from the third example above.
    returned: success
    type: dict
    sample:
        "My 1Password item":
            password: the value of this field
            Custom field name: the value of this field
        "My Other 1Password item":
            password: the value of this field
        "A 1Password item with document attachment":
            document: the contents of the document attached to this item
'''


import errno
import json
import os
import re

from subprocess import Popen, PIPE

from ansible.module_utils._text import to_bytes, to_native
from ansible.module_utils.basic import AnsibleModule


class AnsibleModuleError(Exception):
    def __init__(self, results):
        self.results = results

    def __repr__(self):
        return self.results


class OnePasswordInfo(object):

    def __init__(self):
        self.cli_path = module.params.get('cli_path')
        self.config_file_path = '~/.op/config'
        self.auto_login = module.params.get('auto_login')
        self.logged_in = False
        self.token = None

        terms = module.params.get('search_terms')
        self.terms = self.parse_search_terms(terms)

    def _run(self, args, expected_rc=0, command_input=None, ignore_errors=False):
        if self.token:
            # Adds the session token to all commands if we're logged in.
            args += [to_bytes('--session=') + self.token]

        command = [self.cli_path] + args
        p = Popen(command, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        out, err = p.communicate(input=command_input)
        rc = p.wait()
        if not ignore_errors and rc != expected_rc:
            raise AnsibleModuleError(to_native(err))
        return rc, out, err

    def _parse_field(self, data_json, item_id, field_name, section_title=None):
        data = json.loads(data_json)

        if ('documentAttributes' in data['details']):
            # This is actually a document, let's fetch the document data instead!
            document = self._run(["get", "document", data['overview']['title']])
            return {'document': document[1].strip()}

        else:
            # This is not a document, let's try to find the requested field

            # Some types of 1Password items have a 'password' field directly alongside the 'fields' attribute,
            # not inside it, so we need to check there first.
            if (field_name in data['details']):
                return {field_name: data['details'][field_name]}

            # Otherwise we continue looking inside the 'fields' attribute for the specified field.
            else:
                if section_title is None:
                    for field_data in data['details'].get('fields', []):
                        if field_data.get('name', '').lower() == field_name.lower():
                            return {field_name: field_data.get('value', '')}

                # Not found it yet, so now lets see if there are any sections defined
                # and search through those for the field. If a section was given, we skip
                # any non-matching sections, otherwise we search them all until we find the field.
                for section_data in data['details'].get('sections', []):
                    if section_title is not None and section_title.lower() != section_data['title'].lower():
                        continue
                    for field_data in section_data.get('fields', []):
                        if field_data.get('t', '').lower() == field_name.lower():
                            return {field_name: field_data.get('v', '')}

        # We will get here if the field could not be found in any section and the item wasn't a document to be downloaded.
        optional_section_title = '' if section_title is None else " in the section '%s'" % section_title
        module.fail_json(msg="Unable to find an item in 1Password named '%s' with the field '%s'%s." % (item_id, field_name, optional_section_title))

    def parse_search_terms(self, terms):
        processed_terms = []

        for term in terms:
            if not isinstance(term, dict):
                term = {'name': term}

            if 'name' not in term:
                module.fail_json(msg="Missing required 'name' field from search term, got: '%s'" % to_native(term))

            term['field'] = term.get('field', 'password')
            term['section'] = term.get('section', None)
            term['vault'] = term.get('vault', None)

            processed_terms.append(term)

        return processed_terms

    def get_raw(self, item_id, vault=None):
        try:
            args = ["get", "item", item_id]
            if vault is not None:
                args += ['--vault={0}'.format(vault)]
            rc, output, dummy = self._run(args)
            return output

        except Exception as e:
            if re.search(".*not found.*", to_native(e)):
                module.fail_json(msg="Unable to find an item in 1Password named '%s'." % item_id)
            else:
                module.fail_json(msg="Unexpected error attempting to find an item in 1Password named '%s': %s" % (item_id, to_native(e)))

    def get_field(self, item_id, field, section=None, vault=None):
        output = self.get_raw(item_id, vault)
        return self._parse_field(output, item_id, field, section) if output != '' else ''

    def full_login(self):
        if self.auto_login is not None:
            if None in [self.auto_login.get('subdomain'), self.auto_login.get('username'),
                        self.auto_login.get('secret_key'), self.auto_login.get('master_password')]:
                module.fail_json(msg='Unable to perform initial sign in to 1Password. '
                                     'subdomain, username, secret_key, and master_password are required to perform initial sign in.')

            args = [
                'signin',
                '{0}.1password.com'.format(self.auto_login['subdomain']),
                to_bytes(self.auto_login['username']),
                to_bytes(self.auto_login['secret_key']),
                '--output=raw',
            ]

            try:
                rc, out, err = self._run(args, command_input=to_bytes(self.auto_login['master_password']))
                self.token = out.strip()
            except AnsibleModuleError as e:
                module.fail_json(msg="Failed to perform initial sign in to 1Password: %s" % to_native(e))
        else:
            module.fail_json(msg="Unable to perform an initial sign in to 1Password. Please run '%s sigin' "
                                 "or define credentials in 'auto_login'. See the module documentation for details." % self.cli_path)

    def get_token(self):
        # If the config file exists, assume an initial signin has taken place and try basic sign in
        if os.path.isfile(self.config_file_path):

            if self.auto_login is not None:

                # Since we are not currently signed in, master_password is required at a minimum
                if not self.auto_login.get('master_password'):
                    module.fail_json(msg="Unable to sign in to 1Password. 'auto_login.master_password' is required.")

                # Try signing in using the master_password and a subdomain if one is provided
                try:
                    args = ['signin', '--output=raw']

                    if self.auto_login.get('subdomain'):
                        args = ['signin', self.auto_login['subdomain'], '--output=raw']

                    rc, out, err = self._run(args, command_input=to_bytes(self.auto_login['master_password']))
                    self.token = out.strip()

                except AnsibleModuleError:
                    self.full_login()

            else:
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
                module.fail_json(msg="1Password CLI tool '%s' not installed in path on control machine" % self.cli_path)
            raise e

    def run(self):
        result = {}

        self.assert_logged_in()

        for term in self.terms:
            value = self.get_field(term['name'], term['field'], term['section'], term['vault'])

            if term['name'] in result:
                # If we already have a result for this key, we have to append this result dictionary
                # to the existing one. This is only applicable when there is a single item
                # in 1Password which has two different fields, and we want to retrieve both of them.
                result[term['name']].update(value)
            else:
                # If this is the first result for this key, simply set it.
                result[term['name']] = value

        return result


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            cli_path=dict(type='path', default='op'),
            auto_login=dict(type='dict', options=dict(
                subdomain=dict(type='str'),
                username=dict(type='str'),
                master_password=dict(required=True, type='str', no_log=True),
                secret_key=dict(type='str', no_log=True),
            ), default=None),
            search_terms=dict(required=True, type='list')
        ),
        supports_check_mode=True
    )

    results = {'onepassword': OnePasswordInfo().run()}

    if module._name == 'onepassword_facts':
        module.deprecate("The 'onepassword_facts' module has been renamed to 'onepassword_info'. "
                         "When called with the new name it no longer returns 'ansible_facts'", version='2.13')
        module.exit_json(changed=False, ansible_facts=results)
    else:
        module.exit_json(changed=False, **results)


if __name__ == '__main__':
    main()
