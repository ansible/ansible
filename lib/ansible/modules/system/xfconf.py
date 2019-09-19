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
  - This module allows for the manipulation of Xfce 4 Configuration via xfconf-query.
  - Please see the xfconf-query(1) man pages for more details.
  - "TO-DO: unit tests, list state to retrieve properties, recursive reset."
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
    aliases:
    - array
seealso:
  - name: XFCE documentation on xfconf-query
    description: Manual page for the command
    link: https://docs.xfce.org/xfce/xfconf/xfconf-query
"""

EXAMPLES = """
- name: Change the DPI to "192"
  xfconf:
    channel: "xsettings"
    property: "/Xft/DPI"
    value_type: "int"
    value: "192"
- name: Set workspace names (4)
  xfconf:
    channel: xfwm4
    property: /general/workspace_names
    value_type: string
    value: ['Main', 'Work1', 'Work2', 'Tmp']
- name: Set workspace names (1)
  xfconf:
    channel: xfwm4
    property: /general/workspace_names
    value_type: string
    value: ['Main']
    force_array: yes
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
  previous_value:
    description: The value of the preference key before executing the module (None for "get" state)
    returned: success
    type: str
    sample: "96"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves import shlex_quote


class XfConfException(Exception):
    pass


class XfConfProperty(object):
    SET = "present"
    GET = "get"
    RESET = "absent"
    VALID_STATES = (SET, GET, RESET)
    VALID_VALUE_TYPES = ('int', 'bool', 'float', 'string')
    previous_value = None
    is_array = None

    def __init__(self, module):
        self.module = module
        self.channel = module.params['channel']
        self.property = module.params['property']
        self.value_type = module.params['value_type']
        self.value = module.params['value']
        self.force_array = module.params['force_array']

        self.cmd = "{0} --channel {1} --property {2}".format(
            module.get_bin_path('xfconf-query', True),
            shlex_quote(self.channel),
            shlex_quote(self.property)
        )
        self.method_map = dict(zip((self.SET, self.GET, self.RESET),
                                   (self.set, self.get, self.reset)))

        # @TODO This will not work with non-English translations, but xfconf-query does not return
        #       distinct result codes for distinct outcomes.
        self.does_not = 'Property "{0}" does not exist on channel "{1}".'.format(self.property, self.channel)

        def run(cmd):
            return module.run_command(cmd, check_rc=False)
        self._run = run

    def _execute_xfconf_query(self, args=None):
        try:
            cmd = self.cmd
            if args:
                cmd = "{0} {1}".format(cmd, args)

            self.module.debug("Running cmd={0}".format(cmd))
            rc, out, err = self._run(cmd)
            if err.rstrip() == self.does_not:
                return None
            if rc or len(err):
                raise XfConfException('xfconf-query failed with error (rc={0}): {1}'.format(rc, err))

            return out.rstrip()

        except OSError as exception:
            XfConfException('xfconf-query failed with exception: {0}'.format(exception))

    def get(self):
        previous_value = self._execute_xfconf_query()
        if previous_value is None:
            return

        if "Value is an array with" in previous_value:
            previous_value = previous_value.split("\n")
            previous_value.pop(0)
            previous_value.pop(0)

        return previous_value

    def reset(self):
        self._execute_xfconf_query("--reset")
        return None

    @staticmethod
    def _fix_bool(value):
        if value.lower() in ("true", "false"):
            value = value.lower()
        return value

    def _make_value_args(self, value, value_type):
        if value_type == 'bool':
            value = self._fix_bool(value)
        return " --type '{1}' --set '{0}'".format(shlex_quote(value), shlex_quote(value_type))

    def set(self):
        args = "--create"
        if self.is_array:
            args += " --force-array"
            for v in zip(self.value, self.value_type):
                args += self._make_value_args(*v)
        else:
            args += self._make_value_args(self.value, self.value_type)
        self._execute_xfconf_query(args)
        return self.value

    def call(self, state):
        return self.method_map[state]()

    def sanitize(self):
        self.previous_value = self.get()

        if self.value is None and self.value_type is None:
            return
        if (self.value is None) ^ (self.value_type is None):
            raise XfConfException('Must set both "value" and "value_type"')

        # Check for invalid value types
        for v in self.value_type:
            if v not in self.VALID_VALUE_TYPES:
                raise XfConfException('value_type {0} is not supported'.format(v))

        # stringify all values - in the CLI they will all be happy strings anyway
        # and by doing this here the rest of the code can be agnostic to it
        self.value = [str(v) for v in self.value]

        values_len = len(self.value)
        types_len = len(self.value_type)

        if types_len == 1:
            # use one single type for the entire list
            self.value_type = self.value_type * values_len
        elif types_len != values_len:
            # or complain if lists' lengths are different
            raise XfConfException('Same number of "value" and "value_type" needed')

        # fix boolean values
        self.value = [self._fix_bool(v[0]) if v[1] == 'bool' else v[0] for v in zip(self.value, self.value_type)]

        # calculates if it is an array
        self.is_array = self.force_array or isinstance(self.previous_value, list) or values_len > 1
        if not self.is_array:
            self.value = self.value[0]
            self.value_type = self.value_type[0]


def main():
    module_name = "xfconf"
    # Setup the Ansible module
    module = AnsibleModule(
        argument_spec=dict(
            channel=dict(required=True, type='str'),
            property=dict(required=True, type='str'),
            value_type=dict(required=False, type='list'),
            value=dict(required=False, type='list'),
            state=dict(default=XfConfProperty.SET,
                       choices=XfConfProperty.VALID_STATES,
                       type='str'),
            force_array=dict(default=False, type='bool', aliases=['array']),
        ),
        supports_check_mode=True
    )

    state = module.params['state']

    if state == XfConfProperty.SET:
        if not module.params.get('value'):
            module.fail_json(msg='State {0} requires "value" to be set'.format(state))
        elif not module.params.get('value_type'):
            module.fail_json(msg='State {0} requires "value_type" to be set'.format(state))

    try:
        # Create a Xfconf preference
        xfconf = XfConfProperty(module)
        xfconf.sanitize()

        previous_value = xfconf.get()
        facts = {
            module_name: dict(
                channel=xfconf.channel,
                property=xfconf.property,
                value_type=xfconf.value_type,
                value=previous_value,)}

        if state == XfConfProperty.GET \
                or (previous_value is not None
                    and (state, set(previous_value)) == (XfConfProperty.SET, set(xfconf.value))):
            module.exit_json(changed=False, ansible_facts=facts)
            return

        # If check mode, we know a change would have occurred.
        if module.check_mode:
            new_value = xfconf.value
        else:
            new_value = xfconf.call(state)

        facts[module_name].update(value=new_value, previous_value=previous_value)
        module.exit_json(changed=True, ansible_facts=facts)

    except Exception as e:
        module.fail_json(msg="Failed with exception: {0}".format(e))


if __name__ == '__main__':
    main()
