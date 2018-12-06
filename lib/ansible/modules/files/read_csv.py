#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: read_csv
version_added: '2.8'
short_description: Read a CSV file
description:
- Read a CSV file and return a list or a dictionary, containing one dictionary per row.
author:
- Dag Wieers (@dagwieers)
options:
  path:
    description:
    - The CSV filename to read data from.
    type: str
    required: yes
    aliases: [ filename ]
  key:
    description:
    - The column name used as a key for the resulting dictionary.
    - If C(key) is unset, the module returns a list of dictionaries,
      where each dictionary is a row in the CSV file.
    type: str
  dialect:
    description:
    - The CSV dialect to use when parsing the CSV file.
    - Possible values include C(excel), C(excel-tab) or C(unix).
    type: str
    default: excel
  fieldnames:
    description:
    - A list of field names for every column.
    - This is needed if the CSV does not have a header.
    type: list
  unique:
    description:
    - Whether the C(key) used is expected to be unique.
    type: bool
    default: yes
'''

EXAMPLES = r'''
# Read a CSV file and access user 'dag'
- name: Read users from CSV file and return a dictionary
  read_csv:
    path: users.csv
    key: name
  register: users
  delegate_to: localhost

- debug:
    msg: 'User {{ users.dict.dag.name }} has UID {{ users.dict.dag.uid }} and GID {{ users.dict.dag.gid }}'

# Read a CSV file and access the first item
- name: Read users from CSV file and return a list
  read_csv:
    path: users.csv
  register: users
  delegate_to: localhost

- debug:
    msg: 'User {{ users.list.1.name }} has UID {{ users.list.1.uid }} and GID {{ users.list.1.gid }}'
'''

RETURN = r'''
dict:
  description: The CSV content as a dictionary.
  returned: success
  type: dict
  sample:
    dag:
      name: dag
      uid: 500
      gid: 500
    jeroen:
      name: jeroen
      uid: 501
      gid: 500
list:
  description: The CSV content as a list.
  returned: success
  type: list
  sample:
  - name: dag
    uid: 500
    gid: 500
  - name: jeroen
    uid: 501
    gid: 500
'''

import csv

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text


# Add Unix dialect from Python 3
class unix_dialect(csv.Dialect):
    """Describe the usual properties of Unix-generated CSV files."""
    delimiter = ','
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\n'
    quoting = csv.QUOTE_ALL


csv.register_dialect("unix", unix_dialect)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True, aliases=['filename']),
            dialect=dict(type='str', default='excel'),
            key=dict(type='str'),
            fieldnames=dict(type='list'),
            unique=dict(type='bool', default=True),
        ),
        supports_check_mode=True,
    )

    path = module.params['path']
    dialect = module.params['dialect']
    key = module.params['key']
    fieldnames = module.params['fieldnames']
    unique = module.params['unique']

    if dialect not in csv.list_dialects():
        module.fail_json(msg="Dialect '%s' is not supported by your version of python." % dialect)

    try:
        f = open(path, 'r')
    except (IOError, OSError) as e:
        module.fail_json(msg="Unable to open file '%s': %s" % (path, to_text(e)))

    reader = csv.DictReader(f, fieldnames=fieldnames, dialect=dialect)

    if key and key not in reader.fieldnames:
        module.fail_json(msg="Key '%s' was not found in the CSV header fields: %s" % (key, ', '.join(reader.fieldnames)))

    data_dict = dict()
    data_list = list()

    if key is None:
        for row in reader:
            data_list.append(row)
    else:
        for row in reader:
            if unique and row[key] in data_dict:
                module.fail_json(msg="Key '%s' is not unique for value '%s'" % (key, row[key]))
            data_dict[row[key]] = row

    module.exit_json(dict=data_dict, list=data_list)


if __name__ == '__main__':
    main()
