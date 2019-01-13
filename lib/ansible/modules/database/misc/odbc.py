#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, John Westcott <john.westcott.iv@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: odbc
author: "John Westcott IV (@john-westcott-iv)"
version_added: "2.8"
short_description: Execute SQL via ODBC
description:
    - Read/Write info via ODBC
options:
    dsn:
      description:
        - The connection string passed into ODBC
      required: True
    query:
      description:
        - The SQL query to perform
      required: True
    params:
      description:
        - Parameters to pass to the SQL squery
      required: False

requirements:
  - "python >= 2.6"
  - "pyodbc"
'''

EXAMPLES = '''
- name: Set some values in the test db
  odbc:
    dsn: "DRIVER={ODBC Driver 13 for SQL Server};Server=db.ansible.com;Database=my_db;UID=admin;PWD=password;"
    query: "Select * from table_a where column1 = ?"
    params:
      - "value1"
'''

RETURN = '''
results:
    description: List of dicts containing selected rows, likley empty for DDL statements.
    returned: success
    type: list
description:
    description: "List of dicts about the columns selected from the cursors. See https://github.com/mkleehammer/pyodbc/wiki/Cursor"
    returned: success
    type: list
row_count:
    description: "The number of rows selected or modified according to the cursor. See https://github.com/mkleehammer/pyodbc/wiki/Cursor"
    returned: success
    type: str
'''

from ansible.module_utils.basic import AnsibleModule
HAS_PYODBC = None
try:
    import pyodbc
    HAS_PYODBC = True
except ImportError as e:
    HAS_PYODBC = False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            dsn=dict(type=str, required=True, no_log=True),
            query=dict(type=str, required=False),
            params=dict(type=list, required=False, default=None)
        ),
    )

    dsn = module.params.get('dsn')
    query = module.params.get('query')
    params = module.params.get('params')

    if not HAS_PYODBC:
        module.fail_json(msg='pyodbc python module must be installed to use this module')

    # Try to make a connection with the DSN
    connection = None
    try:
        connection = pyodbc.connect(dsn)
    except Exception as e:
        module.fail_json(msg='Failed to connect to DSN: {0}'.format(e))

    result = dict(
        changed=True,
    )

    try:
        cursor = connection.cursor()

        # Get the rows out into an 2d array
        result['results'] = []
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        cursor.commit()
        try:
            for row in cursor.fetchall():
                new_row = []
                for column in row:
                    new_row.append("{0}".format(column))
                result['results'].append(new_row)

            # Return additional information from the cursor
            result['description'] = []
            for row_description in cursor.description:
                description = {}
                description['name'] = row_description[0]
                description['type'] = row_description[1].__name__
                description['display_size'] = row_description[2]
                description['internal_size'] = row_description[3]
                description['precision'] = row_description[4]
                description['scale'] = row_description[5]
                description['nullable'] = row_description[6]
                result['description'].append(description)

            result['row_count'] = cursor.rowcount
        except pyodbc.ProgrammingError as pe:
            pass
        except Exception as e:
            module.fail_json(msg="Exception while reading rows: {0}".format(e))

        cursor.close()
    except Exception as e:
        module.fail_json(msg="Failed to execute query: {0}".format(e))
    finally:
        connection.close()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
