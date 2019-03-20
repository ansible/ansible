#!/usr/bin/python

# Copyright: (c) 2019, Virgil Chereches <virgil.chereches@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: validate

short_description: This module validate an Ansible variable against a JSON schema

version_added: "2.8"

description:
    - "This module uses JSON schema to validate data structure of an Ansibile variable; Schema may be provided in JSON or YAML format"

options:
    var:
        description:
            - This is the name of the Ansible variable
        required: true
    schema:
        description:
            - Schema file in JSON, YAML or plain (text) format
        required: true
notes:
    - 'This plugin uses JSONSchema python implementation (https://python-jsonschema.readthedocs.io/en/stable/)
       to validate variable data structure against schemas.'
    - 'Due to some bug in jsonschema python module there is not possible to use relative references and in file reference
       in the schema without a patch: https://github.com/Julian/jsonschema/issues/313#issuecomment-300478317.
       Since maintaining such a patch over the jsonschema library is out of discussion,
       the ansible plugin is not working with relative references.'

author:
    - Virgil Chereches (@brutus333)
'''

EXAMPLES = '''
# Pass in a variable and a schema dictionary
- name: Test with a variable
  validate:
    var: ansible_date_time
    schema: "{{ { 'type': 'object','properties': { 'date': { 'type':'string', 'format': 'date' } } } }}"

# Pass in a variable and a schema dictionary in yaml format
- name: Test with a variable
  validate:
    var: ansible_date_time
    schema:
      type: object
      properties:
        date:
          type: string
          format: date

# Pass in a variable and a schema file
# File ansible_ipv4_schema contains equivalent information in json or yaml format
- name: Test with a variable
  validate:
    var: ansible_ipv4
    schema: ansible_date_schema.json
'''

RETURN = '''
message:
    description: In case of failure return the reason for failure
    type: str
    returned: on error
'''
