#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible module to manage symbolic link alternatives.
(c) 2014, Gabe Mulley <gabe.mulley@gmail.com>

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
module: alternatives
short_description: Manages alternative programs for common commands
description:
    - Manages symbolic links using the 'update-alternatives' tool provided on debian-like systems.
    - Useful when multiple programs are installed but provide similar functionality (e.g. different editors).
version_added: "1.6"
options:
  name:
    description:
      - The generic name of the link.
    required: true
  path:
    description:
      - The path to the real executable that the link should point to.
    required: true
  link:
    description:
      - The path to the symbolic link that should point to the real executable.
    required: false
requirements: [ update-alternatives ]
'''

EXAMPLES = '''
- name: correct java version selected
  alternatives: name=java path=/usr/lib/jvm/java-7-openjdk-amd64/jre/bin/java

- name: alternatives link created
  alternatives: name=hadoop-conf link=/etc/hadoop/conf path=/etc/hadoop/conf.ansible
'''

DEFAULT_LINK_PRIORITY = 50

def main():

    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True),
            path  = dict(required=True),
            link = dict(required=False),
        )
    )

    params = module.params
    name = params['name']
    path = params['path']
    link = params['link']

    UPDATE_ALTERNATIVES =  module.get_bin_path('update-alternatives',True)

    current_path = None
    all_alternatives = []

    (rc, query_output, query_error) = module.run_command(
        [UPDATE_ALTERNATIVES, '--query', name]
    )

    # Gather the current setting and all alternatives from the query output.
    # Query output should look something like this:

        # Name: java
        # Link: /usr/bin/java
        # Slaves:
        #  java.1.gz /usr/share/man/man1/java.1.gz
        # Status: manual
        # Best: /usr/lib/jvm/java-7-openjdk-amd64/jre/bin/java
        # Value: /usr/lib/jvm/java-6-openjdk-amd64/jre/bin/java

        # Alternative: /usr/lib/jvm/java-6-openjdk-amd64/jre/bin/java
        # Priority: 1061
        # Slaves:
        #  java.1.gz /usr/lib/jvm/java-6-openjdk-amd64/jre/man/man1/java.1.gz

        # Alternative: /usr/lib/jvm/java-7-openjdk-amd64/jre/bin/java
        # Priority: 1071
        # Slaves:
        #  java.1.gz /usr/lib/jvm/java-7-openjdk-amd64/jre/man/man1/java.1.gz

    if rc == 0:
        for line in query_output.splitlines():
            split_line = line.split(':')
            if len(split_line) == 2:
                key = split_line[0]
                value = split_line[1].strip()
                if key == 'Value':
                    current_path = value
                elif key == 'Alternative':
                    all_alternatives.append(value)
                elif key == 'Link' and not link:
                    link = value

    if current_path != path:
        try:
            # install the requested path if necessary
            if path not in all_alternatives:
                module.run_command(
                    [UPDATE_ALTERNATIVES, '--install', link, name, path, str(DEFAULT_LINK_PRIORITY)],
                    check_rc=True
                )

            # select the requested path
            module.run_command(
                [UPDATE_ALTERNATIVES, '--set', name, path],
                check_rc=True
            )

            module.exit_json(changed=True)
        except subprocess.CalledProcessError, cpe:
            module.fail_json(msg=str(dir(cpe)))
    else:
        module.exit_json(changed=False)


# import module snippets
from ansible.module_utils.basic import *
main()
