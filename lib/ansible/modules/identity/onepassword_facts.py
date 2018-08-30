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
module: onepassword_facts
author:
    - Ryan Conway (@rylon)
version_added: "2.7"
requirements:
    - C(op) 1Password command line utility (v0.5.1). See U(https://support.1password.com/command-line/)
notes:
    - "Based on the C(onepassword) lookup plugin by Scott Buchanan <sbuchanan@ri.pn>."
short_description: Fetch facts from 1Password items
description:
    - M(onepassword_facts) wraps the C(op) command line utility to fetch data about one or more 1password items and return as Ansible facts.
    - A fatal error occurs if any of the items being searched for can not be found.
    - Recommend using with the C(no_log) option to avoid logging the values of the secrets being retrieved.
options:
    search_terms:
        description:
            - A list of one or more search terms.
            - Each search term can either be a simple string or it can be a dictionary for more control.
            - When passing a simple string, I(field) is assumed to be C(password).
            - When passing a dictionary, the following fields are available.
        suboptions:
            name:
                description:
                    - The name of the 1Password item to search for (required).
            field:
                description:
                    - The name of the field to search for within this item (optional, defaults to "password" (or "document" if the item has an attachment).
            section:
                description:
                    - The name of a section within this item containing the specified field (optional, will search all sections if not specified).
            vault:
                description:
                    - The name of the particular 1Password vault to search, useful if your 1Password user has access to multiple vaults (optional).
        required: True
    auto_login:
        description:
            - A dictionary containing authentication details. If this is set, M(onepassword_facts) will attempt to login to 1password automatically.
            - The required values can be stored in Ansible Vault, and passed to the module securely that way.
            - Without this option, you must have already logged in via the 1Password CLI before running Ansible.
        suboptions:
            account:
                description:
                    - 1Password account name (<account>.1password.com).
            username:
                description:
                    - 1Password username.
            masterpassword:
                description:
                    - The master password for your user.
            secretkey:
                description:
                    - The secret key for your user.
        default: {}
        required: False
    cli_path:
        description: Used to specify the exact path to the C(op) command line interface
        required: False
        default: 'op'
'''

EXAMPLES = '''
# Gather secrets from 1Password, assuming there is a 'password' field:
- name: Get a password
  onepassword_facts:
    search_terms: My 1Password item
  delegate_to: local
  no_log:      true   # Don't want to log the secrets to the console!

# Gather secrets from 1Password, with more advanced search terms:
- name: Get a password
  onepassword_facts:
    search_terms:
      - name:    My 1Password item
        field:   Custom field name       # optional, defaults to 'password'
        section: Custom section name     # optional, defaults to 'None'
        vault:   Name of the vault       # optional, only necessary if there is more than 1 Vault available
  delegate_to: local
  no_log:      true   # Don't want to log the secrets to the console!

# Gather secrets combining simple and advanced search terms to retrieve two items, one of which we fetch two
# fields. In the first 'password' is fetched, as a field name is not specified (default behaviour) and in the
# second, 'Custom field name' is fetched, as that is specified explicitly.
- name: Get a password
  onepassword_facts:
    search_terms:
      - My 1Password item                # 'name' is optional when passing a simple string...
      - name: My Other 1Password item    # ...but it can also be set for consistency
      - name:    My 1Password item
        field:   Custom field name       # optional, defaults to 'password'
        section: Custom section name     # optional, defaults to 'None'
        vault:   Name of the vault       # optional, only necessary if there is more than 1 Vault available
      - name: A 1Password item with document attachment
  delegate_to: local
  no_log:      true   # Don't want to log the secrets to the console!
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

from ansible.module_utils.basic import AnsibleModule


class OnePasswordFacts(object):

    def __init__(self):
        self.cli_path = module.params.get('cli_path')
        self.auto_login = module.params.get('auto_login')
        self.token = {}

        terms = module.params.get('search_terms')
        self.terms = self.parse_search_terms(module.params.get('search_terms'))

    def parse_search_terms(self, terms):
        processed_terms = []

        for term in terms:
            if not isinstance(term, dict):
                term = {'name': term}

            if 'name' not in term:
                module.fail_json(msg="Missing required 'name' field from search term, got: '%s'" % str(term))

            term['field'] = term.get('field', 'password')
            term['section'] = term.get('section', None)
            term['vault'] = term.get('vault', None)

            processed_terms.append(term)

        return processed_terms

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

    def assert_logged_in(self):
        try:
            self._run(["get", "account"])

        except OSError as e:
            if e.errno == errno.ENOENT:
                module.fail_json(msg="1Password CLI tool not installed in path '%s': %s" % (self.cli_path, e))
            else:
                module.fail_json(msg="1Password CLI tool failed to execute at path '%s': %s" % (self.cli_path, e))

        except Exception as e:
            # 1Password's CLI doesn't seem to return different error codes, so we need to handle a few of the common
            # error cases by searching via regex, so we can provide a clearer error message to the user.
            if re.search(".*You are not currently signed in.*", str(e)) is not None:
                if (self.auto_login is not None):
                    try:
                        token = self._run([
                            "signin", "%s.1password.com" % self.auto_login['account'],
                            self.auto_login['username'],
                            self.auto_login['secretkey'],
                            self.auto_login['masterpassword'],
                            "--shorthand=ansible_%s" % self.auto_login['account'],
                            "--output=raw"
                        ])
                        self.token = {'OP_SESSION_ansible_%s' % self.auto_login['account']: token[0].strip()}

                    except Exception as e:
                        module.fail_json(msg="Unable to automatically login to 1Password: %s " % e)
                else:
                    module.fail_json(msg=(
                        "Not logged into 1Password: please run '%s signin' first, or see the module docs for "
                        "how to configure for automatic login." % self.cli_path)
                    )

    def get_raw(self, item_id, vault=None):
        try:
            args = ["get", "item", item_id]
            if vault is not None:
                args += ['--vault={0}'.format(vault)]
            output, dummy = self._run(args)
            return output

        except Exception as e:
            if re.search(".*not found.*", str(e)):
                module.fail_json(msg="Unable to find an item in 1Password named '%s'." % item_id)
            else:
                module.fail_json(msg="Unexpected error attempting to find an item in 1Password named '%s': %s" % (item_id, e))

    def get_field(self, item_id, field, section=None, vault=None):
        output = self.get_raw(item_id, vault)
        return self._parse_field(output, item_id, field, section) if output != '' else ''

    def _run(self, args, expected_rc=0):
        # Duplicates the current shell environment before running 'op', so we get the same PATH the user has,
        # but we merge in the auth token dictionary, allowing the auto-login functionality to work (if enabled).
        env = {}
        env.update(os.environ.copy())
        env.update(self.token)

        p = Popen([self.cli_path] + args, stdout=PIPE, stderr=PIPE, stdin=PIPE, env=env)
        out, err = p.communicate()

        rc = p.wait()

        if rc != expected_rc:
            raise Exception(err)

        return out, err

    def _parse_field(self, data_json, item_id, field_name, section_title=None):
        data = json.loads(data_json)

        if ('documentAttributes' in data['details']):
            # This is actually a document, let's fetch the document data instead!
            document = self._run(["get", "document", data['overview']['title']])
            return {'document': document[0].strip()}

        else:
            # This is not a document, let's try to find the requested field
            if section_title is None:
                for field_data in data['details'].get('fields', []):
                    if field_data.get('name').lower() == field_name.lower():
                        return {field_name: field_data.get('value', '')}

            # Not found it yet, so now lets see if there are any sections defined
            # and search through those for the field. If a section was given, we skip
            # any non-matching sections, otherwise we search them all until we find the field.
            for section_data in data['details'].get('sections', []):
                if section_title is not None and section_title.lower() != section_data['title'].lower():
                    continue
                for field_data in section_data.get('fields', []):
                    if field_data.get('t').lower() == field_name.lower():
                        return {field_name: field_data.get('v', '')}

        # We will get here if the field could not be found in any section and the item wasn't a document to be downloaded.
        optional_section_title = '' if section_title is None else " in the section '%s'" % section_title
        module.fail_json(msg="Unable to find an item in 1Password named '%s' with the field '%s'%s." % (item_id, field_name, optional_section_title))


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            cli_path=dict(type='path', default='op'),
            auto_login=dict(type='dict', options=dict(
                account=dict(required=True, type='str'),
                username=dict(required=True, type='str'),
                masterpassword=dict(required=True, type='str'),
                secretkey=dict(required=True, type='str'),
            ), default=None),
            search_terms=dict(required=True, type='list')
        ),
        supports_check_mode=True
    )

    ansible_facts = {'onepassword': OnePasswordFacts().run()}
    module_return = dict(changed=False, ansible_facts=ansible_facts)
    module.exit_json(**module_return)


if __name__ == '__main__':
    main()
