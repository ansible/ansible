# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['stableinterface'],
    'supported_by': 'core'
}


DOCUMENTATION = '''
---
author: Allen Sanabria (@linuxdynasty)
module: include_vars
short_description: Load variables from files, dynamically within a task
description:
  - Loads variables from a YAML/JSON files dynamically from within a file or from a directory recursively during task
    runtime. If loading a directory, the files are sorted alphabetically before being loaded.
  - This module is also supported for Windows targets.
version_added: "1.4"
options:
  file:
    version_added: "2.2"
    description:
      - The file name from which variables should be loaded.
      - If the path is relative, it will look for the file in vars/ subdirectory of a role or relative to playbook.
  dir:
    version_added: "2.2"
    description:
      - The directory name from which the variables should be loaded.
      - If the path is relative, it will look for the file in vars/ subdirectory of a role or relative to playbook.
  name:
    version_added: "2.2"
    description:
      - The name of a variable into which assign the included vars. If omitted (null) they will be made top level vars.
  depth:
    version_added: "2.2"
    description:
      - When using C(dir), this module will, by default, recursively go through each sub directory and load up the
        variables. By explicitly setting the depth, this module will only go as deep as the depth.
    default: 0
  files_matching:
    version_added: "2.2"
    description:
      - Limit the files that are loaded within any directory to this regular expression.
  ignore_files:
    version_added: "2.2"
    description:
      - List of file names to ignore.
  extensions:
    version_added: "2.3"
    description:
      - List of file extensions to read when using C(dir).
    default: [yaml, yml, json]
  ignore_unknown_extensions:
    version_added: "2.7"
    description:
      - Ignore unknown file extensions within the directory. This allows users to specify a directory containing vars files
        that are intermingled with non vars files extension types (For example, a directory with a README in it and vars files)
    default: False
  free-form:
    description:
      - This module allows you to specify the 'file' option directly without any other options.
        There is no 'free-form' option, this is just an indicator, see example below.
notes:
  - This module is also supported for Windows targets.
'''

EXAMPLES = """
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
  include_vars: "{{ item }}"
  with_first_found:
    - "{{ ansible_distribution }}.yaml"
    - "{{ ansible_os_family }}.yaml"
    - default.yaml

- name: Bare include (free-form)
  include_vars: myvars.yaml

- name: Include all .json and .jsn files in vars/all and all nested directories (2.3)
  include_vars:
    dir: vars/all
    extensions:
        - json
        - jsn

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
    ignore_files: [bastion.yaml]
    extensions: [yaml]
"""

RETURN = '''
ansible_facts:
  description: Variables that were included and their values
  returned: success
  type: dict
  sample: {'variable': 'value'}
ansible_included_var_files:
  description: A list of files that were successfully included
  returned: success
  type: list
  sample: [ '/path/to/file.yaml', '/path/to/file.json' ]
  version_added: 2.4
'''
