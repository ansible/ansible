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
  - "TO-DO: unit tests"
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
    default: no
    aliases:
    - array
    version_added: "2.10"
  recursive:
    description:
    - When used with state 'absent', deletes recursively.
    - If used with state 'get', returns the '--list' of properties, without values.
    type: bool
    default: no
    version_added: "2.10"
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
    is_array = None

    def __init__(self, name, module):
        self.name = name
        self.module = module
        self.channel = module.params['channel']
        self.property = module.params['property']
        self.value_type = module.params['value_type']
        self.value = module.params['value']
        self.state = module.params['state']
        self.force_array = module.params['force_array']
        self.recursive = module.params['recursive']
        self._previous_value_set = False
        self._previous_value = None

        self.cmd = "{0} --channel {1}".format(module.get_bin_path('xfconf-query', True), shlex_quote(self.channel))
        if self.property:
            self.cmd = "{0} --property {1}".format(self.cmd, shlex_quote(self.property))

        self.method_map = dict(zip((self.SET, self.GET, self.RESET),
                                   (self.set, self.get, self.reset)))

        # @TODO This will not work with non-English translations, but xfconf-query does not return
        #       distinct result codes for distinct outcomes.
        self.does_not = 'Property "{0}" does not exist on channel "{1}".'.format(self.property, self.channel)

        def run(cmd):
            return module.run_command(cmd, check_rc=False)
        self._run = run

    @property
    def previous_value(self):
        if not self._previous_value_set:
            self._previous_value, _ = self.get()
        return self._previous_value

    def _execute_xfconf_query(self, args=None, check_mode_aware=True, **kwargs):
        try:
            cmd = self.cmd
            if args:
                cmd = "{0} {1}".format(cmd, args)

            self.module.debug("Running cmd={0}".format(cmd))
            if check_mode_aware and self.module.check_mode:
                return 'Would have executed: {}'.format(cmd)

            rc, out, err = self._run(cmd)
            if err.rstrip() == self.does_not:
                return None
            if rc or len(err):
                raise XfConfException('xfconf-query failed with error (rc={0}): {1}'.format(rc, err))

            return out.rstrip()

        except OSError as exception:
            XfConfException('xfconf-query failed with exception: {0}'.format(exception))

    def get_prop(self):
        previous_value = self._execute_xfconf_query()
        if not previous_value:
            return

        if "Value is an array with" in previous_value:
            if " 0 items:" in previous_value:
                return []
            previous_value = previous_value.split("\n")
            previous_value.pop(0)
            previous_value.pop(0)

        return previous_value

    def get_list(self):
        value = self._execute_xfconf_query("--list")
        return value.split('\n')

    def get(self, check_mode_aware=True, **kwargs):
        if self.recursive:
            return self.get_list(), False
        else:
            return self.get_prop(), False

    def reset(self, check_mode_aware=True, **kwargs):
        if not self.previous_value:
            return None, False

        rec = "--recursive" if self.recursive else ""

        self._execute_xfconf_query("--reset {}".format(rec), check_mode_aware=check_mode_aware)
        return None, True

    @staticmethod
    def _fix_bool(value):
        if value.lower() in ("true", "false"):
            value = value.lower()
        return value

    def _make_value_args(self, value, value_type):
        if value_type == 'bool':
            value = self._fix_bool(value)
        return " --type '{1}' --set '{0}'".format(shlex_quote(value), shlex_quote(value_type))

    def set(self, check_mode_aware=True, **kwargs):
        if self.previous_value and set(self.previous_value) == set(self.value):
            return self.value, False

        args = "--create"
        if self.is_array:
            args += " --force-array"
            for v in zip(self.value, self.value_type):
                args += self._make_value_args(*v)
        else:
            args += self._make_value_args(self.value, self.value_type)
        self._execute_xfconf_query(args, check_mode_aware=check_mode_aware)
        return self.value, True

    def call(self, state):
        return self.method_map[state](check_mode_aware=self.module.check_mode)

    def sanitize(self):
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

    def make_facts(self, channel=None, property=None, value_type=None,
                   value=None, state=None, force_array=None, recursive=None):
        return {
            self.name: dict(
                channel=channel if channel else self.channel,
                property=property if property else self.property,
                value_type=value_type if value_type else self.value_type,
                value=value if value else self.value,
                state=state if state else self.state,
                force_array=force_array if force_array else self.force_array,
                recursive=recursive if recursive else self.recursive,
                previous_value=self.previous_value,
            )
        }


def main():
    module_name = "xfconf"
    # Setup the Ansible module
    module = AnsibleModule(
        argument_spec=dict(
            channel=dict(required=True, type='str'),
            property=dict(required=False, type='str'),
            value_type=dict(required=False, type='list'),
            value=dict(required=False, type='list'),
            state=dict(default=XfConfProperty.SET,
                       choices=XfConfProperty.VALID_STATES,
                       type='str'),
            force_array=dict(default=False, type='bool', aliases=['array']),
            recursive=dict(default=False, type=bool),
        ),
        supports_check_mode=True
    )

    state = module.params['state']

    if state == XfConfProperty.SET:
        if not module.params.get('value'):
            module.fail_json(msg='State {0} requires "value" to be set'.format(state))
        elif not module.params.get('value_type'):
            module.fail_json(msg='State {0} requires "value_type" to be set'.format(state))

    # In case we are listing all properties in a channel
    if not module.params.get('property') and (state != XfConfProperty.GET or not module.params.get('recursive')):
        module.fail_json(msg='Property name must be set unless doing a recursive get')

    try:
        # Create a Xfconf preference
        xfconf = XfConfProperty(module_name, module)
        xfconf.sanitize()
        new_value, changed = xfconf.call(state)

        module.exit_json(changed=changed, ansible_facts=xfconf.make_facts(value=new_value))

    except Exception as e:
        module.fail_json(msg="Failed with exception: {0}".format(e))


if __name__ == '__main__':
    main()
