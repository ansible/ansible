#!/usr/bin/python
# encoding: utf-8

# (c) 2017, Jiri Tyr <jiri.tyr@gmail.com>
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


ANSIBLE_METADATA = {
    'status': [
        'preview'
    ],
    'supported_by': 'community',
    'version': '1.0'
}

DOCUMENTATION = '''
---
module: etc_hosts
author: Jiri Tyr (@jtyr)
version_added: '2.3'
short_description: Manages records in the /etc/hosts file
description:
  - Add, remove and modify records in the /etc/hosts file.
options:
  alias:
    required: false
    default: null
    description:
      - Alias(es) of the IP address. Multiple aliases can be either a normal
        YAML list or a string containing comma separated list.
  hostname:
    required: false
    description:
      - Canonical hostname of the IP address. Required if I(state=present).
  ip:
    required: true
    description:
      - IP address.
  path:
    required: false
    default: /etc/hosts
    description:
      - Path to the hosts file. Required if I(state=present).
  state:
    required: false
    choices: [absent, present]
    default: present
    description:
      - State of the record in the hosts file.
      - If C(present), I(ip) and I(hostname) are required.
      - If C(absent), I(ip) or I(hostname) is required.

extends_documentation_fragment:
  - files
'''

EXAMPLES = '''
- name: Add a new record without alias
  etc_hosts:
    ip: 10.0.0.1
    hostname: some.domain1.com

- name: Add a new record with hostname for the same IP
  etc_hosts:
    ip: 10.0.0.1
    hostname: some.domain2.com

- name: Add a new record with another IP for the same hostname
  etc_hosts:
    ip: 10.0.0.2
    hostname: some.domain3.com

- name: Add a new record with hostname and alias for the same IP
  etc_hosts:
    ip: 10.0.0.3
    hostname: some.domain3.com
    alias: some

- name: Add a new record with multiple aliases
  etc_hosts:
    ip: 10.0.0.4
    hostname: some.domain4.com
    alias:
      - some
      - other

- name: Update the list of aliases for the existing IP and hostname
  etc_hosts:
    ip: 10.0.0.4
    hostname: some.domain4.com
    alias:
      - some
      - other
      - alias

- name: Remove all records with the specified IP
  etc_hosts:
    ip: 10.0.0.1
    state: absent

- name: Remove all records with the specified hostname
  etc_hosts:
    hostname: some.domain3.com
    state: absent

- name: Remove record with specified IP and hostname
  etc_hosts:
    ip: 10.0.0.4
    hostname: some.domain4.com
    state: absent
'''

