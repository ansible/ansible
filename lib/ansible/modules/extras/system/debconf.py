#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible module to configure .deb packages.
(c) 2014, Brian Coca <briancoca+ansible@gmail.com>

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Ansible is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""

DOCUMENTATION = '''
---
module: debconf
short_description: Configure a .deb package
description:
     - Configure a .deb package using debconf-set-selections. Or just query
       existing selections.
version_added: "1.6"
notes:
    - This module requires the command line debconf tools.
    - A number of questions have to be answered (depending on the package).
      Use 'debconf-show <package>' on any Debian or derivative with the package
      installed to see questions/settings available.
    - Some distros will always record tasks involving the setting of passwords as changed. This is due to debconf-get-selections masking passwords.
requirements: [ debconf, debconf-utils ]
options:
  name:
    description:
      - Name of package to configure.
    required: true
    default: null
    aliases: ['pkg']
  question:
    description:
      - A debconf configuration setting
    required: false
    default: null
    aliases: ['setting', 'selection']
  vtype:
    description:
      - The type of the value supplied.
      - C(seen) was added in 2.2.
    required: false
    default: null
    choices: [string, password, boolean, select, multiselect, note, error, title, text, seen]
  value:
    description:
      -  Value to set the configuration to
    required: false
    default: null
    aliases: ['answer']
  unseen:
    description:
      - Do not set 'seen' flag when pre-seeding
    required: false
    default: False
author: "Brian Coca (@bcoca)"

'''

EXAMPLES = '''
# Set default locale to fr_FR.UTF-8
debconf: name=locales question='locales/default_environment_locale' value=fr_FR.UTF-8 vtype='select'

# set to generate locales:
debconf: name=locales question='locales/locales_to_be_generated'  value='en_US.UTF-8 UTF-8, fr_FR.UTF-8 UTF-8' vtype='multiselect'

# Accept oracle license
debconf: name='oracle-java7-installer' question='shared/accepted-oracle-license-v1-1' value='true' vtype='select'

# Specifying package you can register/return the list of questions and current values
debconf: name='tzdata'
'''

def get_selections(module, pkg):
    cmd = [module.get_bin_path('debconf-show', True), pkg]
    rc, out, err = module.run_command(' '.join(cmd))

    if rc != 0:
        module.fail_json(msg=err)

    selections = {}

    for line in out.splitlines():
        (key, value) = line.split(':', 1)
        selections[ key.strip('*').strip() ] = value.strip()

    return selections


def set_selection(module, pkg, question, vtype, value, unseen):

    setsel = module.get_bin_path('debconf-set-selections', True)
    cmd = [setsel]
    if unseen:
        cmd.append('-u')

    if vtype == 'boolean':
        if value == 'True':
            value = 'true'
        elif value == 'False':
            value = 'false'
    data = ' '.join([pkg, question, vtype, value])

    return module.run_command(cmd, data=data)

def main():

    module = AnsibleModule(
        argument_spec = dict(
           name = dict(required=True, aliases=['pkg'], type='str'),
           question = dict(required=False, aliases=['setting', 'selection'], type='str'),
           vtype = dict(required=False, type='str', choices=['string', 'password', 'boolean', 'select',  'multiselect', 'note', 'error', 'title', 'text', 'seen']),
           value = dict(required=False, type='str', aliases=['answer']),
           unseen = dict(required=False, type='bool'),
        ),
        required_together = ( ['question','vtype', 'value'],),
        supports_check_mode=True,
    )

    #TODO: enable passing array of options and/or debconf file from get-selections dump
    pkg      = module.params["name"]
    question = module.params["question"]
    vtype    = module.params["vtype"]
    value    = module.params["value"]
    unseen   = module.params["unseen"]

    prev = get_selections(module, pkg)

    changed = False
    msg = ""

    if question is not None:
        if vtype is None or value is None:
            module.fail_json(msg="when supplying a question you must supply a valid vtype and value")

        if not question in prev or prev[question] != value:
            changed = True

    if changed:
        if not module.check_mode:
            rc, msg, e = set_selection(module, pkg, question, vtype, value, unseen)
            if rc:
                module.fail_json(msg=e)

        curr = { question: value }
        if question in prev:
            prev = {question: prev[question]}
        else:
            prev[question] = ''
        if module._diff:
            after = prev.copy()
            after.update(curr)
            diff_dict = {'before': prev, 'after': after}
        else:
            diff_dict = {}

        module.exit_json(changed=changed, msg=msg, current=curr, previous=prev, diff=diff_dict)

    module.exit_json(changed=changed, msg=msg, current=prev)

# import module snippets
from ansible.module_utils.basic import *

main()
