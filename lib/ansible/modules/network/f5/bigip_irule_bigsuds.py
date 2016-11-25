#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Ryan Conway <ryan@rjc.cc>
#
# Inspired by the `bigip_virtual_server` module by
# Etienne Carriere (@Etienne-Carriere) and Tim Rupp (@caphrim007)
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: bigip_irule_bigsuds
short_description: Manage iRules on a BIG-IP
description:
  - Manage iRules on a BIG-IP using the 'bigsuds' module from F5.
version_added: ""
notes:
  - "Requires BIG-IP software version >= 9"
  - "F5 developed module 'bigsuds' required (see http://devcentral.f5.com)"
  - "Best run as a local_action in your playbook"
requirements:
  - bigsuds
author:
  - Ryan Conway (@rylon)
options:
  content:
    description:
      - When used instead of 'src', sets the contents of an iRule directly to
        the specified value. This is for simple values, but can be used with
        lookup plugins for anything complex or with formatting. Either one
        of C(src) or C(content) must be provided.
  partition:
    description:
      - The partition to create the iRule in.
    required: false
    default: Common
  name:
    description:
      - The name of the iRule.
    required: true
  src:
    description:
      - The iRule file to interpret and upload to the BIG-IP. Either one
        of C(src) or C(content) must be provided.
    required: true
  state:
    description:
      - Whether the iRule should exist or not.
    required: false
    default: present
    choices:
      - present
      - absent
extends_documentation_fragment: f5
'''


EXAMPLES = '''
- name: Add an irule with inline content
  delegate_to: localhost
  bigip_irule_bigsuds:
      state:          "present"
      server:         "lb.mydomain.com"
      validate_certs: false
      user:           "username"
      password:       "password"
      partition:      "my_partition"
      name:           "my_irule"
      content:        "when HTTP_REQUEST { HTTP::header insert "MY_TEST_HEADER" "testing" }"

- name: Add an irule by reading from a specific file
  delegate_to: localhost
  bigip_irule_bigsuds:
      state:          "present"
      server:         "lb.mydomain.com"
      validate_certs: false
      user:           "username"
      password:       "password"
      partition:      "my_partition"
      name:           "my_irule"
      src:            "/path/to/rule.tcl"
'''


RETURN = '''
action:
    description: Shows the type of modification made, if there were changes, for example "updated", "deleted", "created"
    returned: changed
    type: string
    sample: "updated"
irule_name:
    description: The fully qualified irule name
    returned: changed and success
    type: string
    sample: "/my_partition/my_irule"
'''


def irule_exists(api, name):
    result = False
    try:
        api.LocalLB.Rule.query_rule(rule_names=[name])
        result = True
    except bigsuds.OperationFailed as e:
        if "was not found" in str(e):
            result = False
        else:
            # genuine exception
            raise
    return result


def irule_create(api, name, content):
    api.LocalLB.Rule.create(rules=[ {'rule_name': name, 'rule_definition': content} ])


def irule_update(api, name, content, diff_enabled):
    updated = {'changed': False, 'irule_name': name}
    existing_irule = irule_get(api, name)

    if existing_irule['rule_definition'] != content:
        api.LocalLB.Rule.modify_rule(rules=[ {'rule_name': name, 'rule_definition': content} ])
        updated['changed'] = True
        updated['action'] = 'updated'
        if diff_enabled:
            updated['diff'] = {
                'before_header': name,
                'before': existing_irule['rule_definition'],
                'after_header': name,
                'after': content
            }

    return updated


def irule_get(api, name):
    # Example response: [{'rule_name': '/my_partition/my_irule', 'rule_definition': '<irule code goes here>'}]
    return api.LocalLB.Rule.query_rule(rule_names=[name])[0]


def irule_remove(api, name):
    api.LocalLB.Rule.delete_rule(rule_names=[name])


def main():
    argument_spec = f5_argument_spec()
    argument_spec.update(dict(
        state=dict(type='str', default='present',
                   choices=['present', 'absent']),
        name=dict(type='str', required=True),
        content=dict(required=False, default=None),
        src=dict(required=False, default=None),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['content', 'src']
        ]
    )

    if not bigsuds_found:
        module.fail_json(msg="the python bigsuds module is required")

    if module.params['validate_certs']:
        import ssl
        if not hasattr(ssl, 'SSLContext'):
            module.fail_json(msg='bigsuds does not support verifying certificates with python < 2.7.9.  Either update python or set validate_certs=False on the task')

    server = module.params['server']
    server_port = module.params['server_port']
    user = module.params['user']
    password = module.params['password']
    partition = module.params['partition']
    validate_certs = module.params['validate_certs']

    state = module.params['state']
    name = fq_name(partition, module.params['name']) # Fully Qualified name (including the partition)

    # Irule contents can either be defined inline via 'content' attribute, or by passing the path to 
    # a file via 'src' attribute, for the latter we need to read those contents from the file.
    content = None
    if module.params['src']:
        try:
            with open(module.params['src']) as f:
                content = f.read()
        except Exception as e:
            raise Exception('Error reading iRule "src" file : %s' % e)
    else:
        content = module.params['content']

    try:
        api = bigip_api(server, user, password, validate_certs, port=server_port)
        result = {'changed': False, 'irule_name': name}  # default module return value

        if state == 'absent':
            # Check mode is disabled
            if not module.check_mode:
                if irule_exists(api, name):
                    try:
                        irule_remove(api, name)
                        result = {'changed': True, 'action': 'deleted'}
                    except bigsuds.OperationFailed as e:
                        # Handles the situation where the irule was deleted in between us querying for its existence and running the delete command.
                        if "was not found" in str(e):
                            result['changed'] = False
                        else:
                            raise
            # Check mode is enabled
            else:
                result = {'changed': True}

        # State is 'present'
        else:
            # Check mode is disabled
            if not module.check_mode:
                # If the irule doesn't exist we can create it.
                if not irule_exists(api, name):
                    try:
                        irule_create(api, name, content)
                        result = {'changed': True, 'action': 'created'}
                    except Exception as e:
                        raise Exception('Error creating iRule : %s' % e)
               
                # The irule already exists so we need to check if it has the correct content
                # and update it only if necessary, so Ansible can report 'changed' correctly.
                else:
                    try:
                        result = irule_update(api, name, content, module._diff)
                    except Exception as e:
                        raise Exception("Error updating iRule : %s" % e)

            # Check mode is disabled
            else:
                # check-mode return value
                result = {'changed': True}

    except Exception as e:
        module.fail_json(msg="Received exception: %s" % e)

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.f5 import *

if __name__ == '__main__':
    main()
