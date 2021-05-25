#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2021 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: validate_argument_spec
short_description: Validate role argument specs.
description:
     - This module validates role arguments with a defined argument specification.
version_added: "2.11"
options:
  argument_spec:
    description:
        - A dictionary like AnsibleModule argument_spec
    required: true
  provided_arguments:
    description:
        - A dictionary of the arguments that will be validated according to argument_spec
author:
    - Ansible Core Team
'''

EXAMPLES = r'''
'''

RETURN = r'''
argument_errors:
  description: A list of arg validation errors.
  returned: failure
  type: list
  elements: str
  sample:
    - "error message 1"
    - "error message 2"

argument_spec_data:
  description: A dict of the data from the 'argument_spec' arg.
  returned: failure
  type: dict
  sample:
    some_arg:
      type: "str"
    some_other_arg:
      type: "int"
      required: true

validate_args_context:
  description: A dict of info about where validate_args_spec was used
  type: dict
  returned: always
  sample:
    name: my_role
    type: role
    path: /home/user/roles/my_role/
    argument_spec_name: main
'''
