#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, Joseph Benden <joe@benden.us>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: xfconf
author:
    - "Joseph Benden (@jbenden)"
short_description: Edit XFCE4 Configurations
description:
  - This module allows for the manipulation of Xfce 4 Configuration via
    xfconf-query.  Please see the xfconf-query(1) man pages for more details.
version_added: "2.8"
options:
  channel:
    description:
    - A Xfconf preference channel is a top-level tree key, inside of the
      Xfconf repository that corresponds to the location for which all
      application properties/keys are stored. See man xfconf-query(1)
    required: yes
  property:
    description:
    - A Xfce preference key is an element in the Xfconf repository
      that corresponds to an application preference. See man xfconf-query(1)
    required: yes
  value:
    description:
    - Preference properties typically have simple values such as strings,
      integers, or lists of strings and integers. This is ignored if the state
      is "get". For array mode, use a list of values. See man xfconf-query(1)
  value_type:
    description:
    - The type of value being set. This is ignored if the state is "get".
      For array mode, use a list of types.
  state:
    description:
    - The action to take upon the property/value.
    choices: [ get, present, absent ]
    default: "present"
  force_array:
    description:
    - Force array even if only one element
    type: bool
    default: 'no'
"""

EXAMPLES = """
- name: Change the DPI to "192"
  xfconf:
    channel: "xsettings"
    property: "/Xft/DPI"
    value_type: "int"
    value: "192"
  become: True
  become_user: johnsmith
"""

RETURN = '''
  channel:
    description: The channel specified in the module parameters
    returned: success
    type: str
    sample: "xsettings"
  property:
    description: The property specified in the module parameters
    returned: success
    type: str
    sample: "/Xft/DPI"
  value_type:
    description: The type of the value that was changed
    returned: success
    type: str
    sample: "int"
  value:
    description: The value of the preference key after executing the module
    returned: success
    type: str
    sample: "192"
'''

import pipes
import sys

from ansible.module_utils.basic import AnsibleModule


class XfconfPreference(object):
    def __init__(self, module, channel, property, value_types, values, array):
        self.module = module
        self.channel = channel
        self.property = property
        self.value_types = value_types
        self.values = values
        self.array = array

    def call(self, call_type, fail_onerr=True):
        """ Helper function to perform xfconf-query operations """
        changed = False
        out = ''

        # Execute the call
        cmd = "{0} --channel {1} --property {2}".format(self.module.get_bin_path('xfconf-query', True),
                                                        pipes.quote(self.channel),
                                                        pipes.quote(self.property))
        try:
            if call_type == 'set':
                if self.array:
                    cmd += " --force-array"
                for i in range(len(self.values)):
                    cmd += " --type {0} --create --set {1}".format(pipes.quote(self.value_types[i]),
                                                                   pipes.quote(self.values[i]))
            elif call_type == 'unset':
                cmd += " --reset"

            # Start external command
            rc, out, err = self.module.run_command(cmd, check_rc=False)

            if rc != 0 or len(err) > 0:
                if fail_onerr:
                    self.module.fail_json(msg='xfconf-query failed with error: %s' % (str(err)))
            else:
                changed = True

        except OSError as exception:
            self.module.fail_json(msg='xfconf-query failed with exception: %s' % exception)
        return changed, out.rstrip()


def main():
    # Setup the Ansible module
    module = AnsibleModule(
        argument_spec=dict(
            channel=dict(required=True, type='str'),
            property=dict(required=True, type='str'),
            value_type=dict(required=False, type='list'),
            value=dict(required=False, type='list'),
            state=dict(default='present',
                       choices=['present', 'get', 'absent'],
                       type='str'),
            force_array=dict(default=False, type='bool')
        ),
        supports_check_mode=True
    )

    state_values = {"present": "set", "absent": "unset", "get": "get"}

    # Assign module values to dictionary values
    channel = module.params['channel']
    property = module.params['property']
    values = module.params['value']
    value_types = module.params['value_type']
    if values is not None and value_types is not None:
        if len(values) != len(value_types):
            module.fail_json(msg='Same number of "value" and "value_type" needed')
        for i in range(len(values)):
            if values[i].lower() == "true" or values[i].lower() == "false":
                values[i] = values[i].lower()
        for value_type in value_types:
            if value_type not in ['int', 'bool', 'float', 'string']:
                module.fail_json(msg='value_type %s is not supported'
                                 % str(value_type))
    else:
        values = value_types = None
    array = module.params['force_array'] or values is not None and len(values) > 1

    state = state_values[module.params['state']]

    # Initialize some variables for later
    change = False
    new_values = ''

    if state != "get":
        if values is None or values[0] == "":
            module.fail_json(msg='State %s requires "value" to be set'
                             % str(state))
        elif value_types is None or value_types[0] == "":
            module.fail_json(msg='State %s requires "value_type" to be set'
                             % str(state))

    # Create a Xfconf preference
    xfconf = XfconfPreference(module,
                              channel,
                              property,
                              value_types,
                              values,
                              array)
    # Now we get the current values, if not found don't fail
    dummy, current_values = xfconf.call("get", fail_onerr=False)

    # Convert current_values to array format
    if "Value is an array with" in current_values:
        current_values = current_values.split("\n")
        current_values.pop(0)
        current_values.pop(0)
    else:
        current_values = [current_values]

    # Check if the current values equals the values we want to set.  If not,
    # make a change
    if current_values != values and state != "get":
        # If check mode, we know a change would have occurred.
        if module.check_mode:
            # So we will set the change to True
            change = True
            # And set the new_values to the values that would have been set
            new_values = values
        # If not check mode make the change.
        else:
            change, new_values = xfconf.call(state)
    # If the value we want to set is the same as the current_values, we will
    # set the new_values to the current_values for reporting
    else:
        new_values = current_values

    facts = dict(xfconf={'changed': change,
                         'channel': channel,
                         'property': property,
                         'value_type': value_types,
                         'new_value': new_values,
                         'previous_value': current_values,
                         'playbook_value': values})

    module.exit_json(changed=change, ansible_facts=facts)


if __name__ == '__main__':
    main()
