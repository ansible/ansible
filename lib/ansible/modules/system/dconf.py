#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Branko Majic <branko@majic.rs>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: dconf
author:
    - "Branko Majic (@azaghal)"
short_description: Modify and read dconf database
description:
  - This module allows modifications and reading of dconf database. The module
    is implemented as a wrapper around dconf tool. Please see the dconf(1) man
    page for more details.
notes:
  - Keep in mind that the C(dconf) CLI tool, which this module wraps around,
    utilises an unusual syntax for the values (GVariant). For example, if you
    wanted to provide a string value, the correct syntax would be
    C(value="'myvalue'") - with single quotes as part of the Ansible parameter
    value.
  - The easiest way to figure out exact syntax/value you need to provide for a
    key is by making the configuration change in application affected by the
    key, and then having a look at value set via commands C(dconf dump
    /path/to/dir/) or C(dconf read /path/to/key).
version_added: "2.4"
options:
  key:
    required: true
    description:
      - A dconf key to modify or read from the dconf database.
  value:
    required: false
    description:
      - Value to set for the specified dconf key. Value should be specified in
        GVariant format. Due to complexity of this format, it is best to have a
        look at existing values in the dconf database. Required for
        C(state=present).
  state:
    required: false
    default: present
    choices:
      - read
      - present
      - absent
    description:
      - The action to take upon the key/value.
"""

RETURN = """
value:
    description: value associated with the requested key
    returned: success, state was "read"
    type: string
    sample: "'Default'"
"""

EXAMPLES = """
- name: Configure available keyboard layouts in Gnome
  dconf:
    key: "/org/gnome/libgnomekbd/keyboard/layouts"
    value: "['us', 'se']"
    state: present

- name: Read currently available keyboard layouts in Gnome
  dconf:
    key: "/org/gnome/libgnomekbd/keyboard/layouts"
    state: read

- name: Reset the available keyboard layouts in Gnome
  dconf:
    key: "/org/gnome/libgnomekbd/keyboard/layouts"
    state: absent

- name: Disable desktop effects in Cinnamon
  dconf:
    key: "/org/cinnamon/desktop-effects"
    value: "false"
    state: present
"""


from ansible.module_utils.basic import AnsibleModule


class DconfPreference(object):

    def __init__(self, module, check_mode=False):
        """
        Initialises instance of the class.

        :param module: Ansible module instance used to signal failures and run commands.
        :type module: AnsibleModule

        :param check_mode: Specify whether to only check if a change should be made or if to actually make a change.
        :type check_mode: bool
        """

        self.module = module
        self.check_mode = check_mode

    def read(self, key):
        """
        Retrieves current value associated with the dconf key.

        If an error occurs, a call will be made to AnsibleModule.fail_json.

        :returns: string -- Value assigned to the provided key. If the value is not set for specified key, returns None.
        """

        command = ["dconf", "read", key]

        rc, out, err = self.module.run_command(command)

        if rc != 0:
            self.module.fail_json(msg='dconf failed while reading the value with error: %s' % err)

        if out == '':
            value = None
        else:
            value = out.rstrip('\n')

        return value

    def write(self, key, value):
        """
        Writes the value for specified key.

        If an error occurs, a call will be made to AnsibleModule.fail_json.

        :param key: dconf key for which the value should be set. Should be a full path.
        :type key: str

        :param value: Value to set for the specified dconf key. Should be specified in GVariant format.
        :type value: str

        :returns: bool -- True if a change was made, False if no change was required.
        """

        # If no change is needed (or won't be done due to check_mode), notify
        # caller straight away.
        if value == self.read(key):
            return False
        elif self.check_mode:
            return True

        # Set-up command to run.
        command = ["dconf", "write", key, value]

        # Run the command and fetch standard return code, stdout, and stderr.
        rc, out, err = self.module.run_command(command)

        if rc != 0:
            self.module.fail_json(msg='dconf failed while write the value with error: %s' % err)

        # Value was changed.
        return True

    def reset(self, key):
        """
        Rests value for the specified key (removes it from user configuration).

        If an error occurs, a call will be made to AnsibleModule.fail_json.

        :param key: dconf key to reset. Should be a full path.
        :type key: str

        :returns: bool -- True if a change was made, False if no change was required.
        """

        # Read the current value first.
        current_value = self.read(key)

        # No change was needed, key is not set at all, or just notify user if we
        # are in check mode.
        if current_value is None:
            return False
        elif self.check_mode:
            return True

        # Set-up command to run.
        command = ["dconf", "reset", key]

        # Run the command and fetch standard return code, stdout, and stderr.
        rc, out, err = self.module.run_command(command)

        if rc != 0:
            self.module.fail_json(msg='dconf failed while reseting the value with error: %s' % err)

        # Value was changed.
        return True


def main():
    # Setup the Ansible module
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent', 'read']),
            key=dict(required=True, type='str'),
            value=dict(required=False, default=None, type='str'),
        ),
        supports_check_mode=True
    )

    # If present state was specified, value must be provided.
    if module.params['state'] == 'present' and module.params['value'] is None:
        module.fail_json(msg='State "present" requires "value" to be set.')

    # Create wrapper instance.
    dconf = DconfPreference(module, module.check_mode)

    # Process based on different states.
    if module.params['state'] == 'read':
        value = dconf.read(module.params['key'])
        module.exit_json(changed=False, value=value)
    elif module.params['state'] == 'present':
        changed = dconf.write(module.params['key'], module.params['value'])
        module.exit_json(changed=changed)
    elif module.params['state'] == 'absent':
        changed = dconf.reset(module.params['key'])
        module.exit_json(changed=changed)

if __name__ == '__main__':
    main()
