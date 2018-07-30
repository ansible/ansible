#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2018 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: validate_arg_spec
short_description: Validate Arg Specs
description:
     - This module validate args specs
version_added: "2.8"
options:
  argument_spec:
    description:
        - A dictionary like AnsibleModule argument_spec
    required: true
  provided_arguments:
    description:
        - A dictionary of the arguments that will be validated according to argument_spec
author:
    - "Ansible Core Team"
    - "Adrian Likins"
'''

EXAMPLES = '''
'''

RETURN = '''
argument_errors:
    description: A list of arg validation errors
    returned: failure
    type: list
    sample:
        - "parameters are mutually exclusive: bust_some_stuff, tidy_expected"
        - "value of things_i_need must be one of: this paddle game, the astray, this remote control, the chair, got: my dog"
        - "value of secret_ballot must be one of: secret_choice1, secret_choice2, got: ********"
argument_spec_data:
    description: A dict of the data from the 'argument_spec' arg
    returned: failure
    type: dict
    sample:
        argument_spec:
            some_arg:
                required: true
                default: 37
                type: "int"
            secret_ballot:
                required: false
                choices:
                    - secret_choice1
                    - secret_choice2
                type: "str"
        required_together:
            - ["peanut_butter", "jelly"]
validate_args_context:
    description: A dict of info about where validate_args_spec was used
    type: dict
    returned: success, failure
    sample:
        name: my_role
        type: role
        path: /home/user/roles/my_role/
'''
