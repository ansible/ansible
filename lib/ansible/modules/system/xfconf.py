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
      is "get". See man xfconf-query(1)
  value_type:
    description:
    - The type of value being set. This is ignored if the state is "get".
    choices: [ int, bool, float, string ]
  state:
    description:
    - The action to take upon the property/value.
    choices: [ get, present, absent ]
    default: "present"
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
...
'''

import pipes
import sys

from ansible.module_utils.basic import AnsibleModule


class XfconfPreference(object):
    def __init__(self, module, channel, property, value_type, value):
        self.module = module
        self.channel = channel
        self.property = property
        self.value_type = value_type
        self.value = value

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
                cmd += " --type {0} --create --set {1}".format(pipes.quote(self.value_type),
                                                               pipes.quote(self.value))
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
            value_type=dict(required=False,
                            choices=['int', 'bool', 'float', 'string'],
                            type='str'),
            value=dict(required=False, default=None, type='str'),
            state=dict(default='present',
                       choices=['present', 'get', 'absent'],
                       type='str')
        ),
        supports_check_mode=True
    )

    state_values = {"present": "set", "absent": "unset", "get": "get"}

    # Assign module values to dictionary values
    channel = module.params['channel']
    property = module.params['property']
    value_type = module.params['value_type']
    if module.params['value'].lower() == "true":
        value = "true"
    elif module.params['value'] == "false":
        value = "false"
    else:
        value = module.params['value']

    state = state_values[module.params['state']]

    # Initialize some variables for later
    change = False
    new_value = ''

    if state != "get":
        if value is None or value == "":
            module.fail_json(msg='State %s requires "value" to be set'
                             % str(state))
        elif value_type is None or value_type == "":
            module.fail_json(msg='State %s requires "value_type" to be set'
                             % str(state))

    # Create a Xfconf preference
    xfconf = XfconfPreference(module,
                              channel,
                              property,
                              value_type,
                              value)
    # Now we get the current value, if not found don't fail
    dummy, current_value = xfconf.call("get", fail_onerr=False)

    # Check if the current value equals the value we want to set.  If not, make
    # a change
    if current_value != value:
        # If check mode, we know a change would have occurred.
        if module.check_mode:
            # So we will set the change to True
            change = True
            # And set the new_value to the value that would have been set
            new_value = value
        # If not check mode make the change.
        else:
            change, new_value = xfconf.call(state)
    # If the value we want to set is the same as the current_value, we will
    # set the new_value to the current_value for reporting
    else:
        new_value = current_value

    facts = dict(xfconf={'changed': change,
                         'channel': channel,
                         'property': property,
                         'value_type': value_type,
                         'new_value': new_value,
                         'previous_value': current_value,
                         'playbook_value': module.params['value']})

    module.exit_json(changed=change, ansible_facts=facts)


if __name__ == '__main__':
    main()
