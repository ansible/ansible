#!/usr/bin/python
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
#

DOCUMENTATION = """
---
module: junos_template
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Manage configuration on remote devices running Junos
description:
  - The M(junos_template) module will load a candidate configuration
    from a template file onto a remote device running Junos.  The
    module will return the differences in configuration if the diff
    option is specified on the Ansible command line
extends_documentation_fragment: junos
options:
  src:
    description:
      - The path to the config source.  The source can be either a
        file with config or a template that will be merged during
        runtime.  By default the task will search for the source
        file in role or playbook root folder in templates directory.
    required: true
    default: null
  backup:
    description:
      - When this argument is configured true, the module will backup
        the configuration from the node prior to making any changes.
        The backup file will be written to backup_{{ hostname }} in
        the root of the playbook directory.
    required: false
    default: false
    choices: ["true", "false"]
  confirm:
    description:
      - The C(confirm) argument will configure a time out value for
        the commit to be confirmed before it is automatically
        rolled back.  If the C(confirm) argument is set to False, this
        argument is silently ignored.  If the value for this argument
        is set to 0, the commit is confirmed immediately.
    required: false
    default: 0
  comment:
    description:
      - The C(comment) argument specifies a text string to be used
        when committing the configuration.  If the C(confirm) argument
        is set to False, this argument is silently ignored.
    required: false
    default: configured by junos_template
  action:
    description:
      - The C(action) argument specifies how the module will apply changes.
    required: false
    default: merge
    choices: ['merge', 'overwrite', 'replace']
    version_added: "2.2"
  config_format:
    description:
      - The C(format) argument specifies the format of the configuration
        template specified in C(src).  If the format argument is not
        specified, the module will attempt to infer the configuration
        format based of file extension.  Files that end in I(xml) will set
        the format to xml.  Files that end in I(set) will set the format
        to set and all other files will default the format to text.
    required: false
    default: null
    choices: ['text', 'xml', 'set']
requirements:
  - junos-eznc
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed
"""

EXAMPLES = """
- junos_template:
    src: config.j2
    comment: update system config

- name: replace config hierarchy
    src: config.j2
    action: replace

- name: overwrite the config
    src: config.j2
    action: overwrite
"""

DEFAULT_COMMENT = 'configured by junos_template'

def main():

    argument_spec = dict(
        src=dict(required=True, type='path'),
        confirm=dict(default=0, type='int'),
        comment=dict(default=DEFAULT_COMMENT),
        action=dict(default='merge', choices=['merge', 'overwrite', 'replace']),
        config_format=dict(choices=['text', 'set', 'xml']),
        backup=dict(default=False, type='bool'),
        transport=dict(default='netconf', choices=['netconf'])
    )

    module = get_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    comment = module.params['comment']
    confirm = module.params['confirm']
    commit = not module.check_mode

    action = module.params['action']

    src = module.params['src']
    fmt = module.params['config_format']

    if action == 'overwrite' and fmt == 'set':
        module.fail_json(msg="overwrite cannot be used when format is "
            "set per junos documentation")

    results = dict(changed=False)
    results['_backup'] = str(module.get_config()).strip()

    diff = module.load_config(src, action=action, comment=comment,
            format=fmt, commit=commit, confirm=confirm)

    if diff:
        results['changed'] = True
        results['diff'] = dict(prepared=diff)

    module.exit_json(**results)


from ansible.module_utils.basic import *
from ansible.module_utils.junos import *

if __name__ == '__main__':
    main()
