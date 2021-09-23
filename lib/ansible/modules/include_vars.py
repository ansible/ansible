#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
author: Allen Sanabria (@linuxdynasty)
module: include_vars
short_description: Load variables from files, dynamically within a task
description:
  - Loads YAML/JSON variables dynamically from a file or directory, recursively, during task runtime.
  - If loading a directory, the files are sorted alphabetically before being loaded.
  - This module is also supported for Windows targets.
  - To assign included variables to a different host than C(inventory_hostname),
    use C(delegate_to) and set C(delegate_facts=yes).
version_added: "1.4"
options:
  file:
    description:
      - The file name from which variables should be loaded.
      - If the path is relative, it will look for the file in vars/ subdirectory of a role or relative to playbook.
    type: path
    version_added: "2.2"
  dir:
    description:
      - The directory name from which the variables should be loaded.
      - If the path is relative and the task is inside a role, it will look inside the role's vars/ subdirectory.
      - If the path is relative and not inside a role, it will be parsed relative to the playbook.
    type: path
    version_added: "2.2"
  name:
    description:
      - The name of a variable into which assign the included vars.
      - If omitted (null) they will be made top level vars.
    type: str
    version_added: "2.2"
  depth:
    description:
      - When using C(dir), this module will, by default, recursively go through each sub directory and load up the
        variables. By explicitly setting the depth, this module will only go as deep as the depth.
    type: int
    default: 0
    version_added: "2.2"
  files_matching:
    description:
      - Limit the files that are loaded within any directory to this regular expression.
    type: str
    version_added: "2.2"
  ignore_files:
    description:
      - List of file names to ignore.
    type: list
    version_added: "2.2"
  extensions:
    description:
      - List of file extensions to read when using C(dir).
    type: list
    default: [ json, yaml, yml ]
    version_added: "2.3"
  ignore_unknown_extensions:
    description:
      - Ignore unknown file extensions within the directory.
      - This allows users to specify a directory containing vars files that are intermingled with non-vars files extension types
        (e.g. a directory with a README in it and vars files).
    type: bool
    default: no
    version_added: "2.7"
  hash_behaviour:
    description:
      - If set to C(merge), merges existing hash variables instead of overwriting them.
      - If omitted C(null), the behavior falls back to the global I(hash_behaviour) configuration.
    default: null
    type: str
    choices: ["replace", "merge"]
    version_added: "2.12"
  free-form:
    description:
      - This module allows you to specify the 'file' option directly without any other options.
      - There is no 'free-form' option, this is just an indicator, see example below.
extends_documentation_fragment:
    - action_common_attributes
    - action_common_attributes.conn
    - action_common_attributes.flow
    - action_core
attributes:
    action:
        details: While the action plugin does do some of the work it relies on the core engine to actually create the variables, that part cannot be overriden
        support: partial
    bypass_host_loop:
        support: none
    bypass_task_loop:
        support: none
    check_mode:
        support: full
    delegation:
        details:
            - while variable assignment can be delegated to a different host the execution context is always the current invenotory_hostname
            - connection variables, if set at all, would reflect the host it would target, even if we are not connecting at all in this case
        support: partial
    diff_mode:
        support: none
    core:
        details: While parts of this action are implemented in core, other parts are still available as normal plugins and can be partially overridden
        support: partial
seealso:
- module: ansible.builtin.set_fact
- ref: playbooks_delegation
  description: More information related to task delegation.
'''

EXAMPLES = r'''
- name: Include vars of stuff.yaml into the 'stuff' variable (2.2).
  include_vars:
    file: stuff.yaml
    name: stuff

- name: Conditionally decide to load in variables into 'plans' when x is 0, otherwise do not. (2.2)
  include_vars:
    file: contingency_plan.yaml
    name: plans
  when: x == 0

- name: Load a variable file based on the OS type, or a default if not found. Using free-form to specify the file.
  include_vars: "{{ lookup('first_found', params) }}"
  vars:
    params:
      files:
        - '{{ansible_distribution}}.yaml'
        - '{{ansible_os_family}}.yaml'
        - default.yaml
      paths:
        - 'vars'

- name: Bare include (free-form)
  include_vars: myvars.yaml

- name: Include all .json and .jsn files in vars/all and all nested directories (2.3)
  include_vars:
    dir: vars/all
    extensions:
      - 'json'
      - 'jsn'

- name: Include all default extension files in vars/all and all nested directories and save the output in test. (2.2)
  include_vars:
    dir: vars/all
    name: test

- name: Include default extension files in vars/services (2.2)
  include_vars:
    dir: vars/services
    depth: 1

- name: Include only files matching bastion.yaml (2.2)
  include_vars:
    dir: vars
    files_matching: bastion.yaml

- name: Include all .yaml files except bastion.yaml (2.3)
  include_vars:
    dir: vars
    ignore_files:
      - 'bastion.yaml'
    extensions:
      - 'yaml'

- name: Ignore warnings raised for files with unknown extensions while loading (2.7)
  include_vars:
    dir: vars
    ignore_unknown_extensions: True
    extensions:
      - ''
      - 'yaml'
      - 'yml'
      - 'json'
'''

RETURN = r'''
ansible_facts:
  description: Variables that were included and their values
  returned: success
  type: dict
  sample: {'variable': 'value'}
ansible_included_var_files:
  description: A list of files that were successfully included
  returned: success
  type: list
  sample: [ /path/to/file.json, /path/to/file.yaml ]
  version_added: '2.4'
'''
