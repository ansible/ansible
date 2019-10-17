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
    type: path
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
  delimiter:
    description:
    - A one-character string used to separate fields.
    - When using this parameter, you change the default value used by C(dialect).
    - The default value depends on the dialect used.
    type: str
  skipinitialspace:
    description:
    - Whether to ignore any whitespaces immediately following the delimiter.
    - When using this parameter, you change the default value used by C(dialect).
    - The default value depends on the dialect used.
    type: bool
  strict:
    description:
    - Whether to raise an exception on bad CSV input.
    - When using this parameter, you change the default value used by C(dialect).
    - The default value depends on the dialect used.
    type: bool
notes:
- Ansible also ships with the C(csvfile) lookup plugin, which can be used to do selective lookups in CSV files from Jinja.
'''

EXAMPLES = r'''
# Example CSV file with header
#
#   name,uid,gid
#   dag,500,500
#   jeroen,501,500

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

# Example CSV file without header and semi-colon delimiter
#
#   dag;500;500
#   jeroen;501;500

# Read a CSV file without headers
- name: Read users from CSV file and return a list
  read_csv:
    path: users.csv
    fieldnames: name,uid,gid
    delimiter: ';'
  register: users
  delegate_to: localhost
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
from io import BytesIO, StringIO

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text
from ansible.module_utils.six import PY3


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
            delimiter=dict(type='str'),
            skipinitialspace=dict(type='bool'),
            strict=dict(type='bool'),
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

    dialect_options = dict(
        delimiter=module.params['delimiter'],
        skipinitialspace=module.params['skipinitialspace'],
        strict=module.params['strict'],
    )

    # Create a dictionary from only set options
    dialect_params = dict((k, v) for k, v in dialect_options.items() if v is not None)
    if dialect_params:
        try:
            csv.register_dialect('custom', dialect, **dialect_params)
        except TypeError as e:
            module.fail_json(msg="Unable to create custom dialect: %s" % to_text(e))
        dialect = 'custom'

    try:
        with open(path, 'rb') as f:
            data = f.read()
    except (IOError, OSError) as e:
        module.fail_json(msg="Unable to open file: %s" % to_text(e))

    if PY3:
        # Manually decode on Python3 so that we can use the surrogateescape error handler
        data = to_text(data, errors='surrogate_or_strict')
        fake_fh = StringIO(data)
    else:
        fake_fh = BytesIO(data)

    reader = csv.DictReader(fake_fh, fieldnames=fieldnames, dialect=dialect)

    if key and key not in reader.fieldnames:
        module.fail_json(msg="Key '%s' was not found in the CSV header fields: %s" % (key, ', '.join(reader.fieldnames)))

    data_dict = dict()
    data_list = list()

    if key is None:
        try:
            for row in reader:
                data_list.append(row)
        except csv.Error as e:
            module.fail_json(msg="Unable to process file: %s" % to_text(e))
    else:
        try:
            for row in reader:
                if unique and row[key] in data_dict:
                    module.fail_json(msg="Key '%s' is not unique for value '%s'" % (key, row[key]))
                data_dict[row[key]] = row
        except csv.Error as e:
            module.fail_json(msg="Unable to process file: %s" % to_text(e))

    module.exit_json(dict=data_dict, list=data_list)


if __name__ == '__main__':
    main()