RETURN = '''
state:
  description: state of the target, after execution
  returned: success
  type: string
  sample: "present"
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils._text import to_bytes
import os
import re
import socket
import tempfile


class EtcHosts(object):
    def __init__(self, module):
        # To be able to use fail_json
        self.module = module

        # Shortcut for params
        self.params = module.params

        # This is where we will store all the hosts file lines
        self.lines = []

        self.diff = {
            'before': '',
            'after': ''
        }

        # Validate the IP address
        if (
                self.params['ip'] is not None and
                not (
                    self._is_valid_ipv4_address(self.params['ip']) or
                    self._is_valid_ipv6_address(self.params['ip']))):
            self.module.fail_json(
                msg="The %s is not a valid IP address." % self.params['ip'])

        # Read the file
        if os.path.isfile(self.params['path']):
            self._read()

    def _is_valid_ipv4_address(self, address):
        try:
            socket.inet_pton(socket.AF_INET, address)
        except AttributeError:
            try:
                socket.inet_aton(address)
            except socket.error:
                return False

            return address.count('.') == 3
        except socket.error:
            return False

        return True

    def _is_valid_ipv6_address(self, address):
        try:
            socket.inet_pton(socket.AF_INET6, address)
        except socket.error:
            return False

        return True

    def _read(self):
        # Open the hosts file
        try:
            f = open(self.params['path'])
        except IOError:
            e = get_exception()
            self.module.fail_json(
                msg=(
                    "Cannot open hosts file %s for reading." %
                    self.params['path']),
                details=str(e))

        # Splitting pattern
        p_comment = re.compile("\s*#.*")
        p_split = re.compile("\s+")

        for line in f:
            self.diff['before'] += line

            record = {
                'valid': False,
                'line': line
            }

            # Remove all comments from the line
            line = p_comment.sub('', line)

            if len(line) > 0:
                # Split the line
                items = p_split.split(line.strip())

                # Check if we have valid line
                if len(items) > 1:
                    record['valid'] = True
                    record['ip'] = items[0]
                    record['hostname'] = items[1]

                    # Optional alias(es)
                    if len(items) == 3:
                        record['alias'] = [items[2], ]
                    elif len(items) > 3:
                        record['alias'] = sorted(items[2:])
                    else:
                        record['alias'] = []

            self.lines.append(record)

        # Close the file
        try:
            f.close()
        except IOError:
            e = get_exception()
            self.module.fail_json(
                msg=(
                    "Cannot close the hosts file %s after reading." %
                    self.module['path']),
                detail=str(e))

    def add(self):
        return self._check('add'), self.diff

    def remove(self):
        return self._check('remove'), self.diff

    def _format_line(self):
        line = "%s  %s" % (self.params['ip'], self.params['hostname'])

        if self.params['alias'] is not None:
            line += "  %s" % ' '.join(self.params['alias'])

        line += "\n"

        return line

    def _check(self, action):
        changed = False
        found = None

        # Check if the same record already is in the file
        for idx, line in enumerate(self.lines):
            match = None

            if line['valid']:
                if (
                        self.params['ip'] is not None and
                        line['ip'] == self.params['ip']):
                    match = True
                elif self.params['ip'] is not None:
                    match = False

                if (
                        self.params['hostname'] is not None and
                        line['hostname'] == self.params['hostname']):
                    if match is None:
                        match = True
                    else:
                        match &= True
                elif self.params['hostname'] is not None:
                    match = False

                if match:
                    if action == 'add':
                        found = idx

                        break
                    else:
                        if found is None:
                            found = []

                        found.append(idx)

        if action == 'add':
            if found is None:
                # If not found, add it
                if not self.module.check_mode:
                    record = self._format_line()

                    self.lines.append({'line': record})

                changed = True
            elif self.params['alias'] is not None:
                sorted_aliases_new = sorted(self.params['alias'])
                sorted_aliases_old = sorted(self.lines[found]['alias'])

                # Check if alias has changed
                if sorted_aliases_new != sorted_aliases_old:
                    self.lines[found]['alias'] = self.params['alias']
                    self.lines[found]['line'] = self._format_line()

                    changed = True

        elif action == 'remove' and found is not None:
            # If found, remove it
            if not self.module.check_mode:
                for idx in reversed(found):
                    self.lines.pop(idx)

            changed = True

        if changed:
            self._write_file()

        return changed

    def _write_file(self):
        # Write into tmp file
        tpm_fd, tmp_file = tempfile.mkstemp()

        # Open the hosts file
        try:
            f = open(tmp_file, 'wb')
        except IOError:
            e = get_exception()
            self.module.fail_json(
                msg=(
                    "Cannot open temporary hosts file %s for writing." %
                    tmp_file),
                details=str(e))

        # Write data back into the file
        for line in self.lines:
            f.write(to_bytes(line['line']))
            self.diff['after'] += line['line']

        # Close the file
        try:
            f.close()
        except IOError:
            e = get_exception()
            self.module.fail_json(
                msg=(
                    "Cannot close the temporal hosts file %s after writing." %
                    tmp_file),
                detail=str(e))

        # Move the tmp file to the right location
        self.module.atomic_move(
            tmp_file, self.params['path'],
            unsafe_writes=self.params['unsafe_writes'])


def main():
    # Module settings
    module = AnsibleModule(
        argument_spec=dict(
            alias=dict(type='list'),
            hostname=dict(),
            ip=dict(),
            path=dict(default='/etc/hosts'),
            state=dict(choices=['present', 'absent'], default='present')
        ),
        add_file_common_args=True,
        supports_check_mode=True
    )

    # Make shorter variable
    state = module.params['state']

    # Check presence of the input options
    if (
            state == 'present' and (
                module.params['ip'] is None or
                module.params['hostname'] is None)):
        module.fail_json(msg="Options 'hostname' and 'ip' are required.")

    if (
            state == 'absent' and
            module.params['ip'] is None and
            module.params['hostname'] is None):
        module.fail_json(msg="Option 'hostname' or 'ip' is required.")

    # Read the hosts file
    hosts = EtcHosts(module)

    changed = False

    # Perform action depending on the state
    if state == 'present':
        changed, diff = hosts.add()
    elif state == 'absent':
        changed, diff = hosts.remove()

    # Change file attributes if needed
    if os.path.isfile(module.params['path']):
        file_args = module.load_file_common_arguments(module.params)
        changed = module.set_fs_attributes_if_different(file_args, changed)

    # Print status of the change
    module.exit_json(changed=changed, state=state, diff=diff)


if __name__ == '__main__':
    main()
