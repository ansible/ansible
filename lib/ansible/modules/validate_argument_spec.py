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
- name: verify vars needed for this task file are present when included
  verify_argument_spec:
        argument_spec: '{{required_data}}'
  vars:
    required_data:
        description: this is basically an inline arg spec
        options:
            stuff
                description: stuff
            type: str
            choices: ['who', 'knows', 'what']
   ...

- name: verify vars needed for this task file are present when included, with spec from a file
  verify_argument_spec:
        argument_spec: "{{lookup('file', 'myargspec.yml'}}"
   ...

- name: verify vars needed for next include and not from inside it, also with params i'll only define there
  block:
    - verify_argument_spec:
        argument_spec: "{{lookup('file', 'myargspec.yml'}}"
        provided_arguments:
            stuff: that is not in play at this point
            but: "that i can define on the include itself, like in it's `vars:` keyword"

    - name: the include itself
      vars:
        stuff: realvalue
        but: nobuts!
    ...
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
