#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2016, Kenneth D. Evensen <kevensen@redhat.com>
# (c) 2017, Abhijeet Kasurde <akasurde@redhat.com>
# (c) 2017, Branko Majic <branko@majic.rs>
#
# This file is part of Ansible (sort of)
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
module: gconftool2
author:
    - "Kenneth D. Evensen (@kevensen)"
    - "Abhijeet Kasurde <akasurde@redhat.com>"
    - "Branko Majic (azaghal)"
short_description: Edit GNOME Configurations
description:
  - This module allows for the manipulation of GNOME 2 Configuration via
    gconftool-2.  Please see the gconftool-2(1) man pages for more details.
version_added: "2.3"
options:
  key:
    required: true
    description:
      - A GConf preference key is an element in the GConf repository
        that corresponds to an application preference. See man gconftool-2(1)
  value:
    required: false
    description:
      - Preference keys typically have simple values such as strings,
        integers, or lists of strings and integers. This is ignored if the state
        is "get". See man gconftool-2(1)
  value_type:
    required: false
    choices:
      - int
      - bool
      - float
      - string
    description:
      - The type of value being set. This is ignored if the state is "get".
  state:
    required: false
    default: present
    choices:
      - get
      - present
      - absent
    description:
      - The action to take upon the key/value.
  config_source:
    required: false
    description:
      - Specify a configuration source to use rather than the default
        path. Specifying configuration source will also result in direct access
        (via C(--direct) option), bypassing the server. See man gconftool-2(1)
        for details.
"""

EXAMPLES = """
- name: Change the widget font to "Serif 12"
  gconftool2:
    key: "/desktop/gnome/interface/font_name"
    state: present
    value_type: "string"
    value: "Serif 12"

- name: Read the value of widget font
  gconftool2:
    key: "/desktop/gnome/interface/font_name"
    state: get
  register: fontname

- name: Output the value of widget font
  debug: var=fontname.value

- name: Unset the widget font setting
  gconftool2:
    key: "/desktop/gnome/interface/font_name"
    state: absent
"""

RETURN = '''
value:
    description: value associated with the requested preference key
    returned: success, state was "get"
    type: string
    sample: "Serif 12"
'''

from ansible.module_utils.basic import AnsibleModule


class GConfTool2(object):
    """
    Small wrapper class around the gconftool-2 binary that can be used for
    manipulating a single preference in GConf repository.
    """

    def __init__(self, module, config_source=None, check_mode=False):
        """
        Initialises instance of the class.

        :param module: Ansible module instance used to signal failures and run commands.
        :type module: AnsibleModule

        :param config_source: Alternative configuration source to use.
        :type config_source: str

        :param check_mode: Specify whether to only check if a change should be made or if to actually make a change.
        :type check_mode: bool
        """

        self.module = module
        self.base_command = [self.module.get_bin_path("gconftool-2", required=True)]
        self.check_mode = check_mode

        # This should help avoiding localisation issues when checking for errors
        # based on stderr.
        self.module.run_command_environ_update = {'LANG': 'C'}

        if config_source:
            self.base_command += ["--direct", "--config-source", config_source]

    def get(self, key):
        """
        Retrieves current value associated with the key.

        If an error occurs, a call will be made to AnsibleModule.fail_json.

        :returns: string -- Value assigned to the provided key. If the key does not exist (i.e. no value is assigned), returns None.
        """

        # Set-up command to run.
        command = list(self.base_command)
        command += ["--get", key]

        # Run the command and fetch standard return code, stdout, and stderr.
        rc, out, err = self.module.run_command(command)

        # Since the tool does not produce proper error return codes, we need to
        # process the stderr output to determine if there are issues.
        if len(err) > 0 and not err.startswith('No value set'):
            self.module.fail_json(msg='gconftool-2 failed while reading the value from GConf with error: %s' % (str(err)))

        # Standard output will contain the value, or message that no value is
        # set at all.
        if err.startswith('No value set'):
            value = None
        else:
            value = out.rstrip("\n")

        return value

    def set(self, key, value_type, value):
        """
        Sets the value for specified key.

        If an error occurs, a call will be made to AnsibleModule.fail_json.

        :param key: GConf preference key to set. Should be a full path.
        :type key: str

        :param value_type: GConf value type. See gconftool-2 for supported values.
        :type value_type: str

        :param value: Value to set for the specified GConf preference key.
        :type value: str

        :returns: bool -- True if a change was made, False if no change was required.
        """

        # If no change is needed (or won't be done due to check_mode), notify
        # caller straight away.
        if value == self.get(key):
            return False
        elif self.check_mode:
            return True

        # Set-up command to run.
        command = list(self.base_command)
        command += ["--set", "--type", value_type, key, value]

        # Run the command and fetch standard return code, stdout, and stderr.
        rc, out, err = self.module.run_command(command)

        # Since the tool does not produce proper error return codes, we need to
        # process the stderr output to determine if there are issues.
        if len(err) > 0:
            self.module.fail_json(msg='gconftool-2 failed while setting the value with error: %s' % (str(err)))

        # Value was changed.
        return True

    def unset(self, key):
        """
        Unsets the specified key (removes it from user configuration).

        If an error occurs, a call will be made to AnsibleModule.fail_json.

        .. note::

          If GConf has global value for the specified key, unsetting will merely
          wipe-out user's local configuration changes. Unfortunately, it is not
          possible to distinguish removal of user value if global value is set
          and identical to user's.

        :param key: GConf preference key to unset. Should be a full path.
        :type key: str

        :returns: bool -- True if a change was made, False if no change was required.
        """

        # Read the current value first.
        current_value = self.get(key)

        # No change was needed, key is not set at all, or just notify user if we
        # are in check mode.
        if current_value is None:
            return False
        elif self.check_mode:
            return True

        # Set-up command to run.
        command = list(self.base_command)
        command += ["--unset", key]

        # Run the command and fetch standard return code, stdout, and stderr.
        rc, out, err = self.module.run_command(command)

        # Since the tool does not produce proper error return codes, we need to
        # process the stderr output to determine if there are issues.
        if len(err) > 0:
            self.ansible.fail_json(msg='gconftool-2 failed while setting the value with error: %s' % (str(err)))

        # Try to detect if there was any change in values. This does not detect
        # set 100% reliably if user's own value was identical to global one.
        if current_value == self.get(key):
            return False

        # Value was changed.
        return True


def main():
    # Setup the Ansible module
    module = AnsibleModule(
        argument_spec=dict(
            key=dict(required=True, default=None, type='str'),
            value_type=dict(required=False,
                            choices=['int', 'bool', 'float', 'string'],
                            type='str'),
            value=dict(required=False, default=None, type='str'),
            state=dict(default='present',
                       choices=['present', 'get', 'absent'],
                       type='str'),
            config_source=dict(required=False, default=None, type='str')
            ),
        supports_check_mode=True,
        required_if = [('state', 'present', ('value', 'value_type'))]
    )

    # Create wrapper instance.
    gconftool2 = GConfTool2(module, module.params['config_source'], module.check_mode)

    # Process based on different states.
    if module.params['state'] == 'get':
        value = gconftool2.get(module.params['key'])
        module.exit_json(changed=False, value=value)
    elif module.params['state'] == 'present':
        changed = gconftool2.set(module.params['key'], module.params['value_type'], module.params['value'])
        module.exit_json(changed=changed)
    elif module.params['state'] == 'absent':
        changed = gconftool2.unset(module.params['key'])
        module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
