#!/usr/bin/python
#
# Copyright 2016, Jeremy Grant <jeremy.grant@outlook.com>
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import yaml
from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    ''' Variable Validation Methods '''

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)


        #################################
        # START OF VALIDATION METHODS ###

        # Method for validating variable value is of specified data type
        def validate_input_type(value, input_type):

            # Map data types
            bool_types = ['bool', 'boolean']
            str_types = ['str', 'string']
            list_types = ['list', 'array']
            dict_types = ['dict', 'hash']
            num_types = ['float', 'int', 'long']
            all_types = bool_types + str_types + list_types + dict_types + num_types

            # Determine Input value type
            if input_type in bool_types:
                real_type = bool
            elif input_type in str_types:
                real_type = str
            elif input_type in list_types:
                real_type = list
            elif input_type in dict_types:
                real_type = dict
            elif input_type in num_types:
                real_type = eval(input_type)
            else:
                raise AnsibleError('Unsupported input_type used - possible values are: {0}"'.format(all_types))

            # Determine actual data type using yaml.safe_load
            yaml_value = yaml.safe_dump(value)
            real_value = yaml.safe_load(yaml_value)

            # Message Formatting
            string_vars = {'value': value, 'value_type': type(real_value), 'real_type': real_type}

            # PASS if value data type matches specified data type - else FAIL
            if isinstance(real_value, real_type):
                pass_msg = ("PASS: Input value '{value}' of '{value_type}' "
                            "matches validation requirement for value to be of: '{real_type}")
                result['msg'] = pass_msg.format(**string_vars)
            else:
                fail_msg = ("FAIL: Input value '{value}' of: '{value_type}' does "
                            "not match validation requirement for value to be of: '{real_type}")
                result['msg'] = fail_msg.format(**string_vars)
                result['failed'] = True

        # Method for validating value against regular expression
        def validate_matcher(value, matcher):
            # Message Formatting
            string_vars = {'value': value, 'matcher': matcher}

            # Compile Matcher regex and determine actual data type using yaml.safe_load
            compiled_matcher = re.compile(matcher)
            yaml_value = yaml.safe_dump(value)
            real_value = yaml.safe_load(yaml_value)
            # PASS if value matches specificed regex - else FAIL
            if compiled_matcher.match(value):
                pass_msg = ("PASS: Input value '{value}' matches "
                            "validation requirement against regex: /{matcher}/")
                result['msg'] = pass_msg.format(**string_vars)
            else:
                fail_msg = ("FAIL: Input value '{value}' does not match "
                            "validation requirement against regex: /{matcher}/")
                result['msg'] = fail_msg.format(**string_vars)
                result['failed'] = True

        # Method for validating number against specified number range
        def validate_num_range(value, range_min, range_max):
            # Convert value to integer
            int_value = int(value)
            # Message Formatting
            string_vars = {'value': value, 'range_min': range_min, 'range_max': range_max}

            # PASS if number within specified range - else FAIL
            if range_min <= int_value <= range_max:
                pass_msg = ("PASS: Input value '{value}' is within bounds of Number Range "
                            "{range_min}-{range_max} for validation requirement")
                result['msg'] = pass_msg.format(**string_vars)
            else:
                fail_msg = ("FAIL: Input value '{value}' is outside bounds of Number Range "
                            "{range_min}-{range_max} for validation requirement")
                result['msg'] = fail_msg.format(**string_vars)
                result['failed'] = True

        # Method for validating values against specificed whitelist
        def validate_whitelist(value, whitelist):
            # Message Formatting
            string_vars = {'value': value, 'whitelist': whitelist}

            # PASS if value in Whitelist - else FAIL
            if value in whitelist:
                pass_msg = ("PASS: Input value '{value}' is contained within value "
                            "whitelist '{whitelist}' validation requirement")
                result['msg'] = pass_msg.format(**string_vars)
            else:
                fail_msg = ("FAIL: Input value '{value}' is not contained within value "
                           "whitelist '{whitelist}' validation requirement")
                result['msg'] = fail_msg.format(**string_vars)
                result['failed'] = True

        # Method for validating values against specificed blacklist
        def validate_blacklist(value, blacklist):
            # Message Formatting
            string_vars = {'value': value, 'blacklist': blacklist}

            # PASS if value not in blacklist - else FAIL
            if value not in blacklist:
                pass_msg = ("PASS: Input value '{value}' is not contained within value "
                           "blacklist '{blacklist}' validation requirement")
                result['msg'] = pass_msg.format(**string_vars)
            else:
                fail_msg = ("FAIL: Input value '{value}' is contained within value "
                            "blacklist'{blacklist}' validation requirement")
                result['msg'] = fail_msg.format(**string_vars)
                result['failed'] = True

        #################################
        ### END OF VALIDATION METHODS ###

        # Parse plugin args and invoke validation methods
        if 'value' not in self._task.args:
            raise AnsibleError('value arg must be provided')
        else:
            value = self._task.args['value']

        # set input_type if passed and invoke type enforcement validation
        if 'input_type' in self._task.args:
            input_type = self._task.args['input_type']
            validate_input_type(value, input_type)
        else:
            input_type = None

        # set regex matcher validation if passed
        if 'matcher' in self._task.args:
            matcher = self._task.args['matcher']
            validate_matcher(str(value), matcher)
        else:
            matcher = None

        # set integer range validation if passed to ensure variable in bounds
        if 'num_range' in self._task.args:
            num_range = self._task.args['num_range'].split('-')
            range_min = int(num_range[0])
            range_max = int(num_range[1])
            validate_num_range(value, range_min, range_max)
        else:
            num_range = None

        # set whitelist item validation if passed to ensure variable contained in list
        if 'whitelist' in self._task.args:
            whitelist = self._task.args['whitelist']
            validate_whitelist(value, whitelist)
        else:
            whitelist = None

        # set blacklist item validation if passed to ensure variable not contained in list
        if 'blacklist' in self._task.args:
            blacklist = self._task.args['blacklist']
            validate_blacklist(value, blacklist)
        else:
            blacklist = None

        # Return result object
        result['changed'] = False
        return result
